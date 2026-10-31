% A43 independent MATLAB R2026a CSV acceptance, no equipment interfaces.
% Checks numerical balances and thermal recurrence. Does NOT build a SLX.
here=fileparts(mfilename('fullpath'));
cases={'both','main_only','backup_only','neither','CF_both','CF_backup_only','CF_neither'};
report=jsondecode(fileread(fullfile(here,'RESULTS_A43.json')));
assert(~report.physical_release && ~report.hardware_control,'A43:UnsafeRelease');
dt=900; capacity=8e6; n=0; maxError=0; maxThermalError=0;
summary=struct();
for i=1:numel(cases)
    label=cases{i};
    t=readtable(fullfile(here,['TRACE_A43_' label '.csv']));
    assert(height(t)==672,'A43:WrongSampleCount');
    assert(all(double(t.k)==(0:671)'),'A43:TimeGrid');
    qit=double(t.active_it_W)+double(t.residual_it_W);
    it=qit-double(t.hx_W)-double(t.leak_W)-double(t.hp_source_W)-double(t.reject_W)-double(t.unhandled_W);
    hp=double(t.hp_condenser_W)-double(t.hp_source_W)-double(t.hp_electric_W);
    user=double(t.pool_dh_demand_W)-double(t.pool_dh_served_W)-double(t.pool_dh_unmet_W);
    tes=double(t.E_next_J)-double(t.E_start_J)-dt*(.93*double(t.tes_charge_W)-double(t.tes_discharge_W)/.91-double(t.tes_loss_W));
    passive=2000*max(0,double(t.T_start_C)-30);
    tnext=max(30,double(t.T_start_C)+dt*(double(t.unhandled_W)-passive)/capacity);
    thermal=max(abs(tnext-double(t.T_next_C)));
    err=max([max(abs(it)),max(abs(hp)),max(abs(user)),max(abs(tes))/1000]);
    assert(max(abs(it))<1e-6 && max(abs(hp))<1e-6,'A43:HeatBalance');
    assert(max(abs(user))<1e-6 && max(abs(tes))<1e-3,'A43:ConsumerTESBalance');
    assert(thermal<1e-8,'A43:ThermalRecurrence');
    assert(all(double(t.reject_W)<=double(t.effective_cap_W)+1e-7),'A43:RejectLimit');
    assert(all(double(t.active_it_W)>=0 & double(t.residual_it_W)>=0),'A43:NonnegativeIT');
    assert(max(abs(double(t.passive_W)-passive))<1e-8,'A43:PassiveCooling');
    assert(max(abs(double(t.T_start_C(2:end))-double(t.T_next_C(1:end-1))))<1e-8,'A43:StateContinuity');
    assert(abs(max(double(t.T_next_C))-report.cases.(label).max_temperature_C)<1e-8,'A43:SummaryMismatch');
    maxError=max(maxError,err);maxThermalError=max(maxThermalError,thermal);
    summary.(label)=struct('samples',height(t),'max_temperature_C',max(double(t.T_next_C)), ...
        'thermal_max_abs_error',thermal,'balance_scaled_max_abs_error',err);
    n=n+height(t);
    fprintf('A43_MATLAB_AUDIT_PASS %s maxT=%.5f\n',label,max(double(t.T_next_C)));
end
t=readtable(fullfile(here,'TRACE_A43_neither.csv'));
assert(strcmp(string(t.state(97)),'TRIP_PENDING') && strcmp(string(t.state(98)),'TRIP_PENDING') && strcmp(string(t.state(99)),'TRIPPED'),'A43:TripSequence');
result=struct('status','A43_MATLAB_INDEPENDENT_CSV_AUDIT_PASS','samples',n, ...
    'max_scaled_balance_error',maxError,'max_thermal_error_C',maxThermalError, ...
    'matlab_simulink_model_built',false,'physical_release',false,'scenarios',summary);
fid=fopen(fullfile(here,'MATLAB_AUDIT_A43.json'),'w');assert(fid>0);
fprintf(fid,'%s\n',jsonencode(result,PrettyPrint=true));fclose(fid);
fprintf('A43_MATLAB_ALL_PASS %d\n',n);
