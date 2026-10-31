function results = run_component_contract_v12()
% Component contract audit v0.12; NOT primary-paper validation.
% No baseline files are modified. Results record both passes and defects.
cfg = default_config_v2();
tol = 1e-9;
names = strings(0,1); passed = false(0,1); observations = strings(0,1);
    function record(name,ok,note)
        names(end+1,1)=string(name);
        passed(end+1,1)=logical(ok);
        observations(end+1,1)=string(note);
    end
hp = dchr.components.heat_pump(5,35,70,cfg);
record('hp_cop_gt_one', isfinite(hp.cop_nominal) && hp.cop_nominal>1, sprintf('COP=%.6f',hp.cop_nominal));
record('hp_capacity_bound',hp.heat_potential_MW>=0 && hp.heat_potential_MW<=cfg.hp.max_heat_output_MW+tol,sprintf('Qhot=%.6f MW',hp.heat_potential_MW));
qhot=hp.heat_potential_MW; p=qhot/hp.cop_nominal; qev=qhot-p;
record('hp_first_law_identity',abs(qhot-qev-p)<tol && qev<=5+tol,sprintf('Qev=%.6f, P=%.6f',qev,p));
hpzero=dchr.components.heat_pump(0,35,70,cfg);
record('hp_zero_source_zero_output',hpzero.heat_potential_MW==0,'zero source must imply zero recovered heat');
st=dchr.components.storage_step(49.5,10,0,cfg);
loss=49.5*cfg.storage.loss_fraction_per_h*cfg.sim.dt_h;
balance=49.5-loss+cfg.storage.eta_charge*st.charge_MW*cfg.sim.dt_h-st.discharge_MW*cfg.sim.dt_h/cfg.storage.eta_discharge;
record('storage_charge_balance',abs(balance-st.energy_next_MWh)<tol,sprintf('E1=%.6f, expected=%.6f',st.energy_next_MWh,balance));
record('storage_capacity_and_power',st.energy_next_MWh<=cfg.storage.capacity_MWh+tol && st.charge_MW<=cfg.storage.charge_limit_MW+tol,'charge saturation');
st2=dchr.components.storage_step(20,0,100,cfg);
balance2=20*(1-cfg.storage.loss_fraction_per_h*cfg.sim.dt_h)-st2.discharge_MW*cfg.sim.dt_h/cfg.storage.eta_discharge;
record('storage_discharge_balance',abs(balance2-st2.energy_next_MWh)<tol,sprintf('E1=%.6f, expected=%.6f',st2.energy_next_MWh,balance2));
record('storage_no_simultaneous_flows',st.charge_MW*st.discharge_MW==0 && st2.charge_MW*st2.discharge_MW==0,'both directions exclusive');
cfgbad=cfg; cfgbad.storage.eta_charge=0;
rejected=false;
try
    dchr.components.storage_step(10,3,0,cfgbad);
catch
    rejected=true;
end
record('invalid_zero_charge_efficiency_rejected',rejected,'expected error for eta_charge=0');
cfgbad=cfg; cfgbad.sim.dt_h=0;
rejected=false;
try
    dchr.components.storage_step(10,3,0,cfgbad);
catch
    rejected=true;
end
record('invalid_zero_timestep_rejected',rejected,'expected error for dt_h=0');
cfgbad=cfg; cfgbad.storage.loss_fraction_per_h=2;
stbad=dchr.components.storage_step(10,0,0,cfgbad);
record('loss_fraction_over_one_rejected_or_bounded',stbad.energy_next_MWh>=0 && stbad.energy_next_MWh<=10,'negative state is physically inadmissible');
results=table(names,passed,observations,'VariableNames',{'Test','Passed','Observation'});
root=fileparts(fileparts(mfilename('fullpath')));
outdir=fullfile(root,'results');
if ~exist(outdir,'dir'), mkdir(outdir); end
writetable(results,fullfile(outdir,'component_contract_v12.csv'));
summary=struct('version','0.12','category','component_contract_mathematical_and_input_validation','total',height(results),'passed',sum(passed),'failed',sum(~passed),'independent_paper_validation',false,'results',table2struct(results));
fid=fopen(fullfile(outdir,'component_contract_v12.json'),'w');
assert(fid>0,'Could not open JSON output');
fprintf(fid,'%s',jsonencode(summary,PrettyPrint=true)); fclose(fid);
disp(results);
end
