function res=normative_kpis_SK(x)
% Independent boundary-metering check. Never certifies statutory compliance.
required=["E_IT_MWh","E_DC_MWh","E_REUSE_MWh","has_boundary_meter",...
  "pool_T_off_C","pool_max_C","sensor_uncertainty_K","thermal_overshoot_K"];
for i=1:numel(required)
 assert(isfield(x,required(i)),"Missing field: "+required(i));
end
assert(isscalar(x.E_IT_MWh)&&isfinite(x.E_IT_MWh)&&x.E_IT_MWh>0);
assert(isscalar(x.E_DC_MWh)&&isfinite(x.E_DC_MWh)&&x.E_DC_MWh>=x.E_IT_MWh);
assert(isscalar(x.E_REUSE_MWh)&&isfinite(x.E_REUSE_MWh)&&x.E_REUSE_MWh>=0);
assert(x.E_REUSE_MWh<=x.E_DC_MWh,"E_REUSE cannot exceed DC input energy");
assert(x.sensor_uncertainty_K>=0&&x.thermal_overshoot_K>=0);
res=struct;
res.PUE=x.E_DC_MWh/x.E_IT_MWh;
res.ERF_proxy=x.E_REUSE_MWh/x.E_DC_MWh;
res.reportable_ERF=NaN;
res.E_REUSE_metered=logical(x.has_boundary_meter);
if x.has_boundary_meter
 res.reportable_ERF=res.ERF_proxy;
end
res.temperature_worst_case_C=x.pool_T_off_C+...
   x.sensor_uncertainty_K+x.thermal_overshoot_K;
res.pool_temperature_screening_pass=...
   res.temperature_worst_case_C<=x.pool_max_C;
res.legal_and_equipment_compliance_confirmed=false;
res.assumptions="PUE/ERF energy meter boundary and identical integration period must be verified";
end
