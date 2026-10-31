# v39 fresh saved-Stateflow HP numerical-domain defect

UTC 2026-10-10T12:36:56.411250+00:00. **OPEN defect; no corrected-controller acceptance.**
Saved model release remains 0.38, SHA256 `fe60aaee835973195ccb94b323f516e7c1a6f413f5016f9b9f4d319251d297b2`. Prior acceptance
is preserved within its tested scope; this audit supplies new counterexamples.

Actual MATLAB batches exit zero. Execution harness 122/122 PASS:
22 completed scenarios, 45 intervals,
45 positive segments and all six required modes;
78 component probes. Separate read-only MAT export binds
the persisted SimulationOutputs and component MAT to the JSON traces.

Independent evidence QA 4040/4040 PASS; synthetic oracle checks
3/3 PASS, counted separately. Analytic implementation comparisons:
**202 PASS / 234 FAIL**. These failures
are neither discarded nor counted as successful controller tests. The evidence
gate passes because independently predicted defects are actually reproduced.
2747 prior sealed entries retain hashes/sizes.
Max independent segment balance residual: 7.7715611723760958e-16 MWh.

| Fixture | Analytic HP output MW | Actual output MW | Actual unmet MW | Actual mode |
|---|---:|---:|---:|---:|
| wide_request_40 | 9.70127681891e-12 | 9.70127681891e-12 | 0 | 2 |
| tight_request_40 | 7.27595761418e-12 | 7.27595761418e-12 | 0 | 1 |
| wide_request_60 | 9.25185853854e-18 | 9.25185798709e-18 | 0 | 2 |
| tight_request_60 | 6.93889390391e-18 | 6.93889390391e-18 | 0 | 1 |
| wide_request_80 | 8.82325986723e-24 | 7.44462551298e-24 | 0 | 2 |
| tight_request_80 | 6.61744490042e-24 | 6.61744490042e-24 | 0 | 1 |
| wide_request_90 | 8.61646471409e-27 | 0 | 6.46234853557e-27 | 5 |
| tight_request_90 | 6.46234853557e-27 | 6.46234853557e-27 | 0 | 1 |
| wide_request_120 | 8.02470810161e-36 | 0 | 6.01853107621e-36 | 5 |
| tight_request_120 | 6.01853107621e-36 | 6.01853107621e-36 | 0 | 1 |

Mode 1 is HEAT_RECOVERY, 2 STORAGE_CHARGE, 5 UNMET_DEMAND. With COP=4,
source S=8*2^-90 MW and a 3 MW charging request, the analytic maximum is
4S/3 while the actual model returns zero and reports all demand unmet.
Disabling charging with the same source and demand gives feasible Q=S and
serves all demand. This is request-dependent numerical loss of service, not
a first-law violation: energy conservation can pass for a falsely OFF plant.
Positive-penalty and capacities 8/1e-100/1e100 MW are also component stress
fixtures. The report ledger retains every input, expected and actual result.

Derivation: `audit/HP_dynamic_range_derivation_v39.md`. No paper formula,
experimental value or calibrated equipment parameter is claimed. The oracle
uses exact-input Decimal stable quadratic roots, distinct from production
bisection, plus Decimal TES ODEs and the inherited independent six-mode reference.

## Failures retained

An earlier unfinished batch executed plant fixtures then failed because the
heterogeneous hp_probes JSON decodes to a MATLAB cell array. Its MATs, logs and
receipt remain. The harness now normalizes structs/cells; fresh execution uses
a new directory and a new source snapshot. This run's sandbox MATLAB startup
failed before simulation; authorized local execution succeeds. Stateflow formal
argument shadow warnings remain visible. Reviewer/packaging failures, if any,
are retained alongside the successful reports without replacing numeric traces.
The first v39 reviewer failed two legacy hash checks: it treated the intentionally
mutable progress ledger and an originally open v22 finalizer log as immutable.
The corrected v22 manifest explicitly supersedes that seal and excludes these
files. The reviewer now honors those declarations, records both exclusions,
and still verifies every immutable model/numeric/source artifact. The failed
QA report, log and exact reviewer source snapshot remain preserved.

## Limitations and next action

- Documented numerical implementation defect, no new SLX or corrected controller acceptance.
- Extreme source/output ratios are numerical stress fixtures, not plausible equipment sizes or measured data.
- Execution/invariant and defect-evidence QA pass; explicit analytic implementation comparisons FAIL and remain open.
- Exact binary64 cutoff fixture is observed but excluded from defect counts; full near-cutoff classification remains unproved.
- Clock residual seeds, nonzero error-bound event ordering, code generation and solver-clock events remain untested here.
- Normal-mode host HP/planner with analytic intra-macro segments; no calibrated hydraulics, stratification or cycling losses.
- Independent algorithms/artifact QA in the same agent, not independent personnel; synthetic checks counted separately.
- Stateflow license and saved-chart execution observed; no standalone Stateflow version inferred from empty ver lookup.
- No new primary article equation, parameter or literature signoff; full signoffs 0/31, no article replication or physical validation.

Next actionable task: Implement additive Stateflow v40 with a source-relative bracket or stable scaled HP root, explicit unsupported-resolution rejection, and source-limited request invariance. Execute v39 dynamic-range/cutoff counterexamples plus all six modes and prior v38 representative references; independently verify analytic maximal output, nonzero electricity, SOC/port limits and first-law closure. Preserve v38 and all v39 evidence. Do not broaden clock seed/bound/event-order acceptance or claim equipment calibration; those audits and primary parameter traceability remain open.
