# Saved-v71 numerical admissibility defects v72

UTC 2026-10-12T03:15:54.936054+00:00. The preserved saved `matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v71.slx` was freshly executed.
Four numerical rejection defects are **CONFIRMED OPEN**. No new SLX or repaired
controller acceptance is claimed; v71's prior acceptance stays scoped.

MATLAB execution/monitor checks **1334 PASS / 0 FAIL**;
independent original-MAT closed-form QA **45766 PASS / 0 FAIL**;
eight separate reviewer corruption controls detected.
These counts mean the audit reproduced and verified its evidence; they do not
mean the controller is repaired. 25 probe scenarios:
16 accepted and 9 runtime rejections.
20 accepted runs including separately executed valid prefixes,
596 completed held intervals, 645 positive segments, 49 interior
events, all six actual final chart modes and 20 singleton v30 comparisons.

| Witness | Actual saved-model outcome | Independent evidence |
|---|---|---|
| Passive HP service, lambda=0.2/h | TES bounds refusal at hour 91 | E=3.74077583572529e-8 remains positive; 90-hour actual prefix retained |
| Passive HP service, lambda=1/h | TES bounds refusal at hour 23 | E=3.07856388951057e-10 remains positive; 22-hour actual prefix retained |
| External disable at exact ON dwell | Refuses at 0.25h | Two exact 0.125h holds meet 0.25h; retained lower-age endpoint falls below equality |
| Source-limited / rounded water tie / below tie | Three finite-source guard refusals | Exact selected host-replay source rates remain below capacity; widened upper boxes fail comparison |
| Restart band 2^-42 K | Nonnegative-energy guard refusal | Exact work=1.68616713036551e-14 is positive; interval subtraction lower endpoint is negative |
| Segment budget control | Explicit 16-segment refusal | Ideal exact policy needs 23 positive segments / 22 interior events; resource limit remains explicit |

All values are synthetic fixture model units, not measurements or article data.
Refusals are fail-closed. No physical capacity violation, negative exact work
or premature physical dwell transition is demonstrated. The concrete blocker
is loss of admissible operation from interval dependencies and equality proof.

Controls pass: 256-hour passive service at lambda=0.01/h; 208-hour repeated
service (four copies of the prior held demand schedule); early disable refuses
and later disable accepts; water-limited and above-tie controls accept; restart
bands 2^-10, 2^-20 and 2^-32 K accept. Every accepted actual trace and prefix
passes independent energy/source/work/service, event, clock and first-law
enclosure checks at 120/160-digit precision. Numeric closed trajectories are
saved in `closed_event_traces_v72_20261012T031418_598448Z.csv`. No broad annual acceptance is inferred.

Evidence: `results/earliest_admissibility_v72_20261012T030907_237961Z`. Original and reopened MAT, binary exports, numeric CSV,
timestamped MATLAB/Python logs, execution receipts, original/diagnostic/reviewer
source seals and prior model/checkpoint preservation hashes are retained.
The four instrumented diagnostic host runs capture operands before the same
source/work guards; they are labelled separately from actual Stateflow and QA.
The production model and source hashes are unchanged.

Development failures retained: initial restricted MATLAB startup with file
system inconsistency; first diagnostic replay incorrectly indexed a singleton
JSON input as a row. The corrected replay reshapes the input, creates a fresh
timestamped diagnostic function and succeeds; failed source/logs are preserved.
No failed run is counted as acceptance and no evidence was deleted.

Limitations:

- Four numerical admissibility defects remain OPEN in saved v71. This checkpoint reproduces defects and accepts no repaired or annual model.
- Accepted traces cover synthetic tested fixtures only. Actual rejected calls have runtime diagnostics; separately executed valid prefixes are saved. No complete trajectory is claimed for a rejected call.
- Diagnostic return/capture copies run on the MATLAB host only. They supply rejection-branch operands and are separately labelled, not saved-model execution or independent QA.
- Same-agent algorithmic QA with exact-binary Fraction and 120/160-digit closed exp/log/source equations; not independent personnel. MAT reopening/export uses MATLAB, not an independent HDF5 parser.
- Macro analytic physical segments execute within Stateflow protocol calls; no solver-clock thermal firing, generated-code or arbitrary-domain acceptance. Sixteen-segment resource limit remains explicit.
- Primary article replication, equipment calibration, measured validation and annual v71 remain untested. Full primary signoffs remain 0/31.

Next actionable task: Implement additive saved v73 numerical-admissibility repairs: stable monotone passive/affine inventory images; correlated ON-age equality certificate; source-capacity proof retaining selected limiter/denominator relation; correlated compressor-work/auxiliary nonnegativity proof. Execute all original v72 counterexamples and six modes, long passive/repeated schedules, exact/early/late disable, source/water ties, narrow bands, genuine collision and explicit segment-exhaustion controls. Preserve v57-v72. Accept only after saved-model execution and independent closed-form original-MAT QA; then develop the held-boundary annual adapter. Primary calibration and measured validation remain OPEN.
Stop after this coherent executed defect checkpoint and handoff.
