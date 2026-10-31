function cesta=vytvor_most_simulink_v85_sk()
% Novy model bez zapisu do zdrojovych v85 a bazen v02.
folder=fileparts(mfilename('fullpath'));
nazov='Bazen_Prepripojenie_Sluzby_v85_v03_SK';
cesta=fullfile(folder,[nazov '.slx']);
if isfile(cesta)
    error('Existujuci model neprepisujeme: %s',cesta);
end
if bdIsLoaded(nazov),close_system(nazov,0);end
new_system(nazov);
% Vzorky 0.25 h presne ako zdrojove v85 drzane intervaly.
assignin('base','profil_v85',timeseries(zeros(4,6),(0:3)'*900));
set_param(nazov,'SolverType','Fixed-step','Solver','FixedStepDiscrete',...
   'FixedStep','900','StopTime','2700','ReturnWorkspaceOutputs','on');
add_block('simulink/Sources/From Workspace',[nazov '/V85_certifikovana_dodavka_sluzby'],...
   'Position',[30 170 220 215],'VariableName','profil_v85','Interpolate','on');
add_block('simulink/Discrete/Unit Delay',[nazov '/Teplota_vody'],...
   'Position',[60 20 130 55],'SampleTime','900','InitialCondition','16');
add_block('simulink/Discrete/Unit Delay',[nazov '/Termostat'],...
   'Position',[60 83 130 115],'SampleTime','900','InitialCondition','1');
add_block('simulink/User-Defined Functions/MATLAB Function',[nazov '/Presmerovanie_v85_do_bazena'],...
   'Position',[305 85 510 220]);
rt=sfroot;
chart=rt.find('-isa','Stateflow.EMChart','Path',[nazov '/Presmerovanie_v85_do_bazena']);
chart.Script=fileread(fullfile(folder,'krok_bazen_v85.txt'));
u=chart.find('-isa','Stateflow.Data','Name','u');u.Props.Array.Size='[1 6]';
y=chart.find('-isa','Stateflow.Data','Name','y');y.Props.Array.Size='[1 9]';
set_param(nazov,'SimulationCommand','update');
add_line(nazov,'Teplota_vody/1','Presmerovanie_v85_do_bazena/1','autorouting','on');
add_line(nazov,'Termostat/1','Presmerovanie_v85_do_bazena/2','autorouting','on');
add_line(nazov,'V85_certifikovana_dodavka_sluzby/1','Presmerovanie_v85_do_bazena/3','autorouting','on');
add_line(nazov,'Presmerovanie_v85_do_bazena/1','Teplota_vody/1','autorouting','on');
add_line(nazov,'Presmerovanie_v85_do_bazena/2','Termostat/1','autorouting','on');
add_block('simulink/Sinks/To Workspace',[nazov '/Zaznam_bilancie_v85_a_bazen'],...
    'Position',[600 147 780 200],'VariableName','spolu_v85_bazen',...
    'SaveFormat','Timeseries');
add_line(nazov,'Presmerovanie_v85_do_bazena/3','Zaznam_bilancie_v85_a_bazen/1','autorouting','on');
x=Simulink.Annotation(nazov,'SK: V85 VYKON UZ DODANEJ SLUZBY -> BAZEN ALEBO POVODNY ODBERATEL');
x.Position=[150 1 790 25];
set_param(nazov,'SimulationCommand','update');
save_system(nazov,cesta);
close_system(nazov,0);
fprintf('NOVY_SIMULINK_V03 %s\n',cesta);
end
