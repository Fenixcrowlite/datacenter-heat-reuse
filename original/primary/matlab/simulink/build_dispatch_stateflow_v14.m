function modelPath=build_dispatch_stateflow_v14()
% Versioned executable Simulink + Stateflow dispatch demonstrator.
% Scenario: constant HP potential 6 MW, heat demand 8 MW, backup cap 2 MW.
% Stateflow chooses RECOVER or BACKUP according to demand.
mdl='DCHR_Dispatch_Stateflow_v14';
here=fileparts(mfilename('fullpath')); modelPath=fullfile(here,[mdl '.slx']);
if bdIsLoaded(mdl), close_system(mdl,0); end
new_system(mdl);
set_param(mdl,'Solver','FixedStepDiscrete','SolverType','Fixed-step','FixedStep','1','StopTime','24');
add_block('simulink/Sources/Constant',[mdl '/Heat_Demand_MW'],'Value','8','Position',[35 70 105 100]);
add_block('simulink/Sources/Constant',[mdl '/HP_Potential_MW'],'Value','6','Position',[35 150 105 180]);
add_block('simulink/User-Defined Functions/MATLAB Function',[mdl '/Dispatch_Controller'],'Position',[220 80 370 190]);
rt=sfroot; chart=rt.find('-isa','Stateflow.EMChart','Path',[mdl '/Dispatch_Controller']);

chart.Script=sprintf(['function [hp,backup,unmet,mode] = dispatch(demand,potential)\n' ...
'%%#codegen\n' ...
'hp=min(max(potential,0),max(demand,0));\n' ...
'backup=min(2,max(0,demand-hp));\n' ...
'unmet=max(0,demand-hp-backup);\n' ...
'mode=double(unmet>0)*2+double(unmet==0 && backup>0);\n' ...
'end']);
save_system(mdl,modelPath);close_system(mdl,0);
end


