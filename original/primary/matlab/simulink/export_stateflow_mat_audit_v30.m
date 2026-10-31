function export_stateflow_mat_audit_v30(folder)
% Read saved SimulationOutput artifacts independently of the simulation harness.
% No simulations, model edits or synthetic numerical data in this exporter.
sourceFolder=fullfile(folder,'mat_audit_source');assert(~isfolder(sourceFolder));mkdir(sourceFolder);
copyfile([mfilename('fullpath') '.m'],sourceFolder);
spec=jsondecode(fileread(fullfile(folder,'source_snapshot','spec','cases.json')));
valid=struct('id',{},'samples',{},'error_message',{},'y',{},'u',{},'energy_start',{},'time_h',{});
legacy=struct('id',{},'samples',{},'error_message',{},'energy_end_MWh',{});
for j=1:numel(spec.cases)
    if iscell(spec.cases),c=spec.cases{j};else,c=spec.cases(j);end
    saved=load(fullfile(folder,[c.id '_simulation.mat']),'result');r=saved.result;
    y=samples(r.dispatch_trace_v30,17);u=samples(r.hp_trace_v30,8);
    valid(end+1)=struct('id',c.id,'samples',size(y,1),'error_message',r.ErrorMessage, ...
        'y',y,'u',u,'energy_start',reshape(r.energy_start_trace_v30.Data,[],1), ...
        'time_h',r.dispatch_trace_v30.Time); %#ok<AGROW>
    if startsWith(c.id,'partition_')
        previous=load(fullfile(folder,[c.id '_v28_comparison.mat']),'oldresult');old=previous.oldresult;
        oldy=samples(old.dispatch_trace_v28,13);
        legacy(end+1)=struct('id',c.id,'samples',size(oldy,1),'error_message',old.ErrorMessage, ...
            'energy_end_MWh',oldy(end,8)); %#ok<AGROW>
    end
end
fault=jsondecode(fileread(fullfile(folder,'fault_evidence_v30.json')));
metadata=struct('id',{},'stop_event',{},'error_phase',{},'error_time_h',{},'error_message',{},'samples',{});
for j=1:numel(fault)
    saved=load(fullfile(folder,[fault(j).id '_fault_simulation.mat']),'result');r=saved.result;
    e=r.SimulationMetadata.ExecutionInfo;d=e.ErrorDiagnostic;count=0;
    if any(strcmp(r.who,'dispatch_trace_v30'))
        ts=r.dispatch_trace_v30;if isa(ts,'timeseries'),count=numel(ts.Time);end
    end
    phase='';time=[];
    if ~isempty(d),phase=d.SimulationPhase;time=d.SimulationTime;end
    metadata(end+1)=struct('id',fault(j).id,'stop_event',e.StopEvent, ...
        'error_phase',phase,'error_time_h',time,'error_message',r.ErrorMessage,'samples',count); %#ok<AGROW>
end
saved=load(fullfile(folder,'post_fault_clean_simulation.mat'),'result');r=saved.result;
report=struct('timestamp_utc',char(datetime('now','TimeZone','UTC')), ...
    'valid_cases',valid,'legacy_cases',legacy,'faults',metadata,'clean_restart_samples',numel(r.dispatch_trace_v30.Time), ...
    'clean_restart_error',r.ErrorMessage,'scope','Read-only saved SimulationOutput export; no new simulations.');
path=fullfile(folder,'mat_audit_v30.json');assert(~isfile(path),'DCHR:v30:NoOverwrite','Refuse overwrite.');
fid=fopen(path,'w');assert(fid>0);cleanup=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(report,PrettyPrint=true));fprintf('MAT_AUDIT_OUTPUT=%s\n',path);
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;
if ismatrix(raw) && isequal(size(raw),[n width]),v=raw;
elseif size(raw,1)==width && numel(raw)==n*width,v=reshape(raw,width,n)';
else,error('DCHR:v30:TraceDimensions','Unexpected saved trace shape.');end
end
