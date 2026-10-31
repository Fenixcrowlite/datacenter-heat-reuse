function ports=adapt_dispatch_energy_v46(out,schema)
% Explicit schema prevents legacy potential HP heat being counted as actual.
% Unmet heat is mandatory; missing shortfall is never assumed to be zero.
assert(istable(out)&&height(out)>0,'DCHR:v46:Schema','Require a nonempty table.');
names={'Heat_Demand_MW','HP_Direct_MW','Storage_Charge_MW', ...
    'Storage_Discharge_MW','Gas_Heat_MW','Unmet_Heat_MW','HP_Heat_MW','HP_Electric_MW'};
if strcmp(schema,'legacy_actual_v13')
    required={'HP_Heat_Used_MW','Storage_Charge_MW','Unmet_Heat_MW'};
    assert(all(ismember(required,out.Properties.VariableNames)), ...
        'DCHR:v46:Schema','Legacy finite-backup actual heat and explicit unmet ports required.');
    out.HP_Heat_MW=out.HP_Heat_Used_MW;
    out.HP_Direct_MW=out.HP_Heat_Used_MW-out.Storage_Charge_MW;
elseif ~strcmp(schema,'explicit_actual_v45')
    error('DCHR:v46:Schema','Select legacy_actual_v13 or explicit_actual_v45 explicitly.');
end
assert(all(ismember(names,out.Properties.VariableNames)), ...
    'DCHR:v46:Schema','Missing explicit actual-energy port.');
ports=out(:,names);
end
