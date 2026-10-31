function outputDir=run_stateflow_fallback_v33(specDirectory)
% Experiment checkpoint v33 executes saved v32 without rebuilding/modifying it.
here=fileparts(mfilename('fullpath'));root=fileparts(fileparts(here));
addpath(fullfile(root,'matlab'),here);
stamp=char(datetime('now','TimeZone','UTC','Format','yyyyMMdd''T''HHmmssSSS''Z'''));
outputDir=fullfile(root,'results',['stateflow_fallback_v33_' stamp]);assert(~isfolder(outputDir));mkdir(outputDir);
diary(fullfile(outputDir,'matlab_diary.log'));dc=onCleanup(@()diary('off')); %#ok<NASGU>
old=Simulink.fileGenControl('getConfig');gc=onCleanup(@()Simulink.fileGenControl('setConfig','config',old)); %#ok<NASGU>
Simulink.fileGenControl('set','CacheFolder',fullfile(outputDir,'cache'),'CodeGenFolder',fullfile(outputDir,'codegen'),'createDir',true);
assert(license('test','Stateflow'),'Stateflow license unavailable');
snap=fullfile(outputDir,'source_snapshot');mkdir(snap);copyfile(specDirectory,fullfile(snap,'spec'));
paths=[dir(fullfile(here,'*v32.m'));dir(fullfile(here,'*v33.m'))];
for k=1:numel(paths),copyfile(fullfile(paths(k).folder,paths(k).name),snap);end
for f={'DCHR_Dispatch_Stateflow_v32.slx','dchr_stateflow_hp_v30.m'},copyfile(fullfile(here,f{1}),snap);end
for f={'heat_pump_step_v14.m','storage_event_kernel_v31.m','storage_kernel_v30.m','storage_parameters_v30.m'}
    copyfile(fullfile(root,'matlab','+dchr','+components',f{1}),snap);
end
for f={'stateflow_fallback_v33.py','verify_stateflow_fallback_v33.py','stateflow_reference_v32.py', ...
        'stateflow_reference_v30.py','TES_event_reference_v31.py','verify_stateflow_v32.py'}
    copyfile(fullfile(root,'audit',f{1}),snap);
end
spec=jsondecode(fileread(fullfile(specDirectory,'cases.json')));
v=readtable(fullfile(specDirectory,'vectors.csv'),'TextType','string');
sv=readtable(fullfile(specDirectory,'segments.csv'),'TextType','string');
mdl='DCHR_Dispatch_Stateflow_v32';load_system(fullfile(here,[mdl '.slx']));
mc=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
totals=table();segments=table();checks=struct('name',{},'passed',{});
names=v.Properties.VariableNames(5:end);snames=sv.Properties.VariableNames(4:end);
for j=1:numel(spec.cases)
    if iscell(spec.cases),c=spec.cases{j};else,c=spec.cases(j);end
    dt=c.p(1);n=size(c.inputs,1);time=(0:n-1)'*dt;
    s=Simulink.SimulationInput(mdl);
    vn={'dt','stop','input','p','h','E0'};
    values={dt,(n-1)*dt,[time c.inputs],reshape(c.p,1,[]),reshape(c.h,1,[]),c.initial_energy_MWh};
    for k=1:numel(vn),s=s.setVariable(['dchr_' vn{k} '_v32'],values{k},'Workspace',mdl);end
    result=sim(s);save(fullfile(outputDir,[c.id '_simulation.mat']),'result');
    y=samples(result.dispatch_trace_v32,25);raw=samples(result.segment_trace_v32,50);
    e=reshape(result.energy_start_trace_v32.Data,[],1);
    expected=v(v.scenario_id==string(c.id),:);actual=array2table(y,'VariableNames',names);
    record([c.id '_no_error'],isempty(result.ErrorMessage));
    record([c.id '_clock'],near(result.dispatch_trace_v32.Time,time));
    record([c.id '_memory'],near(e(1),c.initial_energy_MWh) && near(e(2:end),y(1:end-1,8)));
    for k=1:numel(names),record([c.id '_' names{k}],near(actual.(names{k}),expected.(names{k})));end
    totals=[totals;table(repmat(string(c.id),n,1),(0:n-1)',time,e, ...
        'VariableNames',{'scenario_id','step','Time_h','Storage_E_Start_MWh'}),actual]; %#ok<AGROW>
    for i=1:n
        for k=1:2
            z=array2table(raw(i,(k-1)*25+(1:25)),'VariableNames',snames);
            want=sv(sv.scenario_id==string(c.id) & sv.step==i-1 & sv.segment==k,:);
            for l=1:numel(snames),record(sprintf('%s_%d_%d_%s',c.id,i,k,snames{l}),near(z.(snames{l}),want.(snames{l})));end
            segments=[segments;table(string(c.id),i-1,k,'VariableNames',{'scenario_id','step','segment'}),z]; %#ok<AGROW>
        end
    end
    fprintf('FALLBACK_SCENARIO=%s intervals=%d\n',c.id,n);
end
writetable(totals,fullfile(outputDir,'stateflow_trace_v33.csv'));
writetable(segments,fullfile(outputDir,'stateflow_segments_v33.csv'));
writetable(struct2table(checks),fullfile(outputDir,'assertions_v33.csv'));
summary=struct('checkpoint_version','0.33','model_version','0.32','matlab_version',version, ...
    'stateflow_license_observed',license('test','Stateflow'),'scenarios',numel(spec.cases),'intervals',height(totals), ...
    'segments',height(segments),'passed',sum([checks.passed]),'failed',sum(~[checks.passed]), ...
    'max_abs_balance_residual_MWh',max(abs(totals.System_Balance_Residual_MWh)), ...
    'physical_validation',false,'article_replication',false,'new_model',false);
writejson(fullfile(outputDir,'summary_v33.json'),summary);
export_stateflow_fallback_mat_v33(outputDir);
disp(summary);assert(all([checks.passed]),'DCHR:v33:ExperimentFailed','See saved assertions.');
fprintf('FALLBACK_OUTPUT=%s\n',outputDir);
    function record(name,ok)
        checks(end+1)=struct('name',name,'passed',logical(ok));
        if ~ok,fprintf(2,'FAIL=%s\n',name);end
    end
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;
if ismatrix(raw) && isequal(size(raw),[n width]),v=raw;
elseif size(raw,1)==width && numel(raw)==n*width,v=reshape(raw,width,n)';
else,error('Unexpected timeseries shape.');end
end
function ok=near(a,b)
a=double(a);b=double(b);finite=isfinite(a)&isfinite(b);
ok=isequal(size(a),size(b)) && all((isnan(a)&isnan(b))|finite,'all') && ...
    all(abs(a(finite)-b(finite))<=2e-9+2e-11*abs(b(finite)),'all');
end
function writejson(path,value)
fid=fopen(path,'w');assert(fid>0);c=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(value,PrettyPrint=true));
end
