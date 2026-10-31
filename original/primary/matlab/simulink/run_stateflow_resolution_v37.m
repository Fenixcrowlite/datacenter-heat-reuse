function folder=run_stateflow_resolution_v37(specDirectory)
% Fresh preserved v36 execution. Domain failures are evidence, not repairs.
here=fileparts(mfilename('fullpath'));root=fileparts(fileparts(here));addpath(fullfile(root,'matlab'),here);
spec=jsondecode(fileread(fullfile(specDirectory,'cases.json')));cases=spec.cases;
if ~iscell(cases),cases=num2cell(cases);end
stamp=char(datetime('now','TimeZone','UTC','Format','yyyyMMdd''T''HHmmssSSS''Z'''));
folder=fullfile(root,'results',['stateflow_resolution_v37_' stamp]);assert(~isfolder(folder));mkdir(folder);
snap=fullfile(folder,'source_snapshot');mkdir(snap);copyfile(specDirectory,fullfile(snap,'spec'));
for pattern={'*v36.m','DCHR_Dispatch_Stateflow_v36.slx','dchr_stateflow_hp_v30.m','*resolution_v37.m'}
    paths=dir(fullfile(here,pattern{1}));for k=1:numel(paths),copyfile(fullfile(paths(k).folder,paths(k).name),snap);end
end
for f={'heat_pump_step_v14.m','storage_step_v30.m','storage_kernel_v30.m','storage_parameters_v30.m'}
    copyfile(fullfile(root,'matlab','+dchr','+components',f{1}),snap);
end
for f={'stateflow_resolution_v37.py','verify_stateflow_resolution_v37.py','stateflow_reference_v34.py','stateflow_reference_v32.py','stateflow_reference_v30.py'}
    copyfile(fullfile(root,'audit',f{1}),snap);
end
mdl='DCHR_Dispatch_Stateflow_v36';load_system(fullfile(here,[mdl '.slx']));
cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
out=struct('id',{},'kind',{},'rejected',{},'error_message',{},'phase',{},'time_h',{},'dispatch',{},'clock_start',{},'clock_end',{},'energy_start',{},'sample_time_h',{});
for j=1:numel(cases)
    c=cases{j};s=configure(mdl,c);result=sim(s.setModelParameter('CaptureErrors','on'));
    save(fullfile(folder,[c.id '_simulation.mat']),'result');
    item=extract(result,c.id,c.kind);out(end+1)=item; %#ok<AGROW>
    fprintf('EXECUTED=%s rejected=%d samples=%d phase=%s\n',c.id,item.rejected,size(item.dispatch,1),item.phase);
end
writejson(fullfile(folder,'execution_v37.json'),out);
probes=struct('id',{},'rejected',{},'error_identifier',{},'error_message',{},'output',{});
for j=1:numel(spec.hp_probes)
    q=spec.hp_probes(j);cfg.hp=struct('max_heat_output_MW',q.cap_MW,'carnot_efficiency',.45, ...
        'cop_min',1.2,'cop_max',8.,'part_load_penalty',.3,'poly_c0',4.,'poly_c1',0.,'poly_c2',0.);
    cfg.model.hp_backend='lift_polynomial';rejected=false;eid='';message='';hp=[];
    try,hp=dchr.components.heat_pump_step_v14(q.source_MW,35,75,q.request_MW,cfg);
    catch err,rejected=true;eid=err.identifier;message=err.message;end
    probes(end+1)=struct('id',q.id,'rejected',rejected,'error_identifier',eid,'error_message',message,'output',hp); %#ok<AGROW>
    fprintf('HP_COMPONENT=%s rejected=%d\n',q.id,rejected);
end
save(fullfile(folder,'hp_components.mat'),'probes');writejson(fullfile(folder,'hp_components_v37.json'),probes);
checks=struct('name',{},'passed',{});
record('baseline_execution',all(~[out(1:6).rejected]));
allModes=[];for j=1:6,allModes=[allModes;out(j).dispatch(:,1)];end %#ok<AGROW>
record('six_modes',isequal(unique(allModes)',(0:5)));
record('all_scenarios_recorded',numel(out)==numel(cases));
writejson(fullfile(folder,'assertions_v37.json'),checks);
summary=struct('version','0.37','model_version','0.36','matlab_version',version,'stateflow_version',ver('Stateflow'), ...
    'timestamp_utc',stamp,'scenarios',numel(out),'completed',sum(~[out.rejected]),'rejected',sum([out.rejected]), ...
    'harness_passed',sum([checks.passed]),'harness_failed',sum(~[checks.passed]),'conclusion','Saved-model numerical domain audit, independent QA required', ...
    'physical_validation',false,'article_replication',false);
writejson(fullfile(folder,'summary_v37.json'),summary);disp(summary);
fprintf('AUDIT_OUTPUT=%s\n',folder);assert(all([checks.passed]),'DCHR:v37:HarnessFailed','See evidence.');
    function record(name,ok)
        checks(end+1)=struct('name',name,'passed',logical(ok));
    end
end
function s=configure(mdl,c)
dt=c.p(1);n=size(c.inputs,1);s=Simulink.SimulationInput(mdl);
names={'dt','stop','input','p','h','E0','c','m0'};
values={dt,(n-1)*dt,[(0:n-1)'*dt c.inputs],reshape(c.p,1,[]),reshape(c.h,1,[]),c.initial_energy_MWh,reshape(c.c,1,[]),reshape(c.initial_clock,2,1)};
for k=1:numel(names),s=s.setVariable(['dchr_' names{k} '_v36'],values{k},'Workspace',mdl);end
end
function item=extract(r,id,kind)
d=r.SimulationMetadata.ExecutionInfo.ErrorDiagnostic;phase='';time=[];
if ~isempty(d),phase=d.SimulationPhase;time=d.SimulationTime;end
item=struct('id',id,'kind',kind,'rejected',~isempty(r.ErrorMessage),'error_message',r.ErrorMessage, ...
    'phase',phase,'time_h',time,'dispatch',[],'clock_start',[],'clock_end',[],'energy_start',[],'sample_time_h',[]);
if isempty(r.ErrorMessage)
    item.dispatch=samples(r.dispatch_trace_v36,25);item.clock_start=samples(r.clock_start_trace_v36,2);
    item.clock_end=samples(r.clock_end_trace_v36,2);item.energy_start=samples(r.energy_start_trace_v36,1);
    item.sample_time_h=r.dispatch_trace_v36.Time;
end
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;
if ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;
elseif numel(raw)==n*width,v=reshape(raw,width,n)';
else,error('DCHR:v37:Shape','Unexpected trace dimensions.');end
end
function writejson(path,v)
fid=fopen(path,'w');assert(fid>0);clean=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(v,PrettyPrint=true)); %#ok<NASGU>
end
