# Final independent Stateflow monitor review v29

**PASS** on the preserved v28 model after the root agent repaired the harness cleanup guard. Completed execution: `results/stateflow_monitor_v29_20261009T203631630Z`. MATLAB exit 0 was observed by the root agent; the saved execution log contains all 13 successful case markers, both clean-baseline markers and `MONITOR_OUTPUT`.

The independent verifier passes **775 actual evidence checks, 45 separate synthetic reviewer self-tests and 6 static specification checks (826 total; 0 failures)**. A further 6 console/preservation/cleanup checks are reported separately in this review JSON. Synthetic fixtures exercise the reviewer, including corrupted artifacts with correctly recomputed hashes; they are not plant simulations.

All 13 logical corruption cases reject with `Stateflow:Runtime` exception/cause/diagnostic-tree identifiers, `Execution` phase and `DiagnosticError` at 0 h. Each saved diagnostic has its exact independently anchored assertion and no accepted dispatch sample. There are 26 mutated simulation attempts: one captured and one exception-producing invocation per case. Exact mutated helper text, saved diagnostic/raw JSON, captured MAT header/hash and per-case local paths are independently checked. No unexpected acceptance artifact exists.

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

The independently derived fixed-COP scenario uses COP 4, condenser heat 8 MW, electric input 2 MW, recovered source 6 MW, demand 5 MW and TES charge 3 MW. With `dt=1 h`, `lambda=0.01 h^-1`, charge efficiency 0.9 and initial 1 MWh, passive `dE/dt=-lambda E` gives `r=exp(-0.01)`. The loss-first recurrence `E[n+1]=r E[n]+2.7 MWh` is checked by its geometric closed form. Actual end energies are 3.69004983374917 and 6.35333322442951 MWh. All 20 baseline fields, feedback continuity, independently recomputed TES/system first laws and residual consistency pass. Maximum reported residual magnitude is 1.11022302462516e-15 MWh. These are declared engineering assumptions; no article equations or measured calibration are claimed.

The two-interval restored trace is byte-identical to the initial trace, SHA256 `2324b21db861964dc6e14faf060c4dbf9a38d4620a44cd00be34971143e4e052`. Independent saved-SLX parsing confirms exact allocation, mode-choice and contract-gate scripts and gate-only delivery to accepted trace/TES feedback. All 13 required source snapshots, before/final manifests, source hashes and saved-model bindings pass. The v28 model hash remains `30ea3701f2f04d293d6c9bf528dc625762bf69db9a06c9d6d384293a98497a1d`; the accepted v24 model hash also remains unchanged.

The previous run's cleanup warning is preserved in `audit/Stateflow_monitor_independent_review_v29_20261009T203652583838Z.json`. The root's current harness guards restoration with `bdIsLoaded(mdl)`. The final complete log contains no deleted-object or `onCleanup` warning. Inherited allocator `y` shadow warnings remain nonfatal. This review changed only the independent verifier; it did not modify production code, harnesses, models or ledgers.

Captured MAT containers are hashed and identified, not independently decoded. Runtime JSON and accepted CSV traces are parsed independently; chronology remains local runner evidence without external attestation. This is implementation QA, with no new primary-text verification, physical validation, paper replication, six-mode rerun or standalone code generation. Passive decay is exact only for constant-coefficient ambient-referenced scalar energy; active-port loss-first integration remains approximate.

Evidence paths:

- Final verifier JSON: `audit/stateflow_monitor_independent_qa_v29_20261009T203848726Z.json`
- Final verifier log: `automation/logs/stateflow_monitor_independent_qa_v29_20261009T203848726Z.log`
- Final MATLAB log: `automation/logs/stateflow_monitor_v29_fixed_local_20261009T203624213Z.log`
- Final review JSON: `audit/Stateflow_monitor_independent_review_v29_final_20261009T203931007626Z.json`
- Independent verifier SHA256: `a04f6c9f7a49086f0578392d23c970ad48da36a02359837487174207cbdac6db`
- Final runner SHA256: `af75b32b8d46b230a50b2f29566db484a747a71526346e5a0377ead75dcff275`

Next: finalize v29 using this final monitor evidence and independently reviewed final temporal evidence, retaining scientific limitations and all prior evidence.
