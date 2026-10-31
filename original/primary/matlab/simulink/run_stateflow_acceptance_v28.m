function outputDir = run_stateflow_acceptance_v28()
% Execute new exponential-retention model, compare numerical/reference/legacy ports.
here=fileparts(mfilename('fullpath')); root=fileparts(fileparts(here));
addpath(fullfile(root,'matlab'),here);
stamp=char(datetime('now','TimeZone','UTC','Format','yyyyMMdd''T''HHmmssSSS''Z'''));
outputDir=fullfile(root,'results',['stateflow_v28_' stamp]);
assert(~isfolder(outputDir),'DCHR:v28:EvidenceExists','Refuse evidence overwrite.'); mkdir(outputDir);
snapshot=fullfile(outputDir,'source_snapshot'); mkdir(snapshot);
files=[dir(fullfile(here,'*v28.m'));dir(fullfile(root,'matlab','+dchr','*v28.m')); ...
    dir(fullfile(root,'matlab','+dchr','+components','*v28.m'))];
for k=1:numel(files), copyfile(fullfile(files(k).folder,files(k).name),fullfile(snapshot,files(k).name)); end
copyfile(fullfile(root,'audit','stateflow_qa_vectors_v28.csv'),snapshot);
copyfile(fullfile(root,'audit','stateflow_domain_cases_v28.json'),snapshot);
copyfile(fullfile(root,'audit','dispatch_reference_vectors_v18.csv'),snapshot);
mdl='DCHR_Dispatch_Stateflow_v28'; modelPath=fullfile(here,[mdl '.slx']);
assert(isfile(modelPath),'DCHR:v28:ModelMissing','Build the versioned model first.');
load_system(modelPath); load_system(fullfile(here,'DCHR_Dispatch_Stateflow_v24.slx'));
cleanup=onCleanup(@()close_models(mdl)); %#ok<NASGU>
previousFileGen=Simulink.fileGenControl('getConfig');
fileGenCleanup=onCleanup(@()Simulink.fileGenControl('setConfig','config',previousFileGen)); %#ok<NASGU>
Simulink.fileGenControl('set','CacheFolder',fullfile(outputDir,'cache'), ...
    'CodeGenFolder',fullfile(outputDir,'codegen'),'createDir',true);
checks=struct('name',{},'passed',{},'detail',{}); combined=table();
sources={fullfile(root,'audit','stateflow_qa_vectors_v28.csv'), ...
    fullfile(root,'audit','dispatch_reference_vectors_v18.csv')};
assert(isfile(sources{1}),'DCHR:v28:QAAbsent','Independent QA vectors required.');
for f=1:numel(sources)
    v=readtable(sources{f},'TextType','string');
    if f==2
        % New explicit continuous rate: old numbers reused only as scenarios.
        v.continuous_loss_rate_per_h=v.loss_fraction_per_h;
        v.scenario_id="legacy_input_"+v.scenario_id;
    end
    v.scheme=repmat("exponential_loss_first",height(v),1);
    ids=unique(v.scenario_id,'stable');
    for j=1:numel(ids)
        r=v(v.scenario_id==ids(j),:); cfg=configuration(r(1,:));
        input=r(:,{'Source_Heat_MW','Source_C','Sink_C','Heat_Demand_MW'});
        reference=dchr.simulate_dispatch_v28(cfg,input); % also strict domain gate
        n=height(r); dt=cfg.sim.dt_h;
        p=[dt cfg.storage.capacity_MWh cfg.storage.charge_limit_MW cfg.storage.discharge_limit_MW ...
            cfg.storage.eta_charge cfg.storage.eta_discharge cfg.storage.continuous_loss_rate_per_h cfg.backup.max_heat_MW];
        h=[cfg.hp.max_heat_output_MW cfg.hp.carnot_efficiency cfg.hp.cop_min cfg.hp.cop_max ...
            cfg.hp.part_load_penalty double(string(cfg.model.hp_backend)=="lift_polynomial") ...
            cfg.hp.poly_c0 cfg.hp.poly_c1 cfg.hp.poly_c2];
        s=Simulink.SimulationInput(mdl);
        s=s.setVariable('dchr_dt_v28',dt,'Workspace',mdl);
        s=s.setVariable('dchr_stop_v28',(n-1)*dt,'Workspace',mdl);
        s=s.setVariable('dchr_input_v28',[(0:n-1)'*dt table2array(input)],'Workspace',mdl);
        s=s.setVariable('dchr_p_v28',p,'Workspace',mdl);
        s=s.setVariable('dchr_h_v28',h,'Workspace',mdl);
        s=s.setVariable('dchr_E0_v28',cfg.storage.initial_soc*p(2),'Workspace',mdl);
        result=sim(s);
        save(fullfile(outputDir,char(ids(j)+"_simulation.mat")),'result');
        y=samples(result.dispatch_trace_v28,13);
        u=samples(result.hp_trace_v28,8);
        e=reshape(result.energy_start_trace_v28.Data,[],1);
        time=result.dispatch_trace_v28.Time;
        record(ids(j)+"_sample_times",numel(time)==n && max(abs(time-(0:n-1)'*dt))<1e-10, ...
            'One logged interval at each scenario time; no duplicate initialization/final interval.');
        actual=table(time,input.Source_Heat_MW,input.Source_C,input.Sink_C,input.Heat_Demand_MW, ...
            u(:,5),u(:,2),y(:,2),u(:,3),u(:,4),u(:,6),logical(u(:,7)),u(:,8), ...
            y(:,3),y(:,4),e,y(:,7),y(:,8),y(:,9),y(:,10),y(:,11),y(:,5),y(:,6),y(:,12),y(:,13),y(:,1), ...
            'VariableNames',{'Time_h','Source_Heat_MW','Source_C','Sink_C','Heat_Demand_MW', ...
            'HP_Request_MW','HP_Heat_MW','HP_Direct_MW','HP_Electric_MW','HP_Source_Used_MW','COP', ...
            'HP_Available','Source_Unused_MW','Storage_Charge_MW','Storage_Discharge_MW','Storage_E_Start_MWh', ...
            'Storage_E_After_Loss_MWh','Storage_E_Next_MWh','Storage_Standing_Loss_MWh','Storage_Charge_Loss_MWh', ...
            'Storage_Discharge_Loss_MWh','Gas_Heat_MW','Unmet_Heat_MW','Supplied_Heat_MW','System_Balance_Residual_MWh','Mode'});
        expectedNames=v.Properties.VariableNames(startsWith(v.Properties.VariableNames,'expected_'));
        if f==2, expectedNames={}; end % v18 states follow preserved linear physics.
        for k=1:numel(expectedNames)
            name=extractAfter(string(expectedNames{k}),9);
            record(ids(j)+"_python_"+name,near(actual.(name),r.(expectedNames{k})), ...
                'Actual executable model vs independent stored numerical reference.');
        end
        names=reference.Properties.VariableNames(6:end);
        for k=1:numel(names)
            record(ids(j)+"_v28_reference_"+string(names{k}),near(actual.(names{k}),reference.(names{k})), ...
                'Actual executable Stateflow vs separate v28 MATLAB numerical dispatch.');
        end
        % Same finite-step map as legacy linear model only after explicit conversion.
        legacyCfg=cfg;
        legacyCfg.storage.loss_fraction_per_h=-expm1(-p(7)*dt)/dt;
        oldReference=dchr.simulate_dispatch_v16(legacyCfg,input);
        for k=1:numel(names)
            record(ids(j)+"_v16_equivalent_retention_"+string(names{k}), ...
                near(actual.(names{k}),oldReference.(names{k})), ...
                'Legacy fraction explicitly converted; this is algebraic equivalence, not new physics validation.');
        end
        old=Simulink.SimulationInput('DCHR_Dispatch_Stateflow_v24');
        old=old.setVariable('dchr_dt_v24',dt,'Workspace','DCHR_Dispatch_Stateflow_v24');
        old=old.setVariable('dchr_stop_v24',(n-1)*dt,'Workspace','DCHR_Dispatch_Stateflow_v24');
        old=old.setVariable('dchr_input_v24',[(0:n-1)'*dt table2array(input)],'Workspace','DCHR_Dispatch_Stateflow_v24');
        oldp=p; oldp(7)=legacyCfg.storage.loss_fraction_per_h;
        old=old.setVariable('dchr_p_v24',oldp,'Workspace','DCHR_Dispatch_Stateflow_v24');
        old=old.setVariable('dchr_h_v24',h,'Workspace','DCHR_Dispatch_Stateflow_v24');
        old=old.setVariable('dchr_E0_v24',cfg.storage.initial_soc*p(2),'Workspace','DCHR_Dispatch_Stateflow_v24');
        oldResult=sim(old);
        save(fullfile(outputDir,char(ids(j)+"_legacy_equivalent_simulation.mat")),'oldResult');
        record(ids(j)+"_actual_v24_equivalent_ports", ...
            near(y,samples(oldResult.dispatch_trace_v24,13)) && ...
            near(u,samples(oldResult.hp_trace_v24,8)) && ...
            near(e,reshape(oldResult.energy_start_trace_v24.Data,[],1)), ...
            'Actual preserved v24 model and new v28 match after effective-fraction conversion.');
        expectedMode=zeros(n,1);
        expectedMode(reference.HP_Direct_MW>0)=1;
        expectedMode(reference.Storage_Charge_MW>0)=2;
        expectedMode(reference.Storage_Discharge_MW>0)=3;
        expectedMode(reference.Gas_Heat_MW>0)=4;
        expectedMode(reference.Unmet_Heat_MW>0)=5;
        record(ids(j)+"_mode_transition",isequal(actual.Mode,expectedMode), ...
            'Current-tick active mode matches highest service condition, including startup.');
        record(ids(j)+"_energy_memory",near(e(1),cfg.storage.initial_soc*p(2)) && ...
            near(e(2:end),actual.Storage_E_Next_MWh(1:end-1)), 'Initial SOC and next-to-start feedback continuity.');
        record(ids(j)+"_energy_closure",all(abs(actual.System_Balance_Residual_MWh)<1e-9), ...
            'Source + compressor + boiler + TES start = supplied heat + TES next + losses.');
        record(ids(j)+"_demand_closure",near(actual.HP_Direct_MW+actual.Storage_Discharge_MW+ ...
            actual.Gas_Heat_MW+actual.Unmet_Heat_MW,actual.Heat_Demand_MW), 'Finite boiler plus unmet demand.');
        record(ids(j)+"_bounds",all(actual.Storage_E_Next_MWh>=0 & actual.Storage_E_Next_MWh<=p(2)+1e-9) && ...
            all(actual.Storage_Charge_MW>=0 & actual.Storage_Charge_MW<=p(3)+1e-9) && ...
            all(actual.Storage_Discharge_MW>=0 & actual.Storage_Discharge_MW<=p(4)+1e-9) && ...
            all(actual.Gas_Heat_MW>=0 & actual.Gas_Heat_MW<=p(8)+1e-9) && ...
            all(actual.Unmet_Heat_MW>=0) && all(actual.Storage_Charge_MW.*actual.Storage_Discharge_MW==0), ...
            'Nonnegative bounded TES and boiler, mutually exclusive TES ports.');
        configNames={'scenario_id','step','dt_h','storage_capacity_MWh','charge_limit_MW','discharge_limit_MW', ...
            'eta_charge','eta_discharge','continuous_loss_rate_per_h','boiler_capacity_MW','hp_capacity_MW', ...
            'carnot_efficiency','cop_min','cop_max','part_load_penalty','backend','poly_c0','poly_c1','poly_c2','scheme'};
        trace=[r(:,configNames),actual,table(expectedMode,'VariableNames',{'Mode_Expected'})];
        combined=[combined;trace]; %#ok<AGROW>
    end
end
writetable(combined,fullfile(outputDir,'stateflow_trace_v28.csv'));
record('all_six_modes_executed',isequal(unique(combined.Mode),(0:5)'), 'All required modes observed numerically.');
rt=sfroot; ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Thermal_Dispatch']);
states=ch.find('-isa','Stateflow.State'); transitions=ch.find('-isa','Stateflow.Transition');
labels=string({transitions.LabelString});
embeddedChoose=ch.find('-isa','Stateflow.EMFunction','Name','stateflow_choose_mode_v28');
embeddedAllocate=ch.find('-isa','Stateflow.EMFunction','Name','stateflow_allocate_v28');
structure=struct('matlab_version',version,'stateflow_license',license('test','Stateflow'), ...
    'states',{sort({states.Name})},'transitions',numel(transitions),'transition_labels',{cellstr(labels)}, ...
    'state_actions',{{states.LabelString}},'chart_path',ch.Path,'sample_time',ch.SampleTime, ...
    'initialize_execution',ch.ExecuteAtInitialization,'tes_delay',get_param([mdl '/TES_Energy_Memory'],'BlockType'), ...
    'chart_output_line',get_param([mdl '/Thermal_Dispatch'],'LineHandles'), ...
    'embedded_choose_script',embeddedChoose.Script,'embedded_allocate_script',embeddedAllocate.Script);
writejson(fullfile(outputDir,'model_structure_v28.json'),structure);
record('six_state_guarded_topology',numel(states)==6 && numel(transitions)==37 && ...
    sum(contains(labels,'stateflow_choose_mode_v28'))==36 && ~any(contains(labels,'[true]')|contains(labels,'[false]')), ...
    '6 initial choices plus 30 guarded state changes and one default to initial junction.');
record('chart_drives_energy_and_trace',structure.chart_output_line.Outport(1)>0, ...
    'Chart output is wired into executable contract gate before feedback/trace.');
record('saved_model_embeds_reviewed_functions', ...
    strcmp(embeddedChoose.Script,fileread(fullfile(here,'stateflow_choose_mode_v28.m'))) && ...
    strcmp(embeddedAllocate.Script,fileread(fullfile(here,'stateflow_allocate_v28.m'))), ...
    'Loaded .slx helper scripts exactly equal reviewed source; no stale embedded controller.');
destinationHandles=get_param(get_param([mdl '/Runtime_Contract_Gate'],'LineHandles').Outport(1),'DstBlockHandle');
record('contract_gate_drives_TES_feedback',all(ismember( ...
    [get_param([mdl '/Next_TES_Energy'],'Handle'),get_param([mdl '/Dispatch_Trace'],'Handle')],destinationHandles)), ...
    'Accepted contract-gate destinations include next-energy selector and trace sink.');
monitor=rt.find('-isa','Stateflow.EMChart','Path',[mdl '/Runtime_Contract_Gate']);
record('saved_model_embeds_contract_gate',strcmp(monitor.Script, ...
    fileread(fullfile(here,'stateflow_contract_gate_v28.m'))), ...
    'Actual saved .slx embeds reviewed first-law/runtime monitor source.');
experiments=run_stateflow_loss_experiments_v28(outputDir);
record('actual_storage_timestep_experiments',experiments.failed==0, ...
    'Actual v24/v28 idle and constant charging convergence against exact continuous lumped ODE.');
rejectSummary=run_stateflow_rejections_v28(mdl,outputDir);
record('all_invalid_cases_simulated_and_rejected',rejectSummary.rejected==rejectSummary.cases && ...
    rejectSummary.expected_cause_observed==rejectSummary.cases && rejectSummary.accepted_invalid_traces==0, ...
    'Actual simulations rejected independent invalid-domain/clock cases with expected DCHR cause.');
writetable(struct2table(checks),fullfile(outputDir,'stateflow_assertions_v28.csv'));
summary=struct('version','0.28','timestamp_utc',stamp,'matlab_version',version, ...
    'scenarios',numel(unique(combined.scenario_id)),'intervals',height(combined), ...
    'checks',numel(checks),'passed',sum([checks.passed]),'failed',sum(~[checks.passed]), ...
    'modes_observed',unique(combined.Mode)','max_abs_balance_residual_MWh',max(abs(combined.System_Balance_Residual_MWh)), ...
    'loss_experiments',experiments, ...
    'runtime_invalid_cases',rejectSummary.cases, ...
    'runtime_invalid_cases_rejected',rejectSummary.rejected, ...
    'simulink_executed',true,'stateflow_executed',true,'standalone_codegen',false, ...
    'primary_paper_replication',false,'equipment_validation',false,'output_directory',outputDir);
writejson(fullfile(outputDir,'acceptance_summary_v28.json'),summary); disp(summary);
assert(all([checks.passed]),'DCHR:v28:AcceptanceFailed','See saved assertion report.');
fprintf('ACCEPTANCE_OUTPUT=%s\n',outputDir);

    function record(name,passed,detail)
        checks(end+1)=struct('name',char(name),'passed',logical(passed),'detail',char(detail));
        if ~passed, fprintf(2,'FAIL %s\n',name); end
    end

end

function c=configuration(r)
c=default_config_v2(); c.sim.dt_h=r.dt_h;
c.storage.capacity_MWh=r.storage_capacity_MWh; c.storage.charge_limit_MW=r.charge_limit_MW;
c.storage.discharge_limit_MW=r.discharge_limit_MW; c.storage.eta_charge=r.eta_charge;
c.storage.eta_discharge=r.eta_discharge; c.storage.continuous_loss_rate_per_h=r.continuous_loss_rate_per_h;
c.storage.initial_soc=0;
if r.storage_capacity_MWh>0, c.storage.initial_soc=r.expected_Storage_E_Start_MWh/r.storage_capacity_MWh; end
c.backup.max_heat_MW=r.boiler_capacity_MW; c.hp.max_heat_output_MW=r.hp_capacity_MW;
c.hp.carnot_efficiency=r.carnot_efficiency; c.hp.cop_min=r.cop_min; c.hp.cop_max=r.cop_max;
c.hp.part_load_penalty=r.part_load_penalty; c.model.hp_backend=r.backend;
c.hp.poly_c0=r.poly_c0; c.hp.poly_c1=r.poly_c1; c.hp.poly_c2=r.poly_c2;
end

function ok=near(a,b)
a=double(a); b=double(b); both=isnan(a)&isnan(b); finite=isfinite(a)&isfinite(b);
ok=isequal(size(a),size(b)) && all(both|finite,'all') && all(abs(a(finite)-b(finite))<=1e-9+1e-11*abs(b(finite)),'all');
end

function values=samples(ts,width)
raw=ts.Data; n=numel(ts.Time);
if ismatrix(raw) && isequal(size(raw),[n width])
    values=raw;
elseif size(raw,1)==width && numel(raw)==n*width
    values=reshape(raw,width,n)';
else
    error('DCHR:v28:TraceDimensions','Unexpected timeseries dimensions.');
end
end

function writejson(path,value)
fid=fopen(path,'w'); assert(fid>0,'DCHR:v28:EvidenceWrite','Cannot open evidence file.');
cleanup=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(value,PrettyPrint=true));
end

function close_models(mdl)
close_system(mdl,0); close_system('DCHR_Dispatch_Stateflow_v24',0);
end
