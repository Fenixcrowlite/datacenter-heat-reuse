function b=coupled_temperature_boundary_v55(s,p,E,request)
% Conservative new-interface gate; preserves the v54 and saved-v52 baselines.
c=dchr.components.coupled_branch_certificate_v55(s,p,E,request);
assert(c.resolved,'DCHR:v55:UnresolvedBranch', ...
    'Tank/outlet branch sign is unresolved. Split or resolve exactly before dispatch.');
b=c.nominal_boundary;
b.tank_branch=strcmp(c.branch,'TANK');b.branch_certificate=c;
assert(b.tank_branch==c.nominal_boundary.tank_branch,'DCHR:v55:BranchMismatch', ...
    'Nominal and certified branch disagree.');
end
