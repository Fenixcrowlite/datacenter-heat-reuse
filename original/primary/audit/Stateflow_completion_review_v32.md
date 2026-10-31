# Completion review for Stateflow v32

The current run resumed the saved, unaccepted v32 model and its unfinished
acceptance harness after reading v31 and research v25 STATUS/stageboard records,
the frontier, acceptance criteria, progress ledger and relevant sources. The
model already had a successful build/smoke-test receipt from 2026-10-09. That
receipt did not establish acceptance. No model baseline is overwritten.

## Evidence and mathematical boundary

Inherited primary article evidence is the Cadau standing-loss term recorded in
`TES_standing_loss_primary_v28.md`; its stratified plant is not replicated.
`TES_segment_Stateflow_derivation_v32.md` derives the reduced held-power ODE,
analytic boundary segments, segment COP/electricity and finite-backup service.
All tested numerical parameters and dispatch decisions are engineering assumptions.
The independent Python oracle imports only independent v30/v31 Python references,
uses an analytic HP source-limit root and Decimal TES event bisection, and does
not import production MATLAB functions. Inherited RK4 equation checks test the
reduced ODE, not an independently calibrated physical plant.

On 2026-10-10 the primary MathWorks [For Iterator documentation](https://www.mathworks.com/help/simulink/slref/foriterator.html)
and [iterator execution documentation](https://www.mathworks.com/help/simulink/ug/iterate-subsystem-execution.html)
were reopened. The current online For Iterator page identifies R2026b; the actual
batch reports R2026a Update 5. The documented repeated execution occurs within
the current timestep. `ResetStates=held` and `IndexMode=One-based` are documented
defaults; saved XML omits these default-valued fields. Static QA accepts only
those defaults when the fields are absent, while the MATLAB harness checks the
actual loaded iterator's held setting. Physical event offsets are analytic trace
metadata, not Simulink solver-clock event activations.

## Defects exposed by the first complete run

The first full batch is preserved in
`results/stateflow_v32_20261010T022319311Z` and its timestamped logs/receipt.
It executes 65 scenarios, 242 macro intervals and all six positive-duration
modes, but reports 465 failed assertions and is not accepted.

1. Strict Decimal conversion of a floating loss-replacement port promotes
   approximately one ulp of power difference into a spurious near-zero capacity
   event. Subsequent roundoff near capacity can also choose a full-charge request
   rather than the hold request. Interval totals pass, but segment schedules
   disagree. The host planner and independent oracle now specify a capacity
   roundoff convention: recognize energy within 64 binary ulps of capacity after
   validating the input domain; recognize the initial capacity equilibrium when
   net charge differs from its standing-loss power by at most 64 ulps. This is
   consistent with the allocator's existing 64-ulp energy-roundoff bound. It is
   not a physical deadband, hysteresis or permission for material capacity
   crossings. The runtime ODE and first-law gates still verify every segment.
2. All eight allocator corruptions actually stop at time zero with execution
   diagnostics in the runtime gate. The harness falsely labels them rejected=false
   because it searches for the literal `Assertion`, while R2026a reports the
   custom assertion message and `assert(`. The corrected harness requires the
   runtime-gate path, assertion source, execution phase and exact failure time.
   Independent MAT export separately verifies the stop event and diagnostic.
3. The unfinished reviewer uses an unbound receipt check and expects a short
   chart name in XML. A separate completion reviewer preserves that source and
   binds the command to hashes of every specification file, checks complete
   ordered MAT case coverage and uses the saved hierarchical chart path.
   Saved label indentation and omitted documented defaults are normalized only
   for structural comparison. Failed static attempts and logs are preserved.

Acceptance requires a fresh successful MATLAB run and independent numeric,
saved-archive, MAT, fault, receipt and preservation QA. Synthetic evidence
corruptions remain separately labelled. Neither independent algorithm QA nor
this review is a separate human/agent signoff, article replication or measured
plant validation. Executed final counts belong to the timestamped reports.

## Scope and next work

The saved SLX depends on the versioned host HP planner in normal mode; it is
not a standalone generated-code model. There are at most two analytic segments
per macro sample. Capacity hold can become unavailable at low HP load and then
cool until the next sample. Hysteresis, cycling, dwell, hydraulics, stratification,
sensor/equipment faults, variable ambient and calibrated equipment are not
implemented. Delayed finite domain faults are tested; delayed NaN/Inf timing is
not claimed. A sample at StopTime still represents a complete following interval.

After successful completion, audit the capacity-hold fallback's timestep
dependence and derive a justified restart/hysteresis/dwell policy before changing
the controller. Preserve v24/v28/v30/v32 and finite-backup counterexamples.
