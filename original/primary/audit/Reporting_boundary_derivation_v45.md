# Period energy and delivery reporting — engineering derivation v45

This is an engineering accounting derivation, not a new primary-paper equation
signoff, equipment calibration or standards-ERF interpretation. It builds on
the explicitly scoped v43/v44 compressor and auxiliary boundary audits.
Accepted plant/controller v42 and the historical reports remain preserved.

For held interval i, duration d_i is in hours and powers are in MW. Every
period energy is E_X = sum_i X_i d_i (MWh). The reporting API accepts a scalar
common duration or one explicit duration per row; a timestamp is a start time,
not an implicit duration. A single Stateflow sample at stop time zero represents
one executed macro interval of p(1) hours. A short fixture is not annualized.

Demand closure is D_i = H_direct,i + H_TESout,i + H_boiler,i + U_i.
Actual condenser closure is H_HP,i = H_direct,i + H_TESin,i. Therefore

    E_nonboiler_delivery = E_demand - E_boiler - E_unmet
                        = E_HP_direct + E_TES_discharge.

The legacy demand-minus-boiler numerator overstates nonboiler delivery by
exactly E_unmet when finite backup leaves a shortfall. The new function uses
the explicit delivered ports and validates both closures. It does not silently
infer missing unmet heat or drop NaNs. Initial TES inventory has unknown source
provenance; compressor electricity also enters the hot output. Nonboiler
delivery is consequently not automatically waste-heat recovery or standard ERF.

The period heating COP at the active condenser/compressor boundary is

    COP_H,period = sum_i H_HP,i d_i / sum_i W_HP,i d_i.

For per-interval COP_i = H_HP,i/W_HP,i, the old mean is an arithmetic
heat-weighted diagnostic: sum_i COP_i H_HP,i d_i / sum_i H_HP,i d_i.
The integrated ratio instead equals the harmonic heat-weighted mean, or the
electricity-weighted arithmetic mean. Two equal one-hour intervals with
(H,W)=(4,1) and (8,4) yield 12/5=2.4 integrated versus 8/3 diagnostic.
With durations 1/4 h and 2 h, integrated COP is 17/(33/4)=68/33.
Charge heat belongs in the HP numerator; later TES discharge does not. Replacing
the numerator by nonboiler delivery credits initial inventory and incorporates
storage losses/time shifts, and is a different metric. With no active HP work,
COP is undefined (NaN in MATLAB, null in the JSON evidence), not zero or an eps
denominator artifact. Zero-demand coverage is likewise undefined.

Electrical boundary: W_HP is active HP electricity only. No pump, fan, standby,
network or DC electricity is invented or added. System COP remains unspecified
until explicit nonoverlapping auxiliary electrical ports and their thermal
destinations are supported by data. v44 showed why equal enlarged denominators
do not alone establish COP_H=EER+1. This function does not introduce an annual
economic/exergy/CO2 correction or a source-attribution claim.

Implementation domain: nonempty, finite, nonnegative real numeric ports and
positive durations; actual HP heat/work both positive or both zero; active
heating electrical power no greater than hot output; finite power sums and
integrated energies. Closure tolerance is 128 binary64 spacings at the row
power scale. This is a numerical bookkeeping tolerance, not a physical
measurement uncertainty. General extreme dynamic-range ratio accuracy and
subnormal integration are not certified by the ordinary-scale fixtures.

API: `dchr.compute_energy_metrics_v45(cfg, out)`. Required table columns are
Heat_Demand_MW, HP_Direct_MW, Storage_Charge_MW, Storage_Discharge_MW,
Gas_Heat_MW, Unmet_Heat_MW, HP_Heat_MW (actual), HP_Electric_MW.
`cfg.sim.dt_h` supplies interval duration(s). For v42 dispatch traces use
one-based columns [18,2,3,4,5,6,19,20]. Older annual tables use HP_Heat_MW
for potential heat and HP_Heat_Used_MW for actual output: they require an
explicit adapter and must not be passed to this API unchanged. Historical
compute_metrics and compute_metrics_v2 consumers remain open migration work.
