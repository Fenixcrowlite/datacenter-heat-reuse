function export_stateflow_numeric_metadata_v38(folder)
% Disambiguate JSON null (NaN/Inf) from preserved MAT, and record product API.
here=fileparts(mfilename('fullpath'));snap=fullfile(folder,'metadata_source');mkdir(snap);
copyfile(fullfile(here,'export_stateflow_numeric_metadata_v38.m'),snap);
v=load(fullfile(folder,'hp_components.mat'),'probes');flags=struct('id',{},'COP_is_inf',{},'COP_is_nan',{},'COP_is_finite',{},'slope_is_inf',{});
for k=1:numel(v.probes)
    a=v.probes(k);hp=a.output;if isempty(hp),hp=struct('cop_operating',NaN,'heat_output_MW',0);end;cap=hp.heat_output_MW;
    flags(end+1)=struct('id',a.id,'COP_is_inf',isinf(hp.cop_operating),'COP_is_nan',isnan(hp.cop_operating), ...
        'COP_is_finite',isfinite(hp.cop_operating),'slope_is_inf',isinf(4*.3/cap)); %#ok<AGROW>
end
mdl='DCHR_Dispatch_Stateflow_v38';load_system(fullfile(here,[mdl '.slx']));cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
rt=sfroot;ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/Thermal_Dispatch']);
hc=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/HP_Supervisor']);
states=ch.find('-isa','Stateflow.State');hstates=hc.find('-isa','Stateflow.State');
metadata=struct('matlab_version',version,'product_versions',ver,'stateflow_license_test',license('test','Stateflow'), ...
    'thermal_state_names',{get(states,'Name')},'supervisor_state_names',{get(hstates,'Name')}, ...
    'simulation_mode',get_param(mdl,'SimulationMode'),'component_flags',flags);
path=fullfile(folder,'numeric_metadata_v38.json');assert(~isfile(path));fid=fopen(path,'w');assert(fid>0);
cleanup2=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(metadata,PrettyPrint=true)); %#ok<NASGU>
fprintf('NUMERIC_METADATA=%s\n',path);
end
