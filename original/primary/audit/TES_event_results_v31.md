# v31 executed TES event-policy comparison

UTC: 2026-10-09T21:42:44.178000+00:00. Gate PASS: 3544/3544 MATLAB assertions; 141 component cases; 12 actual component domain rejections; 50 actual saved-v30 simulations / 310 intervals / all six modes. Independent equations 566/566 PASS. Independent evidence categories: `{'actual_numeric': {'passed': 24455, 'failed': 0}, 'static_saved_v30_model': {'passed': 66, 'failed': 0}, 'artifact_runtime_and_preservation': {'passed': 9644, 'failed': 0}, 'synthetic_reviewer_self_checks': {'passed': 4, 'failed': 0}}`. Synthetic reviewer checks are separate. Maximum saved-model balance residual 2.095546e-15 MWh.

The production model remains release **0.30**. New event MATLAB component is tested before its future Stateflow integration. Existing model and immutable numerical baselines are preserved.

## Two-hour totals at the coarse h=2-hour boundary

| Scenario | Uniform TES discharge MWh | Event TES discharge MWh | Uniform unmet MWh | Event unmet MWh | Uniform accepted charge MWh | Event accepted charge MWh |
|---|---:|---:|---:|---:|---:|---:|
| capacity | 0.000000000 | 0.000000000 | 0.000000000 | 0.000000000 | 3.225923459 | 3.301881150 |
| cutoff | 0.645329781 | 1.082135846 | 0.354670219 | 0.458932077 | 0.000000000 | 0.000000000 |
| near_cutoff | 0.000000000 | 0.113637587 | 1.000000000 | 0.943181207 | 0.000000000 | 0.000000000 |
| no_bound_charge | 0.000000000 | 0.000000000 | 0.000000000 | 0.000000000 | 2.000000000 | 2.000000000 |
| no_bound_discharge | 0.200000000 | 0.200000000 | 0.000000000 | 0.000000000 | 0.000000000 | 0.000000000 |
| passive_crossing | 0.000000000 | 0.000000000 | 0.000000000 | 0.000000000 | 0.000000000 | 0.000000000 |
| zero_rate_cutoff | 1.600000000 | 1.600000000 | 0.000000000 | 0.200000000 | 0.000000000 | 0.000000000 |
| high_rate_cutoff | 0.000000000 | 0.031498667 | 1.000000000 | 0.984250666 | 0.000000000 | 0.000000000 |
| hp_only | 0.000000000 | 0.000000000 | 0.000000000 | 0.000000000 | 0.000000000 | 0.000000000 |
| backup_only | 0.000000000 | 0.000000000 | 0.000000000 | 0.000000000 | 0.000000000 | 0.000000000 |

The cutoff example serves more TES heat under the event policy but leaves more unmet demand because full early discharge prevents simultaneous use of backup and the late deficit exceeds the boiler limit. The zero-rate example has equal TES energy under both policies but different unmet demand. Treating event TES energy/h as a constant power would conceal this difference. Near-cutoff cases show that uniform coarse-step throttling can reject all storage service while an initial event pulse is feasible. No policy dominance or optimization claim is made.

## Partition comparison

| Family | Uniform discharge at h=2 / h=0.125 MWh | Event discharge range MWh | Event endpoint range MWh |
|---|---:|---:|---:|
| backup_only | 0.000000000 / 0.000000000 | 0 | 0 |
| capacity | 0.000000000 / 0.000000000 | 0 | 0 |
| cutoff | 0.645329781 / 1.064743577 | 0 | 0 |
| high_rate_cutoff | 0.000000000 / 0.000000000 | 0 | 9.99e-16 |
| hp_only | 0.000000000 / 0.000000000 | 0 | 0 |
| near_cutoff | 0.000000000 / 0.109002083 | 0 | 0 |
| no_bound_charge | 0.000000000 / 0.000000000 | 0 | 0 |
| no_bound_discharge | 0.200000000 / 0.200000000 | 0 | 9.77e-15 |
| passive_crossing | 0.000000000 / 0.000000000 | 0 | 9.77e-15 |
| zero_rate_cutoff | 1.600000000 / 1.600000000 | 0 | 0 |

The event policy preserves endpoint and integrated heat/loss/backup/unmet across these five partitions. The v30 uniform policy changes its constrained port allocation with h; its unbounded controls agree with the event model. This experiment tests the chosen reduced equations and control policy, not calibrated physical behavior.

## Evidence and reproduction

- Result package: `results/TES_event_v31_20261009T214008841Z`: original MAT simulations, separate MAT export, actual trace CSVs, event trace, comparison, source/model/spec snapshots and assertion ledger.
- Independent QA: `audit/TES_event_independent_QA_v31_20261009T214221_956636Z.json`; observed batch receipt: `audit/TES_event_execution_receipt_v31_local_20261009T214001224Z.json`; log: `automation\logs\TES_event_matlab_v31_local_20261009T214001224Z.log`.
- Derivation/provenance: `audit/TES_boundary_event_derivation_v31.md`; new component `matlab/+dchr/+components/storage_event_kernel_v31.m`.
- Run `python -X utf8 audit/TES_event_reference_v31.py` for a fresh spec, then `matlab -batch "addpath('matlab','matlab/simulink'); out=run_TES_event_comparison_v31('<fresh-spec>'); export_TES_event_mat_audit_v31(out);"`. Capture a zero-exit receipt and run `python -X utf8 audit/verify_TES_event_v31.py <fresh-result> <receipt>`.
- Initial sandbox startup failed before tests. First actual batch passed 3534/3544 but exposed ten empty-array shape failures in the one-sample feedback assertion. The assertion was repaired and the complete batch freshly rerun. Prior logs/results are retained. A speculative unused metadata field in the exporter was removed before its first execution; executed exporter source is separately snapshotted.

## Limitations

- Checkpoint v31 executes the saved v30 Stateflow model and a new MATLAB event comparator. No new SLX and no event controller embedded in Stateflow.
- Constant ambient/heat capacity/loss coefficient and held available TES requests; no hydraulic, stratified or measured tank validation.
- Charging modulates to replace ambient loss at capacity; it does not implement shutdown/restart cycling, hysteresis or dwell.
- Charging compares accepted TES heat/loss only. Event comparator has no piecewise HP scheduling, nonlinear COP/electricity or full-system event monitor.
- Discharge backup/unmet is integrated over actual segments. Full-power event dispatch has no universal advantage over uniform throttling.
- Timestep sweep is h=2,1,0.5,0.25,0.125 hours over two hours for ten assumed scenario families, not a general optimizer or empirical sensitivity study.
- Saved v30 normal-mode host HP and helper shadow warnings remain; no standalone generated-code or event Stateflow transition timing acceptance.
- 566 reduced-equation checks and independent Python artifact/numeric QA are not separate human/agent review, article replication or physical validation. Full primary signoffs remain 0/31.

Next: Design and implement additive Stateflow v32 with explicit intra-interval segments: HP request/COP/electricity per segment, capacity hold/recovery curtailment, cutoff shutdown and segment-level finite boiler/unmet balance. Preserve v24/v28/v30. Use v31 event/backup counterexamples as independent acceptance fixtures; never calculate finite backup from average TES power.
