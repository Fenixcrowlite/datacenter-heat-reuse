function run_annual_stateflow_v49(folder)
% Actual saved v42 execution; additive scenario adapter does not modify SLX.
root=fileparts(fileparts(mfilename('fullpath')));here=fullfile(root,'matlab','simulink');
addpath(fullfile(root,'matlab'),here);spec=jsondecode(fileread(fullfile(folder,'spec.json')));
checks=struct('name',{},'passed',{});cfg=default_config_v2();cfg.sim.hours=8760;cfg.backup.max_heat_MW=2;
input=dchr.make_inputs(cfg);policy=spec.policy;
% Demonstrate that a direct seasonal sink mapping cannot support this fixed tank.
badPolicy=policy;badPolicy.condenser_policy='scheduled';unsupported=dchr.adapt_annual_stateflow_v49(cfg,input,badPolicy);
writetable(unsupported.preflight,fullfile(folder,'scheduled_preflight.csv'));
record('scheduled_boundary_rejected',~unsupported.admissible&&any(~unsupported.preflight.Admissible));
a=dchr.adapt_annual_stateflow_v49(cfg,input,policy);writetable(a.preflight,fullfile(folder,'fixed_preflight.csv'));
writematrix(a.inputs,fullfile(folder,'annual_inputs.csv'));
record('8760_static_domain',a.admissible&&height(a.preflight)==8760);assert(a.admissible,'Fixed annual boundary not admissible.');
save(fullfile(folder,'adapter_v49.mat'),'a','unsupported','cfg','input','spec');
% Adapter mutation checks; row thermal faults must be visible in preflight.
faults=[];
for j=1:10
    pp=policy;cc=cfg;xx=input;kind='exception';id='';message='';rejected=false;
    switch j
        case 1,pp.delivery_cutoff_C=86;
        case 2,pp.restart_energy_MWh=0;
        case 3,pp.min_off_h=-1;
        case 4,pp.initial_clock=[1;0;0;1e-4];
        case 5,xx.time(2)=xx.time(1);
        case 6,xx.it_power_MW(1)=-1;
        case 7,cc.hp.part_load_penalty=1;kind='preflight';
        case 8,pp.condenser_C=54;kind='preflight';
        case 9,cc.dc.source_temp_C=100;kind='preflight';
        case 10,cc.storage.eta_charge=0;kind='preflight';
    end
    % Domain faults use three rows to avoid redundant full-year checks.
    fields=fieldnames(xx);for k=1:numel(fields),xx.(fields{k})=xx.(fields{k})(1:3);end
    try,b=dchr.adapt_annual_stateflow_v49(cc,xx,pp);rejected=strcmp(kind,'preflight')&&~b.admissible;
        if rejected,id=char(b.preflight.Error_ID(1));message=char(b.preflight.Message(1));end
    catch err,rejected=strcmp(kind,'exception');id=err.identifier;message=err.message;end
    faults=[faults;struct('index',j,'kind',kind,'rejected',rejected,'error_id',id,'message',message)]; %#ok<AGROW>
    record(sprintf('adapter_fault_%d',j),rejected);
end
work=fullfile(folder,'local_build');mkdir(work);
Simulink.fileGenControl('set','CacheFolder',fullfile(work,'cache'),'CodeGenFolder',fullfile(work,'codegen'),'createDir',true);
assert(license('test','Stateflow'),'Stateflow license unavailable');mdl='DCHR_Dispatch_Stateflow_v42';
load_system(fullfile(here,[mdl '.slx']));cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
rt=sfroot;ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/Thermal_Dispatch']);
metadata=struct('matlab_version',version,'products',ver,'stateflow_version',ver('Stateflow'), ...
    'stateflow_license_test',license('test','Stateflow'),'simulation_mode',get_param(mdl,'SimulationMode'), ...
    'thermal_states',{get(ch.find('-isa','Stateflow.State'),'Name')});
cases=spec.six_mode_cases;
for i=1:numel(cases),cases(i).c=[8 0 0 64];cases(i).initial_clock=[1;0;0;0];end
% A three-day cold sequence is the execution gate before extending to a year.
multi=cases(1);multi.id='cold_72h';multi.p=a.p;multi.h=a.h;multi.c=a.c;
multi.initial_energy_MWh=a.initial_energy_MWh;multi.initial_clock=a.initial_clock;multi.inputs=a.inputs(1:72,:);multi.expected_mode=-1;
cases(end+1)=multi;multi.id='annual_8760h';multi.inputs=a.inputs;cases(end+1)=multi;
stateflow=[];allModes=[];
for j=1:numel(cases)
    c=cases(j);p=c.p(:)';h=c.h(:)';x=c.inputs;n=size(x,1);
    s=Simulink.SimulationInput(mdl);names={'dt','stop','input','p','h','E0','c','m0'};
    values={p(1),(n-1)*p(1),[(0:n-1)'*p(1) x],p,h,c.initial_energy_MWh,c.c(:)',c.initial_clock(:)};
    for k=1:numel(names),s=s.setVariable(['dchr_' names{k} '_v42'],values{k},'Workspace',mdl);end
    timer=tic;result=sim(s.setModelParameter('CaptureErrors','on'));elapsed=toc(timer);
    save(fullfile(folder,[c.id '_simulation.mat']),'result','-v7.3');
    record([c.id '_executed'],isempty(result.ErrorMessage));assert(isempty(result.ErrorMessage),'%s',result.ErrorMessage);
    dispatch=samples(result.dispatch_trace_v42,25);raw=samples(result.segment_trace_v42,1792);
    startClock=samples(result.clock_start_trace_v42,4);endClock=samples(result.clock_end_trace_v42,4);
    chunks=cell(n,1);
    for i=1:n,z=reshape(raw(i,:),28,64)';pos=find(z(:,2)>0);chunks{i}=[repmat(i,numel(pos),1) pos z(pos,:)];end
    segments=vertcat(chunks{:});
    ports=array2table(dispatch(:,[18 2 3 4 5 6 19 20]),'VariableNames',spec.port_columns);
    ports=dchr.adapt_dispatch_energy_v46(ports,'explicit_actual_v45');reportCfg=cfg;reportCfg.sim.dt_h=p(1);
    m=dchr.compute_service_comparison_v46(reportCfg,ports);
    record([c.id '_samples'],size(dispatch,1)==n);record([c.id '_first_law'],max(abs(dispatch(:,13)))<1e-9);
    record([c.id '_inventory'],all(dispatch(:,8)>=0&dispatch(:,8)<=p(2)));
    record([c.id '_service'],abs(m.energy.heat_demand_MWh-m.energy.total_delivered_MWh-m.energy.unmet_heat_MWh)<1e-6);
    if c.expected_mode>=0,record([c.id '_mode'],dispatch(1)==c.expected_mode);end
    if strcmp(c.id,'annual_8760h')
        cold=readmatrix(fullfile(folder,'cold_72h_dispatch.csv'));
        delta=dispatch(1:72,:)-cold;delta(isnan(delta))=0;
        record('cold_prefix_equal',isequal(isnan(dispatch(1:72,:)),isnan(cold))&&max(abs(delta),[],'all')<1e-12);
        record('annual_exact_hours',m.energy.reported_period_h==8760);
    end
    allModes=[allModes;segments(:,3)]; %#ok<AGROW>
    writetable(ports,fullfile(folder,[c.id '_ports.csv']));writematrix(dispatch,fullfile(folder,[c.id '_dispatch.csv']));
    writematrix(segments,fullfile(folder,[c.id '_segments.csv']));writematrix(startClock,fullfile(folder,[c.id '_clock_start.csv']));
    writematrix(endClock,fullfile(folder,[c.id '_clock_end.csv']));
    item=struct('id',c.id,'case',c,'intervals',n,'positive_segments',size(segments,1),'elapsed_seconds',elapsed, ...
        'report',m,'error_message',result.ErrorMessage);
    if isempty(stateflow),stateflow=item;else,stateflow(end+1)=item;end %#ok<AGROW>
    fprintf('ACTUAL_STATEFLOW_V49 id=%s intervals=%d segments=%d seconds=%.3f unmet=%.16g\n',c.id,n,size(segments,1),elapsed,m.energy.unmet_heat_MWh);
    assert(all([checks.passed]),'DCHR:v49:ExecutionGate','Do not extend after failed acceptance.');
end
record('all_six_modes',isequal(unique(allModes),(0:5)'));
% Same synthetic fixed 85C condenser/source boundary; TES/control policies differ.
pairedCfg=cfg;pairedCfg.dh.supply_min_C=policy.condenser_C;pairedCfg.dh.supply_max_C=policy.condenser_C;
paired=dchr.simulate_system_v48(pairedCfg,input);pairedPorts=dchr.adapt_dispatch_energy_v46(paired,'explicit_actual_v45');
pairedReport=dchr.compute_service_comparison_v46(pairedCfg,pairedPorts);
writetable(paired,fullfile(folder,'paired_loss_first_v48.csv'));writetable(pairedPorts,fullfile(folder,'paired_loss_first_ports.csv'));
save(fullfile(folder,'paired_loss_first_v48.mat'),'paired','pairedPorts','pairedCfg','pairedReport');
summary=struct('version','0.49','model_version','0.42','new_model',false,'annual_stateflow_executed',true, ...
    'annual_intervals',8760,'saved_intervals',sum([stateflow.intervals]),'positive_segments',sum([stateflow.positive_segments]), ...
    'harness_passed',sum([checks.passed]),'harness_failed',sum(~[checks.passed]), ...
    'scheduled_rejected_rows',sum(~unsupported.preflight.Admissible),'fixed_admitted_rows',sum(a.preflight.Admissible));
report=struct('metadata',metadata,'cfg',cfg,'policy',policy,'stateflow',stateflow,'paired_cfg',pairedCfg, ...
    'paired_report',pairedReport,'faults',faults,'assertions',checks,'summary',summary);
save(fullfile(folder,'annual_stateflow_v49.mat'),'report','spec');writejson(fullfile(folder,'annual_stateflow_v49.json'),report);
fprintf('ANNUAL_STATEFLOW_V49 pass=%d fail=%d saved_intervals=%d\n',summary.harness_passed,summary.harness_failed,summary.saved_intervals);
assert(all([checks.passed]),'DCHR:v49:Failure','Inspect retained evidence.');
    function record(name,ok),checks(end+1)=struct('name',name,'passed',logical(ok));end
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;if ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;
elseif numel(raw)==n*width,v=reshape(raw,width,n)';else,error('Unexpected trace dimensions.');end
end
function writejson(path,value)
assert(~isfile(path));fid=fopen(path,'w');assert(fid>0);cleanup=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(value,PrettyPrint=true));
end
