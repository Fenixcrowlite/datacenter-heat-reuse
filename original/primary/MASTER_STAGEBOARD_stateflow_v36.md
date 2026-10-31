# v36 executed dimensional-tolerance Stateflow repair

UTC 2026-10-10T07:46:27.486567+00:00. Implementation acceptance PASS; physical validation not tested.

New saved v36: 51 scenarios / 351 intervals /
535 positive segments / six modes. MATLAB 3073/3073 PASS;
55/55 actual runtime faults rejected. Independent QA has zero failures;
536 equation checks pass. All four .01 h clock corruptions and
all four forced early restarts reject independently of TES scale. v34/v35 preserved.

Evidence: STATUS_stateflow_v36.json; audit/TES_dimensional_tolerances_derivation_v36.md;
audit/TES_dimensional_tolerances_results_v36.md; results\stateflow_admissibility_v36_20261010T074332672Z\independent_QA_v36_20261010T074604_519524Z.json.

Next: Audit near-boundary numerical admissibility and the remaining host HP/domain validation: exercise restart/capacity separation near energy ulps, short segments and long persistent ages with held and changing inputs; derive a supported resolution/parameter domain and reject unsupported cases before extending any physical claims. Preserve v36 acceptance and v34/v35 counterexamples; keep primary equipment assumptions uncalibrated.
