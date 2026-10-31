function run_charge_regimes_v56(folder)
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'matlab'),fullfile(root,'matlab','simulink'));
assert(isfolder(folder)&&~isfile(fullfile(folder,'report.json')));
Simulink.fileGenControl('set','CacheFolder',fullfile(folder,'local_build','cache'), ...
    'CodeGenFolder',fullfile(folder,'local_build','codegen'),'createDir',true);
spec=jsondecode(fileread(fullfile(folder,'spec.json')));checks=struct('name',{},'passed',{});cases=cell(numel(spec.cases),1);
for j=1:numel(spec.cases)
    v=spec.cases(j);accepted=false;identifier='';descriptor=[];
    try,descriptor=dchr.components.charge_regime_events_v56(v.s,v.p,v.E,v.request);accepted=true;
    catch e,identifier=e.identifier;end
    record([v.id '_domain'],accepted==strcmp(v.expected,'ACCEPT')&& ...
        (accepted||startsWith(identifier,'DCHR:v54:')||startsWith(identifier,'DCHR:v55:')||startsWith(identifier,'DCHR:v56:')));
    cases{j}=struct('input',v,'accepted',accepted,'identifier',identifier,'descriptor',descriptor);
    if accepted
        r=descriptor;idx=r.limiter_index;limits=r.slope_per_h*v.E+r.intercept_MW;
        record([v.id '_limit'],limits(idx)==min(limits)&&limits(idx)>=0);
        record([v.id '_ODE'],abs(r.initial_velocity_MW-(v.p.eta_charge*limits(idx)-v.p.loss_rate_per_h*v.E))<1e-12);
        record([v.id '_not_certified'],~r.event_times_certified);
        if ~isempty(r.events)
            t=r.next_event_h;k=r.k_per_h;B=r.B_MW;
            if k==0,endpoint=v.E+B*t;else,endpoint=v.E*exp(k*t)+B*expm1(k*t)/k;end
            first=r.events([r.events.time_h]==t);
            record([v.id '_event_endpoint'],abs(endpoint-first(1).energy_MWh)<1e-9);
        end
    end
end
mdl='DCHR_Dispatch_Stateflow_v52';load_system(fullfile(root,'matlab','simulink',[mdl '.slx']));
cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
rt=sfroot;charts=[rt.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/Thermal_Dispatch']); ...
    rt.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/HP_Supervisor'])];
metadata=struct('matlab_version',version,'stateflow_license_test',license('test','Stateflow'), ...
    'stateflow_version',ver('stateflow'),'chart_count',numel(charts),'simulation_mode','normal');
record('actual_charts',metadata.stateflow_license_test==1&&numel(charts)==2);
base=struct('id','','p',[.25 10 3 4 .9 .8 0 5 .2 20 2], ...
    'h',[8 .45 1.2 8 0 1 4 0 0],'c',[8 .25 .25 64], ...
    'inputs',[6 35 75 1 45],'initial_energy_MWh',1,'initial_clock',[1;0;0;0]);
ids={'zero_demand','hp_only','tes_charge','tes_discharge','boiler_limit','insufficient_heat'};runs=cell(6,1);originals=runs;
for j=1:6
    c=base;c.id=ids{j};
    if j==1,c.inputs(1)=0;c.inputs(4)=0;c.initial_energy_MWh=0;end
    if j==2,c.p(3)=0;c.initial_energy_MWh=0;end
    if j==4,c.inputs(1)=0;c.initial_energy_MWh=9;end
    if j==5,c.inputs(1)=0;c.inputs(4)=2;c.initial_energy_MWh=0;end
    if j==6,c.inputs(1)=0;c.inputs(4)=5;c.initial_energy_MWh=0;end
    result=sim(configure(c).setModelParameter('CaptureErrors','on'));
    save(fullfile(folder,[c.id '_simulation.mat']),'result','c','-v7.3');
    record([c.id '_execution'],isempty(result.ErrorMessage));assert(isempty(result.ErrorMessage),result.ErrorMessage);
    z=reshape(samples(result.segment_trace_v52,1792),28,64)';q=reshape(samples(result.plan_trace_v52,1472),23,64)';
    dispatch=samples(result.dispatch_trace_v52,25);positive=z(:,2)>0;
    record([c.id '_mode'],dispatch(1)==j-1);
    record([c.id '_handoff'],all(z(1:63,5)==z(2:64,4))&&all(z(:,5)==q(:,23)));
    record([c.id '_bounds'],all(z(:,4:5)>=0,'all')&&all(z(:,4:5)<=c.p(2),'all')&&all(z(:,6:14)>=0,'all'));
    record([c.id '_closure'],all(abs(z(:,21))<1e-10));
    record([c.id '_padding'],all(z(~positive,4)==z(~positive,5))&&all(z(~positive,6:14)==0,'all')&&all(z(~positive,17:21)==0,'all'));
    cfg=default_config_v2();cfg.sim.dt_h=c.p(1);cfg.backup.max_heat_MW=c.p(11);
    cfg.storage.heat_capacity_MWh_per_K=c.p(9);cfg.storage.ambient_C=c.p(10);
    cfg.storage.max_temperature_C=c.p(10)+c.p(2)/c.p(9);cfg.storage.delivery_cutoff_C=c.p(10)+c.p(8)/c.p(9);
    cfg.storage.initial_temperature_C=c.p(10)+c.initial_energy_MWh/c.p(9);
    cfg.storage.charge_limit_MW=c.p(3);cfg.storage.discharge_limit_MW=c.p(4);
    cfg.storage.eta_charge=c.p(5);cfg.storage.eta_discharge=c.p(6);cfg.storage.continuous_loss_rate_per_h=c.p(7);
    cfg.hp.max_heat_output_MW=8;cfg.hp.carnot_efficiency=.45;cfg.hp.cop_min=1.2;cfg.hp.cop_max=8;
    cfg.hp.part_load_penalty=0;cfg.hp.poly_c0=4;cfg.hp.poly_c1=0;cfg.hp.poly_c2=0;cfg.model.hp_backend='lift_polynomial';
    input=array2table(c.inputs,'VariableNames',{'Source_Heat_MW','Source_C','Sink_C','Heat_Demand_MW','Delivery_C'});
    reference=table2array(dchr.simulate_dispatch_v30(cfg,input));shared=[1:21 23:25];
    delta=dispatch(:,shared)-reference(:,shared);delta(isnan(delta))=0;
    record([c.id '_reference'],isequal(isnan(dispatch(:,shared)),isnan(reference(:,shared)))&&max(abs(delta),[],'all')<1e-9);
    item=struct('id',c.id,'case',c,'dispatch',dispatch,'raw_segments',z,'raw_plans',q,'reference',reference(:,1:25));
    runs{j}=item;reopened=load(fullfile(folder,[c.id '_simulation.mat']));
    record([c.id '_MAT_binding'],isequaln(c,reopened.c)&&isequaln(result,reopened.result));
    item.case=reopened.c;item.dispatch=samples(reopened.result.dispatch_trace_v52,25);
    item.raw_segments=reshape(samples(reopened.result.segment_trace_v52,1792),28,64)';
    item.raw_plans=reshape(samples(reopened.result.plan_trace_v52,1472),23,64)';originals{j}=item;
end
% One actual saved-model domain fault, distinct from component rejections.
bad=base;bad.inputs(1)=-1;fault=sim(configure(bad).setModelParameter('CaptureErrors','on'));
save(fullfile(folder,'negative_source_fault.mat'),'fault','bad','-v7.3');
record('actual_negative_source_rejection',~isempty(fault.ErrorMessage)&&contains(fault.ErrorMessage,'Runtime physical-domain rejection'));
report=struct('version','0.56','model_version','0.52','new_model',false,'metadata',metadata, ...
    'cases',{cases},'runs',{runs},'runtime_fault_message',fault.ErrorMessage,'assertions',checks, ...
    'summary',struct('passed',sum([checks.passed]),'failed',sum(~[checks.passed])));
save(fullfile(folder,'charge_regimes_v56.mat'),'report','-v7.3');writejson('report.json',report);
reopened=load(fullfile(folder,'charge_regimes_v56.mat'));assert(isequaln(report,reopened.report));writejson('mat_reopen.json',reopened.report);
writejson('original_simulation_reopen.json',originals);
fprintf('CHARGE_REGIMES_V56 PASS=%d FAIL=%d\n',report.summary.passed,report.summary.failed);
assert(all([checks.passed]),'DCHR:v56:AcceptanceFailure','Inspect retained evidence.');
    function record(name,ok),checks(end+1)=struct('name',name,'passed',logical(ok));end
    function si=configure(c)
        si=Simulink.SimulationInput(mdl);names={'dt','stop','input','p','h','E0','c','m0'};
        values={c.p(1),0,[0 c.inputs],c.p,c.h,c.initial_energy_MWh,c.c,c.initial_clock};
        for jj=1:numel(names),si=si.setVariable(['dchr_' names{jj} '_v52'],values{jj},'Workspace',mdl);end
    end
    function writejson(name,value)
        path=fullfile(folder,name);assert(~isfile(path));fid=fopen(path,'w');assert(fid>0);closefile=onCleanup(@()fclose(fid)); %#ok<NASGU>
        fprintf(fid,'%s\n',jsonencode(value,PrettyPrint=true));
    end
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;
if ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;
elseif numel(raw)==n*width,v=reshape(raw,width,n)';else,error('DCHR:v56:TraceShape','Unexpected trace shape.');end
end
