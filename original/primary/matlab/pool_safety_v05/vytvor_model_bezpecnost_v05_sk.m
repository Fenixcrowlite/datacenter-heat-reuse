function pathNew = vytvor_model_bezpecnost_v05_sk()
% Novy model v05, kopia v04 s havarijnym medziobvodom. v04/v85 sa neuklada.
folder=fileparts(mfilename('fullpath'));
proj=fileparts(fileparts(folder));
source=fullfile(proj,'matlab','pool_feedback_v04','DC_Bazen_Uzavreta_Regulacia_v04_SK.slx');
nameOld='DC_Bazen_Uzavreta_Regulacia_v04_SK';
name='DC_Bazen_Bezpecnost_v05_SK';
pathNew=fullfile(folder,[name '.slx']);
assert(isfile(source),'V04 neexistuje');
assert(~isfile(pathNew),'Model v05 uz existuje - neprepisovat');
assignin('base','profil_v04',timeseries(zeros(2,11),[0;603900]));
assignin('base','profil_bezpecnost_v05',timeseries(zeros(2,16),[0;603900]));
load_system(source);
save_system(nameOld,pathNew);
if bdIsLoaded(nameOld)
   close_system(nameOld,0);
end
load_system(pathNew);
model=get_param(name,'Name');assert(strcmp(model,name),'Nespravny nazov kopie SLX');
% Vstup fyzikálneho riadenia zostava 11-kanalovy, surove data maju 16 kan.
delete_block([name '/Prevadzkove_vstupy_DC']);
% Remove dangling connections left on the three original input ports.
ports={[name '/Dopyt_bazena_a_straty'],3;[name '/Dispecer_Stateflow'],2;[name '/Rozdelovac_energie_DC_TES_Bazen'],6};
for idx=1:size(ports,1)
 lh=get_param(ports{idx,1},'LineHandles');
 oldhandle=lh.Inport(ports{idx,2});
 if oldhandle~=-1,delete_line(oldhandle);end
end
add_block('simulink/Sources/From Workspace',[name '/Vstupy_DC_a_senzoricke_poruchy'],...
    'Position',[24 305 220 350],'VariableName','profil_bezpecnost_v05',...
    'Interpolate','on','OutputAfterFinalValue','Holding final value');
add_block('simulink/Discrete/Unit Delay',[name '/Pamat_zablokovania_bazena'],...
    'Position',[44 375 125 405],'InitialCondition','0','SampleTime','900');
add_block('simulink/User-Defined Functions/MATLAB Function',...
    [name '/Bezpecnostny_gate_bazena'],...
    'Position',[260 305 480 435]);
rt=sfroot;
chart=rt.find('-isa','Stateflow.EMChart','Path',[name '/Bezpecnostny_gate_bazena']);
assert(numel(chart)==1,'Chyba bezpecnostna MATLAB Function');
chart.Script=fileread(fullfile(folder,'pool_safety_gate_v05.txt'));
data=chart.find('-isa','Stateflow.Data','Name','raw');data.Props.Array.Size='[1 16]';
data=chart.find('-isa','Stateflow.Data','Name','safe');data.Props.Array.Size='[1 11]';
data=chart.find('-isa','Stateflow.Data','Name','flags');data.Props.Array.Size='[1 10]';
add_block('simulink/Sinks/To Workspace',[name '/Zaznam_zabezpecenia'],...
    'Position',[550 363 730 395],...
    'VariableName','zaznam_interlock_v05','SaveFormat','Timeseries');
% T je oneskorena skutocna modelova teplota, nikoliv meranie od realneho senzora.
add_line(name,'Teplota_bazena_pred_krokom/1','Bezpecnostny_gate_bazena/1','autorouting','on');
add_line(name,'Pamat_zablokovania_bazena/1','Bezpecnostny_gate_bazena/2','autorouting','on');
add_line(name,'Vstupy_DC_a_senzoricke_poruchy/1','Bezpecnostny_gate_bazena/3','autorouting','on');
add_line(name,'Bezpecnostny_gate_bazena/2','Pamat_zablokovania_bazena/1','autorouting','on');
add_line(name,'Bezpecnostny_gate_bazena/3','Zaznam_zabezpecenia/1','autorouting','on');
add_line(name,'Bezpecnostny_gate_bazena/1','Dopyt_bazena_a_straty/3','autorouting','on');
add_line(name,'Bezpecnostny_gate_bazena/1','Dispecer_Stateflow/2','autorouting','on');
add_line(name,'Bezpecnostny_gate_bazena/1','Rozdelovac_energie_DC_TES_Bazen/6','autorouting','on');
a=Simulink.Annotation(name, ...
 'SK | v05 Bezpecnost: senzory 1/2, prietok, E-STOP, rucny reset; ochrana bazena bez vypnutia IT');
a.Position=[250 480 950 510];
set_param(name,'SimulationCommand','update');
save_system(name,pathNew);
close_system(name,0);
fprintf('SAFETY_V05_MODEL_BUILT %s\n',pathNew);
end
