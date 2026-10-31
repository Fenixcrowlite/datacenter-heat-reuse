function m=compute_energy_metrics_v45(cfg,out)
% Explicit period-energy report for held-interval dispatch (MW, hours, MWh).
% Additive API; old annual/economic reports remain unchanged.
% HP_Heat_MW is ACTUAL condenser output, including TES charge, not potential.
% Nonboiler heat includes initial TES inventory and compressor work; it is
% not source-attributed waste heat or a standards-defined ERF numerator.
assert(istable(out)&&height(out)>0,'DCHR:v45:Domain','Require nonempty dispatch table.');
n=height(out);dt=cfg.sim.dt_h;
validateattributes(dt,{'numeric'},{'real','finite','vector','positive'});
assert(isscalar(dt)||numel(dt)==n,'DCHR:v45:Domain','One duration per interval or scalar duration required.');
dt=double(dt(:));if isscalar(dt),dt=repmat(dt,n,1);end
names={'Heat_Demand_MW','HP_Direct_MW','Storage_Charge_MW', ...
    'Storage_Discharge_MW','Gas_Heat_MW','Unmet_Heat_MW','HP_Heat_MW','HP_Electric_MW'};
v=zeros(n,numel(names));
for j=1:numel(names)
    assert(ismember(names{j},out.Properties.VariableNames),'DCHR:v45:Domain','Missing explicit port %s.',names{j});
    x=out.(names{j});validateattributes(x,{'numeric'},{'real','finite','column','numel',n,'nonnegative'});
    v(:,j)=double(x);
end
assert(all(isfinite(sum(v,2))),'DCHR:v45:Domain','Unrepresentable power scale.');
tol=128*eps(max(1,max(v,[],2)));
assert(all(abs(v(:,1)-v(:,2)-v(:,4)-v(:,5)-v(:,6))<=tol), ...
    'DCHR:v45:Balance','Demand must close with explicit unmet heat.');
assert(all(abs(v(:,7)-v(:,2)-v(:,3))<=tol), ...
    'DCHR:v45:Balance','Actual HP heat must close with direct and charge ports.');
assert(all((v(:,7)>0)==(v(:,8)>0))&&all(v(:,8)<=v(:,7)), ...
    'DCHR:v45:Domain','Active heating HP requires positive heat/work; off ports must both be zero.');
e=sum(v.*dt,1);period=sum(dt);
assert(all(isfinite([e period])),'DCHR:v45:Domain','Unrepresentable period energy.');
m=struct('version','0.45','reported_period_h',period,'intervals',n, ...
    'heat_demand_MWh',e(1),'hp_direct_MWh',e(2),'storage_charge_MWh',e(3), ...
    'storage_discharge_MWh',e(4),'gas_heat_MWh',e(5),'unmet_heat_MWh',e(6), ...
    'hp_heat_MWh',e(7),'hp_electric_MWh',e(8));
m.nonboiler_delivered_MWh=e(2)+e(4);
m.total_delivered_MWh=m.nonboiler_delivered_MWh+e(5);
m.nonboiler_coverage_fraction=ratio(m.nonboiler_delivered_MWh,e(1));
m.unmet_fraction=ratio(e(6),e(1));
m.hp_heating_COP_integrated=ratio(e(7),e(8));
active=v(:,8)>0;
m.hp_heat_weighted_COP_diagnostic=NaN;
if any(active)
    m.hp_heat_weighted_COP_diagnostic=sum((v(active,7)/e(7)).*dt(active).* ...
        (v(active,7)./v(active,8)));
end
% No invented pump/fan/standby loads or annualization of short test periods.
m.electrical_boundary='ACTIVE_HP_ONLY_AUXILIARIES_UNSPECIFIED';
m.reuse_boundary='NONBOILER_DELIVERY_INCLUDES_INITIAL_TES_AND_COMPRESSOR_WORK';
m.auxiliary_electricity_included=false;
end
function y=ratio(a,b)
y=NaN;if b>0,y=a/b;end
end
