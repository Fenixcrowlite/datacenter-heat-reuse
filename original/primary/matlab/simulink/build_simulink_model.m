function modelPath = build_simulink_model()
%BUILD_SIMULINK_MODEL Generate an executable Simulink core for no-storage dispatch.
% The annual/storage reference implementation remains in +dchr/simulate_system.m.

thisDir = fileparts(mfilename('fullpath'));
matlabDir = fileparts(thisDir); addpath(matlabDir);
cfg = default_config();
hp = dchr.heat_pump_capability(1,cfg.dc.source_temp_C,cfg);
cop = hp.cop(1); hpFactor = cop/(cop-1);

mdl='DataCenterHeatReuse_Core'; modelPath=fullfile(thisDir,[mdl '.slx']);
if bdIsLoaded(mdl), close_system(mdl,0); end
if exist(modelPath,'file'), delete(modelPath); end
new_system(mdl); open_system(mdl);
set_param(mdl,'StopTime','24','SolverType','Fixed-step','Solver','FixedStepDiscrete','FixedStep','1');

add_block('simulink/Sources/In1',[mdl '/IT_Load_MW'],'Position',[40 80 70 100]);
add_block('simulink/Sources/In1',[mdl '/Heat_Demand_MW'],'Position',[40 210 70 230]);
add_block('simulink/Math Operations/Gain',[mdl '/Heat_Recovery'],'Gain',num2str(cfg.dc.recovery_fraction),'Position',[130 70 240 110]);
add_block('simulink/Math Operations/Gain',[mdl '/Heat_Pump_Lift'],'Gain',num2str(hpFactor,12),'Position',[290 70 400 110]);
add_block('simulink/Discontinuities/Saturation',[mdl '/HP_Capacity'],'UpperLimit',num2str(cfg.hp.max_heat_output_MW),'LowerLimit','0','Position',[450 70 550 110]);
add_block('simulink/Math Operations/MinMax',[mdl '/Direct_Heat_Min'],'Function','min','Inputs','2','Position',[620 90 680 140]);
add_block('simulink/Math Operations/Sum',[mdl '/Heat_Deficit'],'Inputs','+-','Position',[760 205 790 235]);
add_block('simulink/Discontinuities/Saturation',[mdl '/Gas_Backup'],'UpperLimit','inf','LowerLimit','0','Position',[850 195 950 245]);
add_block('simulink/Math Operations/Sum',[mdl '/Unused_HP_Potential'],'Inputs','+-','Position',[760 65 790 95]);
add_block('simulink/Discontinuities/Saturation',[mdl '/Curtailment_Positive'],'UpperLimit','inf','LowerLimit','0','Position',[850 55 950 105]);
add_block('simulink/Math Operations/Gain',[mdl '/HP_Electricity'],'Gain',num2str(1/cop,12),'Position',[760 125 860 165]);

add_block('simulink/Sinks/Out1',[mdl '/HP_Heat_to_DH_MW'],'Position',[1030 125 1060 145]);
add_block('simulink/Sinks/Out1',[mdl '/HP_Electric_MW'],'Position',[1030 155 1060 175]);
add_block('simulink/Sinks/Out1',[mdl '/Gas_Heat_MW'],'Position',[1030 215 1060 235]);
add_block('simulink/Sinks/Out1',[mdl '/Curtailed_Heat_MW'],'Position',[1030 75 1060 95]);

add_line(mdl,'IT_Load_MW/1','Heat_Recovery/1');
add_line(mdl,'Heat_Recovery/1','Heat_Pump_Lift/1');
add_line(mdl,'Heat_Pump_Lift/1','HP_Capacity/1');
add_line(mdl,'HP_Capacity/1','Direct_Heat_Min/1');
add_line(mdl,'Heat_Demand_MW/1','Direct_Heat_Min/2');
add_line(mdl,'Heat_Demand_MW/1','Heat_Deficit/1');
add_line(mdl,'Direct_Heat_Min/1','Heat_Deficit/2');
add_line(mdl,'Heat_Deficit/1','Gas_Backup/1');
add_line(mdl,'HP_Capacity/1','Unused_HP_Potential/1');
add_line(mdl,'Direct_Heat_Min/1','Unused_HP_Potential/2');
add_line(mdl,'Unused_HP_Potential/1','Curtailment_Positive/1');
add_line(mdl,'Direct_Heat_Min/1','HP_Electricity/1');
add_line(mdl,'Direct_Heat_Min/1','HP_Heat_to_DH_MW/1');
add_line(mdl,'HP_Electricity/1','HP_Electric_MW/1');
add_line(mdl,'Gas_Backup/1','Gas_Heat_MW/1');
add_line(mdl,'Curtailment_Positive/1','Curtailed_Heat_MW/1');

set_param(mdl,'Location',[100 100 1200 520]);
save_system(mdl,modelPath); close_system(mdl,0);
fprintf('Saved %s\n',modelPath);
end

