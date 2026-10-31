function f=build_IT_emergency_cooling_SK()
here=fileparts(mfilename('fullpath'));
name='IT_Independent_HeatRejection_20261023_SK';
f=fullfile(here,[name '.slx']);
assert(exist(f,'file')~=2,'Preserve previous model');
new_system(name);
set_param(name,'SolverType','Fixed-step','Solver','FixedStepDiscrete',...
 'FixedStep','5','StopTime','3600','ReturnWorkspaceOutputs','on');
in={'IT_MW','HeatReuse_MW','CoolerAvailable_MW','PumpOK'};
vars={'safe_IT','safe_reuse','safe_capacity','safe_pump'};
for i=1:4
 add_block('simulink/Sources/From Workspace',[name '/' in{i}],...
  'Position',[35 75*i 205 75*i+25],'VariableName',vars{i},'Interpolate','on');
end
add_block('simulink/Discrete/Unit Delay',[name '/Tank_Tprev'],...
 'Position',[155 420 225 450],'InitialCondition','35','SampleTime','5');
add_block('simulink/Sources/Constant',[name '/CoolingParams'],...
 'Position',[155 500 290 530],'Value','safe_params');
fblock=[name '/Independent_IT_cooling_safety'];
add_block('simulink/User-Defined Functions/MATLAB Function',fblock,...
 'Position',[380 135 660 520]);
chart=sfroot().find('-isa','Stateflow.EMChart','Path',fblock);
assert(~isempty(chart));
chart.Script=fileread(fullfile(here,'it_independent_cooling_step_SK.m'));
for i=1:4,add_line(name,[in{i} '/1'],sprintf('Independent_IT_cooling_safety/%d',i),'autorouting','on');end
add_line(name,'Tank_Tprev/1','Independent_IT_cooling_safety/5','autorouting','on');
add_line(name,'CoolingParams/1','Independent_IT_cooling_safety/6','autorouting','on');
out={'Tnext','Qrejected_MW','Residual_MW','Trip','FlowTrip'};
for i=1:5
 add_block('simulink/Sinks/To Workspace',[name '/' out{i}],...
  'Position',[840 100*i 1000 100*i+25],...
  'VariableName',['saf_' out{i}],'SaveFormat','Timeseries');
 add_line(name,sprintf('Independent_IT_cooling_safety/%d',i),[out{i} '/1'],'autorouting','on');
end
add_line(name,'Independent_IT_cooling_safety/1','Tank_Tprev/1','autorouting','on');
seed=timeseries([0;0;0],[0;5;10]);
for i=1:4,assignin('base',vars{i},seed);end
assignin('base','safe_params',[997*10*4182,5,35,40]);
save_system(name,f);close_system(name);
fprintf('INDEPENDENT_IT_SIMULINK_CREATED %s\n',f);
end
