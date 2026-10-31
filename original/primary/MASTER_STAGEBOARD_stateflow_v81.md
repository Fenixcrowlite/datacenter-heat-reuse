# Saved-Stateflow physical partition sensitivity v81

UTC 2026-10-13T06:03:28.517890+00:00. Preserved saved Stateflow v80 actually executes 26 complete schedules,
1581 held intervals, 1645 positive segments and 64 interior events;
all six required final modes observed. MATLAB 80 PASS / 0 FAIL;
independent equation/artifact QA 247353 PASS / 0 FAIL;
15 matched partition comparisons PASS / 0 FAIL and four separate reviewer
self-checks PASS. Saved model reopened clean and first fixture replayed bitwise.

Five identical physical input histories were split into 1, 2, 4 and 8 pieces
per original hold. Exact Fraction histories verify operand sums and held inputs.
Closed exp/log trajectories at 120/160 digits independently verify original-MAT
inventory, event ordering/dwell, source/work/loss/service/backup/unmet and reports.
Every compared reporting hull overlaps and every event sequence/time meets the
predeclared budget. Maximum absolute aggregate difference across all 15
comparisons is 5.79E-157 MWh. This is a reconstruction difference, not a
midpoint estimate of a simulated hull. Differences at roughly 160-digit
reviewer precision indicate reconstruction roundoff, not measured plant accuracy.

The practical tradeoff is in the enclosures. For the 48-hour schedule,
splitting 0.5-hour holds into eight 0.0625-hour holds reduces the recovered-source
hull width from about 0.00220020 to 0.000277281 MWh (about 7.94 times narrower),
while the final-inventory hull widens from about 3.36e-12 to 2.59e-11 MWh.
Additional protocol calls tighten the source quadrature rectangles but accumulate
more outward binary roundoff. Smaller steps do not uniformly tighten every hull.

| Physical schedule, split8 | Delivered service (MWh) | Final TES (MWh) | Max aggregate delta (MWh) | Source hull width, split1 → split8 (MWh) | Work hull width, split1 → split8 (MWh) |
|---|---:|---:|---:|---:|---:|
| multiple_cycles_one_call | 0 | 8.13633009 | 1.3e-158 | 0.000292153 → 0.000266396 | 0.000458425 → 0.000417981 |
| OFF_discharge_restart_0p01 | 1 | 9.05366417 | 8.66e-158 | 0.00126909 → 0.00023831 | 0.00202863 → 0.000381174 |
| seasonal_0p5 | 46.9095378 | 5.00818801 | 5.79e-157 | 0.0022002 → 0.000277281 | 0.00334957 → 0.000422453 |
| enable_changes | 3 | 2.9113366 | 6.14e-159 | 3.21965e-14 → 4.68514e-14 | 6.60583e-15 → 9.60343e-15 |
| passive_lambda0.5_E3.0 | 0 | 1.81959198 | 1e-159 | 0 → 0 | 0 → 0 |

No new SLX: actual model remains `matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v80.slx`,
SHA256 `f7032682f4d6c338a99f1425311a807254c3022ba8527dba5f616f53b0ac66be`. Its six-mode Stateflow builder and all prior models,
MATLAB code and status/stageboards are hash-preserved. Checkpoint version is 0.81.
This delivers a fresh executable MATLAB sensitivity harness and independent
physical-schedule comparison, not another runtime monitor.

Evidence `results/partition_sensitivity_v81_20261013T055938_959011Z` includes timestamped MATLAB/Simulink logs, execution receipts,
26 original MAT files and reopened combined MAT, binary exports, numeric CSV,
specification, source snapshots and preservation hashes. Initial restricted
MATLAB startup failure is retained separately; only the successful completed
batch counts. No runtime schedule refusals occurred.

Limits:
- Synthetic bounded normal-mode schedules for the reduced engineering HP/TES equations only; no annual, calibrated equipment, article replication, measured physical validation or generated-code acceptance. Primary signoffs remain 0/31.
- No new SLX or thermal/controller/reporting change: actual saved model 0.80, embedded thermal kernel/trace schema 75 and reporting API 0.76 remain preserved. Checkpoint and model versions differ.
- Same-agent algorithmic independence: Fraction operand histories and 120/160-digit closed exp/log trajectories call no production MATLAB solver. MATLAB reopens original MAT and exports binary; no independent personnel or independent MAT parser claim.
- Sensitivity budget 1e-10 relative to max(1,absolute quantity) is an experiment acceptance threshold, never a relaxed production guard. Hull overlap and widths are also recorded; no midpoint is used as physical truth.
- Five physical schedules and dyadic partitions do not prove arbitrary partition invariance. Existing clock/span/event collision/segment-budget domains and necessary-only runtime monitors remain.

Next actionable task: Resume primary equipment-map evidence and boundary audit from audit/HP_upstream_boundary_results_v44.md. Seek a new accessible route to primary text and the performance-correlation supplement for DOI 10.1016/j.tsep.2025.103513; distinguish verified coefficients/domains from metadata and access blockers. Preserve saved v80 and v81 actual partition evidence; do not repeat the same monitor or sensitivity fixtures without new evidence.
