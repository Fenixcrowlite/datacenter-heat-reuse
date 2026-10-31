function outputDir=run_stateflow_acceptance_v32(specDirectory)
% Actual saved-model runs against independently generated segment/totals fixtures.
here=fileparts(mfilename('fullpath'));root=fileparts(fileparts(here));addpath(fullfile(root,'matlab'),here);
spec=jsondecode(fileread(fullfile(specDirectory,'cases.json')));
stamp=char(datetime('now','TimeZone','UTC','Format','yyyyMMdd''T''HHmmssSSS''Z'''));
outputDir=fullfile(root,'results',['stateflow_v32_' stamp]);assert(~isfolder(outputDir));mkdir(outputDir);
snap=fullfile(outputDir,'source_snapshot');mkdir(snap);copyfile(specDirectory,fullfile(snap,'spec'));
paths=[dir(fullfile(here,'*v32.m'));dir(fullfile(root,'audit','*v32.py'))];
for k=1:numel(paths),copyfile(fullfile(paths(k).folder,paths(k).name),snap);end
for f={'dchr_stateflow_hp_v30.m','DCHR_Dispatch_Stateflow_v32.slx','DCHR_Dispatch_Stateflow_v30.slx'}
    copyfile(fullfile(here,f{1}),snap);
end
for f={'heat_pump_step_v14.m','storage_event_kernel_v31.m','storage_step_v30.m','storage_kernel_v30.m','storage_parameters_v30.m'}
    copyfile(fullfile(root,'matlab','+dchr','+components',f{1}),snap);
end
for f={'stateflow_reference_v30.py','TES_event_reference_v31.py'}
    copyfile(fullfile(root,'audit',f{1}),snap);
end
mdl='DCHR_Dispatch_Stateflow_v32';load_system(fullfile(here,[mdl '.slx']));
load_system(fullfile(here,'DCHR_Dispatch_Stateflow_v30.slx'));
cleanup=onCleanup(@()closeModels()); %#ok<NASGU>
v=readtable(fullfile(specDirectory,'vectors.csv'),'TextType','string');
sv=readtable(fullfile(specDirectory,'segments.csv'),'TextType','string');
totals=table();segments=table();legacy=table();checks=struct('name',{},'passed',{},'detail',{});
names={'Mode','HP_Direct_MW','Storage_Charge_MW','Storage_Discharge_MW','Gas_Heat_MW','Unmet_Heat_MW', ...
    'Storage_E_After_Loss_MWh','Storage_E_Next_MWh','Storage_Standing_Loss_MWh','Storage_Charge_Loss_MWh', ...
    'Storage_Discharge_Loss_MWh','Supplied_Heat_MW','System_Balance_Residual_MWh','Storage_T_Start_C', ...
    'Storage_T_Next_C','Storage_Usable_Start_MWh','Storage_Usable_Next_MWh','Heat_Demand_MW', ...
    'HP_Heat_MW','HP_Electric_MW','HP_Source_Used_MW','HP_Request_MW','COP','HP_Available','Source_Unused_MW'};
snames={'Mode','Duration_h','Offset_h','Energy_Start_MWh','Energy_Next_MWh','HP_Direct_MW', ...
    'Storage_Charge_MW','Storage_Discharge_MW','Gas_Heat_MW','Unmet_Heat_MW','HP_Heat_MW', ...
    'HP_Electric_MW','HP_Source_Used_MW','HP_Request_MW','COP','Source_Unused_MW', ...
    'Storage_Standing_Loss_MWh','Storage_Charge_Loss_MWh','Storage_Discharge_Loss_MWh', ...
    'Supplied_Heat_MW','System_Balance_Residual_MWh','Storage_T_Start_C','Storage_T_Next_C','Event_Kind','HP_Available'};
for j=1:numel(spec.cases)
    c=getcase(spec.cases,j);n=size(c.inputs,1);time=(0:n-1)'*c.p(1);
    result=sim(configure(mdl,c));save(fullfile(outputDir,[c.id '_simulation.mat']),'result');
    y=samples(result.dispatch_trace_v32,25);raw=samples(result.segment_trace_v32,50);
    e=reshape(result.energy_start_trace_v32.Data,[],1);
    actual=array2table(y,'VariableNames',names);
    expected=v(v.scenario_id==string(c.id),:);
    record([c.id '_time'],near(result.dispatch_trace_v32.Time,time),'One complete following interval per input sample.');
    for k=1:numel(names)
        record([c.id '_oracle_' names{k}],near(actual.(names{k}),expected.(names{k})),'Independent Python Decimal/event and analytic HP oracle.');
    end
    record([c.id '_memory'],near(e(1),c.initial_energy_MWh) && near(reshape(e(2:end),[],1),y(1:end-1,8)), ...
        'Accepted endpoint fed back once per macro interval.');
    totals=[totals;table(repmat(string(c.id),n,1),(0:n-1)',time,e, ...
        'VariableNames',{'scenario_id','step','Time_h','Storage_E_Start_MWh'}),actual]; %#ok<AGROW>
    for i=1:n
        for s=1:2
            z=raw(i,(s-1)*25+(1:25));a=array2table(z,'VariableNames',snames);
            expected=sv(sv.scenario_id==string(c.id) & sv.step==i-1 & sv.segment==s,:);
            for k=1:numel(snames)
                record(sprintf('%s_%d_%d_%s',c.id,i,s,snames{k}),near(a.(snames{k}),expected.(snames{k})), ...
                    'Actual chart segment execution versus independent fixture.');
            end
            segments=[segments;table(string(c.id),i-1,s,'VariableNames',{'scenario_id','step','segment'}),a]; %#ok<AGROW>
        end
    end
    if any(strcmp(c.id,spec.comparison_ids))
        oldresult=sim(configure('DCHR_Dispatch_Stateflow_v30',c));
        save(fullfile(outputDir,[c.id '_v30_simulation.mat']),'oldresult');
        oldy=samples(oldresult.dispatch_trace_v30,17);oldu=samples(oldresult.hp_trace_v30,8);
        olde=reshape(oldresult.energy_start_trace_v30.Data,[],1);
        legacy=[legacy;table(repmat(string(c.id),n,1),(0:n-1)',time,olde, ...
            'VariableNames',{'scenario_id','step','Time_h','Storage_E_Start_MWh'}), ...
            array2table([oldy oldu],'VariableNames',names)]; %#ok<AGROW>
        record([c.id '_actual_v30_comparison'],isempty(oldresult.ErrorMessage) && size(oldy,1)==n, ...
            'Fresh preserved-v30 reference execution; policy differences expected.');
    end
    fprintf('SCENARIO_EXECUTED=%s intervals=%d\n',c.id,n);
end
writetable(totals,fullfile(outputDir,'stateflow_trace_v32.csv'));
writetable(segments,fullfile(outputDir,'stateflow_segments_v32.csv'));
writetable(legacy,fullfile(outputDir,'stateflow_v30_comparison.csv'));
rt=sfroot;ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/Thermal_Dispatch']);
states=ch.find('-isa','Stateflow.State');transitions=ch.find('-isa','Stateflow.Transition');
record('six_guarded_states',numel(states)==6 && numel(transitions)==37,'Actual saved chart structure.');
record('two_iterations',strcmp(get_param([mdl '/Execute_Segments/For Iterator'],'IterationLimit'),'2') && ...
    strcmp(get_param([mdl '/Execute_Segments/For Iterator'],'ResetStates'),'held'), ...
    'Two chart activations per macro step; states persist between ordered segments.');
record('all_modes',isequal(unique(segments.Mode(segments.Duration_h>0))',(0:5)),'Six positive-duration executed modes.');
fault=run_stateflow_faults_v32(mdl,outputDir,spec);
record('all_runtime_rejections',all([fault.rejected]),'Finite domain/delayed and actual in-memory chart corruption rejections.');
writejson(fullfile(outputDir,'fault_evidence_v32.json'),fault);
writetable(struct2table(checks),fullfile(outputDir,'stateflow_assertions_v32.csv'));
summary=struct('version','0.32','timestamp_utc',stamp,'matlab_version',version,'scenarios',numel(spec.cases), ...
    'intervals',height(totals),'segments',height(segments),'positive_duration_segments',sum(segments.Duration_h>0), ...
    'passed',sum([checks.passed]),'failed',sum(~[checks.passed]),'runtime_faults',numel(fault), ...
    'runtime_rejected',sum([fault.rejected]),'modes_observed',unique(segments.Mode(segments.Duration_h>0))', ...
    'max_abs_balance_residual_MWh',max(abs(totals.System_Balance_Residual_MWh)), ...
    'actual_saved_model_executed',true,'standalone_codegen',false,'physical_validation',false,'article_replication',false);
writejson(fullfile(outputDir,'acceptance_summary_v32.json'),summary);disp(summary);
assert(all([checks.passed]),'DCHR:v32:AcceptanceFailed','See timestamped assertions.');
fprintf('ACCEPTANCE_OUTPUT=%s\n',outputDir);
    function record(name,ok,detail)
        checks(end+1)=struct('name',name,'passed',logical(ok),'detail',detail);
        if ~ok,fprintf(2,'FAIL=%s\n',name);end
    end
end
function c=getcase(cases,j)
if iscell(cases),c=cases{j};else,c=cases(j);end
c.p=reshape(c.p,1,[]);c.h=reshape(c.h,1,[]);
end
function s=configure(mdl,c)
suffix=extractAfter(string(mdl),'Stateflow_');n=size(c.inputs,1);dt=c.p(1);
s=Simulink.SimulationInput(mdl);
names={'dt','stop','input','p','h','E0'};
values={dt,(n-1)*dt,[(0:n-1)'*dt c.inputs],c.p,c.h,c.initial_energy_MWh};
for k=1:numel(names),s=s.setVariable(char("dchr_"+names{k}+"_"+suffix),values{k},'Workspace',mdl);end
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;
if ismatrix(raw) && isequal(size(raw),[n width]),v=raw;
elseif size(raw,1)==width && numel(raw)==n*width,v=reshape(raw,width,n)';
else,error('DCHR:v32:TraceShape','Unexpected timeseries shape.');end
end
function ok=near(a,b)
a=double(a);b=double(b);finite=isfinite(a)&isfinite(b);
ok=isequal(size(a),size(b)) && all((isnan(a)&isnan(b))|finite,'all') && ...
    all(abs(a(finite)-b(finite))<=2e-9+2e-11*abs(b(finite)),'all');
end
function writejson(path,value)
fid=fopen(path,'w');assert(fid>0);cleanup=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(value,PrettyPrint=true));
end
function closeModels()
for m={'DCHR_Dispatch_Stateflow_v32','DCHR_Dispatch_Stateflow_v30'}
    if bdIsLoaded(m{1}),close_system(m{1},0);end
end
end
