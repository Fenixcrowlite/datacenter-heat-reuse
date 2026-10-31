root = 'C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse';
assets = fullfile(root,'presentation','assets_v04');
if ~exist(assets,'dir'), mkdir(assets); end
mdlfile = fullfile(root,'matlab','simulink','DataCenterHeatReuse_Core.slx');
load_system(mdlfile);
mdl = 'DataCenterHeatReuse_Core';
try
    set_param(mdl,'ZoomFactor','FitSystem');
catch
end
try
    print(['-s' mdl],'-dpng','-r170',fullfile(assets,'simulink_full.png'));
    fprintf('SIMULINK_EXPORT_OK\n');
catch ME
    fprintf('SIMULINK_EXPORT_ERROR: %s\n', getReport(ME));
end
close_system(mdl,0);
