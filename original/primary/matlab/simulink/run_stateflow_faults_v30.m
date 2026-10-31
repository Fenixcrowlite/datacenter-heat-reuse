function summary = run_stateflow_faults_v30(mdl,outputDir,cases)
% Actual saved-model domain and in-memory monitor corruption smoke gates.
% Every modified allocator is restored without saving the production model.
if iscell(cases),base=cases{1};else,base=cases(1);end
base.p=reshape(base.p,1,[]);base.h=reshape(base.h,1,[]);
base.inputs=[0 35 75 0 45;0 35 75 0 45];
rt=sfroot;ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Thermal_Dispatch']);
allocator=ch.find('-isa','Stateflow.EMFunction','Name','stateflow_allocate_v30');
original=allocator.Script;restore=onCleanup(@()restoreAllocator(mdl,original)); %#ok<NASGU>
records=struct('id',{},'kind',{},'expected_diagnostic',{},'expected_prefix_samples',{}, ...
    'actual_prefix_samples',{},'passed',{},'diagnostic',{},'configured_case',{},'mutation',{});
for j=1:18
    c=base;kind='domain';prefix=0;mutation='';expected='Runtime physical-domain rejection';
    switch j
        case 1,id='negative_source';c.inputs(1,1)=-1;
        case 2,id='negative_demand';c.inputs(1,4)=-1;
        case 3,id='delivery_above_cutoff';c.inputs(1,5)=51;
        case 4,id='condenser_below_tank_max';c.inputs(1,3)=69;
        case 5,id='cutoff_above_capacity';c.p(8)=11;
        case 6,id='negative_rate';c.p(7)=-.1;
        case 7,id='invalid_efficiency';c.p(5)=0;
        case 8,id='zero_heat_capacity';c.p(9)=0;
        case 9,id='above_capacity_state';c.initial_energy_MWh=11;
        case 10,id='negative_boiler';c.p(11)=-1;
        case 11,id='invalid_hp_backend';c.h(6)=2;
        case 12,id='invalid_heating_lift';c.inputs(1,2)=80;
        case 13,id='delayed_negative_source';c.inputs(2,1)=-1;prefix=1;kind='delayed_domain';
        case 14,id='delayed_delivery_fault';c.inputs(2,5)=51;prefix=1;kind='delayed_domain';
        case 15,id='corrupt_temperature';mutation='y(15)=y(15)+1;';expected='Temperature/usable-energy mismatch.';kind='monitor';
        case 16,id='corrupt_usable_inventory';mutation='y(17)=y(17)+1;';expected='Temperature/usable-energy mismatch.';kind='monitor';
        case 17,id='corrupt_next_energy';mutation='y(8)=y(8)+1;';expected='Exact constant-power solution mismatch.';kind='monitor';
        case 18,id='corrupt_standing_loss';mutation='y(9)=y(9)+1;';expected='TES loss mismatch.';kind='monitor';
    end
    if ~isempty(mutation)
        changed=regexprep(original,'end\s*$',[mutation newline 'end']);allocator.Script=changed;
        fid=fopen(fullfile(outputDir,[id '_in_memory_allocation.m']),'w');assert(fid>0);fprintf(fid,'%s',changed);fclose(fid);
    end
    s=Simulink.SimulationInput(mdl);n=size(c.inputs,1);dt=c.p(1);
    s=s.setVariable('dchr_dt_v30',dt,'Workspace',mdl);
    s=s.setVariable('dchr_stop_v30',(n-1)*dt,'Workspace',mdl);
    s=s.setVariable('dchr_input_v30',[(0:n-1)'*dt c.inputs],'Workspace',mdl);
    s=s.setVariable('dchr_p_v30',c.p,'Workspace',mdl);
    s=s.setVariable('dchr_h_v30',c.h,'Workspace',mdl);
    s=s.setVariable('dchr_E0_v30',c.initial_energy_MWh,'Workspace',mdl);
    s=s.setModelParameter('CaptureErrors','on');result=sim(s);
    save(fullfile(outputDir,[id '_fault_simulation.mat']),'result');
    diagnostic=char(result.ErrorMessage);count=0;
    if any(strcmp(result.who,'dispatch_trace_v30'))
        ts=result.dispatch_trace_v30;if isa(ts,'timeseries'),count=numel(ts.Time);end
    end
    passed=~isempty(diagnostic) && contains(diagnostic,expected) && count==prefix;
    records(end+1)=struct('id',id,'kind',kind,'expected_diagnostic',expected, ...
        'expected_prefix_samples',prefix,'actual_prefix_samples',count,'passed',passed, ...
        'diagnostic',diagnostic,'configured_case',c,'mutation',mutation); %#ok<AGROW>
    allocator.Script=original;
    if ~passed,fprintf(2,'FAULT FAIL %s expected=%s prefix=%d/%d\n',id,expected,count,prefix);end
end
% Prove in-memory mutations were restored and model runs cleanly afterwards.
s=Simulink.SimulationInput(mdl);dt=base.p(1);
s=s.setVariable('dchr_dt_v30',dt,'Workspace',mdl);
s=s.setVariable('dchr_stop_v30',dt,'Workspace',mdl);
s=s.setVariable('dchr_input_v30',[(0:1)'*dt base.inputs],'Workspace',mdl);
s=s.setVariable('dchr_p_v30',base.p,'Workspace',mdl);
s=s.setVariable('dchr_h_v30',base.h,'Workspace',mdl);
s=s.setVariable('dchr_E0_v30',base.initial_energy_MWh,'Workspace',mdl);
result=sim(s);save(fullfile(outputDir,'post_fault_clean_simulation.mat'),'result');
fid=fopen(fullfile(outputDir,'fault_evidence_v30.json'),'w');assert(fid>0);
fprintf(fid,'%s\n',jsonencode(records,PrettyPrint=true));fclose(fid);
summary=struct('cases',numel(records),'rejected',sum([records.passed]),'failed',sum(~[records.passed]), ...
    'domain_cases',12,'delayed_cases',2,'monitor_cases',4, ...
    'clean_restart_samples',numel(result.dispatch_trace_v30.Time), ...
    'restored_allocator_matches_source',strcmp(allocator.Script,original));
assert(summary.clean_restart_samples==2 && summary.restored_allocator_matches_source);
end
function restoreAllocator(mdl,source)
if bdIsLoaded(mdl)
    rt=sfroot;ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Thermal_Dispatch']);
    a=ch.find('-isa','Stateflow.EMFunction','Name','stateflow_allocate_v30');a.Script=source;
end
end
