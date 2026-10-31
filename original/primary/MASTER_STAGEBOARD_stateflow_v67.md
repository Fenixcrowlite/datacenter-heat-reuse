# Executed held-trajectory event bracket observer v67

UTC 2026-10-11T21:49:14.264886+00:00. Saved `DCHR_Event_Brackets_Stateflow_v67r2.slx` executes the inherited
sampled dispatch and new root observer in one actual six-mode Stateflow chart.
All six states run. Plant memory schema remains 66; the observer appends root
and forcing certificates. Root observations do not switch the plant at events.

MATLAB **1372 PASS / 0 FAIL**; independent **36166
PASS / 0 FAIL**. 19 actual runs / 426 protocol ticks;
12 actual runtime rejections; 390 executed v30 comparisons;
545 active compiled root observations; 11
separate function probes; six reviewer corruptions detected.

Root observation counts: strict interior 61, no crossing in horizon 436,
unresolved near-boundary 2, already reached 46. Readiness ordering counts:
strictly before 106, no event 436, unresolved 2, strictly after 1.
These are observations along sampled trajectories, not event-policy transitions.

The original v66 stop witness has a certified potential stop bracket of roughly
0.124300824 hours. This quantifies the event that sampled whole-interval
withholding loses. Three repeated dt=0.25/0.5/1 schedules retain the full incoming
inventory box, cumulative ports, OFF/ON ages and physical clocks. Their existing
sampled service policy is independently checked again in the new chart.

Actual near-boundary and delayed strict probes reject `v67 unresolved event
ordering`. The delayed probe retains two identical valid samples before the
rejection. Independent closed-form exp/log QA checks every E/B/threshold corner,
strict endpoint witnesses, readiness and exact threshold expressions. Eleven
function probes additionally include broad incoming boxes, nonzero loss,
passive restart, exact boundary equality and OFF dwell ending before/at/after
the held boundary. The embedded certifier equals the host-probed source.

Evidence: `results/event_brackets_v67_final_20261011T214624_493950Z`. Original MAT reopened/exported by MATLAB, binary and numeric
traces, observed batch receipt/exit 0, timestamped MATLAB log, immutable QA JSON,
sealed sources and unchanged baseline hashes. Development evidence stays in
`results/event_brackets_v67_20261011T214411_093986Z`, including the original saved
v67 model and source snapshot. Corrected final saved model is revision v67r2.

Concrete integration blocker: v66 allocation consumes one held scalar duration;
a certified root is an interval correlated with threshold identity and every
energy/age offset. Passing a midpoint or independently resetting inventory would
erase this relationship. The observer resolves root existence/order for tested
paths, while correlated post-event service integration remains the next task.
No earliest-event switching acceptance is claimed.

Limitations:

- Executed root observer only. Sampled plant schema 66 and policy remain embedded unchanged; roots do not control service or reset inventory.
- Coupled repeated earliest-event switching OPEN: brackets alone cannot provide scalar service authority. Symbolic threshold, event-time, inventory, port and OFF-age dependencies must persist across both segments.
- Strict unresolved-order guards are demonstrated in near-boundary and delayed fixtures. Inactive or no-crossing lanes do not establish general event-policy acceptance.
- Root solver requires a certified strict derivative sign and lambda*horizon<=1. Unsupported monotonicity rejects; no standalone generated-code/subnormal rounding guarantee accepted.
- Candidate lanes are alternative potential full held-power paths, not simultaneous executed ports or an optimized control policy. Earliest-event source/compressor comparison remains open.
- Exact root at held boundary is a standalone function probe; actual compiled near-boundary candidate uses conservative water-limited forcing and has a small binary gap. No exact compiled tie is fabricated.
- Same-agent independent Fraction/160-digit all-corner closed exp/log QA; not independent personnel or measured physical validation.
- Inherited v66 finite-water/correlated prefix/endpoint/policy limits remain. Fixed thermal approaches and cooling-factor boundary are engineering assumptions.
- No new primary article text, calibrated equipment, article replication or physical validation. Full source signoffs remain 0/31.
- Development model v67 preserved separately. First batch 1368 pass / 3 wrong expected-mode labels fail; initial sandbox startup and shadow warnings retained. Revised saved model is v67r2.

Next actionable task: Integrate one certified repeated earliest-event cycle into an additive SAME six-mode chart using the v67 strict root witnesses. Carry threshold identity plus correlated root-time, inventory, source/work/loss/service offsets and OFF-age across event segments; never substitute a midpoint. Certify OFF dwell and ordering against held demand/source boundaries; reject unresolved collisions. Compare actual original-MAT service and source/work enclosures with an independent event trajectory. Preserve v57-v67r2, and regress the near-boundary/delayed witnesses plus dt=0.25/0.5/1 repeated schedules. Primary calibration and measured validation remain OPEN.
