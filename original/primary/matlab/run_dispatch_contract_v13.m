function results=run_dispatch_contract_v13()
% Non-destructive v13 executable dispatch tests. Scenario assumptions only.
cfg=default_config_v2(); cfg.backup.max_heat_MW=2;
input=dchr.make_inputs(cfg);
f=fieldnames(input); for k=1:numel(f), input.(f{k})=input.(f{k})(1:24,:); end
o=dchr.simulate_system_v13(cfg,input);
tol=1e-7;
names=["finite_boiler";"nonnegative_unmet";"demand_closure";"supplied_definition"];
checks=[all(o.Gas_Heat_MW<=2+tol);all(o.Unmet_Heat_MW>=-tol); ...
all(abs(o.HP_Heat_Used_MW-o.Storage_Charge_MW+o.Storage_Discharge_MW+o.Gas_Heat_MW+o.Unmet_Heat_MW-o.Heat_Demand_MW)<tol); ...
all(abs(o.Supplied_Heat_MW+o.Unmet_Heat_MW-o.Heat_Demand_MW)<tol)];
results=table(names,checks,'VariableNames',{'Test','Passed'});
disp(results);
assert(all(checks),'DCHR:v13:ContractFailure');
end

