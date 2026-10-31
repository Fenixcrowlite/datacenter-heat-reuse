# DCHR C36: 100 MWh provenance and v2 scenario filename mismatch
Verified local: 2026-10-28T17:56:17+01:00

FOUND: original MATLAB run_experiment.m and run_experiment_v2.m explicitly configure 100 MWh energy-only storage.
FOUND: run_experiment_v2.m exports O{end} to best_scenario_v2_timeseries.csv; O{end} is Liquid35_LowTempDH.
This is NOT the highest-coverage scenario Warm45_Storage100 in scenario_summary_v2.csv.
Annual gas difference (last vs highest-coverage) = 2006.503263392 MWh.
Independently replayed 8760+8760 CSV hourly storage states; 140160 Decimal dispatch checks, 14/14 separate QA tests PASS.
v85 10 MWh cases are different from early 100 MWh assumptions; no tank volume or temperature validation.
No MATLAB execution, no source edits, no GUI, no new Codex/GPU workers, no VRS, no OAuth changes.
Existing task scc-2aab24704c2bd0, evidence event #1396; remains queued, no worker.
Card: https://desktop-m9l3i4m.taila1c6bd.ts.net/?synapse_task=scc-2aab24704c2bd0
Artifact: C:\Users\Lysda\Desktop\SynapseControlCenter\recovery\AUTONOMOUS_RUN_20261028_1754_DCHR_C36_BASELINE_PROVENANCE
SHA256 manifest: f460e7f950a63d730893eae58c31699518394a9c4b283d9c558cfa93a6653d48
SHA256 evidence: 03701be9f0eb87b4ae6eed87a05cf7cc830197679ba982be995bfae76e0213a9
Primary-source signoffs 0/31. Next: Export the Warm45_Storage100 v2 timeseries into a NEW isolated filename, never overwrite best_scenario_v2_timeseries.csv; then compare same-boundary v1/v2/Stateflow 10 MWh and physical stratified tank. No MATLAB run or model parity claimed yet.
