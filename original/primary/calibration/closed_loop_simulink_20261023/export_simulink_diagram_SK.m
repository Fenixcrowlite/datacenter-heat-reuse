% Export actual Simulink chart diagram for QA and Obsidian.
here=fileparts(mfilename('fullpath'));
model='DC_Pool_Coupled_ClosedLoop_20261023_SK';
load_system(fullfile(here,[model '.slx']));
output=fullfile(here,'DC_Pool_Coupled_Simulink_diagram.png');
print(['-s' model],'-dpng','-r130',output);
close_system(model,0);
fprintf('CLOSED_LOOP_MODEL_DIAGRAM_EXPORTED %s\n',output);
