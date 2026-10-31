function export_hp_traceability_v43(folder)
% Separate read-only batch: reopen saved MAT artifacts, do not simulate.
comp=load(fullfile(folder,'component_vectors_v43.mat'),'matrix');items=[];
names={'same_factor_refrigerant','converted_refrigerant','converted_water_proxy','converted_with_assumed_partload'};
for k=1:numel(names)
    s=load(fullfile(folder,[names{k} '_simulation.mat']),'result');r=s.result;
    item=struct('id',names{k},'error_message',r.ErrorMessage, ...
        'dispatch',reshape(r.dispatch_trace_v42.Data,25,[])', ...
        'segments',reshape(r.segment_trace_v42.Data,28,64)');
    if isempty(items),items=item;else,items(end+1)=item;end %#ok<AGROW>
end
value=struct('matrix',comp.matrix,'cases',items);
path=fullfile(folder,'mat_reexport_v43.json');assert(~isfile(path));
fid=fopen(path,'w');assert(fid>0);clean=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(value,PrettyPrint=true));
fprintf('SAVED_MAT_EXPORT_CASES=%d component_vectors=%d\n',numel(items),size(comp.matrix,1));
end
