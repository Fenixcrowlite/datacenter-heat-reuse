% Jednorazova oprava NOVEJ v08 po prvom QA, iba v08.
f=fileparts(mfilename('fullpath'));model='DC_Bazen_Externe_Merania_v08_SK';
assignin('base','profil_merani_v08',timeseries(zeros(2,23),[0;603900]));
load_system(fullfile(f,[model '.slx']));
rt=sfroot;
gate=rt.find('-isa','Stateflow.EMChart','Path',[model '/Bezpecnostny_gate_bazena']);
assert(numel(gate)==1);
gate.Script=fileread(fullfile(f,'bezpecnostne_meranie_externe_v08.txt'));
set_param(model,'SimulationCommand','update');
save_system(model);close_system(model,0);
fprintf('V08_DOUBLE_BIAS_REMOVED_MODEL_PATCH_PASS\n');
