# Independent Stateflow monitor acceptance review — v26

Reviewer lane `/root/stateflow_qa` read `automation/STATEFLOW_ACCEPTANCE.md`, `STATUS_stateflow_v22.json`, `MASTER_STAGEBOARD_stateflow_v22.md`, latest research `STATUS_v25.json` / `MASTER_STAGEBOARD_v25.md`, and `audit/research_frontier_2026_10_08.md` before inspecting the v22/v24 builders, HP adapters, state-choice/allocation helpers, runtime contract gate, numerical reference and saved evidence. This lane changed only its independent audit specification, verifier and review artifacts. MATLAB execution was performed by the implementation lane; no concurrent MATLAB process was started by this reviewer.

## Concrete acceptance gap found

The actual v24 ordinary acceptance was already executed: `results/stateflow_v24_20261009T031325970Z/acceptance_summary_v24.json` records 464/464 MATLAB checks, 39 intervals, all six modes and 44/44 invalid-domain/clock simulation rejections. Its independent trace audit records 2860 checks with zero failures. These results establish valid dispatch and adapter failure paths, but do not alone establish that downstream monitor assertions reject corrupted chart outputs before accepting traces or TES feedback.

The earlier `automation/logs/stateflow_gate_faults_v24_20261009T031512549Z.log` ends during the unmutated baseline simulation. `results/stateflow_gate_faults_v24_20261009T031521833Z` contains cache/codegen artifacts but no baseline MAT file or completed fault summary. This is an incomplete-evidence defect; the cause of the old run's interruption is unknown. A zero stop time appears in its harness source, but the available log does not prove that setting caused the interruption. The preserved v24 model itself has not been shown defective by that missing evidence.

## Independent tests and hand calculation

`audit/stateflow_monitor_fault_cases_v26.json` independently specifies twelve first-output corruptions. Eight preserve the earlier pending test intentions: false residual, false next energy, negative backup, wrong active mode, false standing loss, unallocated HP heat, simultaneous TES ports and false useful heat. Four add direct finite-value, integral-mode, backup-limit and TES-capacity rejection coverage. These are in-memory QA corruptions, not equipment fault scenarios.

The two-tick valid baseline fixes COP at 4 with recovered source 6 MW, HP capacity/request 8 MW, demand 5 MW, charge 3 MW, TES capacity 10 MWh, initial energy 1 MWh, charge/discharge efficiencies 0.9/0.8 and linear standing loss 0.01 per hour. All values are explicit engineering assumptions, not paper or equipment values.

From the HP first law, `H <= 6/(1-1/4) = 8 MW`; request and capacity reach that same bound, so compressor electricity is 2 MW and extracted source is 6 MW. Demand receives 5 MW directly and the remaining 3 MW charge TES. The independently derived recurrence is `E_next = 0.99 E_start + 2.7 MWh`. Thus the actual two model samples must have:

| Time (h) | TES start (MWh) | After standing loss (MWh) | Next TES (MWh) | Mode |
| --- | --- | --- | --- | --- |
| 0 | 1 | 0.99 | 3.69 | STORAGE_CHARGE (2) |
| 1 | 3.69 | 3.6531 | 6.3531 | STORAGE_CHARGE (2) |

For both samples, standing loss plus charge loss closes `E_start + 3 MW × 1 h = E_next + losses`. Whole-boundary input `(6+2) MW × 1 h + E_start` equals useful demand `5 MW × 1 h + E_next + losses`. This calculation is independent of the MATLAB component implementation.

## Actual executed result and independent QA

The additive `matlab/simulink/run_stateflow_monitor_faults_v26.m` reads the independent specification and loads the preserved `DCHR_Dispatch_Stateflow_v24.slx`. It executes a two-tick baseline, mutates only the in-memory allocation helper for each case, restores it after each simulation, saves actual failure diagnostics, then executes the clean baseline again. This source was reviewed before reading the completed evidence.

`results/stateflow_monitor_v26_20261009T075607297Z/gate_fault_rejections_v26.json` records 12/12 actual simulation rejections, 12/12 expected runtime-gate assertions and zero unexpectedly accepted simulations. Each saved diagnostic identifies `DCHR_Dispatch_Stateflow_v24/Runtime_Contract_Gate` and its specific assertion; thus these are runtime monitor failures rather than generic compile failures. Both valid traces contain the exact two hand-case samples. The restored trace and initial trace have identical SHA256 `82f27c06d22d80d2752b1e99c904a25d9960a45342dcacb64668099d9d4a515d`.

The new independent verifier `audit/verify_stateflow_gate_evidence_v26.py` imports no MATLAB algorithm. It checks the exact independent case set, mutation and expected message, per-case restoration, actual diagnostic contents/hashes, finite numerical trace anchors, independently recomputed TES/system closure, actual next-to-start feedback, before/after model and allocator hashes, clean rerun equality and absence of unexpected-acceptance artifacts. It passed **255/255 assertions, zero failures**:

- `results/stateflow_monitor_v26_20261009T075607297Z/independent_monitor_qa_v26_20261009T075827307Z.json`
- `automation/logs/stateflow_independent_monitor_qa_v26_20261009T075827307Z.log`

The saved model retains preexisting SHA256 `1f1c826f0f61d04bea58c2ab39d607268ac273bad9564e69bec89e361c461389`. A distinct Python ZIP/XML inspection passed **78/78 structure/provenance assertions**, including six states, guarded transitions, shared timing, all monitor connections, absence of raw chart bypass to trace/memory and embedded-source equality:

- `audit/stateflow_saved_model_preservation_v26_20261009T075811264Z.json`
- `automation/logs/stateflow_saved_model_preservation_v26_20261009T075811264Z.log`

The new evidence verifier also passed **16/16 synthetic self-tests**, including deliberately wrong mutations, generic diagnostics, hash corruption, missing/duplicate cases, timing/state/mode corruption, nonfinite residual and simultaneous ports. This checks reviewer sensitivity; it is expressly separate from actual simulation results:

- `audit/stateflow_gate_qa_selftest_v26_20261009T075712188Z.json`
- `automation/logs/stateflow_gate_qa_selftest_v26_20261009T075712188Z.log`

## Fresh full acceptance after fault restoration

The implementation lane's combined MATLAB batch completed with exit code 0 and separately generated `results/stateflow_v24_20261009T075807903Z`. Its fresh summary records **464/464 MATLAB assertions**, ten scenarios, 39 intervals, all six modes and **44/44 actual domain/clock rejections**. Thus the post-fault acceptance demonstrates six-mode dispatch, numerical v16 reference comparison, TES feedback and invalid-input rejection after the monitor test's in-memory alterations have been discarded.

This reviewer independently reran `audit/verify_stateflow_runtime_v24.py` against that fresh saved-model/trace/rejection evidence. Results were **2860/2860 valid-trace assertions**, **309/309 rejection-schema assertions** and **78/78 saved-model structure/source assertions**, all with zero failures. Its **10/10 synthetic schema self-tests** are separate from execution evidence. The independent residual recomputed from exported CSV ports is at most `2.867150961094467e-14 MWh`; MATLAB's directly recorded balance residual is at most `7.771561172376096e-16 MWh`. Both pass their declared numerical tolerances. CSV rounding and independently reordered arithmetic need not produce bit-identical residuals.

- `results/stateflow_v24_20261009T075807903Z/independent_full_acceptance_qa_v26_20261009T080009595Z.json`
- `automation/logs/stateflow_independent_full_acceptance_qa_v26_20261009T080009595Z.log`

The v24 model remains at the original locked SHA256 after this full rerun. This lane also reviewed `audit/finalize_stateflow_checkpoint_v26.py` without executing it: its required acceptance flags/counts, reported QA identities, actual file hashes, log receipt and distinct immutable status/stageboard outputs align with the evidence reviewed here. No packaging defect was identified in this source review.

Reproduce the independent actual monitor audit from project root with:

```powershell
python audit/verify_stateflow_gate_evidence_v26.py --result-dir results/stateflow_monitor_v26_20261009T075607297Z --report <new_unique_report.json>
```

## Evidence classification and remaining limits

The model traces and diagnostic files are actual local MATLAB/Simulink/Stateflow execution evidence. The state/memory/monitor topology and script matches are static saved-file evidence. The recurrence and first-law checks are independent arithmetic under declared assumptions. The synthetic fixtures test the verifier. No primary article text was newly verified; no experimental result, equipment performance, publication equation or calibration is claimed.

The runner records before/after hashes for the saved model and allocation source. The verifier records other current source hashes as inspection provenance; it does not claim independently recorded historical before/after identity for those host dependencies. The separate full v24 acceptance rerun is independently audited above and must be packaged with its own result paths. This monitor hand case uses STORAGE_CHARGE; its purpose is downstream assertion authority and restoration, not additional six-mode transition coverage.

Normal-mode host MATLAB HP execution remains the supported boundary. Standalone generated code, measured-system validation and paper replication remain untested. Linear loss-first TES retention remains time-partition dependent; the implementation still lacks hysteresis, minimum dwell, compressor cycling, equipment/sensor faults and calibrated hydraulic/network/fuel/auxiliary physics. After packaging the successful full acceptance rerun and this completed monitor evidence, the next actionable research task is the already documented primary-text TES standing-loss audit and independently derived continuous/exponential reference with timestep convergence, preserving v22/v24's explicit discrete baseline.
