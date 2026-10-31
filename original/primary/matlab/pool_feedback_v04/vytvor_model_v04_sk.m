function cesta=vytvor_model_v04_sk()
% Novy model, Stateflow chart + termodynamika + TES; v85/v86 untouched.
folder=fileparts(mfilename('fullpath'));
nazov='DC_Bazen_Uzavreta_Regulacia_v04_SK';
cesta=fullfile(folder,[nazov '.slx']);
assert(~isfile(cesta),'V04:ModelExistuje','Model uz existuje, nic neprepisujeme');
assert(license('test','Stateflow'),'V04:Stateflow','Chyba licencia Stateflow');
if bdIsLoaded(nazov),close_system(nazov,0);end
load_system('sflib');new_system(nazov);
assignin('base','profil_v04',timeseries(zeros(2,11),[0;603900]));
set_param(nazov,'Solver','FixedStepDiscrete','SolverType','Fixed-step',...
    'FixedStep','900','StopTime','603900','ReturnWorkspaceOutputs','on',...
    'SimulationMode','normal');
add_block('simulink/Sources/From Workspace',[nazov '/Prevadzkove_vstupy_DC'],...
    'Position',[40 240 220 285],'VariableName','profil_v04','Interpolate','on',...
    'OutputAfterFinalValue','Holding final value');
add_block('simulink/Discrete/Unit Delay',[nazov '/Teplota_bazena_pred_krokom'],...
    'Position',[55 35 120 65],'SampleTime','900','InitialCondition','16');
add_block('simulink/Discrete/Unit Delay',[nazov '/Energia_TES_pred_krokom'],...
    'Position',[55 85 120 115],'SampleTime','900','InitialCondition','0.45*3.6e9');
add_block('simulink/Discrete/Unit Delay',[nazov '/Termostat_pred_krokom'],...
    'Position',[55 145 120 175],'SampleTime','900','InitialCondition','1');
add_block('simulink/User-Defined Functions/MATLAB Function',[nazov '/Dopyt_bazena_a_straty'],...
    'Position',[280 40 455 185]);
add_block('sflib/Chart',[nazov '/Dispecer_Stateflow'],...
    'Position',[525 45 750 225]);
add_block('simulink/User-Defined Functions/MATLAB Function',[nazov '/Rozdelovac_energie_DC_TES_Bazen'],...
    'Position',[825 80 1050 280]);
rt=sfroot();
demand=rt.find('-isa','Stateflow.EMChart','Path',[nazov '/Dopyt_bazena_a_straty']);
demand.Script=fileread(fullfile(folder,'vypocitaj_dopyt_bazena_sk.txt'));
du=demand.find('-isa','Stateflow.Data','Name','u');du.Props.Array.Size='[1 11]';
alloc=rt.find('-isa','Stateflow.EMChart','Path',[nazov '/Rozdelovac_energie_DC_TES_Bazen']);
alloc.Script=fileread(fullfile(folder,'alokuj_teplo_v04_sk.txt'));
au=alloc.find('-isa','Stateflow.Data','Name','u');au.Props.Array.Size='[1 11]';
ay=alloc.find('-isa','Stateflow.Data','Name','y');ay.Props.Array.Size='[1 25]';
ch=rt.find('-isa','Stateflow.Chart','Path',[nazov '/Dispecer_Stateflow']);
ch.ActionLanguage='MATLAB';ch.ChartUpdate='DISCRETE';ch.SampleTime='900';
ch.Description='Stavy dispecera su realne Stateflow; ich prechody zavisia od teploty bazena, jeho dopytu, zdroja a TES.';
mkData(ch,'ziad','Input',1,'1');
mkData(ch,'u','Input',2,'[1 11]');
mkData(ch,'T','Input',3,'1');
mkData(ch,'E','Input',4,'1');
mkData(ch,'rezim','Output',1,'1');
fun=Stateflow.EMFunction(ch);fun.Name='volba_rezimu_v04_sk';
fun.Script=fileread(fullfile(folder,'volba_rezimu_v04_sk.m'));
fun.Position=[115 505 390 65];
names={'BEZ_ZDROJA','PRIAMY_VYMENNIK','TEPELNE_CERPADLO','CERPAJ_Z_TES','IT_BEZPECNE_ODSTAVENIE'};
states=cell(5,1);
for k=1:5
 st=Stateflow.State(ch);st.Name=names{k};
 st.Position=[60+mod(k-1,3)*290,120+floor((k-1)/3)*160,250,90];
 st.LabelString=sprintf('%s\nen,du:\nrezim=%d;',names{k},k-1);
 states{k}=st;
end
j=Stateflow.Junction(ch);j.Position.Center=[36 42];j.Position.Radius=8;
t=Stateflow.Transition(ch);t.Destination=j;t.DestinationOClock=12;
t.SourceEndPoint=[36 6];t.MidPoint=[36 21];
for k=1:5
 t=Stateflow.Transition(ch);t.Source=j;t.Destination=states{k};
 t.SourceOClock=3;t.DestinationOClock=12;
 t.LabelString=sprintf('[volba_rezimu_v04_sk(ziad,u,T,E)==%d]',k-1);
end
for k=1:5
 for n=1:5
   if n==k,continue;end
   t=Stateflow.Transition(ch);t.Source=states{k};t.Destination=states{n};
   t.SourceOClock=3;t.DestinationOClock=9;
   t.LabelString=sprintf('[volba_rezimu_v04_sk(ziad,u,T,E)==%d]',n-1);
 end
end
% Selector pre stavove veličiny [1,2] z vystupneho vektora 25.
add_block('simulink/Signal Routing/Selector',[nazov '/Nova_teplota'],...
 'NumberOfDimensions','1','IndexOptionArray',{'Index vector (dialog)'},...
 'Indices','1','InputPortWidth','25','Position',[1100 35 1160 65]);
add_block('simulink/Signal Routing/Selector',[nazov '/Nova_energia_TES'],...
 'NumberOfDimensions','1','IndexOptionArray',{'Index vector (dialog)'},...
 'Indices','2','InputPortWidth','25','Position',[1100 105 1160 135]);
add_block('simulink/Sinks/To Workspace',[nazov '/Vysledny_tok_v04'],...
 'Position',[1120 215 1300 255],'VariableName','sim_energeticka_bilancia_v04','SaveFormat','Timeseries');
add_line(nazov,'Teplota_bazena_pred_krokom/1','Dopyt_bazena_a_straty/1','autorouting','on');
add_line(nazov,'Termostat_pred_krokom/1','Dopyt_bazena_a_straty/2','autorouting','on');
add_line(nazov,'Prevadzkove_vstupy_DC/1','Dopyt_bazena_a_straty/3','autorouting','on');
add_line(nazov,'Dopyt_bazena_a_straty/3','Termostat_pred_krokom/1','autorouting','on');
add_line(nazov,'Dopyt_bazena_a_straty/1','Dispecer_Stateflow/1','autorouting','on');
add_line(nazov,'Prevadzkove_vstupy_DC/1','Dispecer_Stateflow/2','autorouting','on');
add_line(nazov,'Teplota_bazena_pred_krokom/1','Dispecer_Stateflow/3','autorouting','on');
add_line(nazov,'Energia_TES_pred_krokom/1','Dispecer_Stateflow/4','autorouting','on');
add_line(nazov,'Teplota_bazena_pred_krokom/1','Rozdelovac_energie_DC_TES_Bazen/1','autorouting','on');
add_line(nazov,'Energia_TES_pred_krokom/1','Rozdelovac_energie_DC_TES_Bazen/2','autorouting','on');
add_line(nazov,'Dopyt_bazena_a_straty/1','Rozdelovac_energie_DC_TES_Bazen/3','autorouting','on');
add_line(nazov,'Dopyt_bazena_a_straty/2','Rozdelovac_energie_DC_TES_Bazen/4','autorouting','on');
add_line(nazov,'Dispecer_Stateflow/1','Rozdelovac_energie_DC_TES_Bazen/5','autorouting','on');
add_line(nazov,'Prevadzkove_vstupy_DC/1','Rozdelovac_energie_DC_TES_Bazen/6','autorouting','on');
add_line(nazov,'Rozdelovac_energie_DC_TES_Bazen/1','Nova_teplota/1','autorouting','on');
add_line(nazov,'Rozdelovac_energie_DC_TES_Bazen/1','Nova_energia_TES/1','autorouting','on');
add_line(nazov,'Nova_teplota/1','Teplota_bazena_pred_krokom/1','autorouting','on');
add_line(nazov,'Nova_energia_TES/1','Energia_TES_pred_krokom/1','autorouting','on');
add_line(nazov,'Rozdelovac_energie_DC_TES_Bazen/1','Vysledny_tok_v04/1','autorouting','on');
an=Simulink.Annotation(nazov,...
 'DC -> HX/TC -> bazen/DH/TES/REJECT | TEPELNÉ A ELEKTRICKÉ BILANCIE | SK | 15 minut');
an.Position=[240 3 1120 28];
set_param(nazov,'SimulationCommand','update');
save_system(nazov,cesta);close_system(nazov,0);
fprintf('MODEL_V04_OK %s\n',cesta);
end
function mkData(ch,name,scope,port,sizeStr)
 d=Stateflow.Data(ch);d.Name=name;d.Scope=scope;d.Port=port;
 d.Props.Array.Size=sizeStr;
end
