# v41 saved-v40 clock uncertainty defect checkpoint

2026-10-10T13:00:37.509896+00:00. DEFECT_CONFIRMED_OPEN; saved model remains 0.40; no new SLX.
29 scenarios / 27 completed / 33 intervals /
47 positive segments / six modes. MATLAB 56 PASS / 0 FAIL;
two actual clock-budget rejections. Independent actual QA 1359 PASS / 0 FAIL;
synthetic 4 PASS / 0 FAIL. Ten interval-unresolved dwell transitions;
zero certainly premature physical transitions proved. Controller guarantee defect OPEN.

Evidence: STATUS_stateflow_v41.json; audit/Clock_uncertainty_derivation_v41.md;
audit/Clock_uncertainty_results_v41.md; results/stateflow_clock_v41_20261010T125630995Z/independent_QA_v41_20261010T130008_944237Z.json.

Next: Implement additive Stateflow v42 uncertainty-aware dwell decisions in planner, saved supervisor and runtime gate: require physical-age lower endpoint hi+lo-bound >= minimum dwell using cancellation-safe comparisons; schedule a conservative wait with certified post-add enclosure or explicitly reject unresolvable progress. Retain ON-dwell safety overrides and all v41 seeds/ties, then execute new SLX with independent interval timing, six-mode/reference, actual fault and saved-MAT QA. Preserve v40/v41 evidence. Then resume primary equipment traceability.
