# Energy-reporting boundary results — v45

2026-10-10T17:53:57.019616+00:00. PASS_SCOPED_ENERGY_REPORT_API; legacy consumer migration OPEN.
Evidence folder: `results/reporting_v45_20261010T175127_627392Z`. QA: `results/reporting_v45_20261010T175127_627392Z/independent_QA_v45_20261010T175249_660324Z.json`.
Accepted saved model remains 0.42; original prototype and all prior models preserved.

Fresh MATLAB 26.1.0.3346908 (R2026a) Update 5 / observed Stateflow license:
six saved-v42 cases execute IDLE, HEAT_RECOVERY, STORAGE_CHARGE,
STORAGE_DISCHARGE, BACKUP and UNMET_DEMAND. MATLAB 62 PASS / 0 FAIL, with
12 actual new reporting-domain rejections. v30 numerical reference agrees on
physical ports/states and COP; OFF supervisor request semantics are separately
documented rather than asserted equivalent. Numeric CSV, original SimulationOutput
MATs and independent saved-MAT reopen are retained.

| Fixture | Demand MWh | Boiler MWh | Unmet MWh | Actual nonboiler delivery MWh | Legacy reuse MWh |
|---|---:|---:|---:|---:|---:|
| Insufficient heat | 5 | 2 | 3 | 0 | 3 |
| TES charge | 1 | 0 | 0 | 1 | 1 |
| TES discharge from initial inventory | 2 | 0 | 0 | 2 | 2 |

Both historical report functions count the finite-backup shortfall as reused
heat. `compute_energy_metrics_v45` instead integrates explicit direct and TES
discharge ports, reports unmet heat separately and verifies closure.
Two actual MATLAB reporting intervals (4 MW heat/1 MW electric and 8/4 for one
hour each) give integrated heating COP 2.4 versus heat-weighted diagnostic
2.6666666666666665. Unequal durations 0.25 h / 2 h give 68/33. The legacy
mean_cop equals the diagnostic. With no HP work, heating COP is undefined;
initial TES delivery does not create HP COP. No system COP/auxiliary load is invented.

Independent Fraction equations, segment first laws/ports, duration partition,
numeric trace integration, v30 reference, original MAT reopen, SLX chart archive,
receipts, source snapshots and preservation: 688 PASS / 0 FAIL. Maximum
independent first-law residual is 0 MWh for these lossless synthetic fixtures.
Separate reviewer corruptions: 4 detected / 0 missed. 153 baseline
artifacts preserve recorded bytes/hashes. These are independent algorithms
run by the same agent; no independent personnel or physical validation is claimed.

Retained failed attempts: sandbox MATLAB startup exit1; first execution
53 PASS / 3 FAIL because the harness compared v30 requested demand against
v42 OFF supervisor request; fresh execution repaired the harness comparison
while preserving every physical-port check and adding COP checks. First
independent review 686 PASS / 1 FAIL was a saved-spec singleton-matrix JSON
serialization shape check; normalization is restricted to known 1x5 inputs,
then all numeric values/other fields are compared exactly. No production
metric function or saved model changed in response to these harness errors.

Limitations: short synthetic fixtures, active HP-only electrical boundary,
unknown initial-inventory heat provenance, inherited Stateflow shadow warnings,
ordinary numerical scale; no primary equation signoff/calibration, economics
repair, source-attributed ERF, article replication or measured validation.
Existing annual consumers still call the old report functions. Their ERE,
screening LCOH and claimed economics need explicit migration/boundary review.

Next actionable task: Create an additive annual reporting adapter/pipeline (preserve run_experiment_v2, run_sensitivity_v2, run_uncertainty_v3, historical CSVs and accepted v42). Map legacy actual HP_Heat_Used_MW to v45 HP_Heat_MW, derive HP_Direct_MW=HP_Heat_Used_MW-Storage_Charge_MW, and require explicit Unmet_Heat_MW from simulate_system_v13 or a newer finite-backup dispatch. Produce a fresh finite-backup period experiment with explicit durations, integrated COP, nonboiler delivery and service shortfall. Audit gas-baseline economics/CO2 at equal supplied service before claiming savings; unmet demand must not become avoided fuel. Do not relabel nonboiler heat as source-attributed ERF or fill absent pump/fan loads with assumptions. Upstream62 equipment calibration remains blocked until primary supplement/map/domain data are acquired.
Stop this coherent run; handoff recorded in STATUS_v45 and the progress ledger.
