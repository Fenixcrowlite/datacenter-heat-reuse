function report = run_full_study_v3(N)
%RUN_FULL_STUDY_V3 Reproducible entry point for the current research package.
if nargin < 1, N = 300; end
rootDir=fileparts(fileparts(mfilename('fullpath')));
logPath=fullfile(rootDir,'results','full_study_v3.log');
diary(logPath); cleanup=onCleanup(@() diary('off'));
fprintf('DataCenter Heat Reuse v0.3\nStarted: %s\n\n',string(datetime('now')));
report.tests = run_tests_v3();
report.scenarios = run_experiment_v2();
run_sensitivity_v2();
report.uncertainty = run_uncertainty_v3(N);
save(fullfile(rootDir,'results','full_study_v3.mat'),'report');
fprintf('\nFinished: %s\n',string(datetime('now')));
end
