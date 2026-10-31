# Certified reachable-temperature Stateflow acceptance v85

UTC 2026-10-13T11:16:28.197369+00:00.

New saved `matlab/simulink/DCHR_Electrical_Dispatch_Stateflow_v85.slx` actually executes 28 schedules / 87 held intervals / 100 positive segments / 13 interior events, with all six modes. MATLAB 129 PASS / 0 FAIL; independent QA 25354 PASS / 0 FAIL; 3 separate reviewer corruptions detected. Seven actual chart refusals include exhausted/mutated horizon and uncertified ON dwell. 8 fresh saved-v80 comparisons and clean saved-v85 reopening are bitwise equal. Every schedule also executes preserved v83r2 on identical inputs.

A declared-horizon inventory upper bound replaces the global maximum-temperature electrical cap. It safely raises available heat for cold schedules while retaining the verified held-power loss/event kernel. Positive-loss charging crosses the hot-water floor; binding stop and repeated stop/cutoff/restart histories execute and pass independent closed-equation and pointwise electrical-power QA.

| Case | v83r2 HP heat (MWh) | v85 HP heat (MWh) | Extra recovered source (MWh) | Extra compressor work (MWh) | Extra delivered service (MWh) | Extra final TES (MWh) |
|---|---:|---:|---:|---:|---:|---:|
| service_E3.0_a1.0 | 0.2216761364 | 0.4475657895 | 0.2006542957 | 0.02523535740 | 0.2258896531 | 0e-55 |
| service_E8.5_a1.0 | 0.2216761364 | 0.2460272341 | 0.01961264608 | 0.004738451643 | 0.02435109772 | 0e-55 |
| charge_E4.95_a1.0 | 0.2216761364 | 0.4134373660 | 0.1691661984 | 0.02259503115 | 0.00 | 0.1725851066 |
| loss_charge_E4.95_a1.0 | 0.2216761364 | 0.4134373660 | 0.1692986016 | 0.02246262799 | 0.00 | 0.1717250503 |

Gains use additional compressor work. Charging gains are inventory, not delivered district heat. Comparisons use closed equations reconstructed from original-MAT binary exports, never reporting-hull midpoints.

Model SHA256 `2a9de22c0c55e8c4a87f7b0e0cfe9cd97db08c991f09d98361b009de310adde7`. Timestamped execution/QA logs, original/reopened MAT, binary traces/certificates, source/preservation seals, predeclared cases and comparison evidence: `results/reachable_cap_v85_20261013T111338_510493Z`. Derivation: `audit/Reachable_cap_derivation_v85.md`.

Limitations:

- One certified constant cap over the declared horizon, not a maximal nonlinear instantaneous electrical limiter. Ignoring passive loss in the reachability bound is conservative; larger horizons can recover global-cap behavior.
- Compressor rating, approaches, cooling-factor and storage parameters remain synthetic. No new primary text, equipment calibration, article replication, measured physical validation, annual or generated-code acceptance; full signoffs remain 0/31.
- Auxiliary electricity is separate and total external electricity may exceed the compressor ceiling.
- Raw 27-operand policy and declared horizon are immutable. Thermal schema 75/reporter 76 authenticate effective policy; separate 29-operand certificate and independent QA bind raw policy, cap and reachable inventory.
- Same-agent algorithmic independence: exact Fraction and 120/160-digit closed exp/log equations call no production MATLAB solver. MATLAB reopens MAT for binary export; no independent personnel or independent MAT parser.
- Inherited finite-span, physical-clock, segment-count and unresolved-event domains remain. Analytic event segments execute within macro protocol ticks, not solver-clock events.
- Restricted startup failure, first successful 122-assertion candidate with stale inherited release label, and corrected 124-assertion/24930-pass candidate with one missing-cutoff-coverage QA failure are retained. Final expanded suite adds a focused cutoff witness; saved production model remains v85 and execution harness v85r2.

Next actionable task: Compare declared-horizon cap dependence against the v84 nonlinear comparator at H=1/2/4 hours and held-input partitions on identical histories, then derive a versioned interval-renewal contract before changing the immutable effective-policy kernel. Seek primary equipment supplement/calibration through a new accessible route. Preserve v80-v85 and all failed attempts.
