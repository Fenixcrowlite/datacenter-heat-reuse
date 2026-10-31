# Executed Stateflow numerical-span repair v68

UTC 2026-10-11T21:59:51.851975+00:00. Actual new saved `DCHR_Span_Repair_Stateflow_v68.slx`
executes all six modes and the repaired event-root observer in one chart.
It remains a sampled service controller; earliest-event switching is OPEN.

MATLAB **1435 PASS / 0 FAIL**;
independent QA **36986 PASS / 0 FAIL**;
23 runs / 432 protocol ticks; 12 actual runtime
fault rejections; 396 executed v30 reference comparisons;
549 compiled observations / 14 host root probes.
All six deliberate reviewer corruptions were detected.

The saved v67r2 model rejects exact-binary lambda=1/8, duration=8
at the private outward-span guard despite the nominal product being exactly 1.
A delayed actual witness completes two valid ticks before the same rejection.
The host root function reproduces that rejection; adjacent values below 8 are
passing controls. The new saved model executes all four new boundary/delayed
witnesses, preserving inventory, port and physical-clock enclosures.

Repair: use a private outward evaluation domain |x|<=2 and a common proved
degree-24 Taylor remainder 8*2^25/26! for phi1 and phi2. The public root
predicate stays unchanged. The dispatch kernel differs only in its function
name, private-span guard and remainder. No argument clipping or event midpoint
is introduced. Independent integral-form proof and exact rational polynomial
checks cover the complete claimed private domain; exp/log corner QA reviews
actual original-MAT root/energy/source/work/clock traces.

Evidence: `results/span_repair_v68_release_20261011T215822_761796Z`. Timestamped MATLAB log and observed exit 0,
original/reopened MAT, binary exports, numeric CSV, immutable QA JSON,
execution source snapshot, corrected reviewer/proof snapshot and preservation
hashes all pass. Stateflow license observation and actual chart execution are
recorded; an empty ver('stateflow') response is not presented as a version.

Retained development:
- `results/span_repair_v68_20261011T215413_685622Z`: sandbox startup failure;
  MATLAB 1432/3 due to wrong near-boundary expectations and appended fault base.
- `results/span_repair_v68_final_20261011T215609_349756Z`: MATLAB 1434/1 due to
  wrong delayed-prefix comparison; independent 36981/2 correctly rejects the
  failed assertion and nonzero batch receipt, with all six mutations detected.
- The first sealed proof/reviewer draft is preserved. Revised proof uses the
  valid conservative geometric e-tail ratio 1/5, and QA matches actual chart
  stack reporting and already-reached delayed-restart classification.
- No saved v68 model or production kernel changed after the first build.

Limitations:

- Numerical-span repair and executed root observer only; roots do not control service or reset inventory. Earliest-event integration remains OPEN.
- Public root-domain predicate is the unchanged represented lambda*horizon<=1. The private outward evaluation span must be <=2; its remainder is widened with a proved bound.
- More conservative tail padding can widen enclosures and classify additional near-contacts as unresolved; no tolerance selects an event side.
- Plant schema remains 66 with unchanged conservative sampled allocation and finite-water/port/clock guards. Thermal thresholds and approach parameters remain engineering assumptions.
- Normal-mode Stateflow execution and conditional binary64 interval arithmetic; generated-code/subnormal rounding and calibrated hardware behavior are not accepted.
- Same-agent independent rational/160-digit closed exp/log QA and reviewer mutations; not independent personnel or measured validation.
- No new primary source text, equipment calibration, article replication or measured physical validation; full source signoffs remain 0/31.
- Development and first final batches failed due to harness expectations/case lookup. Original logs, MAT reports and reviewer failures remain preserved. Corrected QA/proof revision has a separate source seal.

Next actionable task: Implement a correlated event-segment record for one repeated earliest-event cycle in an additive SAME six-mode chart. Use the repaired v68 certifier and retain threshold identity, root-time hull, inventory, source/work/loss/service offsets and OFF age across the split without midpoint substitution. Certify dwell and strict ordering against held boundaries; reject unresolved collisions. Compare original-MAT service and source/work enclosures with an independent event trajectory, including the v66 stop witness, repeated dt=0.25/0.5/1 schedules and the exact lambda*duration=1 boundary. Preserve v57-v68. Primary calibration and measured validation remain OPEN.
