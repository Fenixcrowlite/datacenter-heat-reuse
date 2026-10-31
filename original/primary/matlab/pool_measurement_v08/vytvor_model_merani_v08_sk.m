function cesta=vytvor_model_merani_v08_sk()
% V08: realny vstup merani do safety gate; zdrojova v07/v85 sa NEPREPISUJE.
f=fileparts(mfilename('fullpath'));root=fileparts(fileparts(f));
old='DC_Bazen_Dvojita_Ochrana_v07_SK';
name='DC_Bazen_Externe_Merania_v08_SK';
src=fullfile(root,'matlab','pool_redundancy_v07',[old '.slx']);
cesta=fullfile(f,[name '.slx']);
assert(isfile(src),'v07 source missing');
assert(~isfile(cesta),'Refuse to overwrite existing v08');
assignin('base','profil_merani_v07',timeseries(zeros(2,21),[0;603900]));
assignin('base','profil_merani_v08',timeseries(zeros(2,23),[0;603900]));
assignin('base','profil_v04',timeseries(zeros(2,11),[0;603900]));
load_system(src);
save_system(old,cesta);close_system(old,0);
load_system(cesta);
% Odstranime virtualne senzory vazane na stav T_model. Nove snimace prichadzaju
% SAMOSTATNE v poslednych dvoch stlpcoch datovej casovej rady.
delete_block([name '/Surove_merania_v07']);
delete_block([name '/Snimac_1_oneskorenie_15min']);
delete_block([name '/Snimac_2_oneskorenie_30min']);
input=[name '/Skutocne_Alebo_Replay_Merania_23'];
add_block('simulink/Sources/From Workspace',input, ...
 'VariableName','profil_merani_v08','Interpolate','on', ...
 'OutputAfterFinalValue','Holding final value','Position',[23 700 252 749]);
demux=[name '/Rozdelenie_21_Signalov_a_2_Teplot'];
add_block('simulink/Signal Routing/Demux',demux,...
 'Outputs','[21 1 1]','Position',[297 680 302 788]);
% Vymazat zostavajuce vetvy na cielovych vstupoch z povodneho modelu.
ports={[name '/Redukcia_IT_zataze'],2;[name '/Bezpecnostny_gate_bazena'],1;[name '/Bezpecnostny_gate_bazena'],2};
for ix=1:size(ports,1)
 hs=get_param(ports{ix,1},'LineHandles');
 existing=hs.Inport(ports{ix,2});
 if existing~=-1,delete_line(existing);end
end
add_line(name,'Skutocne_Alebo_Replay_Merania_23/1',...
 'Rozdelenie_21_Signalov_a_2_Teplot/1','autorouting','on');
add_line(name,'Rozdelenie_21_Signalov_a_2_Teplot/1',...
 'Redukcia_IT_zataze/2','autorouting','on');
add_line(name,'Rozdelenie_21_Signalov_a_2_Teplot/2',...
 'Bezpecnostny_gate_bazena/1','autorouting','on');
add_line(name,'Rozdelenie_21_Signalov_a_2_Teplot/3',...
 'Bezpecnostny_gate_bazena/2','autorouting','on');
% Meranie uz obsahuje bias: zabranujeme jeho druhemu pripocitaniu.
rt=sfroot;
actualGate=rt.find('-isa','Stateflow.EMChart','Path',[name '/Bezpecnostny_gate_bazena']);
actualGate.Script=fileread(fullfile(f,'bezpecnostne_meranie_externe_v08.txt'));
set_param([name '/Vysledny_tok_v04'],'VariableName','tok_v08');
set_param([name '/Zaznam_zabezpecenia'],'VariableName','interlock_v08');
a=Simulink.Annotation(name, ...
 'SK v08: EXTERNE T1/T2 - ZIADNY T_true do BEZPECNOSTNEHO GATE | D-REPLAY != skutocne meranie');
a.Position=[290 906 1340 936];
set_param(name,'SimulationCommand','update');
save_system(name,cesta);close_system(name,0);
fprintf('V08_REAL_EXTERNAL_SENSOR_INPUT_MODEL_BUILT %s\n',cesta);
end
