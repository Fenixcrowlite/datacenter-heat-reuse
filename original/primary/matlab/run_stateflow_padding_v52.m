function run_stateflow_padding_v52(folder)
% Build new saved model, reproduce original defects, execute repair and modes.
root=fileparts(fileparts(mfilename('fullpath')));here=fullfile(root,'matlab','simulink');
addpath(fullfile(root,'matlab'),here);spec=jsondecode(fileread(fullfile(folder,'spec.json')));
Simulink.fileGenControl('set','CacheFolder',fullfile(folder,'local_build','cache'), ...
    'CodeGenFolder',fullfile(folder,'local_build','codegen'),'createDir',true);
assert(license('test','Stateflow'));fprintf('MATLAB=%s STATEFLOW_LICENSE=%d\n',version,license('test','Stateflow'));
old=load(fullfile(root,spec.defect_evidence,'annual_sensitivity_v50.mat'));
defects=load(fullfile(root,spec.defect_evidence,'defect_evidence','defects_v50.mat'));
if ~isfile(fullfile(here,'DCHR_Dispatch_Stateflow_v52.slx')),build_dispatch_stateflow_v52();end
items=[];checks=struct('name',{},'passed',{});
for versionNumber=[42 52]
    mdl=sprintf('DCHR_Dispatch_Stateflow_v%d',versionNumber);load_system(fullfile(here,[mdl '.slx']));
    for j=1:numel(defects.items)
        d=defects.items(j);seed=d.candidate;a=old.report.stateflow(strcmp({old.report.stateflow.id},d.id));
        c=struct('id',[d.id '_exact_seed'],'p',a.p,'h',a.h,'c',a.c, ...
            'inputs',seed.input,'initial_energy_MWh',seed.initial_energy_MWh,'initial_clock',seed.initial_clock);
        result=sim(configure(mdl,c,versionNumber).setModelParameter('CaptureErrors','on'));
        save(fullfile(folder,sprintf('%s_v%d_simulation.mat',c.id,versionNumber)),'result','c','-v7.3');
        if versionNumber==42
            ok=contains(result.ErrorMessage,'Zero-span segment has service.');
            record([c.id '_v42_reproduced'],ok);
            evidence=struct('id',c.id,'version',42,'expected_rejection',true,'error_message',result.ErrorMessage);
        else
            record([c.id '_v52_repaired'],isempty(result.ErrorMessage));
            assert(isempty(result.ErrorMessage),result.ErrorMessage);
            evidence=inspect(result,c,versionNumber);
        end
        if isempty(items),items=evidence;else
            % Mixed old/new records are retained as JSON cells below.
            items(end+1).id=evidence.id;items(end).version=evidence.version;
            items(end).expected_rejection=false;items(end).error_message=evidence.error_message;
        end
        writejson(fullfile(folder,sprintf('%s_v%d_evidence.json',c.id,versionNumber)),evidence);
        fprintf('EXACT_SEED_V52 id=%s model=%d expected_result=%d\n',c.id,versionNumber,ok_or_empty(result,versionNumber));
    end
    close_system(mdl,0);
end
mdl='DCHR_Dispatch_Stateflow_v52';load_system(fullfile(here,[mdl '.slx']));
cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
fixtures=[];base=struct('id','','p',[.25 10 3 4 .9 .8 0 5 .2 20 2], ...
    'h',[8 .45 1.2 8 0 1 4 0 0],'c',[8 .25 .25 64], ...
    'inputs',[6 35 75 1 45],'initial_energy_MWh',1,'initial_clock',[1;0;0;0]);
ids={'zero_demand','hp_only','tes_charge','tes_discharge','boiler_limit','insufficient_heat'};
for j=1:6
    c=base;c.id=ids{j};
    if j==1,c.inputs(1)=0;c.inputs(4)=0;c.initial_energy_MWh=0;end
    if j==2,c.p(3)=0;c.initial_energy_MWh=0;end
    if j==4,c.inputs(1)=0;c.initial_energy_MWh=9;end
    if j==5,c.inputs(1)=0;c.inputs(4)=2;c.initial_energy_MWh=0;end
    if j==6,c.inputs(1)=0;c.inputs(4)=5;c.initial_energy_MWh=0;end
    result=sim(configure(mdl,c,52).setModelParameter('CaptureErrors','on'));
    save(fullfile(folder,[c.id '_fixture_simulation.mat']),'result','c','-v7.3');
    record([c.id '_executed'],isempty(result.ErrorMessage));assert(isempty(result.ErrorMessage),result.ErrorMessage);
    evidence=inspect(result,c,52);record([c.id '_mode'],evidence.dispatch(1)==j-1);
    cfg=default_config_v2();cfg.sim.dt_h=c.p(1);cfg.backup.max_heat_MW=c.p(11);
    cfg.storage.heat_capacity_MWh_per_K=c.p(9);cfg.storage.ambient_C=c.p(10);
    cfg.storage.max_temperature_C=c.p(10)+c.p(2)/c.p(9);
    cfg.storage.delivery_cutoff_C=c.p(10)+c.p(8)/c.p(9);
    cfg.storage.initial_temperature_C=c.p(10)+c.initial_energy_MWh/c.p(9);
    cfg.storage.charge_limit_MW=c.p(3);cfg.storage.discharge_limit_MW=c.p(4);
    cfg.storage.eta_charge=c.p(5);cfg.storage.eta_discharge=c.p(6);cfg.storage.continuous_loss_rate_per_h=c.p(7);
    cfg.hp.max_heat_output_MW=8;cfg.hp.carnot_efficiency=.45;cfg.hp.cop_min=1.2;cfg.hp.cop_max=8;
    cfg.hp.part_load_penalty=0;cfg.hp.poly_c0=4;cfg.hp.poly_c1=0;cfg.hp.poly_c2=0;cfg.model.hp_backend='lift_polynomial';
    input=array2table(c.inputs,'VariableNames',{'Source_Heat_MW','Source_C','Sink_C','Heat_Demand_MW','Delivery_C'});
    reference=dchr.simulate_dispatch_v30(cfg,input);
    evidence.reference=table2array(reference(:,1:25));
    shared=[1:21 23:25]; % v30 attempted request differs from OFF-latch request.
    delta=evidence.dispatch(:,shared)-evidence.reference(:,shared);delta(isnan(delta))=0;
    record([c.id '_independent_MATLAB_reference'],isequal(isnan(evidence.dispatch(:,shared)),isnan(evidence.reference(:,shared)))&&max(abs(delta),[],'all')<1e-9);
    if isempty(fixtures),fixtures=evidence;else,fixtures(end+1)=evidence;end %#ok<AGROW>
    fprintf('FIXTURE_V52 id=%s mode=%d\n',c.id,evidence.dispatch(1));
end
writejson(fullfile(folder,'fixtures_v52.json'),fixtures);
faultFolder=fullfile(folder,'faults');mkdir(faultFolder);
faults=run_stateflow_faults_v52(mdl,faultFolder,base);
record('actual_runtime_fault_rejections',all([faults.rejected]));writejson(fullfile(folder,'faults_v52.json'),faults);
writejson(fullfile(folder,'repair_assertions_v52.json'),checks);
fprintf('PADDING_REPAIR_V52 pass=%d fail=%d\n',sum([checks.passed]),sum(~[checks.passed]));
assert(all([checks.passed]),'Inspect v52 repair evidence.');
    function record(name,ok),checks(end+1)=struct('name',name,'passed',logical(ok));end
end
function evidence=inspect(result,c,v)
raw=samples(result.segment_trace_v52,1792);plan=samples(result.plan_trace_v52,1472);
z=reshape(raw(1,:),28,64)';s=reshape(plan(1,:),23,64)';d=samples(result.dispatch_trace_v52,25);
assert(all(z(:,4)>=0 & z(:,5)<=c.p(2)) && all(z(2:end,4)==z(1:end-1,5)));
assert(all(s(:,2)==z(:,4)) && d(end,8)==z(end,5));
padding=z(:,2)==0;assert(all(z(padding,1)==0)&&all(z(padding,4)==z(padding,5))&&all(z(padding,6:14)==0,'all')&&all(z(padding,17:21)==0,'all'));
evidence=struct('id',c.id,'version',v,'expected_rejection',false,'error_message',result.ErrorMessage, ...
    'case',c,'dispatch',d,'segments',z(z(:,2)>0,:),'plan',s(s(:,1)>0,:), ...
    'clock_start',samples(result.clock_start_trace_v52,4),'clock_end',samples(result.clock_end_trace_v52,4), ...
    'padding_slots',sum(padding),'exact_handoff',true,'strict_padding_identity',true, ...
    'endpoint_hex',{cellstr(num2hex(z(:,5)))},'start_hex',{cellstr(num2hex(z(:,4)))});
end
function s=configure(mdl,c,v)
dt=c.p(1);n=size(c.inputs,1);s=Simulink.SimulationInput(mdl);names={'dt','stop','input','p','h','E0','c','m0'};
values={dt,(n-1)*dt,[(0:n-1)'*dt c.inputs],c.p,c.h,c.initial_energy_MWh,c.c,reshape(c.initial_clock,4,1)};
for k=1:numel(names),s=s.setVariable(sprintf('dchr_%s_v%d',names{k},v),values{k},'Workspace',mdl);end
end
function ok=ok_or_empty(r,v)
ok=isempty(r.ErrorMessage);if v==42,ok=contains(r.ErrorMessage,'Zero-span segment has service.');end
end
function v=samples(ts,width)
n=numel(ts.Time);v=reshape(ts.Data,width,n)';
end
function writejson(path,value)
assert(~isfile(path));fid=fopen(path,'w');assert(fid>0);clean=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(value,PrettyPrint=true));
end
