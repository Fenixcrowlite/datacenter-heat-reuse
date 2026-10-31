# v45 energy-reporting handoff

2026-10-10T17:53:57.019616+00:00. Scoped additive reporting API PASS; legacy consumer migration OPEN.
Saved model 0.42 executed afresh in six required modes; no new SLX.
MATLAB 62/0; 12 reporting faults rejected; independent actual QA 688/0;
separate reviewer mutations 4/0. Nonboiler delivery excludes unmet heat;
integrated HP heating COP is distinct from the heat-weighted diagnostic.
153 baseline artifacts preserved. Physical validation/calibration
and full primary signoffs (0/31) remain open.

Evidence: STATUS_v45.json; audit/Reporting_boundary_derivation_v45.md;
audit/Reporting_boundary_results_v45.md; results/reporting_v45_20261010T175127_627392Z; results/reporting_v45_20261010T175127_627392Z/independent_QA_v45_20261010T175249_660324Z.json.

Next actionable task: Create an additive annual reporting adapter/pipeline (preserve run_experiment_v2, run_sensitivity_v2, run_uncertainty_v3, historical CSVs and accepted v42). Map legacy actual HP_Heat_Used_MW to v45 HP_Heat_MW, derive HP_Direct_MW=HP_Heat_Used_MW-Storage_Charge_MW, and require explicit Unmet_Heat_MW from simulate_system_v13 or a newer finite-backup dispatch. Produce a fresh finite-backup period experiment with explicit durations, integrated COP, nonboiler delivery and service shortfall. Audit gas-baseline economics/CO2 at equal supplied service before claiming savings; unmet demand must not become avoided fuel. Do not relabel nonboiler heat as source-attributed ERF or fill absent pump/fan loads with assumptions. Upstream62 equipment calibration remains blocked until primary supplement/map/domain data are acquired.
Run complete; stop with this handoff.
