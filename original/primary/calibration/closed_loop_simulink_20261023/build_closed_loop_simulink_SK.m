function pathSaved=build_closed_loop_simulink_SK()
% Vlastny SLX projekt so skutocnou okamzitou spatnou vazbou bazena k DC.
here=fileparts(mfilename('fullpath'));
name='DC_Pool_Coupled_ClosedLoop_20261023_SK';
pathSaved=fullfile(here,[name '.slx']);
assert(exist(pathSaved,'file')~=2,'Existing SLX is preserved. Explicitly version a new file.');
if bdIsLoaded(name),close_system(name,0);end
new_system(name);
set_param(name,'SolverType','Fixed-step','Solver','FixedStepDiscrete',...
    'FixedStep','300','StopTime','604800','ReturnWorkspaceOutputs','on');
inputs={'SrcAvail';'Dhdemand';'Activity';'Cover';...
    'Tprev';'Eprev';'Hprev';'Mode';'SourceTemp';'COPpool';'P'};
outnames={'Tnext';'Enext';'Hnext';'Qpool';'QsrcPool';'Wpool';...
    'Qdh';'QsrcDh';'Wdh';'Qgas';'Qcharge';'Qdischarge';'Qloss';'COPdh'};
variables={'cl_Tnext';'cl_Enext';'cl_Hnext';'cl_Qpool';...
    'cl_QsrcPool';'cl_Wpool';'cl_Qdh';'cl_QsrcDh';...
    'cl_Wdh';'cl_Qgas';'cl_Qcharge';'cl_Qdischarge';'cl_Qloss';'cl_COPdh'};
% Four independent time-varying input signals.
z={'SrcAvail','cl_source_series';'Dhdemand','cl_dh_series';...
   'Activity','cl_activity_series';'Cover','cl_cover_series'};
for i=1:size(z,1)
    add_block('simulink/Sources/From Workspace',[name '/' z{i,1}],...
      'Position',[40 30+63*i 190 55+63*i],'VariableName',z{i,2},...
      'Interpolate','on');
end
delays={'Tprev','16';'Eprev','0';'Hprev','1'};
for i=1:3
  add_block('simulink/Discrete/Unit Delay',[name '/' delays{i,1}],...
   'Position',[160 350+67*i 230 380+67*i],...
   'SampleTime','300','InitialCondition',delays{i,2});
end
cons={'Mode','cl_mode';'SourceTemp','cl_source_temp';...
      'COPpool','cl_cop_pool';'P','cl_params'};
for i=1:size(cons,1)
  add_block('simulink/Sources/Constant',[name '/' cons{i,1}],...
   'Position',[40 590+62*i 180 618+62*i],'Value',cons{i,2});
end
fblock=[name '/DC_bazen_spatna_vazba'];
add_block('simulink/User-Defined Functions/MATLAB Function',fblock,...
    'Position',[380 140 620 650]);
rt=sfroot();
chart=rt.find('-isa','Stateflow.EMChart','Path',fblock);
assert(~isempty(chart),'MATLAB Function block is not a Stateflow EMChart');
chart.Script=fileread(fullfile(here,'dc_pool_coupled_step_SK.m'));
% Seed complete numeric workspace for stand-alone model compile/build.
seed=timeseries([0;0;0],[0;300;600]);
for k=1:4
 vars={'cl_source_series','cl_dh_series','cl_activity_series','cl_cover_series'};
 assignin('base',vars{k},seed);
end
assignin('base','cl_mode',1);
assignin('base','cl_source_temp',35);
assignin('base','cl_cop_pool',4);
assignin('base','cl_params',[997*500*4182,312.5,800,0.15,27.25,27.60,27.8,300,0.5,70,12,50,5,5,0.95,0.95,1e-4,2.2,7]);

for i=1:numel(inputs)
  add_line(name,[inputs{i} '/1'],sprintf('DC_bazen_spatna_vazba/%d',i),...
    'autorouting','on');
end
for i=1:numel(outnames)
 add_block('simulink/Sinks/To Workspace',[name '/' outnames{i}],...
  'Position',[840 28+50*i 1000 50+50*i],...
  'VariableName',variables{i},'SaveFormat','Timeseries');
 add_line(name,sprintf('DC_bazen_spatna_vazba/%d',i),...
  [outnames{i} '/1'],'autorouting','on');
end
for i=1:3
 add_line(name,sprintf('DC_bazen_spatna_vazba/%d',i),[delays{i,1} '/1'],'autorouting','on');
end
ann=Simulink.Annotation(name,...
 ['Closed loop: bazen odoberie realne teplo -> zvysny zdroj DC -> TČ/teplovodna siet, kazdych 300 s. ' ...
  'Unit Delay states: voda T, energia TES E a termostat H.']);
ann.Position=[220 -15 850 20];
save_system(name,pathSaved);
close_system(name);
fprintf('CLOSED_LOOP_SIMULINK_CREATED %s\n',pathSaved);
end
