% A42 independent MATLAB R2026a numerical acceptance.
% Reads Python-generated synthetic traces; DOES NOT implement Simulink or actuate equipment.
here=fileparts(mfilename('fullpath'));
cases={'both','main_only','backup_only','neither', ...
    'COUNTERFACTUAL_both','COUNTERFACTUAL_backup_only','COUNTERFACTUAL_neither'};
result=struct();
totalSamples=0;
for j=1:numel(cases)
    label=cases{j};
    file=fullfile(here,['TRACE_A42_' label '.csv']);
    t=readtable(file,'TextType','string');
    assert(height(t)==672,'A42:SampleCount');
    assert(all(double(t.k)==(0:671)'),'A42:TimeGrid');
    qit=double(t.qit_W);hx=double(t.hx_W);leak=double(t.leak_W);
    source=double(t.hp_source_W);power=double(t.hp_electric_W);
    condenser=double(t.hp_condenser_W);
    rejected=double(t.reject_W);unhandled=double(t.unhandled_W);
    cap=double(t.cap_W);demand=double(t.pool_dh_demand_W);
    served=double(t.pool_dh_served_W);unmet=double(t.pool_dh_unmet_W);
    charge=double(t.tes_charge_W);dis=double(t.tes_discharge_W);
    loss=double(t.tes_loss_W);e0=double(t.E_start_J);e1=double(t.E_next_J);
    T0=double(t.T_start_C);T1=double(t.T_next_C);
    passive=double(t.passive_W);
    residualIT=qit-hx-leak-source-rejected-unhandled;
    residualHP=condenser-source-power;
    residualUser=demand-served-unmet;
    residualTES=e1-e0-900*(.93*charge-dis/.91-loss);
    thermal=max(30,T0+900*(unhandled-passive)/8e6);
    assert(max(abs(residualIT))<1e-6,'A42:ITBalance');
    assert(max(abs(residualHP))<1e-6,'A42:HPBalance');
    assert(max(abs(residualUser))<1e-6,'A42:UserBalance');
    assert(max(abs(residualTES))<1e-3,'A42:TESBalance');
    assert(max(abs(T1-thermal))<1e-8,'A42:ThermalRecurrence');
    assert(all(rejected<=cap+1e-7),'A42:RejectCap');
    assert(all(source+hx+leak<=qit+1e-7),'A42:ITSourceCap');
    assert(all(e1>=-1e-5 & e1<=900*3.6e6+1e-5),'A42:TESLimits');
    assert(all(qit(cap==0)==0),'A42:ZeroCapacityTrip');
    assert(all(unhandled(cap==0)==0),'A42:ZeroCapacityResidual');
    field=matlab.lang.makeValidName(label);
    result.(field)=struct('samples',height(t), ...
        'max_temperature_C',max(T1),'max_it_residual_W',max(abs(residualIT)), ...
        'max_tes_residual_J',max(abs(residualTES)), ...
        'unmet_kWh',sum(unmet)/4000,'acceptance','PASS');
    totalSamples=totalSamples+height(t);
    fprintf('A42_MATLAB_PASS %s 672\n',label);
end
report=struct('status','MATLAB_INDEPENDENT_NUMERIC_AUDIT_PASS', ...
    'matlab_simulink_model_built',false,'physical_release_allowed',false, ...
    'scenarios',numel(cases),'samples',totalSamples,'cases',result);
fid=fopen(fullfile(here,'MATLAB_AUDIT_A42.json'),'w');
assert(fid>0,'A42:AuditOutput');
fprintf(fid,'%s\n',jsonencode(report,PrettyPrint=true));fclose(fid);
fprintf('A42_MATLAB_ALL_PASS %d\n',totalSamples);
