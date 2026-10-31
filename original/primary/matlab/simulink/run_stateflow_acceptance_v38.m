function folder=run_stateflow_acceptance_v38(specDirectory)
% Execute saved v38, independent references, fresh v36 comparisons and faults.
here=fileparts(mfilename('fullpath'));root=fileparts(fileparts(here));addpath(fullfile(root,'matlab'),here);
spec=jsondecode(fileread(fullfile(specDirectory,'cases.json')));cases=spec.cases;
if ~iscell(cases),cases=num2cell(cases);end
stamp=char(datetime('now','TimeZone','UTC','Format','yyyyMMdd''T''HHmmssSSS''Z'''));
folder=fullfile(root,'results',['stateflow_v38_' stamp]);assert(~isfolder(folder));mkdir(folder);
snap=fullfile(folder,'source_snapshot');mkdir(snap);copyfile(specDirectory,fullfile(snap,'spec'));
for pattern={'*v38.m','DCHR_Dispatch_Stateflow_v38.slx','stateflow_time_tolerance_v36.m'}
    paths=dir(fullfile(here,pattern{1}));for k=1:numel(paths),copyfile(fullfile(paths(k).folder,paths(k).name),snap);end
end
for f={'heat_pump_step_v38.m','storage_step_v30.m','storage_kernel_v30.m','storage_parameters_v30.m'}
    copyfile(fullfile(root,'matlab','+dchr','+components',f{1}),snap);
end
for f={'stateflow_specification_v38.py','stateflow_reference_v34.py','stateflow_reference_v32.py','stateflow_reference_v30.py'}
    copyfile(fullfile(root,'audit',f{1}),snap);
end
mdl='DCHR_Dispatch_Stateflow_v38';load_system(fullfile(here,[mdl '.slx']));
old='DCHR_Dispatch_Stateflow_v36';load_system(fullfile(here,[old '.slx']));
cleanup=onCleanup(@()closeModels()); %#ok<NASGU>
vectors=readtable(fullfile(specDirectory,'vectors.csv'),'TextType','string');
checks=struct('name',{},'passed',{});out=[];allModes=[];comparisons=[];
for j=1:numel(cases)
    c=cases{j};s=configure(mdl,c,'v38');result=sim(s.setModelParameter('CaptureErrors','on'));
    save(fullfile(folder,[c.id '_simulation.mat']),'result');item=extract(result,c.id);
    if isempty(out),out=item;else,out(end+1)=item;end %#ok<AGROW>
    record([c.id '_expected_runtime_domain'],item.rejected==c.expected_reject);
    if ~item.rejected
        allModes=[allModes;item.dispatch(:,1)]; %#ok<AGROW>
        record([c.id '_sample_count'],size(item.dispatch,1)==size(c.inputs,1));
        expected=vectors(vectors.scenario_id==string(c.id),:);
        if ~isempty(expected)
            for k=3:width(expected)
                record([c.id '_' expected.Properties.VariableNames{k}],near(item.dispatch(:,k-2),expected{:,k}));
            end
        end
        if j<=6 || ismember(c.id,{'source_demand_changes','source_limited','physical_off_dwell','capacity_on_dwell'})
            os=configure(old,c,'v36');oldresult=sim(os); %#ok<NASGU>
            save(fullfile(folder,[c.id '_v36_comparison.mat']),'oldresult');
            y=samples(oldresult.dispatch_trace_v36,25);
            record([c.id '_fresh_v36_reference'],near(item.dispatch,y));
            comparisons=[comparisons;struct('id',c.id,'old_dispatch',y,'new_dispatch',item.dispatch)]; %#ok<AGROW>
        end
    else
        record([c.id '_reject_during_execution'],strcmp(item.phase,'Execution'));
        if ismember(c.kind,{'band','cutoff_band'})
            record([c.id '_band_diagnostic'],contains(item.error_message,'Unresolved capacity/restart/cutoff'));
        end
    end
    fprintf('EXECUTED=%s rejected=%d intervals=%d\n',c.id,item.rejected,size(item.dispatch,1));
end
writejson(fullfile(folder,'execution_v38.json'),out);writejson(fullfile(folder,'comparison_v36.json'),comparisons);
probes=struct('id',{},'rejected',{},'error_identifier',{},'error_message',{},'output',{});
for j=1:numel(spec.hp_probes)
    q=spec.hp_probes(j);cfg.hp=struct('max_heat_output_MW',q.cap_MW,'carnot_efficiency',.45, ...
        'cop_min',q.cop_min,'cop_max',8.,'part_load_penalty',q.penalty,'poly_c0',4.,'poly_c1',0.,'poly_c2',0.);
    cfg.model.hp_backend='lift_polynomial';rejected=false;eid='';message='';hp=[];
    try,hp=dchr.components.heat_pump_step_v38(q.source_MW,35,75,q.request_MW,cfg);
    catch err,rejected=true;eid=err.identifier;message=err.message;end
    probes(end+1)=struct('id',q.id,'rejected',rejected,'error_identifier',eid,'error_message',message,'output',hp); %#ok<AGROW>
    record([q.id '_expected_domain'],rejected==q.expected_reject);
    if ~rejected
        record([q.id '_finite_flows'],all(isfinite([hp.heat_output_MW hp.electric_MW hp.source_used_MW])));
        record([q.id '_finite_operating_COP'],~hp.available || isfinite(hp.cop_operating));
    end
end
save(fullfile(folder,'hp_components.mat'),'probes');writejson(fullfile(folder,'hp_components_v38.json'),probes);
faults=run_stateflow_faults_v38(mdl,folder,cases{1});writejson(fullfile(folder,'runtime_faults_v38.json'),faults);
record('30_actual_runtime_rejections',numel(faults)==30 && all([faults.rejected]));
record('six_modes',isequal(unique(allModes)',0:5));
writejson(fullfile(folder,'assertions_v38.json'),checks);
summary=struct('version','0.38','model_version','0.38','matlab_version',version,'stateflow_version',ver('Stateflow'), ...
    'timestamp_utc',stamp,'scenarios',numel(out),'completed',sum(~[out.rejected]),'rejected',sum([out.rejected]), ...
    'intervals',sum(arrayfun(@(a)size(a.dispatch,1),out)),'positive_segments',sum(arrayfun(@(a)size(a.segments,1),out)), ...
    'harness_passed',sum([checks.passed]),'harness_failed',sum(~[checks.passed]),'hp_probes',numel(probes), ...
    'physical_validation',false,'article_replication',false);
writejson(fullfile(folder,'summary_v38.json'),summary);disp(summary);
fprintf('AUDIT_OUTPUT=%s\n',folder);assert(all([checks.passed]),'DCHR:v38:HarnessFailed','See evidence.');
    function record(name,ok)
        checks(end+1)=struct('name',name,'passed',logical(ok));if ~ok,fprintf(2,'FAIL=%s\n',name);end
    end
end
function s=configure(mdl,c,v)
dt=c.p(1);n=size(c.inputs,1);s=Simulink.SimulationInput(mdl);m=c.initial_clock;
if strcmp(v,'v36'),m=m(1:2);end
names={'dt','stop','input','p','h','E0','c','m0'};
values={dt,(n-1)*dt,[(0:n-1)'*dt c.inputs],reshape(c.p,1,[]),reshape(c.h,1,[]),c.initial_energy_MWh,reshape(c.c,1,[]),m(:)};
for k=1:numel(names),s=s.setVariable(['dchr_' names{k} '_' v],values{k},'Workspace',mdl);end
end
function item=extract(r,id)
d=r.SimulationMetadata.ExecutionInfo.ErrorDiagnostic;phase='';time=[];
if ~isempty(d),phase=d.SimulationPhase;time=d.SimulationTime;end
item=struct('id',id,'rejected',~isempty(r.ErrorMessage),'error_message',r.ErrorMessage,'phase',phase,'time_h',time, ...
    'dispatch',[],'clock_start',[],'clock_end',[],'energy_start',[],'sample_time_h',[],'segments',[]);
if isempty(r.ErrorMessage)
    item.dispatch=samples(r.dispatch_trace_v38,25);item.clock_start=samples(r.clock_start_trace_v38,4);
    item.clock_end=samples(r.clock_end_trace_v38,4);item.energy_start=samples(r.energy_start_trace_v38,1);
    item.sample_time_h=r.dispatch_trace_v38.Time;
    raw=samples(r.segment_trace_v38,1792);plan=samples(r.plan_trace_v38,1408);
    for i=1:size(raw,1)
        z=reshape(raw(i,:),28,64)';s=reshape(plan(i,:),22,64)';
        for j=1:64
            if z(j,2)>0,item.segments(end+1,:)=[i-1 j z(j,:) s(j,:)];end %#ok<AGROW>
        end
    end
end
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;
if ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;
elseif numel(raw)==n*width,v=reshape(raw,width,n)';
else,error('DCHR:v38:Shape','Unexpected trace dimensions.');end
end
function ok=near(a,b)
a=double(a);b=double(b);finite=isfinite(a)&isfinite(b);
ok=isequal(size(a),size(b))&&all((isnan(a)&isnan(b))|finite,'all')&&all(abs(a(finite)-b(finite))<=2e-9+2e-11*abs(b(finite)),'all');
end
function writejson(path,v)
fid=fopen(path,'w');assert(fid>0);clean=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(v,PrettyPrint=true)); %#ok<NASGU>
end
function closeModels()
for m={'DCHR_Dispatch_Stateflow_v38','DCHR_Dispatch_Stateflow_v36'}
    if bdIsLoaded(m{1}),close_system(m{1},0);end
end
end
