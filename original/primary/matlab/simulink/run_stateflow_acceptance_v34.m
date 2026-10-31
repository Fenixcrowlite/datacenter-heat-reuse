function outputDir=run_stateflow_acceptance_v34(specDirectory)
here=fileparts(mfilename('fullpath'));root=fileparts(fileparts(here));addpath(fullfile(root,'matlab'),here);
spec=jsondecode(fileread(fullfile(specDirectory,'cases.json')));
stamp=char(datetime('now','TimeZone','UTC','Format','yyyyMMdd''T''HHmmssSSS''Z'''));
outputDir=fullfile(root,'results',['stateflow_v34_' stamp]);assert(~isfolder(outputDir));mkdir(outputDir);
snap=fullfile(outputDir,'source_snapshot');mkdir(snap);copyfile(specDirectory,fullfile(snap,'spec'));
for pattern={'*v34.m','DCHR_Dispatch_Stateflow_v34.slx','DCHR_Dispatch_Stateflow_v32.slx','dchr_stateflow_hp_v30.m'}
    paths=dir(fullfile(here,pattern{1}));for k=1:numel(paths),copyfile(fullfile(paths(k).folder,paths(k).name),snap);end
end
for f={'heat_pump_step_v14.m','storage_step_v30.m','storage_kernel_v30.m','storage_parameters_v30.m'}
    copyfile(fullfile(root,'matlab','+dchr','+components',f{1}),snap);
end
for f={'stateflow_reference_v34.py','stateflow_reference_v30.py','stateflow_reference_v32.py','verify_stateflow_v34.py'}
    if isfile(fullfile(root,'audit',f{1})),copyfile(fullfile(root,'audit',f{1}),snap);end
end
mdl='DCHR_Dispatch_Stateflow_v34';load_system(fullfile(here,[mdl '.slx']));
load_system(fullfile(here,'DCHR_Dispatch_Stateflow_v32.slx'));
cleanup=onCleanup(@()closeModels()); %#ok<NASGU>
v=readtable(fullfile(specDirectory,'vectors.csv'),'TextType','string');sv=readtable(fullfile(specDirectory,'segments.csv'),'TextType','string');
names={'Mode','HP_Direct_MW','Storage_Charge_MW','Storage_Discharge_MW','Gas_Heat_MW','Unmet_Heat_MW', ...
    'Storage_E_After_Loss_MWh','Storage_E_Next_MWh','Storage_Standing_Loss_MWh','Storage_Charge_Loss_MWh', ...
    'Storage_Discharge_Loss_MWh','Supplied_Heat_MW','System_Balance_Residual_MWh','Storage_T_Start_C', ...
    'Storage_T_Next_C','Storage_Usable_Start_MWh','Storage_Usable_Next_MWh','Heat_Demand_MW', ...
    'HP_Heat_MW','HP_Electric_MW','HP_Source_Used_MW','HP_Request_MW','COP','HP_Available','Source_Unused_MW'};
snames={'Mode','Duration_h','Offset_h','Energy_Start_MWh','Energy_Next_MWh','HP_Direct_MW', ...
    'Storage_Charge_MW','Storage_Discharge_MW','Gas_Heat_MW','Unmet_Heat_MW','HP_Heat_MW', ...
    'HP_Electric_MW','HP_Source_Used_MW','HP_Request_MW','COP','Source_Unused_MW', ...
    'Storage_Standing_Loss_MWh','Storage_Charge_Loss_MWh','Storage_Discharge_Loss_MWh', ...
    'Supplied_Heat_MW','System_Balance_Residual_MWh','Storage_T_Start_C','Storage_T_Next_C','Event_Kind','HP_Available', ...
    'HP_Latch','HP_Age_Start_h','HP_Age_End_h'};
totals=table();segments=table();legacy=table();checks=struct('name',{},'passed',{},'detail',{});
for j=1:numel(spec.cases)
    c=spec.cases(j);c.p=reshape(c.p,1,[]);c.h=reshape(c.h,1,[]);c.c=reshape(c.c,1,[]);
    n=size(c.inputs,1);time=(0:n-1)'*c.p(1);
    result=sim(configure(mdl,c));save(fullfile(outputDir,[c.id '_simulation.mat']),'result');
    y=samples(result.dispatch_trace_v34,25);raw=samples(result.segment_trace_v34,1792);
    e=samples(result.energy_start_trace_v34,1);m=samples(result.clock_start_trace_v34,2);mc=samples(result.clock_end_trace_v34,2);
    actual=array2table(y,'VariableNames',names);expected=v(v.scenario_id==string(c.id),:);
    record([c.id '_time'],near(result.dispatch_trace_v34.Time,time),'One physical interval per input.');
    for k=1:numel(names),record([c.id '_' names{k}],near(actual.(names{k}),expected.(names{k})),'Independent fixture.');end
    record([c.id '_clock'],near([m mc],expected{:,{'HP_Latch_Start','HP_Age_Start_h','HP_Latch_End','HP_Age_End_h'}}),'Physical-hour memory.');
    record([c.id '_memory'],near(e(1),c.initial_energy_MWh)&&near(reshape(e(2:end),[],1),y(1:end-1,8))&& ...
        near(m(1,:),reshape(c.initial_clock,1,[]))&&near(m(2:end,:),mc(1:end-1,:)),'Persistent clock and TES feedback.');
    totals=[totals;table(repmat(string(c.id),n,1),(0:n-1)',time,e,m(:,1),m(:,2),mc(:,1),mc(:,2), ...
        'VariableNames',{'scenario_id','step','Time_h','Storage_E_Start_MWh','HP_Latch_Start','HP_Age_Start_h','HP_Latch_End','HP_Age_End_h'}),actual]; %#ok<AGROW>
    for i=1:n
        expected=sv(sv.scenario_id==string(c.id)&sv.step==i-1,:);positive=0;
        for s=1:64
            z=raw(i,(s-1)*28+(1:28));a=array2table(z,'VariableNames',snames);
            if z(2)>0
                positive=positive+1;exp=expected(expected.segment==s,:);
                for k=1:numel(snames),record(sprintf('%s_%d_%d_%s',c.id,i,s,snames{k}),near(a.(snames{k}),exp.(snames{k})),'Executed event segment.');end
            else
                record(sprintf('%s_%d_%d_padding',c.id,i,s),z(1)==0&&all(z(6:14)==0)&&all(z(17:21)==0)&&z(4)==z(5)&&z(27)==z(28),'Padding has no physical time/flow.');
            end
            segments=[segments;table(string(c.id),i-1,s,'VariableNames',{'scenario_id','step','segment'}),a]; %#ok<AGROW>
        end
        record(sprintf('%s_%d_segment_count',c.id,i),positive==height(expected),'No dropped positive event.');
    end
    if j<=6 || startsWith(c.id,'fallback_') || startsWith(c.id,'initial_capacity_')
        oldresult=sim(configure('DCHR_Dispatch_Stateflow_v32',c));save(fullfile(outputDir,[c.id '_v32_simulation.mat']),'oldresult');
        oldy=samples(oldresult.dispatch_trace_v32,25);
        legacy=[legacy;table(repmat(string(c.id),n,1),(0:n-1)',time,'VariableNames',{'scenario_id','step','Time_h'}),array2table(oldy,'VariableNames',names)]; %#ok<AGROW>
        if j<=6,record([c.id '_verified_v32'],near(y(:,[1:21 23:25]),oldy(:,[1:21 23:25])), ...
            'Six base physical-flow/energy cases agree; explicit HP-OFF command request is now zero.');end
    end
    fprintf('SCENARIO_EXECUTED=%s intervals=%d\n',c.id,n);
end
writetable(totals,fullfile(outputDir,'stateflow_trace_v34.csv'));writetable(segments,fullfile(outputDir,'stateflow_segments_v34.csv'));
writetable(legacy,fullfile(outputDir,'stateflow_v32_comparison.csv'));
rt=sfroot;ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/Thermal_Dispatch']);
hc=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/HP_Supervisor']);
record('saved_chart_structure',numel(ch.find('-isa','Stateflow.State'))==6&&numel(hc.find('-isa','Stateflow.State'))==2,'Actual six thermal and two HP states.');
record('all_modes',isequal(unique(segments.Mode(segments.Duration_h>0))',(0:5)),'All six positive duration modes.');
faults=run_stateflow_faults_v34(mdl,outputDir,spec.cases(1));
record('actual_runtime_rejections',all([faults.rejected]),'Actual domain, event-budget and in-memory corruption rejection.');
writejson(fullfile(outputDir,'fault_evidence_v34.json'),faults);
writetable(struct2table(checks),fullfile(outputDir,'stateflow_assertions_v34.csv'));
summary=struct('version','0.34','timestamp_utc',stamp,'matlab_version',version,'scenarios',numel(spec.cases), ...
    'intervals',height(totals),'slots',height(segments),'positive_segments',sum(segments.Duration_h>0), ...
    'passed',sum([checks.passed]),'failed',sum(~[checks.passed]),'runtime_faults',numel(faults), ...
    'runtime_rejected',sum([faults.rejected]),'modes_observed',unique(segments.Mode(segments.Duration_h>0))', ...
    'max_abs_balance_residual_MWh',max(abs(totals.System_Balance_Residual_MWh)), ...
    'actual_saved_model_executed',true,'standalone_codegen',false,'physical_validation',false,'article_replication',false);
writejson(fullfile(outputDir,'acceptance_summary_v34.json'),summary);disp(summary);
assert(all([checks.passed]),'DCHR:v34:AcceptanceFailed','See timestamped evidence.');fprintf('ACCEPTANCE_OUTPUT=%s\n',outputDir);
    function record(name,ok,detail)
        checks(end+1)=struct('name',name,'passed',logical(ok),'detail',detail);
        if ~ok,fprintf(2,'FAIL=%s\n',name);end
    end
end
function s=configure(mdl,c)
suffix=extractAfter(string(mdl),'Stateflow_');n=size(c.inputs,1);dt=c.p(1);
s=Simulink.SimulationInput(mdl);names={'dt','stop','input','p','h','E0'};
values={dt,(n-1)*dt,[(0:n-1)'*dt c.inputs],c.p,c.h,c.initial_energy_MWh};
if endsWith(mdl,'v34'),names=[names {'c','m0'}];values=[values {c.c,reshape(c.initial_clock,2,1)}];end
for k=1:numel(names),s=s.setVariable(char("dchr_"+names{k}+"_"+suffix),values{k},'Workspace',mdl);end
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;
if ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;
elseif size(raw,1)==width&&numel(raw)==n*width,v=reshape(raw,width,n)';
else,error('DCHR:v34:TraceShape','Unexpected trace shape.');end
end
function ok=near(a,b)
a=double(a);b=double(b);finite=isfinite(a)&isfinite(b);
ok=isequal(size(a),size(b))&&all((isnan(a)&isnan(b))|finite,'all')&&all(abs(a(finite)-b(finite))<=2e-9+2e-11*abs(b(finite)),'all');
end
function writejson(path,value)
fid=fopen(path,'w');assert(fid>0);cleanup=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(value,PrettyPrint=true)); %#ok<NASGU>
end
function closeModels()
for m={'DCHR_Dispatch_Stateflow_v34','DCHR_Dispatch_Stateflow_v32'},if bdIsLoaded(m{1}),close_system(m{1},0);end,end
end
