function dst=vytvor_model_v06_sk()
% New independent v06. Saved v85, v04 and v05 are never modified.
folder=fileparts(mfilename('fullpath'));
root=fileparts(fileparts(folder));
old='DC_Bazen_Bezpecnost_v05_SK';
name='DC_Bazen_Fyzikalne_Poruchy_v06_SK';
src=fullfile(root,'matlab','pool_safety_v05',[old '.slx']);
dst=fullfile(folder,[name '.slx']);
assert(isfile(src),'Source v05 missing');
assert(~isfile(dst),'Refuse to overwrite existing v06');
assignin('base','profil_bezpecnost_v05',timeseries(zeros(2,16),[0;603900]));
assignin('base','profil_v04',timeseries(zeros(2,11),[0;603900]));
assignin('base','profil_poruchy_v06',timeseries(zeros(2,18),[0;603900]));
load_system(src);
save_system(old,dst);
close_system(old,0);
load_system(dst);
% Disconnect the old three-channel sensor logic from physical and raw inputs.
gate=[name '/Bezpecnostny_gate_bazena'];
lh=get_param(gate,'LineHandles');
for k=1:numel(lh.Inport)
 if lh.Inport(k)~=-1,delete_line(lh.Inport(k));end
end
delete_block([name '/Vstupy_DC_a_senzoricke_poruchy']);
add_block('simulink/Sources/From Workspace',...
 [name '/Merane_signaly_a_injekcie_poruch'],...
 'Position',[20 480 232 515],...
 'VariableName','profil_poruchy_v06','Interpolate','on',...
 'OutputAfterFinalValue','Holding final value');
add_block('simulink/Discrete/Unit Delay',...
 [name '/Snimac_1_oneskorenie_15min'],...
 'Position',[30 550 135 585],'SampleTime','900','InitialCondition','16');
add_block('simulink/Discrete/Unit Delay',...
 [name '/Snimac_2_oneskorenie_30min'],...
 'Position',[30 610 135 645],'SampleTime','900','InitialCondition','16');
rt=sfroot;
chart=rt.find('-isa','Stateflow.EMChart','Path',gate);
assert(numel(chart)==1,'Original gate not found in cloned model');
chart.Script=fileread(fullfile(folder,'bezpecnostne_meranie_v06.txt'));
z=chart.find('-isa','Stateflow.Data','Name','raw');
z.Props.Array.Size='[1 18]';
z=chart.find('-isa','Stateflow.Data','Name','safe');
z.Props.Array.Size='[1 11]';
z=chart.find('-isa','Stateflow.Data','Name','flags');
z.Props.Array.Size='[1 10]';
add_line(name,'Teplota_bazena_pred_krokom/1','Snimac_1_oneskorenie_15min/1','autorouting','on');
add_line(name,'Snimac_1_oneskorenie_15min/1','Snimac_2_oneskorenie_30min/1','autorouting','on');
add_line(name,'Snimac_1_oneskorenie_15min/1','Bezpecnostny_gate_bazena/1','autorouting','on');
add_line(name,'Snimac_2_oneskorenie_30min/1','Bezpecnostny_gate_bazena/2','autorouting','on');
add_line(name,'Pamat_zablokovania_bazena/1','Bezpecnostny_gate_bazena/3','autorouting','on');
add_line(name,'Merane_signaly_a_injekcie_poruch/1','Bezpecnostny_gate_bazena/4','autorouting','on');
% Replace ideal command result with physical heat accounting + IT risk buffer.
physical=[name '/Fyzikalny_ventil_a_IT_chladenie'];
add_block('simulink/User-Defined Functions/MATLAB Function',physical,...
 'Position',[1060 355 1305 510]);
ph=rt.find('-isa','Stateflow.EMChart','Path',physical);
ph.Script=fileread(fullfile(folder,'fyzikalne_poruchy_v06.txt'));
z=ph.find('-isa','Stateflow.Data','Name','core');z.Props.Array.Size='[1 25]';
z=ph.find('-isa','Stateflow.Data','Name','raw');z.Props.Array.Size='[1 18]';
z=ph.find('-isa','Stateflow.Data','Name','y');z.Props.Array.Size='[1 33]';
add_block('simulink/Discrete/Unit Delay',[name '/Tepelny_buffer_IT'],...
 'Position',[1060 565 1165 600],'InitialCondition','30','SampleTime','900');
add_block('simulink/Signal Routing/Selector',[name '/Nova_teplota_IT'],...
 'NumberOfDimensions','1','IndexOptionArray',{'Index vector (dialog)'},...
 'Indices','28','InputPortWidth','33','Position',[1370 565 1435 600]);
% Disconnect old ideal-state feedback selectors and diagnostics.
targets={[name '/Nova_teplota'],1;[name '/Nova_energia_TES'],1;[name '/Vysledny_tok_v04'],1};
for k=1:size(targets,1)
 h=get_param(targets{k,1},'LineHandles');
 oldLine=h.Inport(targets{k,2});
 if oldLine~=-1,delete_line(oldLine);end
end
set_param([name '/Nova_teplota'],'InputPortWidth','33');
set_param([name '/Nova_energia_TES'],'InputPortWidth','33');
set_param([name '/Vysledny_tok_v04'],'VariableName','tok_v06');
set_param([name '/Zaznam_zabezpecenia'],'VariableName','interlock_v06');
add_line(name,'Rozdelovac_energie_DC_TES_Bazen/1','Fyzikalny_ventil_a_IT_chladenie/1','autorouting','on');
add_line(name,'Teplota_bazena_pred_krokom/1','Fyzikalny_ventil_a_IT_chladenie/2','autorouting','on');
add_line(name,'Merane_signaly_a_injekcie_poruch/1','Fyzikalny_ventil_a_IT_chladenie/3','autorouting','on');
add_line(name,'Tepelny_buffer_IT/1','Fyzikalny_ventil_a_IT_chladenie/4','autorouting','on');
add_line(name,'Fyzikalny_ventil_a_IT_chladenie/1','Nova_teplota/1','autorouting','on');
add_line(name,'Fyzikalny_ventil_a_IT_chladenie/1','Nova_energia_TES/1','autorouting','on');
add_line(name,'Fyzikalny_ventil_a_IT_chladenie/1','Vysledny_tok_v04/1','autorouting','on');
add_line(name,'Fyzikalny_ventil_a_IT_chladenie/1','Nova_teplota_IT/1','autorouting','on');
add_line(name,'Nova_teplota_IT/1','Tepelny_buffer_IT/1','autorouting','on');
an=Simulink.Annotation(name,...
 'SK v06: ODDIELENY POVEL A REALNY TOK | ZASEKNUTY VENTIL | REJECT FAIL | DVA ONESKORENE SNIMACE');
an.Position=[300 660 1360 690];
set_param(name,'SimulationCommand','update');
save_system(name,dst);
close_system(name,0);
fprintf('V06_BUILT %s\n',dst);
end
