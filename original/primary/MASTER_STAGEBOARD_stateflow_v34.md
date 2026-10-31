# v34: persistent HP hysteresis/dwell Stateflow

2026-10-10T03:01:39.854221+00:00. Implementation acceptance PASS; model v34 saved and simulated.

37 scenarios / 255 intervals / 412 positive analytic segments / six modes. 28744 MATLAB assertions; 30 runtime rejections; 412 independent RK4 checks; QA `{"numeric": {"passed": 58045, "failed": 0}, "artifact": {"passed": 24018, "failed": 0}, "legacy": {"passed": 139, "failed": 0}, "alternate": {"passed": 14, "failed": 0}, "archive": {"passed": 26, "failed": 0}, "faults": {"passed": 32, "failed": 0}, "synthetic": {"passed": 8, "failed": 0}, "preservation": {"passed": 1040, "failed": 0}}`; zero failures.

v33 capacity-tail service defect repaired for tested v34 fixtures; zero unmet and matching energy/electricity/physical clock over six held-input partitions. All earlier baselines preserved. ON dwell has explicit safety overrides.

Evidence: `audit/TES_hysteresis_results_v34.md`, `audit/TES_hysteresis_derivation_v34.md`, `results\stateflow_v34_20261010T025818184Z`, `audit\Stateflow_QA_v34_20261010T030114_814113Z.json`.

No calibrated/physical validation, article replication, real compressor-cycle data, standalone code generation or solver-clock event scheduling. Full primary signoffs 0/31.

Next: Audit primary equipment/engineering evidence for the minimum-load COP cutoff, compressor dwell and cycling-loss assumptions; derive admissible restart-band constraints under changing source/demand. Preserve accepted v34 and distinguish screening assumptions from calibrated hardware before adding an equipment-fault or cycling-loss plant model.
