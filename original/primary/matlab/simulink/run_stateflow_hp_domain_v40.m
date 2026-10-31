function folder=run_stateflow_hp_domain_v40(specDirectory)
% Execute saved v40 HP repair, all six modes, references and actual faults.
here=fileparts(mfilename('fullpath'));root=fileparts(fileparts(here));addpath(fullfile(root,'matlab'),here);
spec=jsondecode(fileread(fullfile(specDirectory,'cases.json')));cases=spec.cases;
if ~iscell(cases),cases=num2cell(cases);end
stamp=char(datetime('now','TimeZone','UTC','Format','yyyyMMdd''T''HHmmssSSS''Z'''));
folder=fullfile(root,'results',['stateflow_hp_domain_v40_' stamp]);assert(~isfolder(folder));mkdir(folder);
snap=fullfile(folder,'source_snapshot');mkdir(snap);copyfile(specDirectory,fullfile(snap,'spec'));
for pattern={'*v40.m','DCHR_Dispatch_Stateflow_v40.slx','stateflow_time_tolerance_v36.m','run_stateflow_hp_domain_v40.m'}
    paths=dir(fullfile(here,pattern{1}));for k=1:numel(paths),copyfile(fullfile(paths(k).folder,paths(k).name),snap);end
end
for f={'heat_pump_step_v40.m','storage_step_v30.m','storage_kernel_v30.m','storage_parameters_v30.m'}
    copyfile(fullfile(root,'matlab','+dchr','+components',f{1}),snap);
end
for f={'stateflow_hp_domain_v40.py','stateflow_reference_v34.py','stateflow_reference_v32.py','stateflow_reference_v30.py'}
    copyfile(fullfile(root,'audit',f{1}),snap);
end
work=fullfile(folder,'local_build');mkdir(work);
Simulink.fileGenControl('set','CacheFolder',fullfile(work,'cache'),'CodeGenFolder',fullfile(work,'codegen'),'createDir',true);
mdl='DCHR_Dispatch_Stateflow_v40';load_system(fullfile(here,[mdl '.slx']));cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
assert(license('test','Stateflow'),'Stateflow license unavailable');
rt=sfroot;ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/Thermal_Dispatch']);
hc=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/HP_Supervisor']);
states=ch.find('-isa','Stateflow.State');hstates=hc.find('-isa','Stateflow.State');
metadata=struct('matlab_version',version,'product_versions',ver,'stateflow_version',ver('Stateflow'), ...
    'stateflow_license_test',license('test','Stateflow'),'thermal_state_names',{get(states,'Name')}, ...
    'supervisor_state_names',{get(hstates,'Name')},'simulation_mode',get_param(mdl,'SimulationMode'));
writejson(fullfile(folder,'metadata_v40.json'),metadata);
checks=struct('name',{},'passed',{});outputs=[];
for j=1:numel(cases)
    c=cases{j};dt=c.p(1);n=size(c.inputs,1);s=Simulink.SimulationInput(mdl);
    names={'dt','stop','input','p','h','E0','c','m0'};
    values={dt,(n-1)*dt,[(0:n-1)'*dt c.inputs],reshape(c.p,1,[]),reshape(c.h,1,[]), ...
        c.initial_energy_MWh,reshape(c.c,1,[]),c.initial_clock(:)};
    for k=1:numel(names),s=s.setVariable(['dchr_' names{k} '_v40'],values{k},'Workspace',mdl);end
    result=sim(s.setModelParameter('CaptureErrors','on')); %#ok<NASGU>
    save(fullfile(folder,[c.id '_simulation.mat']),'result');
    rejected=~isempty(result.ErrorMessage);
    record([c.id '_completed'],~rejected);
    item=struct('id',c.id,'rejected',rejected,'error_message',result.ErrorMessage,'dispatch',[], ...
        'clock_start',[],'clock_end',[],'energy_start',[],'sample_time_h',[],'segments',[]);
    if ~rejected
        item.dispatch=samples(result.dispatch_trace_v40,25);
        item.clock_start=samples(result.clock_start_trace_v40,4);item.clock_end=samples(result.clock_end_trace_v40,4);
        item.energy_start=samples(result.energy_start_trace_v40,1);item.sample_time_h=result.dispatch_trace_v40.Time;
        raw=samples(result.segment_trace_v40,1792);plan=samples(result.plan_trace_v40,1408);
        for i=1:size(raw,1)
            z=reshape(raw(i,:),28,64)';ss=reshape(plan(i,:),22,64)';
            for k=1:64
                if z(k,2)>0,item.segments(end+1,:)=[i-1 k z(k,:) ss(k,:)];end %#ok<AGROW>
            end
        end
        record([c.id '_sample_count'],size(item.dispatch,1)==n);
    end
    if isempty(outputs),outputs=item;else,outputs(end+1)=item;end %#ok<AGROW>
    fprintf('EXECUTED=%s rejected=%d\n',c.id,rejected);
end
writejson(fullfile(folder,'execution_v40.json'),outputs);
probes=struct('id',{},'rejected',{},'error_identifier',{},'error_message',{},'output',{});
hpCases=spec.hp_probes;if ~iscell(hpCases),hpCases=num2cell(hpCases);end
for j=1:numel(hpCases)
    q=hpCases{j};cfg.hp=struct('max_heat_output_MW',q.cap_MW,'carnot_efficiency',.45, ...
        'cop_min',q.cop_min,'cop_max',8.,'part_load_penalty',q.penalty,'poly_c0',4.,'poly_c1',0.,'poly_c2',0.);
    if isfield(q,'nominal_cop'),cfg.hp.poly_c0=q.nominal_cop;end
    cfg.model.hp_backend='lift_polynomial';rejected=false;eid='';message='';hp=[];
    try,hp=dchr.components.heat_pump_step_v40(q.source_MW,35,75,q.request_MW,cfg);
    catch err,rejected=true;eid=err.identifier;message=err.message;end
    probes(end+1)=struct('id',q.id,'rejected',rejected,'error_identifier',eid,'error_message',message,'output',hp); %#ok<AGROW>
    expectedReject=false;if isfield(q,'expected_reject'),expectedReject=q.expected_reject;end
    record([q.id '_expected_domain'],rejected==expectedReject);
    if expectedReject,record([q.id '_resolution_diagnostic'],strcmp(eid,'DCHR:v40:HPResolution'));end
end
save(fullfile(folder,'hp_components.mat'),'probes');writejson(fullfile(folder,'hp_components_v40.json'),probes);
faults=run_stateflow_faults_v40(mdl,folder,cases{1});
writejson(fullfile(folder,'runtime_faults_v40.json'),faults);
record('30_actual_runtime_rejections',numel(faults)==30 && all([faults.rejected]));
writejson(fullfile(folder,'assertions_v40.json'),checks);
summary=struct('version','0.40','model_version','0.40','new_model',true,'scenarios',numel(outputs), ...
    'completed_scenarios',sum(~[outputs.rejected]),'intervals',sum(arrayfun(@(a)size(a.dispatch,1),outputs)), ...
    'positive_segments',sum(arrayfun(@(a)size(a.segments,1),outputs)), ...
    'harness_passed',sum([checks.passed]),'harness_failed',sum(~[checks.passed]),'hp_probes',numel(probes), ...
    'runtime_faults',numel(faults),'note','Independent analytic comparisons must also pass before scoped acceptance.');
writejson(fullfile(folder,'summary_v40.json'),summary);disp(summary);
fprintf('AUDIT_OUTPUT=%s\n',folder);assert(all([checks.passed]),'DCHR:v40:ExecutionFailed','See preserved evidence.');
    function record(name,ok)
        checks(end+1)=struct('name',name,'passed',logical(ok));if ~ok,fprintf(2,'FAIL=%s\n',name);end
    end
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;
if ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;
elseif numel(raw)==n*width,v=reshape(raw,width,n)';
else,error('DCHR:v40:Shape','Unexpected trace dimensions.');end
end
function writejson(path,v)
assert(~isfile(path));fid=fopen(path,'w');assert(fid>0);clean=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(v,PrettyPrint=true));
end
