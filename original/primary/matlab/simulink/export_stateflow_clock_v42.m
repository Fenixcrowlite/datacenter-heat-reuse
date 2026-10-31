function export_stateflow_clock_v42(folder)
% Separate read-only MATLAB process: bind JSON evidence to saved MAT outputs.
snap=fullfile(folder,'mat_audit_source');mkdir(snap);copyfile([mfilename('fullpath') '.m'],snap);
execution=jsondecode(fileread(fullfile(folder,'execution_v42.json')));items=[];
for k=1:numel(execution)
    saved=load(fullfile(folder,[execution(k).id '_simulation.mat']),'result');r=saved.result;
    item=struct('id',execution(k).id,'rejected',~isempty(r.ErrorMessage), ...
        'error_message',r.ErrorMessage,'dispatch',[],'clock_start',[],'clock_end',[], ...
        'energy_start',[],'sample_time_h',[],'segments',[]);
    if ~item.rejected
        item.dispatch=unpack(r.dispatch_trace_v42,25);item.clock_start=unpack(r.clock_start_trace_v42,4);
        item.clock_end=unpack(r.clock_end_trace_v42,4);item.energy_start=unpack(r.energy_start_trace_v42,1);
        item.sample_time_h=r.dispatch_trace_v42.Time;
        raw=unpack(r.segment_trace_v42,1792);plan=unpack(r.plan_trace_v42,1408);
        for i=1:size(raw,1)
            segments=reshape(raw(i,:),28,64)';schedule=reshape(plan(i,:),22,64)';
            positive=find(segments(:,2)>0);
            for j=positive'
                item.segments(end+1,:)=[i-1 j segments(j,:) schedule(j,:)]; %#ok<AGROW>
            end
        end
    end
    if isempty(items),items=item;else,items(end+1)=item;end %#ok<AGROW>
end
path=fullfile(folder,'mat_audit_v42.json');assert(~isfile(path));fid=fopen(path,'w');assert(fid>0);
cleanup=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(items,PrettyPrint=true)); %#ok<NASGU>
fprintf('MAT_AUDIT_OUTPUT=%s\n',path);
faults=jsondecode(fileread(fullfile(folder,'faults_v42.json')));faultItems=[];
for k=1:numel(faults)
    saved=load(fullfile(folder,[faults(k).id '_fault_simulation.mat']),'result');r=saved.result;
    diag=r.SimulationMetadata.ExecutionInfo.ErrorDiagnostic;phase='';time=[];
    if ~isempty(diag),phase=diag.SimulationPhase;time=diag.SimulationTime;end
    item=struct('id',faults(k).id,'error_message',r.ErrorMessage,'phase',phase,'time_h',time);
    if isempty(faultItems),faultItems=item;else,faultItems(end+1)=item;end
end
path=fullfile(folder,'fault_mat_audit_v42.json');assert(~isfile(path));fid=fopen(path,'w');assert(fid>0);
cleanFault=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(faultItems,PrettyPrint=true));
attacks=jsondecode(fileread(fullfile(folder,'uncertainty_attacks_v42.json')));attackItems=[];
for k=1:numel(attacks)
    saved=load(fullfile(folder,[attacks(k).id '_attack.mat']),'result');r=saved.result;
    diag=r.SimulationMetadata.ExecutionInfo.ErrorDiagnostic;
    item=struct('id',attacks(k).id,'error_message',r.ErrorMessage,'phase',diag.SimulationPhase,'time_h',diag.SimulationTime);
    if isempty(attackItems),attackItems=item;else,attackItems(end+1)=item;end
end
path=fullfile(folder,'attack_mat_audit_v42.json');assert(~isfile(path));fid=fopen(path,'w');assert(fid>0);
cleanAttack=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(attackItems,PrettyPrint=true));
end
function v=unpack(ts,width)
v=reshape(ts.Data,width,numel(ts.Time))';
if ismatrix(ts.Data) && isequal(size(ts.Data),[numel(ts.Time),width]),v=ts.Data;end
end
