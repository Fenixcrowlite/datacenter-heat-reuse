function run_charge_temporal_v56(folder)
% Focused temporal saved-model controls and an explicit coupled event blocker.
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'matlab'),fullfile(root,'matlab','simulink'));
assert(~isfile(fullfile(folder,'temporal_report.json')));
Simulink.fileGenControl('set','CacheFolder',fullfile(folder,'temporal_build','cache'), ...
    'CodeGenFolder',fullfile(folder,'temporal_build','codegen'),'createDir',true);
spec=jsondecode(fileread(fullfile(folder,'spec.json')));v=spec.cases(strcmp({spec.cases.id},'floor_branch'));
r=dchr.components.charge_regime_events_v56(v.s,v.p,v.E,v.request);
assert(any(strcmp(r.first_event_labels,'BRANCH')));
identifier='';try,dchr.components.charge_regime_events_v56(v.s,v.p,r.branch_energy_MWh,v.request);
catch e,identifier=e.identifier;end
blocker=struct('input',v,'descriptor',r,'nominal_endpoint_MWh',r.branch_energy_MWh, ...
    'endpoint_identifier',identifier,'coupled_release_blocked',strcmp(identifier,'DCHR:v55:UnresolvedBranch'));
assert(blocker.coupled_release_blocked,'DCHR:v56:BlockerNotReproduced','Inspect endpoint policy.');
mdl='DCHR_Dispatch_Stateflow_v52';load_system(fullfile(root,'matlab','simulink',[mdl '.slx']));
cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
inputs=[0 35 75 0 45;6 35 75 1 45;0 35 75 1 45;0 35 75 12 45; ...
    0 35 75 2 45;0 35 75 2 45;0 35 75 5 45];
c=struct('p',[.25 10 3 4 .9 .8 0 5 .2 20 2],'h',[8 .45 1.2 8 0 1 4 0 0], ...
    'c',[8 .25 .25 64],'inputs',inputs,'initial_energy_MWh',7,'initial_clock',[1;0;0;0]);
si=Simulink.SimulationInput(mdl);names={'dt','stop','input','p','h','E0','c','m0'};
values={.25,1.5,[(0:6)'*.25 inputs],c.p,c.h,7,c.c,c.initial_clock};
for j=1:numel(names),si=si.setVariable(['dchr_' names{j} '_v52'],values{j},'Workspace',mdl);end
result=sim(si.setModelParameter('CaptureErrors','on'));save(fullfile(folder,'temporal_simulation.mat'),'result','c','blocker','-v7.3');
assert(isempty(result.ErrorMessage),result.ErrorMessage);
item=extract(result,c,blocker);reopened=load(fullfile(folder,'temporal_simulation.mat'));
assert(isequaln(result,reopened.result)&&isequaln(c,reopened.c)&&isequaln(blocker,reopened.blocker));
writejson('temporal_original_reopen.json',extract(reopened.result,reopened.c,reopened.blocker));
checks=struct('name',{},'passed',{});
record('MAT_binding',isequaln(item,extract(reopened.result,reopened.c,reopened.blocker)));
record('blocking_kink_reproduced',blocker.coupled_release_blocked);
record('temporal_mode_transitions',sum(diff(item.dispatch(:,1))~=0)>=4);
record('temporal_segment_modes',all(ismember([0 2 3 4 5],item.positive_modes)));
record('macro_handoff',all(item.energy_start(2:end)==item.dispatch(1:end-1,8)));
for j=1:7
    z=reshape(item.raw_segments(j,:),28,64)';q=reshape(item.raw_plans(j,:),23,64)';padding=z(:,2)==0;
    record(sprintf('interval_%d_handoff',j),all(z(1:63,5)==z(2:64,4))&&all(z(:,5)==q(:,23)));
    record(sprintf('interval_%d_bounds',j),all(z(:,4:5)>=0,'all')&&all(z(:,4:5)<=10,'all')&&all(z(:,6:14)>=0,'all'));
    record(sprintf('interval_%d_closure',j),all(abs(z(:,21))<1e-10));
    record(sprintf('interval_%d_padding',j),all(z(padding,4)==z(padding,5))&&all(z(padding,6:14)==0,'all')&&all(z(padding,17:21)==0,'all'));
end
report=struct('version','0.56','saved_model_version','0.52','new_model',false,'run',item, ...
    'assertions',checks,'summary',struct('passed',sum([checks.passed]),'failed',sum(~[checks.passed])));
writejson('temporal_report.json',report);
fprintf('CHARGE_TEMPORAL_V56 PASS=%d FAIL=%d TRANSITIONS=%d BLOCKER=%s\n', ...
    report.summary.passed,report.summary.failed,sum(diff(item.dispatch(:,1))~=0),identifier);
assert(all([checks.passed]),'DCHR:v56:TemporalFailure','Inspect retained evidence.');
    function record(name,ok),checks(end+1)=struct('name',name,'passed',logical(ok));end
    function writejson(name,value)
        fid=fopen(fullfile(folder,name),'w');assert(fid>0);cl=onCleanup(@()fclose(fid)); %#ok<NASGU>
        fprintf(fid,'%s\n',jsonencode(value,PrettyPrint=true));
    end
end
function item=extract(r,c,blocker)
raw=samples(r.segment_trace_v52,1792);positive=[];
for j=1:7,z=reshape(raw(j,:),28,64)';positive=[positive;z(z(:,2)>0,1)];end %#ok<AGROW>
item=struct('case',c,'blocker',blocker,'dispatch',samples(r.dispatch_trace_v52,25), ...
    'raw_segments',raw,'raw_plans',samples(r.plan_trace_v52,1472),'energy_start',samples(r.energy_start_trace_v52,1), ...
    'clock_start',samples(r.clock_start_trace_v52,4),'clock_end',samples(r.clock_end_trace_v52,4),'positive_modes',unique(positive)');
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;
if ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;
elseif numel(raw)==n*width,v=reshape(raw,width,n)';else,error('DCHR:v56:TraceShape','Unexpected trace shape.');end
end
