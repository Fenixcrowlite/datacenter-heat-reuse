# v47 annual HP defect handoff

2026-10-10T18:16:51.034755+00:00. Scoped audit PASS; annual v13 HP output nonmaximality OPEN.
Fresh annual 8760 intervals: zero source violations, 3925
nonmaximal outputs; static extra capability 220.771579093 MWh.
This is not actual extra delivered heat or savings. Accepted saved v42 freshly
executes eight intervals/all six modes and matches analytic source-limited roots.
No new SLX or corrected annual dispatch is accepted.

MATLAB 193/0; independent actual 36312/0;
four reviewer mutations; 849 preserved hashes.
Same-agent algorithmic QA; physical validation and primary calibration OPEN.

Evidence: STATUS_v47.json; audit/HP_annual_derivation_v47.md;
audit/HP_annual_results_v47.md; results/hp_annual_v47_20261010T181354_797146Z; results/hp_annual_v47_20261010T181354_797146Z/independent_QA_v47_20261010T181530_627876Z.json.

Next actionable task: Implement additive simulate_system_v48 using verified heat_pump_step_v40 for actual source-constrained HP output, with demand plus admissible TES charge request. Preserve v13/v2, saved Stateflow v42 and v46/v47 evidence. Initially keep the legacy TES loss-first law explicitly labelled to isolate the HP dispatch correction; do not claim equivalence to v42 exact/event TES. Recompute the entire 8760-interval dispatch and inventory trajectory, not a static capability-gap credit. Verify source limits, HP/request maximality, TES recurrence, boiler cap, unmet heat and first-law closure independently. Compare matched constant-input/no-storage cases with actual saved v42 execution; include zero-penalty compatibility and operating-cutoff domain distinctions. Feed corrected actual ports to v45/v46 period reports and equal-delivered-service comparison. Only then plan an actual annual Stateflow adapter/execution. Equipment-specific primary calibration, auxiliary loads and inventory valuation remain open.

Run complete; stop with this handoff.
