function export_hp_boundary_v44(folder)
root=fileparts(fileparts(fileparts(mfilename('fullpath')))); out=fullfile(root,folder);
data=load(fullfile(out,'boundary_v44.mat'),'matrix','report','spec');
fid=fopen(fullfile(out,'mat_reexport_v44.json'),'w'); clean=onCleanup(@()fclose(fid));
fprintf(fid,'%s\n',jsonencode(data));
fprintf('MAT_REEXPORT_V44 rows=%d\n',size(data.matrix,1));
end
