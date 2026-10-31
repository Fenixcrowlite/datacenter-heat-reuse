function folder=run_stateflow_clock_v42(specDirectory)
% Fresh execution of saved uncertainty-aware v42 with clock uncertainty/event-tie seeds.
here=fileparts(mfilename('fullpath'));root=fileparts(fileparts(here));addpath(fullfile(root,'matlab'),here);
spec=jsondecode(fileread(fullfile(specDirectory,'cases.json')));cases=spec.cases;
if ~iscell(cases),cases=num2cell(cases);end
stamp=char(datetime('now','TimeZone','UTC','Format','yyyyMMdd''T''HHmmssSSS''Z'''));
folder=fullfile(root,'results',['stateflow_clock_v42_' stamp]);assert(~isfolder(folder));mkdir(folder);
snap=fullfile(folder,'source_snapshot');mkdir(snap);copyfile(specDirectory,fullfile(snap,'spec'));
for pattern={'*v42.m','DCHR_Dispatch_Stateflow_v42.slx','stateflow_time_tolerance_v36.m','*clock*v42.m'}
    paths=dir(fullfile(here,pattern{1}));for k=1:numel(paths),copyfile(fullfile(paths(k).folder,paths(k).name),snap);end
end
for f={'heat_pump_step_v40.m','storage_step_v30.m','storage_kernel_v30.m','storage_parameters_v30.m'}
    copyfile(fullfile(root,'matlab','+dchr','+components',f{1}),snap);
end
work=fullfile(folder,'local_build');mkdir(work);
Simulink.fileGenControl('set','CacheFolder',fullfile(work,'cache'),'CodeGenFolder',fullfile(work,'codegen'),'createDir',true);
mdl='DCHR_Dispatch_Stateflow_v42';load_system(fullfile(here,[mdl '.slx']));cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
assert(license('test','Stateflow'),'Stateflow license unavailable');rt=sfroot;
ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/Thermal_Dispatch']);
hc=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/HP_Supervisor']);
metadata=struct('matlab_version',version,'product_versions',ver,'stateflow_version',ver('Stateflow'), ...
    'stateflow_license_test',license('test','Stateflow'),'thermal_state_names',{get(ch.find('-isa','Stateflow.State'),'Name')}, ...
    'supervisor_state_names',{get(hc.find('-isa','Stateflow.State'),'Name')},'simulation_mode',get_param(mdl,'SimulationMode'));
writejson(fullfile(folder,'metadata_v42.json'),metadata);
outputs=[];checks=struct('name',{},'passed',{});
for j=1:numel(cases)
    c=cases{j};dt=c.p(1);n=size(c.inputs,1);s=Simulink.SimulationInput(mdl);
    names={'dt','stop','input','p','h','E0','c','m0'};
    values={dt,(n-1)*dt,[(0:n-1)'*dt c.inputs],reshape(c.p,1,[]),reshape(c.h,1,[]), ...
        c.initial_energy_MWh,reshape(c.c,1,[]),c.initial_clock(:)};
    for k=1:numel(names),s=s.setVariable(['dchr_' names{k} '_v42'],values{k},'Workspace',mdl);end
    result=sim(s.setModelParameter('CaptureErrors','on'));save(fullfile(folder,[c.id '_simulation.mat']),'result');
    item=struct('id',c.id,'rejected',~isempty(result.ErrorMessage),'error_message',result.ErrorMessage, ...
        'dispatch',[],'clock_start',[],'clock_end',[],'energy_start',[],'sample_time_h',[],'segments',[]);
    record([c.id '_expected_execution'],item.rejected==c.expected_reject);
    if ~item.rejected
        item.dispatch=samples(result.dispatch_trace_v42,25);item.clock_start=samples(result.clock_start_trace_v42,4);
        item.clock_end=samples(result.clock_end_trace_v42,4);item.energy_start=samples(result.energy_start_trace_v42,1);
        item.sample_time_h=result.dispatch_trace_v42.Time;
        raw=samples(result.segment_trace_v42,1792);plan=samples(result.plan_trace_v42,1408);
        for i=1:size(raw,1)
            z=reshape(raw(i,:),28,64)';ss=reshape(plan(i,:),22,64)';
            for k=1:64
                if z(k,2)>0,item.segments(end+1,:)=[i-1 k z(k,:) ss(k,:)];end %#ok<AGROW>
            end
        end
        record([c.id '_samples'],size(item.dispatch,1)==n);
    end
    if isempty(outputs),outputs=item;else,outputs(end+1)=item;end %#ok<AGROW>
    fprintf('EXECUTED=%s rejected=%d\n',c.id,item.rejected);
end
faults=run_stateflow_faults_v42(mdl,folder,cases{1});
writejson(fullfile(folder,'faults_v42.json'),faults);
record('actual_runtime_fault_rejections',all([faults.rejected]));
writejson(fullfile(folder,'execution_v42.json'),outputs);writejson(fullfile(folder,'assertions_v42.json'),checks);
summary=struct('version','0.42','model_version','0.42','new_model',true,'scenarios',numel(outputs), ...
    'completed_scenarios',sum(~[outputs.rejected]),'intervals',sum(arrayfun(@(a)size(a.dispatch,1),outputs)), ...
    'positive_segments',sum(arrayfun(@(a)size(a.segments,1),outputs)), ...
    'harness_passed',sum([checks.passed]),'harness_failed',sum(~[checks.passed]));
writejson(fullfile(folder,'summary_v42.json'),summary);disp(summary);fprintf('AUDIT_OUTPUT=%s\n',folder);
assert(all([checks.passed]),'DCHR:v42:ExecutionFailed','See preserved evidence.');
    function record(name,ok)
        checks(end+1)=struct('name',name,'passed',logical(ok));
    end
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;
if ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;
elseif numel(raw)==n*width,v=reshape(raw,width,n)';else,error('Unexpected trace dimensions.');end
end
function writejson(path,v)
assert(~isfile(path));fid=fopen(path,'w');assert(fid>0);clean=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(v,PrettyPrint=true));
end
