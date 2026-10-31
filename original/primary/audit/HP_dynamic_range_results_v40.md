# v40 HP numerical-domain repair results

UTC 2026-10-10T12:49:21.176639+00:00. **PASS scoped implementation acceptance.**
New actual saved model: `matlab/simulink/DCHR_Dispatch_Stateflow_v40.slx`, SHA256 `eabb893ed5465b754981bb45ad06a1bb4ad1700ce031ce3531737b28ff7392f6`.
v38, v39 defect traces and all prior sealed evidence remain preserved.

Source-relative search replaces fixed 80-step output-space search; floating-point
adjacency ends bisection. Stable evaporator evaluation avoids Q-W cancellation
near COP=1. Unrepresentable positive electricity/source flow rejects explicitly.
Derivation: `audit/HP_dynamic_range_derivation_v40.md`. These are assumed
engineering screening equations, with no newly adopted article/equipment values.

Actual MATLAB build/simulation and separate read-only saved-MAT export exit zero.
33 scenarios / 101 completed intervals /
151 positive physical segments execute all six modes.
MATLAB harness 391/391 PASS;
321 HP probes and 30 actual runtime fault rejections.
Clean model traces agree before and after temporary in-memory corruption tests.

Independent actual evidence checks 8491/8491 PASS; separate synthetic
oracle self-checks 3/3 PASS. Analytic implementation comparisons
1396 PASS / 0 FAIL. The reviewer evaluates
150-digit exact-input quadratic maxima, Decimal TES ODEs and the independently
implemented prior six-mode/dwell/fallback reference. It binds JSON to MATs
re-exported in another MATLAB batch and checks saved chart/source hashes.
Source-limited request invariance covers source ratios through 2^-1070 with
positive representable electricity. ULP and relative tolerances remain explicit.
2903 prior immutable entries retain hashes/sizes.
Maximum independent segment balance residual 4.7683715781454694e-08 MWh.

| Retained counterexample | Analytic HP MW | Actual HP MW | Actual unmet MW | Mode |
|---|---:|---:|---:|---:|
| wide_request_60 | 9.25185853854e-18 | 9.25185853854e-18 | 0 | 2 |
| wide_request_80 | 8.82325986723e-24 | 8.82325986723e-24 | 0 | 2 |
| wide_request_90 | 8.61646471409e-27 | 8.61646471409e-27 | 0 | 2 |
| wide_request_120 | 8.02470810161e-36 | 8.02470810161e-36 | 0 | 2 |

Mode 2 is STORAGE_CHARGE. The formerly false-OFF wide-request cases at source
ratios 2^-90 and 2^-120 now operate and serve their complete tiny demands.
The old failed comparisons remain sealed in v39; this release does not relabel them.

The sandbox startup failure occurred before any simulation and is retained
with its receipt/log. Authorized local batches then completed. Stateflow formal
argument shadow warnings are retained. Any unsuccessful reviewer reports retain
their exact source snapshots and logs beside the successful report.

## Limits and next task

- Scoped numerical implementation acceptance, not measured physical validation or article replication.
- Extreme ratios/subnormal powers and COP near one are numerical fixtures, not plausible equipment sizes.
- Exact v39 binary64 cutoff fixture observed only; comprehensive near-cutoff classification remains unproved.
- Clock residual seeds, nonzero error-bound event ordering, generated code and solver-clock events remain open.
- Host HP/planner executes in normal mode with analytic intra-macro physical segments; no calibrated hydraulics, stratification or cycling losses.
- Independent algorithms and artifact checks in same agent, not independent personnel; synthetic checks separate.
- Stateflow license and saved-chart execution observed; empty ver(Stateflow) does not establish a standalone product version.
- No new primary-source equation/value/signoff; full primary signoffs remain 0/31.
- Inherited Stateflow formal-argument shadow warnings remain in timestamped logs.

Next actionable task: Audit saved-v40 clock residual seeds, nonzero accumulated error bounds and event ordering near dwell/capacity/cutoff boundaries against independent interval or high-precision timing. Use focused fresh simulations and document any defect before broadening acceptance. Then resume primary-source equipment/parameter traceability; preserve all v38-v40 evidence.
