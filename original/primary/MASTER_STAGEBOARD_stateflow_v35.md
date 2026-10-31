# v35: saved-v34 dimensional tolerance defect

2026-10-10T07:32:15.442162+00:00. Audit PASS; controller defect OPEN. Saved model remains v34, preserved.

20 scenarios / 109 intervals / 136 positive segments / six modes; 1205 MATLAB assertions; 27 RK4 bound checks; independent QA zero failures. Clock mutation rejected at three scales and wrongly accepted at largest; early-age guard defect independently confirmed.

Evidence: audit/TES_admissibility_results_v35.md, audit/TES_admissibility_derivation_v35.md, STATUS_stateflow_v35.json.

Next: Implement additive Stateflow v36 with separate energy, power, temperature, dimensionless and physical-hour tolerances; embed corrected guard/monitor, preserve v34 and v35 counterexamples, execute the six modes and changing-input fixtures, and require clock corruption and early-dwell guards to reject at every tested energy scale. Audit representable time resolution and retain equipment assumptions without calibrated cycling-loss claims.
