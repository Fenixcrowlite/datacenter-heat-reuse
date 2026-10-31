# v33: saved-v32 fallback audit

2026-10-10T02:42:41.191702+00:00. Experiment PASS; production controller defect CONFIRMED OPEN. Model remains v32; no new SLX.

25 scenarios / 310 intervals / 620 slots; 16200 MATLAB assertions; 643 equation checks; independent QA `{'actual_generic_oracle': {'passed': 34863, 'failed': 0}, 'alternate_targeted_recurrence': {'passed': 625, 'failed': 0}, 'static_saved_model': {'passed': 73, 'failed': 0}, 'artifact_runtime_preservation': {'passed': 24898, 'failed': 0}, 'synthetic_reviewer_checks': {'passed': 3, 'failed': 0}}`, zero failures.

Capacity tail can leave usable TES idle while demand is unmet. Low-load hold cutoff produces macro-step-sensitive service and HP availability pulses. Source shortage at initial capacity is distinct; feasible hold/passive/source-limited controls are invariant across the tested constant-input partitions.

Evidence: `audit/TES_capacity_fallback_results_v33.md`, `audit/TES_capacity_fallback_derivation_v33.md`, `results\stateflow_fallback_v33_20261010T023623898Z`, `audit\Stateflow_fallback_QA_v33_20261010T023838_807159Z.json`.

No calibrated/physical validation, article replication, new fault acceptance or standalone code generation. Full primary signoffs 0/31.

Next: Implement additive Stateflow model v34 with persistent HP hysteresis/dwell latch, explicit physical-duration timers, TES service during HP OFF and a bounded multi-event integrator; test exact-capacity initialization, changing inputs, finite backup, cutoff safety, timer units and timestep partitions against the preserved v32 counterexample.
