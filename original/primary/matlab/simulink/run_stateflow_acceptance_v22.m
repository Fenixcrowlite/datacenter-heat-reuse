function outputDir = run_stateflow_acceptance_v22()
% Execute actual model intervals, compare all v16 ports, and inspect topology.
here=fileparts(mfilename('fullpath')); root=fileparts(fileparts(here));
addpath(fullfile(root,'matlab'),here);
stamp=char(datetime('now','TimeZone','UTC','Format','yyyyMMdd''T''HHmmssSSS''Z'''));
outputDir=fullfile(root,'results',['stateflow_v22_' stamp]);
assert(~isfolder(outputDir),'DCHR:v22:EvidenceExists','Refuse evidence overwrite.'); mkdir(outputDir);
mdl='DCHR_Dispatch_Stateflow_v22'; modelPath=fullfile(here,[mdl '.slx']);
assert(isfile(modelPath),'DCHR:v22:ModelMissing','Build the versioned model first.');
load_system(modelPath); cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
previousFileGen=Simulink.fileGenControl('getConfig');
fileGenCleanup=onCleanup(@()Simulink.fileGenControl('setConfig','config',previousFileGen)); %#ok<NASGU>
Simulink.fileGenControl('set','CacheFolder',fullfile(outputDir,'cache'), ...
    'CodeGenFolder',fullfile(outputDir,'codegen'),'createDir',true);
checks=struct('name',{},'passed',{},'detail',{}); combined=table();
sources={fullfile(root,'audit','dispatch_reference_vectors_v18.csv'), ...
    fullfile(root,'audit','stateflow_qa_vectors_v22.csv')};
assert(isfile(sources{2}),'DCHR:v22:QAAbsent','Independent QA vectors required.');
for f=1:numel(sources)
    v=readtable(sources{f},'TextType','string'); ids=unique(v.scenario_id,'stable');
    for j=1:numel(ids)
        r=v(v.scenario_id==ids(j),:); cfg=configuration(r(1,:));
        input=r(:,{'Source_Heat_MW','Source_C','Sink_C','Heat_Demand_MW'});
        reference=dchr.simulate_dispatch_v16(cfg,input); % also strict domain gate
        n=height(r); dt=cfg.sim.dt_h;
        p=[dt cfg.storage.capacity_MWh cfg.storage.charge_limit_MW cfg.storage.discharge_limit_MW ...
            cfg.storage.eta_charge cfg.storage.eta_discharge cfg.storage.loss_fraction_per_h cfg.backup.max_heat_MW];
        h=[cfg.hp.max_heat_output_MW cfg.hp.carnot_efficiency cfg.hp.cop_min cfg.hp.cop_max ...
            cfg.hp.part_load_penalty double(string(cfg.model.hp_backend)=="lift_polynomial") ...
            cfg.hp.poly_c0 cfg.hp.poly_c1 cfg.hp.poly_c2];
        s=Simulink.SimulationInput(mdl);
        s=s.setVariable('dchr_dt_v22',dt,'Workspace',mdl);
        s=s.setVariable('dchr_stop_v22',(n-1)*dt,'Workspace',mdl);
        s=s.setVariable('dchr_input_v22',[(0:n-1)'*dt table2array(input)],'Workspace',mdl);
        s=s.setVariable('dchr_p_v22',p,'Workspace',mdl);
        s=s.setVariable('dchr_h_v22',h,'Workspace',mdl);
        s=s.setVariable('dchr_E0_v22',cfg.storage.initial_soc*p(2),'Workspace',mdl);
        result=sim(s);
        save(fullfile(outputDir,char(ids(j)+"_simulation.mat")),'result');
        y=samples(result.dispatch_trace_v22,13);
        u=samples(result.hp_trace_v22,8);
        e=reshape(result.energy_start_trace_v22.Data,[],1);
        time=result.dispatch_trace_v22.Time;
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
        for k=1:numel(expectedNames)
            name=extractAfter(string(expectedNames{k}),9);
            record(ids(j)+"_python_"+name,near(actual.(name),r.(expectedNames{k})), ...
                'Actual executable model vs independent stored numerical reference.');
        end
        names=reference.Properties.VariableNames(6:end);
        for k=1:numel(names)
            record(ids(j)+"_v16_"+string(names{k}),near(actual.(names{k}),reference.(names{k})), ...
                'Actual executable Stateflow vs verified v16 MATLAB numerical dispatch.');
        end
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
            'eta_charge','eta_discharge','loss_fraction_per_h','boiler_capacity_MW','hp_capacity_MW', ...
            'carnot_efficiency','cop_min','cop_max','part_load_penalty','backend','poly_c0','poly_c1','poly_c2'};
        trace=[r(:,configNames),actual,table(expectedMode,'VariableNames',{'Mode_Expected'})];
        combined=[combined;trace]; %#ok<AGROW>
    end
end
writetable(combined,fullfile(outputDir,'stateflow_trace_v22.csv'));
record('all_six_modes_executed',isequal(unique(combined.Mode),(0:5)'), 'All required modes observed numerically.');
rt=sfroot; ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Thermal_Dispatch']);
states=ch.find('-isa','Stateflow.State'); transitions=ch.find('-isa','Stateflow.Transition');
labels=string({transitions.LabelString});
embeddedChoose=ch.find('-isa','Stateflow.EMFunction','Name','stateflow_choose_mode_v22');
embeddedAllocate=ch.find('-isa','Stateflow.EMFunction','Name','stateflow_allocate_v22');
structure=struct('matlab_version',version,'stateflow_license',license('test','Stateflow'), ...
    'states',{sort({states.Name})},'transitions',numel(transitions),'transition_labels',{cellstr(labels)}, ...
    'state_actions',{{states.LabelString}},'chart_path',ch.Path,'sample_time',ch.SampleTime, ...
    'initialize_execution',ch.ExecuteAtInitialization,'tes_delay',get_param([mdl '/TES_Energy_Memory'],'BlockType'), ...
    'chart_output_line',get_param([mdl '/Thermal_Dispatch'],'LineHandles'), ...
    'embedded_choose_script',embeddedChoose.Script,'embedded_allocate_script',embeddedAllocate.Script);
writejson(fullfile(outputDir,'model_structure_v22.json'),structure);
record('six_state_guarded_topology',numel(states)==6 && numel(transitions)==37 && ...
    sum(contains(labels,'stateflow_choose_mode_v22'))==36 && ~any(contains(labels,'[true]')|contains(labels,'[false]')), ...
    '6 initial choices plus 30 guarded state changes and one default to initial junction.');
record('chart_drives_energy_and_trace',structure.chart_output_line.Outport(1)>0, ...
    'Chart output is wired to energy selector/feedback and numeric trace.');
record('saved_model_embeds_reviewed_functions', ...
    strcmp(embeddedChoose.Script,fileread(fullfile(here,'stateflow_choose_mode_v22.m'))) && ...
    strcmp(embeddedAllocate.Script,fileread(fullfile(here,'stateflow_allocate_v22.m'))), ...
    'Loaded .slx helper scripts exactly equal reviewed source; no stale embedded controller.');
destinationHandles=get_param(structure.chart_output_line.Outport(1),'DstBlockHandle');
record('chart_port_drives_TES_feedback',all(ismember( ...
    [get_param([mdl '/Next_TES_Energy'],'Handle'),get_param([mdl '/Dispatch_Trace'],'Handle')],destinationHandles)), ...
    'Actual chart port destinations include next-energy selector and trace sink.');
invalids();
writetable(struct2table(checks),fullfile(outputDir,'stateflow_assertions_v22.csv'));
summary=struct('version','0.22','timestamp_utc',stamp,'matlab_version',version, ...
    'scenarios',numel(unique(combined.scenario_id)),'intervals',height(combined), ...
    'checks',numel(checks),'passed',sum([checks.passed]),'failed',sum(~[checks.passed]), ...
    'modes_observed',unique(combined.Mode)','max_abs_balance_residual_MWh',max(abs(combined.System_Balance_Residual_MWh)), ...
    'simulink_executed',true,'stateflow_executed',true,'standalone_codegen',false, ...
    'primary_paper_replication',false,'equipment_validation',false,'output_directory',outputDir);
writejson(fullfile(outputDir,'acceptance_summary_v22.json'),summary); disp(summary);
assert(all([checks.passed]),'DCHR:v22:AcceptanceFailed','See saved assertion report.');
fprintf('ACCEPTANCE_OUTPUT=%s\n',outputDir);

    function record(name,passed,detail)
        checks(end+1)=struct('name',char(name),'passed',logical(passed),'detail',char(detail));
        if ~passed, fprintf(2,'FAIL %s\n',name); end
    end
    function invalids()
        c=configuration(v(1,:)); in=input(1,:);
        bad=c; bad.storage.initial_soc=1.1; reject('invalid_initial_SOC',bad,in);
        bad=c; bad.storage.eta_charge=0; reject('invalid_charge_efficiency',bad,in);
        bad=c; bad.storage.charge_limit_MW=-1; reject('invalid_charge_limit',bad,in);
        bad=c; bad.sim.dt_h=0; reject('invalid_zero_timestep',bad,in);
        bad=c; bad.storage.loss_fraction_per_h=2/bad.sim.dt_h; reject('invalid_loss_interval',bad,in);
        bad=c; bad.backup.max_heat_MW=-1; reject('invalid_boiler_limit',bad,in);
        badInput=in; badInput.Source_Heat_MW=NaN; reject('invalid_nonfinite_source',c,badInput);
        badInput=in; badInput.Heat_Demand_MW=-1; reject('invalid_negative_demand',c,badInput);
        badInput=in; badInput.Sink_C=badInput.Source_C; reject('invalid_temperature_lift',c,badInput);
        x=table2array(in)';
        badX=x; badX(4)=-1; rejectAdapter('adapter_negative_demand',badX,p,h);
        badP=p; badP(8)=-1; rejectAdapter('adapter_negative_boiler',x,badP,h);
        badH=h; badH(6)=2; rejectAdapter('adapter_invalid_backend',x,p,badH);
        badP=p; badP(5)=0; rejectAdapter('adapter_zero_charge_efficiency',x,badP,h);
        badP=p; badP(1)=0; rejectAdapter('adapter_zero_timestep',x,badP,h);
    end
    function rejectAdapter(name,x,p,h)
        caught=false;
        try, dchr_stateflow_hp_v22(x,0,p,h); catch, caught=true; end
        record(name,caught,'Actual HP adapter enforces runtime input/configuration domain.');
    end
    function reject(name,c,in)
        caught=false;
        try, dchr.simulate_dispatch_v16(c,in); catch ex, caught=startsWith(ex.identifier,'DCHR:'); end
        record(name,caught,'Pre-simulation validation must reject invalid physical input/configuration.');
    end
end

function c=configuration(r)
c=default_config_v2(); c.sim.dt_h=r.dt_h;
c.storage.capacity_MWh=r.storage_capacity_MWh; c.storage.charge_limit_MW=r.charge_limit_MW;
c.storage.discharge_limit_MW=r.discharge_limit_MW; c.storage.eta_charge=r.eta_charge;
c.storage.eta_discharge=r.eta_discharge; c.storage.loss_fraction_per_h=r.loss_fraction_per_h;
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
    error('DCHR:v22:TraceDimensions','Unexpected timeseries dimensions.');
end
end

function writejson(path,value)
fid=fopen(path,'w'); assert(fid>0,'DCHR:v22:EvidenceWrite','Cannot open evidence file.');
cleanup=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(value,PrettyPrint=true));
end
