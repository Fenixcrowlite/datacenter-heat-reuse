# Independent monitor evidence review v29

PASS for runtime-monitor implementation acceptance on the preserved v28 model. Verifier: **775 actual evidence checks, 40 separate synthetic reviewer self-tests, 6 static specification checks; 0 failures**. An additional 5 independent console/preservation checks pass and are reported separately. Completed evidence: `results/stateflow_monitor_v29_20261009T203316008Z`.

All 13 independently anchored corruptions reject with `Stateflow:Runtime` identifiers in the thrown exception and captured diagnostic cause/tree, `Execution` phase, `DiagnosticError` at 0 h, the exact expected assertion and no accepted dispatch sample. The harness attempts 26 mutated simulations (captured and thrown-error passes for each case); the logical case count remains 13. Saved diagnostic and raw JSON payloads match summary records and hashes; exact mutated helper files and captured MAT containers match recorded hashes. No unexpected acceptance artifact exists.

| Corruption case | Expected runtime assertion | QA |
|---|---|---|
| false_system_residual | System first-law failure or false residual. | PASS |
| false_next_energy | TES first-law failure. | PASS |
| negative_backup_flow | Negative dispatch/HP port. | PASS |
| wrong_active_mode | Active state does not match delivered flows. | PASS |
| false_standing_loss | TES loss reporting mismatch. | PASS |
| unallocated_hp_heat | Unallocated HP condenser heat. | PASS |
| simultaneous_tes_ports | Simultaneous TES charge and discharge. | PASS |
| false_useful_heat | Useful heat mismatch. | PASS |
| nonfinite_dispatch | Accepted dispatch and parameters must be finite. | PASS |
| undefined_nonintegral_mode | Undefined mode. | PASS |
| backup_above_capacity | TES/backup power limit exceeded. | PASS |
| tes_state_above_capacity | TES state outside capacity. | PASS |
| false_exponential_retention | Standing-retention mismatch. | PASS |

Independent equation anchor: declared fixed COP 4 gives 8 MW condenser heat, 2 MW electricity and 6 MW recovered source heat; 5 MW serves demand and 3 MW charges TES. With initial 1 MWh, charge efficiency 0.9, interval 1 h and declared decay coefficient 0.01 h^-1, passive `dE/dt = -lambda E` gives `r = exp(-0.01)`. The implemented loss-first recurrence is `E[n+1] = r E[n] + 2.7 MWh`, independently evaluated with its geometric closed form. Executed end energies are **3.69004983374917** and **6.35333322442951 MWh**. All 20 trace fields, TES continuity, separately recomputed TES/system first laws and reported residual consistency are checked for both accepted baselines. Largest reported absolute residual is 1.11022e-15 MWh. These are scenario assumptions, not calibrated equipment or quoted article equations.

The restored two-interval trace is byte-identical to the initial trace (SHA256 `2324b21db861964dc6e14faf060c4dbf9a38d4620a44cd00be34971143e4e052`). The saved SLX archive independently contains the exact allocation/choice/gate scripts and gate-to-trace/feedback wiring. All 13 required source snapshots and before/final manifests agree with current source hashes. v28 SHA256 remains `30ea3701f2f04d293d6c9bf528dc625762bf69db9a06c9d6d384293a98497a1d`; the prior v24 hash also remains unchanged.

Nonblocking defect: MATLAB log line 645 reports an `onCleanup` warning, `Invalid or deleted object`, at `restore_helper` line 259 after model closure. It occurs after the completed summary and `MONITOR_OUTPUT`, and after the actual restored run; therefore it does not invalidate the rejection traces or model preservation evidence. A future versioned harness should restore the helper before closing the model or check for an already-deleted helper. Inherited allocator `y` shadow warnings remain nonfatal. No production/harness edits were made by this review.

Captured MAT containers are hashed and identified but not independently decoded. Saved runtime JSON and accepted CSV traces are parsed independently; source chronology remains local runner evidence without external attestation. This review establishes implementation QA only. No new primary text verification, physical validation, paper replication, six-mode rerun or standalone code generation is claimed. Passive exponential decay remains limited to the constant-coefficient ambient-referenced scalar model, and active-port loss-first integration remains approximate.

Evidence paths:

- Verifier JSON: `audit/stateflow_monitor_independent_qa_v29_20261009T203535986Z.json`
- Verifier log: `automation/logs/stateflow_monitor_independent_qa_v29_20261009T203535986Z.log`
- MATLAB log: `automation/logs/stateflow_monitor_v29_resume_local_20261009T203300662Z.log`
- Review JSON: `audit/Stateflow_monitor_independent_review_v29_20261009T203652583838Z.json`
- Initial self-test JSON: `audit/stateflow_monitor_verifier_selftest_v29_20261009T203454744Z.json`
- Initial self-test log: `automation/logs/stateflow_monitor_verifier_selftest_v29_20261009T203454744Z.log`

The prior unfinished directory `results/stateflow_monitor_v29_20261009T154831124Z` contains no monitor acceptance evidence; its console records only version/license. Next: finalize v29 from this completed monitor evidence and independently reviewed temporal evidence, retaining the teardown defect and scientific limitations.
