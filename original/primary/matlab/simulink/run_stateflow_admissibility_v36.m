function folder=run_stateflow_admissibility_v36(specDirectory)
% Unified dispatch acceptance of new saved v36; temporary in-memory faults only.
here=fileparts(mfilename('fullpath'));root=fileparts(fileparts(here));addpath(fullfile(root,'matlab'),here);
spec=jsondecode(fileread(fullfile(specDirectory,'cases.json')));
cases=spec.cases;if ~iscell(cases),cases=num2cell(cases);end
stamp=char(datetime('now','TimeZone','UTC','Format','yyyyMMdd''T''HHmmssSSS''Z'''));
folder=fullfile(root,'results',['stateflow_admissibility_v36_' stamp]);assert(~isfolder(folder));mkdir(folder);
snap=fullfile(folder,'source_snapshot');mkdir(snap);copyfile(specDirectory,fullfile(snap,'spec'));
for pattern={'*v36.m','DCHR_Dispatch_Stateflow_v36.slx','dchr_stateflow_hp_v30.m','run_stateflow_admissibility_v36.m','export_stateflow_admissibility_v36.m'}
    paths=dir(fullfile(here,pattern{1}));for k=1:numel(paths),copyfile(fullfile(paths(k).folder,paths(k).name),snap);end
end
for f={'heat_pump_step_v14.m','storage_step_v30.m','storage_kernel_v30.m','storage_parameters_v30.m'}
    copyfile(fullfile(root,'matlab','+dchr','+components',f{1}),snap);
end
for f={'stateflow_specification_v36.py','stateflow_reference_v34.py','stateflow_reference_v32.py','stateflow_reference_v30.py','verify_stateflow_v36.py','verify_stateflow_v34.py'}
    copyfile(fullfile(root,'audit',f{1}),snap);
end
mdl='DCHR_Dispatch_Stateflow_v36';load_system(fullfile(here,[mdl '.slx']));
load_system(fullfile(here,'DCHR_Dispatch_Stateflow_v32.slx'));
cleanup=onCleanup(@()closeModels()); %#ok<NASGU>
v=readtable(fullfile(specDirectory,'vectors.csv'),'TextType','string');sv=readtable(fullfile(specDirectory,'segments.csv'),'TextType','string');
names=v.Properties.VariableNames(9:end);snames=sv.Properties.VariableNames(4:end);
totals=table();segments=table();checks=struct('name',{},'passed',{});
for j=1:numel(spec.cases)
    c=cases{j};result=sim(configure(mdl,c));save(fullfile(folder,[c.id '_simulation.mat']),'result');
    [a,b]=tables(result,c,names,snames);totals=[totals;a];segments=[segments;b]; %#ok<AGROW>
    expected=v(v.scenario_id==string(c.id),:);
    for k=3:width(expected)
        name=expected.Properties.VariableNames{k};record([c.id '_' name],near(a.(name),expected.(name)));
    end
    positive=b(b.Duration_h>0,:);expected=sv(sv.scenario_id==string(c.id),:);
    record([c.id '_positive_segment_count'],height(positive)==height(expected));
    for k=4:width(expected)
        name=expected.Properties.VariableNames{k};record([c.id '_segment_' name],near(positive.(name),expected.(name)));
    end
    if j<=6
        dt=c.p(1);n=size(c.inputs,1);old='DCHR_Dispatch_Stateflow_v32';
        os=Simulink.SimulationInput(old);
        ns={'dt','stop','input','p','h','E0'};
        vs={dt,(n-1)*dt,[(0:n-1)'*dt c.inputs],reshape(c.p,1,[]),reshape(c.h,1,[]),c.initial_energy_MWh};
        for ii=1:numel(ns),os=os.setVariable(['dchr_' ns{ii} '_v32'],vs{ii},'Workspace',old);end
        oldresult=sim(os);save(fullfile(folder,[c.id '_v32_comparison.mat']),'oldresult');
        oldy=samples(oldresult.dispatch_trace_v32,25);newy=samples(result.dispatch_trace_v36,25);
        record([c.id '_verified_v32'],near(newy(:,[1:21 23:25]),oldy(:,[1:21 23:25])));
        writematrix(oldy,fullfile(folder,[c.id '_v32_comparison.csv']));
    end
    fprintf('CLEAN_EXECUTED=%s intervals=%d\n',c.id,height(a));
end
writetable(totals,fullfile(folder,'trace_v36.csv'));writetable(segments,fullfile(folder,'segments_v36.csv'));
runtimeFaults=run_stateflow_faults_v36(mdl,folder,cases{1});
writejson(fullfile(folder,'runtime_fault_evidence_v36.json'),runtimeFaults);
record('30_runtime_faults_rejected',numel(runtimeFaults)==30 && all([runtimeFaults.rejected]));
% A scale-independent 0.01 physical-hour clock error, injected into executed allocator.
rt=sfroot;ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/Thermal_Dispatch']);
f=ch.find('-isa','Stateflow.EMFunction','Name','stateflow_allocate_v36');original=f.Script;
restore=onCleanup(@()set(f,'Script',original)); %#ok<NASGU>
mutation=sprintf('z(28)=z(28)+%.17g;\n',spec.clock_corruption_h);
f.Script=regexprep(original,'end\s*$',sprintf('%send\n',mutation));
fid=fopen(fullfile(folder,'corrupted_in_memory_allocation.m'),'w');assert(fid>0);fprintf(fid,'%s',f.Script);fclose(fid);
faults=struct('id',{},'capacity_MWh',{},'rejected',{},'phase',{},'time_h',{},'error_message',{},'clock_error_h',{});
guard=struct('capacity_MWh',{},'age_h',{},'required_off_h',{},'permitted',{});
faultSegments=table();
for j=1:numel(spec.cases)
    c=cases{j};if ~startsWith(c.id,'scale_'),continue;end
    result=sim(configure(mdl,c).setModelParameter('CaptureErrors','on'));
    save(fullfile(folder,[c.id '_corruption_simulation.mat']),'result');
    diag=result.SimulationMetadata.ExecutionInfo.ErrorDiagnostic;phase='';time=[];
    if ~isempty(diag),phase=diag.SimulationPhase;time=diag.SimulationTime;end
    rejected=~isempty(result.ErrorMessage);err=[];
    if ~rejected
        [~,b]=tables(result,c,names,snames);faultSegments=[faultSegments;b]; %#ok<AGROW>
        err=max(abs(b.HP_Age_End_h-b.HP_Age_Start_h-b.Duration_h));
    end
    faults(end+1)=struct('id',c.id,'capacity_MWh',c.p(2),'rejected',rejected,'phase',phase,'time_h',time, ...
        'error_message',result.ErrorMessage,'clock_error_h',err); %#ok<AGROW>
    s=zeros(18,1);s(17)=3;s(2)=.6*c.p(2);s(4)=6;
    allowed=stateflow_supervisor_guard_v36(1,s,reshape(c.p,1,[]),reshape(c.c,1,[]),spec.guard_age_h);
    guard(end+1)=struct('capacity_MWh',c.p(2),'age_h',spec.guard_age_h,'required_off_h',c.c(3),'permitted',allowed); %#ok<AGROW>
    fprintf('CLOCK_CORRUPTION=%s rejected=%d early_guard=%d\n',c.id,rejected,allowed);
end
f.Script=original;
clear restore % Restore while the chart is alive, before model cleanup.
% Re-execute after fault injection; closing without saving preserves the SLX.
c=cases{end};result=sim(configure(mdl,c));save(fullfile(folder,'restored_simulation.mat'),'result');
baseline=load(fullfile(folder,[c.id '_simulation.mat']),'result');
record('restored_clock_and_segments',isequaln(result.clock_end_trace_v36.Data,baseline.result.clock_end_trace_v36.Data)&& ...
    isequaln(result.segment_trace_v36.Data,baseline.result.segment_trace_v36.Data));
record('six_modes',isequal(unique(segments.Mode(segments.Duration_h>0))',(0:5)));
% Corrected release must reject every actual clock corruption and early guard.
record('all_scale_clock_corruptions_rejected',numel(faults)==4 && all([faults.rejected]));
record('all_early_dwell_guards_rejected',numel(guard)==4 && all(~[guard.permitted]));
extended=run_stateflow_dimensional_faults_v36(mdl,folder,cases);
writejson(fullfile(folder,'dimensional_fault_evidence_v36.json'),extended.faults);
writejson(fullfile(folder,'time_resolution_evidence_v36.json'),extended.time);
record('extended_dimensional_runtime_faults_rejected',all([extended.faults.rejected]));
record('physical_time_boundary_checks',all([extended.time.passed]));
writetable(faultSegments,fullfile(folder,'accepted_corrupted_segments_v36.csv'));
writejson(fullfile(folder,'fault_evidence_v36.json'),faults);writejson(fullfile(folder,'guard_evidence_v36.json'),guard);
writetable(struct2table(checks),fullfile(folder,'assertions_v36.csv'));
summary=struct('version','0.36','model_version','0.36','matlab_version',version,'timestamp_utc',stamp, ...
    'scenarios',numel(spec.cases),'intervals',height(totals),'positive_segments',sum(segments.Duration_h>0), ...
    'passed',sum([checks.passed]),'failed',sum(~[checks.passed]),'actual_fault_trials',numel(faults), ...
    'faults_rejected',sum([faults.rejected]),'faults_incorrectly_accepted',sum(~[faults.rejected]), ...
    'max_abs_balance_residual_MWh',max(abs(totals.System_Balance_Residual_MWh)), ...
    'runtime_fault_trials',numel(runtimeFaults),'runtime_faults_rejected',sum([runtimeFaults.rejected]), ...
    'extended_fault_trials',numel(extended.faults),'extended_faults_rejected',sum([extended.faults.rejected]), ...
    'conclusion','Dimensional tolerance repair executed; implementation acceptance only', ...
    'physical_validation',false,'article_replication',false);
writejson(fullfile(folder,'summary_v36.json'),summary);disp(summary);
assert(all([checks.passed]),'DCHR:v36:AuditFailed','See timestamped evidence.');fprintf('AUDIT_OUTPUT=%s\n',folder);
    function record(name,ok)
        checks(end+1)=struct('name',name,'passed',logical(ok));if ~ok,fprintf(2,'FAIL=%s\n',name);end
    end
end
function s=configure(mdl,c)
dt=c.p(1);n=size(c.inputs,1);s=Simulink.SimulationInput(mdl);
names={'dt','stop','input','p','h','E0','c','m0'};
values={dt,(n-1)*dt,[(0:n-1)'*dt c.inputs],reshape(c.p,1,[]),reshape(c.h,1,[]),c.initial_energy_MWh,reshape(c.c,1,[]),reshape(c.initial_clock,2,1)};
for k=1:numel(names),s=s.setVariable(['dchr_' names{k} '_v36'],values{k},'Workspace',mdl);end
end
function [a,b]=tables(r,c,names,snames)
y=samples(r.dispatch_trace_v36,25);raw=samples(r.segment_trace_v36,1792);
e=samples(r.energy_start_trace_v36,1);m=samples(r.clock_start_trace_v36,2);mc=samples(r.clock_end_trace_v36,2);n=size(y,1);
a=[table(repmat(string(c.id),n,1),(0:n-1)',r.dispatch_trace_v36.Time,e,m(:,1),m(:,2),mc(:,1),mc(:,2), ...
    'VariableNames',{'scenario_id','step','Time_h','Storage_E_Start_MWh','HP_Latch_Start','HP_Age_Start_h','HP_Latch_End','HP_Age_End_h'}),array2table(y,'VariableNames',names)];
b=table();
for i=1:n
    z=reshape(raw(i,:),28,64)';
    b=[b;table(repmat(string(c.id),64,1),repmat(i-1,64,1),(1:64)', ...
        'VariableNames',{'scenario_id','step','segment'}),array2table(z,'VariableNames',snames)]; %#ok<AGROW>
end
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;
if ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;
elseif numel(raw)==n*width,v=reshape(raw,width,n)';
else,error('DCHR:v36:TraceShape','Unexpected trace shape.');end
end
function ok=near(a,b)
a=double(a);b=double(b);finite=isfinite(a)&isfinite(b);
ok=isequal(size(a),size(b))&&all((isnan(a)&isnan(b))|finite,'all')&&all(abs(a(finite)-b(finite))<=2e-9+2e-11*abs(b(finite)),'all');
end
function writejson(path,v)
fid=fopen(path,'w');assert(fid>0);clean=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(v,PrettyPrint=true)); %#ok<NASGU>
end

function closeModels()
for m={'DCHR_Dispatch_Stateflow_v36','DCHR_Dispatch_Stateflow_v32'}
    if bdIsLoaded(m{1}),close_system(m{1},0);end
end
end
