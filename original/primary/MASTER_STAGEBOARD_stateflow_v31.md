# v31: executed TES boundary-event comparison

UTC: 2026-10-09T21:42:44.178000+00:00. Gate PASS: 3544/3544 MATLAB assertions; 141 component cases; 12 actual component domain rejections; 50 actual saved-v30 simulations / 310 intervals / all six modes. Independent equations 566/566 PASS. Independent evidence categories: `{'actual_numeric': {'passed': 24455, 'failed': 0}, 'static_saved_v30_model': {'passed': 66, 'failed': 0}, 'artifact_runtime_and_preservation': {'passed': 9644, 'failed': 0}, 'synthetic_reviewer_self_checks': {'passed': 4, 'failed': 0}}`. Synthetic reviewer checks are separate. Maximum saved-model balance residual 2.095546e-15 MWh.

Model release remains 0.30; the event component is not embedded in Stateflow. See `audit/TES_event_results_v31.md` and `audit/TES_boundary_event_derivation_v31.md`.

Next: Design and implement additive Stateflow v32 with explicit intra-interval segments: HP request/COP/electricity per segment, capacity hold/recovery curtailment, cutoff shutdown and segment-level finite boiler/unmet balance. Preserve v24/v28/v30. Use v31 event/backup counterexamples as independent acceptance fixtures; never calculate finite backup from average TES power.
