% Oprava warningov tienovania vstupnych parametrov funkcnej casti chartu v04.
folder=fileparts(mfilename('fullpath'));
model='DC_Bazen_Uzavreta_Regulacia_v04_SK';
assignin('base','profil_v04',timeseries(zeros(2,11),[0;603900]));
load_system(fullfile(folder,[model '.slx']));
rt=sfroot;ch=rt.find('-isa','Stateflow.Chart','Path',[model '/Dispecer_Stateflow']);
fun=ch.find('-isa','Stateflow.EMFunction','Name','volba_rezimu_v04_sk');
assert(numel(fun)==1,'Funkcia chartu nenajdena');
fun.Script=fileread(fullfile(folder,'volba_rezimu_v04_sk.m'));
set_param(model,'SimulationCommand','update');
save_system(model);close_system(model,0);
fprintf('STATEFLOW_SYMBOL_SHADOWING_PATCH_OK\n');
