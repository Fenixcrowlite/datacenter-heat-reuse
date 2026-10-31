function export_stateflow_dwell_v42(folder)
% Bind focused attack evidence to saved MAT errors after the model closes.
snap=fullfile(folder,'mat_audit_source');mkdir(snap);copyfile([mfilename('fullpath') '.m'],snap);
attacks=jsondecode(fileread(fullfile(folder,'uncertainty_attacks_v42.json')));items=[];
for k=1:numel(attacks)
    saved=load(fullfile(folder,[attacks(k).id '_attack.mat']),'result');r=saved.result;
    diag=r.SimulationMetadata.ExecutionInfo.ErrorDiagnostic;
    item=struct('id',attacks(k).id,'error_message',r.ErrorMessage,'phase',diag.SimulationPhase,'time_h',diag.SimulationTime);
    if isempty(items),items=item;else,items(end+1)=item;end %#ok<AGROW>
end
path=fullfile(folder,'attack_mat_audit_v42.json');assert(~isfile(path));fid=fopen(path,'w');assert(fid>0);
clean=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(items,PrettyPrint=true)); %#ok<NASGU>
fprintf('FOCUSED_MAT_EXPORT=%s\n',path);
end
