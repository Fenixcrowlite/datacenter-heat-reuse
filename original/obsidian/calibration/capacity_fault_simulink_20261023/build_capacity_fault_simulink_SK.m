function pathSaved=build_capacity_fault_simulink_SK()
% Own versioned SLX. Original baseline and parallel pool models unchanged.
here=fileparts(mfilename('fullpath'));
name='DC_Pool_Capacity_Fault_20261023_SK';
pathSaved=fullfile(here,[name '.slx']);
assert(exist(pathSaved,'file')~=2,'New version required, never overwrite SLX');
if bdIsLoaded(name),close_system(name,0);end
new_system(name);
set_param(name,'SolverType','Fixed-step','Solver','FixedStepDiscrete',...
    'FixedStep','300','StopTime','604800','ReturnWorkspaceOutputs','on');
inputs={'SrcAvail';'Dhdemand';'Activity';'Cover';...
    'Tprev';'Eprev';'Hprev';'Mode';'SourceTemp';'COPpool';'P';'HPmaxAvailable'};
outnames={'Tnext';'Enext';'Hnext';'Qpool';'QsrcPool';'Wpool';...
    'Qdh';'QsrcDh';'Wdh';'Qgas';'Qcharge';'Qdischarge';'Qloss';'COPdh'};
variables={'cl_Tnext';'cl_Enext';'cl_Hnext';'cl_Qpool';...
    'cl_QsrcPool';'cl_Wpool';'cl_Qdh';'cl_QsrcDh';...
    'cl_Wdh';'cl_Qgas';'cl_Qcharge';'cl_Qdischarge';'cl_Qloss';'cl_COPdh'};
z={'SrcAvail','cl_source_series';'Dhdemand','cl_dh_series';...
   'Activity','cl_activity_series';'Cover','cl_cover_series';...
   'HPmaxAvailable','cl_hp_capacity_series'};
for i=1:size(z,1)
    add_block('simulink/Sources/From Workspace',[name '/' z{i,1}],...
      'Position',[30 30+63*i 190 55+63*i],'VariableName',z{i,2},...
      'Interpolate','on');
end
delays={'Tprev','16';'Eprev','0';'Hprev','1'};
for i=1:3
  add_block('simulink/Discrete/Unit Delay',[name '/' delays{i,1}],...
   'Position',[160 420+67*i 240 450+67*i],...
   'SampleTime','300','InitialCondition',delays{i,2});
end
cons={'Mode','cl_mode';'SourceTemp','cl_source_temp';...
      'COPpool','cl_cop_pool';'P','cl_params'};
for i=1:size(cons,1)
  add_block('simulink/Sources/Constant',[name '/' cons{i,1}],...
   'Position',[30 690+62*i 190 718+62*i],'Value',cons{i,2});
end
fblock=[name '/DC_bazen_kapacita_porucha'];
add_block('simulink/User-Defined Functions/MATLAB Function',fblock,...
    'Position',[390 155 650 730]);
rt=sfroot();
chart=rt.find('-isa','Stateflow.EMChart','Path',fblock);
assert(~isempty(chart),'MATLAB Function block required');
chart.Script=fileread(fullfile(here,'dc_pool_coupled_step_capacity_SK.m'));
seed=timeseries([0;0;0],[0;300;600]);
vars={'cl_source_series','cl_dh_series','cl_activity_series',...
      'cl_cover_series','cl_hp_capacity_series'};
for k=1:numel(vars),assignin('base',vars{k},seed);end
assignin('base','cl_mode',1);
assignin('base','cl_source_temp',35);
assignin('base','cl_cop_pool',4);
assignin('base','cl_params',[997*500*4182,312.5,800,0.15,27.25,27.60,27.8,300,0.5,70,12,50,5,5,0.95,0.95,1e-4,2.2,7]);
for i=1:numel(inputs)
  add_line(name,[inputs{i} '/1'],sprintf('DC_bazen_kapacita_porucha/%d',i),...
    'autorouting','on');
end
for i=1:numel(outnames)
 add_block('simulink/Sinks/To Workspace',[name '/' outnames{i}],...
  'Position',[870 28+50*i 1030 50+50*i],...
  'VariableName',variables{i},'SaveFormat','Timeseries');
 add_line(name,sprintf('DC_bazen_kapacita_porucha/%d',i),...
  [outnames{i} '/1'],'autorouting','on');
end
for i=1:3
 add_line(name,sprintf('DC_bazen_kapacita_porucha/%d',i),[delays{i,1} '/1'],'autorouting','on');
end
ann=Simulink.Annotation(name,...
 ['Samostatna 300s simulacia: realne okamzita alokacia DC tepla pre bazen a DH. ' ...
  'HPmaxAvailable MW je volitelne dostupna menovita kapacita siete pri N+1/fault. ' ...
  'TES a regulacia bazena cez Unit Delay; nezavisi od povodneho SLX.']);
ann.Position=[200 -15 1010 20];
save_system(name,pathSaved);
close_system(name);
fprintf('CAPACITY_FAULT_SIMULINK_CREATED %s\n',pathSaved);
end
