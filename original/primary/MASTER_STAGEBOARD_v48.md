# v48 annual dispatch implementation handoff

2026-10-10T18:28:37.571775+00:00. Scoped repair PASS. New annual MATLAB adapter uses verified HP
step v40 and explicitly retains legacy loss-first TES. Saved actual Stateflow
remains v42 and was freshly executed; no annual Stateflow/new SLX claim.

MATLAB 75/0; independent 106795/0; four separate
reviewer mutations; 12 domain rejections; 26,280 full-year intervals plus nine
matched fixture intervals. Actual saved-v42: 63 intervals/all six modes/47
transitions. Corrected annual output has zero nonmaximal intervals. At 2 MW
backup, unmet heat falls by 136.350293 MWh on synthetic inputs.

Evidence: STATUS_v48.json; audit/Annual_dispatch_derivation_v48.md;
audit/Annual_dispatch_results_v48.md; results/annual_dispatch_v48_20261010T182553_348909Z; results/annual_dispatch_v48_20261010T182553_348909Z/independent_QA_v48_20261010T182722_145809Z.json.

Next actionable task: Design and test an additive annual saved-v42 input adapter with explicit TES temperature/cutoff parameters and HP hysteresis/dwell policy. Preflight all 8760 source/sink/delivery inputs against the actual model contract before running it; document unsupported regimes rather than inventing equipment calibration. Execute an initial multi-day sequence with independent port, event, inventory and report QA, then extend to actual annual execution if admissible. Compare exact/event TES with v48 loss-first traces as distinct policies; never relabel v48 MATLAB results as annual Stateflow. Primary equipment calibration, auxiliary loads and inventory valuation remain open.

Run complete; stop with this handoff.
