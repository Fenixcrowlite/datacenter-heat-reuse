function outputDir = run_stateflow_acceptance_v30(specDirectory)
% Executable v30 six-mode, temperature, cutoff, exact-flow and comparison gate.
here=fileparts(mfilename('fullpath')); root=fileparts(fileparts(here));
addpath(fullfile(root,'matlab'),here);
assert(nargin==1,'DCHR:v30:SpecRequired','Provide independent timestamped specification directory.');
stamp=char(datetime('now','TimeZone','UTC','Format','yyyyMMdd''T''HHmmssSSS''Z'''));
outputDir=fullfile(root,'results',['stateflow_v30_' stamp]);
assert(~isfolder(outputDir));mkdir(outputDir);
snap=fullfile(outputDir,'source_snapshot');mkdir(snap);
copyfile(specDirectory,fullfile(snap,'spec'));
files=[dir(fullfile(here,'*v30.m'));dir(fullfile(root,'matlab','+dchr','*v30.m')); ...
    dir(fullfile(root,'matlab','+dchr','+components','*v30.m'))];
for k=1:numel(files),copyfile(fullfile(files(k).folder,files(k).name),snap);end
copyfile(fullfile(root,'matlab','+dchr','+components','heat_pump_step_v14.m'),snap);
copyfile(fullfile(root,'audit','stateflow_reference_v30.py'),snap);
mdl='DCHR_Dispatch_Stateflow_v30';path=fullfile(here,[mdl '.slx']);
assert(isfile(path),'DCHR:v30:ModelMissing','Build model first.');copyfile(path,snap);
copyfile(fullfile(here,'DCHR_Dispatch_Stateflow_v28.slx'),snap);
load_system(path);load_system(fullfile(here,'DCHR_Dispatch_Stateflow_v28.slx'));
cleanup=onCleanup(@()closeModels()); %#ok<NASGU>
oldGen=Simulink.fileGenControl('getConfig');
genCleanup=onCleanup(@()Simulink.fileGenControl('setConfig','config',oldGen)); %#ok<NASGU>
Simulink.fileGenControl('set','CacheFolder',fullfile(outputDir,'cache'), ...
    'CodeGenFolder',fullfile(outputDir,'codegen'),'createDir',true);
spec=jsondecode(fileread(fullfile(specDirectory,'cases.json')));
vectors=readtable(fullfile(specDirectory,'vectors.csv'),'TextType','string');
checks=struct('name',{},'passed',{},'detail',{});combined=table();comparison=table();
ports={'Mode','HP_Direct_MW','Storage_Charge_MW','Storage_Discharge_MW','Gas_Heat_MW', ...
    'Unmet_Heat_MW','Storage_E_After_Loss_MWh','Storage_E_Next_MWh','Storage_Standing_Loss_MWh', ...
    'Storage_Charge_Loss_MWh','Storage_Discharge_Loss_MWh','Supplied_Heat_MW', ...
    'System_Balance_Residual_MWh','Storage_T_Start_C','Storage_T_Next_C', ...
    'Storage_Usable_Start_MWh','Storage_Usable_Next_MWh'};
hpNames={'Heat_Demand_MW','HP_Heat_MW','HP_Electric_MW','HP_Source_Used_MW', ...
    'HP_Request_MW','COP','HP_Available','Source_Unused_MW'};
for j=1:numel(spec.cases)
    if iscell(spec.cases), c=spec.cases{j}; else,c=spec.cases(j);end
    c.p=reshape(c.p,1,[]);c.h=reshape(c.h,1,[]);
    x=c.inputs;n=size(x,1);dt=c.p(1);time=(0:n-1)'*dt;
    input=array2table(x,'VariableNames',{'Source_Heat_MW','Source_C','Sink_C','Heat_Demand_MW','Delivery_C'});
    result=sim(configure(mdl,c));save(fullfile(outputDir,[c.id '_simulation.mat']),'result');
    y=samples(result.dispatch_trace_v30,17);u=samples(result.hp_trace_v30,8);
    e=reshape(result.energy_start_trace_v30.Data,[],1);
    actual=[array2table(y,'VariableNames',ports),array2table(u,'VariableNames',hpNames), ...
        table(e,'VariableNames',{'Storage_E_Start_MWh'})];
    expected=vectors(vectors.scenario_id==string(c.id),:);
    record([c.id '_sample_times'],numel(result.dispatch_trace_v30.Time)==n && ...
        near(result.dispatch_trace_v30.Time,time),'One following interval per sampled input including StopTime.');
    names=actual.Properties.VariableNames;
    for k=1:numel(names)
        expectedColumn=['expected_' names{k}];
        if strcmp(names{k},'Storage_E_Start_MWh'),expectedColumn=names{k};end
        record([c.id '_python_' names{k}],near(actual.(names{k}),expected.(expectedColumn)) , ...
            'Actual Stateflow vs independent Decimal TES and analytic HP-root oracle.');
    end
    cfg=configuration(c);reference=dchr.simulate_dispatch_v30(cfg,input);
    for k=1:numel(names)
        record([c.id '_matlab_' names{k}],near(actual.(names{k}),reference.(names{k})), ...
            'Separate numerical dispatch without chart chooser/allocator; shared components.');
    end
    record([c.id '_memory'],near(e(1),c.initial_energy_MWh) && near(reshape(e(2:end),[],1),y(1:end-1,8)), ...
        'Unit Delay carries accepted endpoint physical energy.');
    record([c.id '_balance'],all(abs(y(:,13))<1e-9),'Independent interval first-law closure.');
    record([c.id '_cutoff'],all(y(:,4)==0 | min(e,y(:,8))>=c.p(8)-1e-9), ...
        'Constant-port monotone trajectory stays above cutoff during discharge.');
    record([c.id '_bounds'],all(y(:,8)>=-1e-10 & y(:,8)<=c.p(2)+1e-10) && ...
        all(y(:,3)>=0 & y(:,3)<=c.p(3)+1e-10) && all(y(:,4)>=0 & y(:,4)<=c.p(4)+1e-10) && ...
        all(y(:,5)>=0 & y(:,5)<=c.p(11)+1e-10) && all(y(:,3).*y(:,4)==0), ...
        'Capacity, charge/discharge/boiler limits and exclusivity.');
    combined=[combined;table(repmat(string(c.id),n,1),time,'VariableNames',{'scenario_id','Time_h'}),actual]; %#ok<AGROW>
    fprintf('SCENARIO_EXECUTED=%s intervals=%d\n',c.id,n);
    if startsWith(c.id,'partition_')
        old=c;old.p=[c.p(1:7),c.p(11)];
        old.inputs=x(:,1:4);oldresult=sim(configure('DCHR_Dispatch_Stateflow_v28',old));
        save(fullfile(outputDir,[c.id '_v28_comparison.mat']),'oldresult');
        oldy=samples(oldresult.dispatch_trace_v28,13);
        difference=oldy(end,8)-y(end,8);
        power=c.p(5)*y(1,3)-y(1,4)/c.p(6);rate=c.p(7);
        exact=exp(-rate*2)*c.initial_energy_MWh+power*(-expm1(-rate*2)/rate);
        expectedBias=power*(dt+expm1(-rate*dt)/rate)*(-expm1(-rate*2))/(-expm1(-rate*dt));
        record([c.id '_exact_active_partition'],near(y(end,8),exact),'Unconstrained two-hour exact constant-power endpoint.');
        record([c.id '_actual_v28_bias'],near(difference,expectedBias),'Actual preserved v28 loss-first discretization bias.');
        comparison=[comparison;table(string(c.id),dt,power,y(end,8),oldy(end,8),exact,difference,expectedBias, ...
            'VariableNames',{'scenario_id','dt_h','internal_power_MW','v30_end_MWh','v28_end_MWh', ...
            'continuous_end_MWh','v28_minus_v30_MWh','predicted_split_bias_MWh'})]; %#ok<AGROW>
    end
end
writetable(combined,fullfile(outputDir,'stateflow_trace_v30.csv'));
writetable(comparison,fullfile(outputDir,'active_flow_comparison_v30.csv'));
record('all_six_modes',isequal(unique(combined.Mode),(0:5)'),'Six required operating modes executed.');
rt=sfroot;chart=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Thermal_Dispatch']);
states=chart.find('-isa','Stateflow.State');transitions=chart.find('-isa','Stateflow.Transition');
structure=struct('matlab_version',version,'stateflow_license',license('test','Stateflow'), ...
    'states',{{states.Name}},'state_actions',{{states.LabelString}}, ...
    'transition_labels',{{transitions.LabelString}},'sample_time',chart.SampleTime, ...
    'initialize_execution',chart.ExecuteAtInitialization,'embedded_sources',struct());
functions={'stateflow_choose_mode_v30','stateflow_allocate_v30','storage_kernel_v30'};
for k=1:numel(functions)
    f=chart.find('-isa','Stateflow.EMFunction','Name',functions{k});
    source=fullfile(snap,[functions{k} '.m']);
    structure.embedded_sources.(functions{k})=f.Script;
    record(['embedded_' functions{k}],strcmp(f.Script,fileread(source)),'Saved chart embeds snapshotted reviewed source.');
end
monitor=rt.find('-isa','Stateflow.EMChart','Path',[mdl '/Runtime_Contract_Gate']);
record('embedded_monitor',strcmp(monitor.Script,fileread(fullfile(snap,'stateflow_contract_gate_v30.m'))),'Saved numerical gate matches source.');
structure.embedded_sources.stateflow_contract_gate_v30=monitor.Script;
structure.tes_delay=get_param([mdl '/TES_Energy_Memory'],'BlockType');
structure.feedback_index=get_param([mdl '/Next_TES_Energy'],'Indices');
record('guarded_state_chart',numel(states)==6 && numel(transitions)==37 && ...
    sum(contains(string({transitions.LabelString}),'stateflow_choose_mode_v30'))==36, ...
    'All initial and inter-state transitions use physical dispatch guards.');
writejson(fullfile(outputDir,'model_structure_v30.json'),structure);
faults=run_stateflow_faults_v30(mdl,outputDir,spec.cases);
record('fault_gate',faults.failed==0 && faults.cases==18,'Executed 12 domain, 2 delayed and 4 monitor faults.');
writetable(struct2table(checks),fullfile(outputDir,'stateflow_assertions_v30.csv'));
summary=struct('version','0.30','timestamp_utc',stamp,'matlab_version',version, ...
    'scenarios',numel(spec.cases),'intervals',height(combined),'checks',numel(checks), ...
    'passed',sum([checks.passed]),'failed',sum(~[checks.passed]),'faults',faults, ...
    'modes_observed',unique(combined.Mode)','max_abs_balance_residual_MWh',max(abs(combined.System_Balance_Residual_MWh)), ...
    'actual_saved_model_executed',true,'standalone_codegen',false,'measured_physical_validation',false, ...
    'primary_article_replication',false,'output_directory',outputDir);
writejson(fullfile(outputDir,'acceptance_summary_v30.json'),summary);disp(summary);
assert(all([checks.passed]),'DCHR:v30:AcceptanceFailed','See saved assertions.');
fprintf('ACCEPTANCE_OUTPUT=%s\n',outputDir);
    function record(name,passed,detail)
        checks(end+1)=struct('name',name,'passed',logical(passed),'detail',detail);
        if ~passed,fprintf(2,'FAIL %s\n',name);end
    end
end

function s=configure(mdl,c)
suffix=extractAfter(string(mdl),'Stateflow_');n=size(c.inputs,1);dt=c.p(1);
s=Simulink.SimulationInput(mdl);
names={'dt','stop','input','p','h','E0'};
values={dt,(n-1)*dt,[(0:n-1)'*dt c.inputs],c.p,c.h,c.initial_energy_MWh};
for k=1:numel(names),s=s.setVariable(char("dchr_"+names{k}+"_"+suffix),values{k},'Workspace',mdl);end
end

function cfg=configuration(c)
p=c.p;h=c.h;cfg.sim.dt_h=p(1);
cfg.storage=struct('heat_capacity_MWh_per_K',p(9),'ambient_C',p(10), ...
    'delivery_cutoff_C',p(10)+p(8)/p(9),'max_temperature_C',p(10)+p(2)/p(9), ...
    'initial_temperature_C',p(10)+c.initial_energy_MWh/p(9), ...
    'charge_limit_MW',p(3),'discharge_limit_MW',p(4),'eta_charge',p(5), ...
    'eta_discharge',p(6),'continuous_loss_rate_per_h',p(7));
cfg.backup.max_heat_MW=p(11);
cfg.hp=struct('max_heat_output_MW',h(1),'carnot_efficiency',h(2),'cop_min',h(3), ...
    'cop_max',h(4),'part_load_penalty',h(5),'poly_c0',h(7),'poly_c1',h(8),'poly_c2',h(9));
cfg.model.hp_backend='carnot';if h(6)==1,cfg.model.hp_backend='lift_polynomial';end
end

function ok=near(a,b)
a=double(a);b=double(b);finite=isfinite(a)&isfinite(b);
ok=isequal(size(a),size(b)) && all((isnan(a)&isnan(b))|finite,'all') && ...
    all(abs(a(finite)-b(finite))<=1e-9+1e-11*abs(b(finite)),'all');
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;
if ismatrix(raw) && isequal(size(raw),[n width]),v=raw;
elseif size(raw,1)==width && numel(raw)==n*width,v=reshape(raw,width,n)';
else,error('DCHR:v30:TraceDimensions','Unexpected trace shape.');end
end
function writejson(path,value)
fid=fopen(path,'w');assert(fid>0);cleanup=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(value,PrettyPrint=true));
end
function closeModels()
for m={'DCHR_Dispatch_Stateflow_v30','DCHR_Dispatch_Stateflow_v28'}
    if bdIsLoaded(m{1}),close_system(m{1},0);end
end
end
