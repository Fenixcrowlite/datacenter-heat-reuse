function probe_stateflow_v32()
root=fileparts(fileparts(mfilename('fullpath')));
stamp=char(datetime('now','TimeZone','UTC','Format','yyyyMMdd''T''HHmmssSSS''Z'''));
diary(fullfile(root,'automation','logs',['stateflow_probe_v32_' stamp '.log']));
cleanup=onCleanup(@()diary('off')); %#ok<NASGU>
disp(version); disp(ver('Stateflow'));
assert(license('test','Stateflow'),'Stateflow license unavailable');
load_system('simulink'); load_system('sflib');
block='simulink/Ports & Subsystems/For Iterator Subsystem/For Iterator';
params=get_param(block,'DialogParameters');
disp(params); disp(get_param(block,'IterationSource'));
disp(get_param(block,'IndexMode'));
disp(get_param(block,'ResetStates'));
fprintf('PROBE_PASS\n');
end
