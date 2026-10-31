function modelPath=vytvor_rocny_model_sk()
% Samostatna nova verzia. Pôvodne v85/v86 ani bazen v01 sa nemenia.
folder=fileparts(mfilename('fullpath'));
name='DC_Bazen_Alokacia_Rok_v02_SK';
modelPath=fullfile(folder,[name '.slx']);
if bdIsLoaded(name), close_system(name,0); end
if exist(modelPath,'file')
  error('Model v02 uz existuje: %s. Neprepisujeme.',modelPath);
end
new_system(name);
assignin('base','profil_roka',timeseries(zeros(2,10),[0;8759*3600]));
set_param(name,'SolverType','Fixed-step','Solver','FixedStepDiscrete', ...
    'FixedStep','3600','StopTime',num2str(8759*3600),'ReturnWorkspaceOutputs','on');
add_block('simulink/Sources/From Workspace',[name '/Rocny_profil_DC_a_bazena'],...
    'Position',[40 160 220 210],'VariableName','profil_roka','Interpolate','on');
add_block('simulink/Discrete/Unit Delay',[name '/Teplota_vody_pred_krokom'],...
    'Position',[85 40 150 80],'SampleTime','3600','InitialCondition','16');
add_block('simulink/Discrete/Unit Delay',[name '/Termostat_pred_krokom'],...
    'Position',[85 95 150 135],'SampleTime','3600','InitialCondition','1');
add_block('simulink/User-Defined Functions/MATLAB Function',[name '/Tok_tepla_DC_Bazen'],...
    'Position',[300 80 505 225]);
rt=sfroot();
block=rt.find('-isa','Stateflow.EMChart','Path',[name '/Tok_tepla_DC_Bazen']);
assert(~isempty(block),'MATLAB Function blok nebol vytvoreny');
block.Script=fileread(fullfile(folder,'blok_tok_dc_bazen_sk.txt'));
inputU=block.find('-isa','Stateflow.Data','Name','u');
inputU.Props.Array.Size='[1 10]';
outputM=block.find('-isa','Stateflow.Data','Name','meranie');
outputM.Props.Array.Size='[1 12]';
set_param(name,'SimulationCommand','update');
add_line(name,'Teplota_vody_pred_krokom/1','Tok_tepla_DC_Bazen/1','autorouting','on');
add_line(name,'Termostat_pred_krokom/1','Tok_tepla_DC_Bazen/2','autorouting','on');
add_line(name,'Rocny_profil_DC_a_bazena/1','Tok_tepla_DC_Bazen/3','autorouting','on');
add_line(name,'Tok_tepla_DC_Bazen/1','Teplota_vody_pred_krokom/1','autorouting','on');
add_line(name,'Tok_tepla_DC_Bazen/2','Termostat_pred_krokom/1','autorouting','on');
add_block('simulink/Sinks/To Workspace',[name '/Zaznam_rocnej_bilancie'],...
    'Position',[590 150 770 200],'VariableName','rok_signaly','SaveFormat','Timeseries');
add_line(name,'Tok_tepla_DC_Bazen/3','Zaznam_rocnej_bilancie/1','autorouting','on');
a=Simulink.Annotation(name,'SK: DC -> VYMENNIK / TC -> BAZEN | DH / TES / ODPAD, rocna hodinova bilancia');
a.Position=[180 5 720 30];
set_param(name,'SimulationCommand','update');
save_system(name,modelPath);
close_system(name,0);
fprintf('MODEL_V02_VYTVORENY %s\n',modelPath);
end
