# C96 | Counterflow UA/NTU and pumping: synthetic engineering envelope

## Real change
Implemented counterflow exchanger effectiveness (epsilon-NTU), both finite heat-capacity streams, source return floor, explicit pump electricity, thermal/electric heat-pump caps and 8760-hour dynamic pool dispatch. Pinned upstream C93/C90 by SHA; no shared MATLAB, SCADA, Jarvice or GUI edits.

## Scope and evidence
26 scenarios: 35 C baseline and 38/50 C sensitivity, source flow 0.5/2 kg/s, UA 2/10 kW/K, assumed COP 2.2/4.0, plus two 50 kW-backup cases. 227,760 hourly rows in compressed CSV. All source temperatures, flows, UA, cold-loop temperature 15 C, pressure drops 30/40 kPa and pump efficiency 0.60 are **hypotheses**, not measurements. COP is a constant scenario input, NOT a manufacturer performance curve. Pool water-only model uses C93 synthetic loss assumptions.

## Observed outputs
- 26/26 scenarios stayed above 27.5 C with the chosen UA values; no backup heat dispatched in the two tested backup cases. This means the selected grid does not locate the failure boundary.
- Annual heat pump delivered approximately 197.28-202.51 MWh across scenarios; modeled pumping consumes 0.284-1.107 MWh/year. Do not compare COP alone without pump energy.
- Example baseline 35 C, 0.5 kg/s, UA=2 kW/K, assumed COP=2.2: min pool 27.796 C, HP heat 200.18 MWh/year, pump electricity 0.75 MWh/year.
- These numbers differ from C94 because C94 constrained source cooling to a 6 K drop and used a Carnot COP proxy. C96 assumes a separate finite cold stream at 15 C and UA/NTU; neither model is field-calibrated.

## Independent QA
Model 16/16 unit/negative checks PASS. Independent reader recomputed 227,760 hourly rows, 26 annual group totals, 12 independent LMTD identities, and detected an intentionally corrupted electric-consumption field. Upstream source SHA checked. All balances are numerical checks, **not** real-world equipment validation.

## Next executable steps
1. Narrow UA grid below 2 kW/K to find minimum UA required and sensitivity to cold-side temperature/flow; do not extrapolate the all-pass grid to real hardware.
2. Obtain actual source and secondary loop flow/temperature series, vendor COP map and pressure-drop curves. Re-run with bounded uncertainties and verify heat-exchanger design against manufacturer data.
3. Add ventilation and dehumidification and independent primary-source signoffs (still 0/31).
