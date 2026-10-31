function fileNew=vytvor_model_v07_sk()
% Novy samostatny SLX. Povodne v85/v04/v05/v06 sa neupravuju.
f=fileparts(mfilename('fullpath'));root=fileparts(fileparts(f));
old='DC_Bazen_Fyzikalne_Poruchy_v06_SK';
name='DC_Bazen_Dvojita_Ochrana_v07_SK';
input=fullfile(root,'matlab','pool_failure_v06',[old '.slx']);
fileNew=fullfile(f,[name '.slx']);
assert(isfile(input),'V06 model unavailable');
assert(~isfile(fileNew),'Refuse to overwrite v07 model');
assignin('base','profil_poruchy_v06',timeseries(zeros(2,18),[0;603900]));
assignin('base','profil_v04',timeseries(zeros(2,11),[0;603900]));
assignin('base','profil_merani_v07',timeseries(zeros(2,21),[0;603900]));
load_system(input);
save_system(old,fileNew);
close_system(old,0);
load_system(fileNew);
assert(strcmp(get_param(name,'Name'),name),'Clone name mismatch');
% Replace 18-column raw input with 21-column scenario input.
delete_block([name '/Merane_signaly_a_injekcie_poruch']);
gate=[name '/Bezpecnostny_gate_bazena'];
phys=[name '/Fyzikalny_ventil_a_IT_chladenie'];
for pair={gate,4;phys,3}'
  blk=pair{1};idx=pair{2};
  h=get_param(blk,'LineHandles');line=h.Inport(idx);
  if line~=-1,delete_line(line);end
end
add_block('simulink/Sources/From Workspace',[name '/Surove_merania_v07'], ...
 'VariableName','profil_merani_v07','Interpolate','on',...
 'OutputAfterFinalValue','Holding final value','Position',[20 710 235 755]);
add_block('simulink/User-Defined Functions/MATLAB Function',[name '/Redukcia_IT_zataze'],...
 'Position',[280 720 490 820]);
r=sfroot;
der=r.find('-isa','Stateflow.EMChart','Path',[name '/Redukcia_IT_zataze']);
assert(numel(der)==1);
der.Script=fileread(fullfile(f,'uprava_zataze_IT_v07.txt'));
z=der.find('-isa','Stateflow.Data','Name','raw');z.Props.Array.Size='[1 21]';
z=der.find('-isa','Stateflow.Data','Name','y');z.Props.Array.Size='[1 22]';
gateChart=r.find('-isa','Stateflow.EMChart','Path',gate);
z=gateChart.find('-isa','Stateflow.Data','Name','raw');z.Props.Array.Size='[1 22]';
ph=r.find('-isa','Stateflow.EMChart','Path',phys);
ph.Script=fileread(fullfile(f,'fyzikalne_ochrany_v07.txt'));
z=ph.find('-isa','Stateflow.Data','Name','raw');z.Props.Array.Size='[1 22]';
z=ph.find('-isa','Stateflow.Data','Name','y');z.Props.Array.Size='[1 39]';
set_param([name '/Nova_teplota'],'InputPortWidth','39');
set_param([name '/Nova_energia_TES'],'InputPortWidth','39');
set_param([name '/Nova_teplota_IT'],'InputPortWidth','39');
set_param([name '/Vysledny_tok_v04'],'VariableName','tok_v07');
set_param([name '/Zaznam_zabezpecenia'],'VariableName','interlock_v07');
add_line(name,'Surove_merania_v07/1','Redukcia_IT_zataze/2','autorouting','on');
add_line(name,'Tepelny_buffer_IT/1','Redukcia_IT_zataze/1','autorouting','on');
add_line(name,'Redukcia_IT_zataze/1','Bezpecnostny_gate_bazena/4','autorouting','on');
add_line(name,'Redukcia_IT_zataze/1','Fyzikalny_ventil_a_IT_chladenie/3','autorouting','on');
a=Simulink.Annotation(name,'SK v07 | 2 SERIOVE VENTILY | MAIN + BACKUP REJECT | PODMIENENA IT REDUKCIA 70%');
a.Position=[260 860 1290 890];
set_param(name,'SimulationCommand','update');
save_system(name,fileNew);close_system(name,0);
fprintf('BUILT_V07 %s\n',fileNew);
end
