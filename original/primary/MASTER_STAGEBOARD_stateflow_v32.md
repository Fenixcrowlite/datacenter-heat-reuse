# v32: executed segment Stateflow acceptance

UTC: 2026-10-10T02:30:36.007723+00:00. PASS: 13868/13868 MATLAB assertions; 65 scenarios / 242 intervals / 484 segment slots (272 positive-duration) / six modes; 23 runtime fault rejections; 1294 independent equation checks.

Independent QA: `{'actual_numeric': {'passed': 27202, 'failed': 0}, 'static_saved_model': {'passed': 73, 'failed': 0}, 'artifact_runtime_preservation': {'passed': 20312, 'failed': 0}, 'synthetic_reviewer_checks': {'passed': 9, 'failed': 0}}`; zero failures. Synthetic reviewer checks are separate. Maximum interval balance residual: 3.5527137e-15 MWh.

Model `matlab/simulink/DCHR_Dispatch_Stateflow_v32.slx` uses `dchr_segment_plan_v32.m`; HP operating point/electricity and finite boiler/unmet are calculated per physical segment. Iterated chart activations occur within the macro timestep.

Evidence: `results/stateflow_v32_20261010T022704149Z`, `audit/Stateflow_independent_QA_v32_20261010T022948_982369Z.json`, `audit/Stateflow_execution_v32_accept_20261010T022650039Z.json`. See `audit/Stateflow_completion_review_v32.md`, `audit/TES_segment_Stateflow_derivation_v32.md` and `audit/TES_segment_Stateflow_results_v32.md`.

Reproduce using `audit/run_stateflow_batch_v32.ps1 -Operation accept -SpecDirectory <spec>` and `python -X utf8 audit/verify_stateflow_completion_v32.py <fresh-result-directory> <receipt>`. The builder refuses to overwrite the saved release.

- Two ordered analytic physical segments execute within each macro Simulink timestep; no solver-clock event activation claim.
- Normal-mode host HP planner is required. Standalone generated code remains untested.
- Constant ambient/heat capacity/loss coefficient and assumed screening COP/temperatures; no calibrated, stratified or hydraulic plant validation.
- Capacity fallback can cool until the next sample if the low-load HP hold is unavailable or source-limited; no cycling, hysteresis, dwell or equipment/sensor faults.
- 64-ulp capacity-energy/equilibrium recognition handles binary roundoff; this is not a physical controller deadband.
- Fault coverage is 13 finite domain, two delayed finite and eight actual allocator corruption cases; delayed NaN/Inf timing is untested.
- A sample at StopTime represents a complete following interval. Interval mode summarizes segment modes, whose ordered traces remain authoritative.
- Independent algorithm/artifact QA is not separate human/agent review, article replication or measured physical validation. Full primary signoffs remain 0/31.
- Preserved v30 reference helper shadow warnings remain in the logs; no universal partition-invariance or policy superiority claim.

Next: Audit capacity-hold HP unavailability/source-limited fallback across macro timesteps; independently derive a justified restart/hysteresis/dwell policy before a new Stateflow version. Preserve v24/v28/v30/v32 and the finite-backup/electricity counterexamples; do not claim universal event-policy superiority.
