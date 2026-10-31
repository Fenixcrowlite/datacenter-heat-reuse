# Executed earliest-event Stateflow segments v71

UTC 2026-10-12T03:04:12.782319+00:00. New saved model: `matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v71.slx`.
Actual normal-mode MATLAB simulation executes repeated analytic stop/cutoff/
restart segments in the same six-mode chart. This is scoped executable
implementation acceptance, with the limitations below.

MATLAB **2385 PASS / 0 FAIL**; independent exact-binary
closed-form QA **31346 PASS / 0 FAIL**; separate
closure/preservation QA **1309 PASS / 0 FAIL**.
29 runs / 396 held intervals / 446 positive segments /
50 interior events / all six actual final chart modes;
8 actual runtime rejections, 21 singleton v30
comparisons, eight detected reviewer corruptions.

One macro interval executes eleven stop/restart events. The dt=0.25/0.5/1
52-hour schedules each execute eight interior events. Independent physical
service, source/work, standing losses and final inventory agree between those
partitions within the labelled 1e-90 high-precision comparison budget. Actual
trace enclosure checks use no tolerance. Cutoff-before-restart recomputes
passive forcing and elapsed OFF age; forced-discharge restart, inactive
contacts/delayed controls, future charge sink, zero/positive loss and exact
lambda*duration=1 witnesses execute. Genuine enabled event collisions,
held-boundary contacts and unresolved derivative signs reject.

Comparison uses exact matched inputs/equipment and preserved v70 original-MAT
binary exports. Numeric values are synthetic project fixture energy units,
not paper data or measured performance. The stop witness has no heat demand;
its meaningful difference is positive charging before its actual stop rather
than sampled whole-interval withholding. Earlier sampled controller outcomes
remain valid under their own policy.

| Synthetic schedule | Earliest events | Earliest served | Sampled served hull | Earliest unmet | Sampled unmet hull |
|---|---:|---:|---|---:|---|
| stop_overshoot_repair | 1 | 0.000000000 | [0.000000000, 0.000000000] | 0.000000000 | [0.000000000, 0.000000000] |
| repeated_0p25 | 8 | 26.933679986 | [26.177181244, 26.177181244] | 21.066320014 | [21.822818756, 21.822818756] |
| repeated_0p5 | 8 | 26.933679986 | [25.807207775, 25.807207775] | 21.066320014 | [22.192792225, 22.192792225] |
| repeated_1p0 | 8 | 26.933679986 | [25.916440576, 25.916440576] | 21.066320014 | [22.083559424, 22.083559424] |

Detailed heat/source/work and service enclosures are in
`handoff_QA_v71_20261012T030412_782337Z.json` and `closed_event_traces_v71_20261012T030144_674314Z.csv`. All original/reopened MAT,
little-endian binary/JSON traces, timestamped MATLAB/Python logs, exit receipts,
model/source/reviewer seals and prior-model/checkpoint hashes are retained in
`results/earliest_dispatch_v71_20261012T030016_337397Z`. The accepted model was built once at 02:57:47 execution and then loaded
unchanged for the successful run; subsequent edits corrected test expectations
and increased the explicit synthetic multi-cycle fixture's finite water limit.

Development failures preserved: workspace-restricted MATLAB startup at
02:56:09; non-scalar increment-array compile diagnostic in 02:56:09/02:57:13
folders; 02:57:47 full simulation with 2338 PASS / 4 FAIL (three old sampled-mode
expectations and one unreachable multi-cycle fixture); first independent QA
with no trajectory failures but failed acceptance/exit checks and two inactive
mutation controls. Preparation initially used a stale fault fixture identifier;
it failed before creating an evidence folder and was corrected. No failed
development run is counted as acceptance; none was deleted or overwritten.

Limitations:

- Analytic earliest physical segments execute within macro Stateflow protocol calls. Chart state is final positive segment mode; solver-clock thermal event firing is not claimed.
- Conditional normal-mode interval arithmetic, conservative lower-bound HP limiter and hull eligibility; lambda*heldDt<=1, sixteen segments per call, kind=1 only. Unresolved boundary/root/dwell/pair order rejects. No generated-code or arbitrary-domain acceptance.
- Root-time and symbolic threshold/manifold provenance plus port/clock/age offsets are retained; Cartesian evaluation conservatively widens correlations. No root midpoint consumed. Broad long-horizon numerical-resolution audit remains open.
- Same-agent algorithmic independence using exact-binary Fraction and 120/160-digit closed exp/log/source integrals, not independent personnel. Original MAT reopened/exported by MATLAB, not an independent HDF5 parser.
- Synthetic engineering fixtures and reduced fixed-approach equipment model. Primary calibration, article replication, measured validation and full primary signoffs remain OPEN (0/31).
- No annual v71 simulation or migration of annual adapters/report consumers is accepted. Legacy accepted v57/v66/v70 and earlier evidence are preserved.

Next actionable task: Audit saved-v71 earliest-segment numerical admissibility and conservation under long repeated service, small restart bands, finite source/water limiter ties, external-disable ON dwell and segment-budget exhaustion. Execute original-MAT counterexamples or scoped acceptance with closed-form QA; preserve v57-v71. Then adapt a held-boundary annual input/reporting interface for v71 before any annual earliest-event claim. Primary calibration and measured validation remain OPEN.
Stop after this coherent executable deliverable and handoff.
