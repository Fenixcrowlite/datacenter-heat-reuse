# Saved-v40 clock uncertainty results — checkpoint v41

2026-10-10T13:00:37.509896+00:00. **DEFECT_CONFIRMED_OPEN**. No new SLX or corrected-model acceptance.

Fresh saved model release 0.40 executes 27/29 scenarios,
33 intervals and 47 positive segments. Two deliberate
out-of-budget clock seeds reject at runtime. All six thermal modes are now executed,
including dedicated HP-only and BACKUP fixtures. MATLAB harness 56/56 PASS.
Four successful batches execute the broad fixtures and targeted BACKUP supplement,
then separately re-export each set of saved MAT traces. Supplement: results/stateflow_clock_v41_20261010T125848772Z.
Independent actual evidence checks 1359 PASS / 0 FAIL;
separate synthetic reviewer checks 4 PASS / 0 FAIL.
These counts validate defect evidence, not a corrected controller.

The persisted clock represents age in [hi+lo-bound,hi+lo+bound]. The saved
planner, supervisor guard and runtime guard omit bound in their minimum-dwell
decision. **Ten transitions have lower age below the dwell threshold while
upper age reaches it.** No certainly premature physical transition is proved.
The guarantee is unresolved for those valid seeds, so broadening acceptance
is blocked until an uncertainty-aware policy is implemented and tested.

| Seed (both ON and OFF) | Transition offset, hours | Lower-age shortfall, hours |
|---|---:|---:|
| hi=1, lo=0, bound=1e-9 | 0 | 1e-9 |
| hi=1-5e-10, lo=0, bound=1e-9 | 5.000000413701855e-10 | 1e-9 |
| hi=1+5e-10, lo=0, bound=1e-9 | 0 | 4.999999586298146e-10 |
| hi=1-2e-9, lo=0, bound=1e-9 | 2.0000000544584395e-9 | 1e-9 |
| hi=1, lo=0, bound=2^-80 | 0 | 8.271806125530277e-25 |

All seeds use minimum dwell=1 hour. Shortfalls are exact-input interval
properties, not measured errors. Positive/negative zero-bound residuals,
zero-bound threshold and confidently late controls pass. The certainly early
bound control waits to nominal equality but still ignores the remaining
uncertainty. Decimal compensated-add enclosures, TES ODE, bounds and first laws
pass; maximum independent system residual 7.2164496600635175e-16 MWh.

Zero-loss ties at dwell=1 hour and adjacent doubles are executed. At cutoff,
the earlier dwell event precedes the cutoff; exact tie selects cutoff; later
dwell retains a tiny additional OFF segment. At capacity, later ON dwell has
the documented unavailable-HP safety override. These are scoped resolution
observations, not a proof over all real input ordering. The independent
six-mode baseline comparison passes.

The first audit completed but lacked BACKUP; its failed coverage report
is preserved at results/stateflow_clock_v41_20261010T125341508Z. Its initial
reviewer assumed all cutoff fixtures would contain a cutoff event, which was
wrong for an earlier dwell event; the aborted source/log are retained. Added
HP-only control, the targeted BACKUP supplement and the corrected independent
earliest-event expectation pass. The supplement avoids another broad rerun.
Initial commentary misidentified the missing mode; saved traces and final
mode assertions establish the corrected coverage. No prior model evidence changes.

Evidence: results/stateflow_clock_v41_20261010T125630995Z; results/stateflow_clock_v41_20261010T125630995Z/independent_QA_v41_20261010T130008_944237Z.json; STATUS_stateflow_v41.json;
audit/Clock_uncertainty_derivation_v41.md; timestamped logs/receipts.

Limitations:
- Audit evidence QA passes; uncertainty-aware controller acceptance FAILS for ten interval-unresolved transitions.
- No certainly premature physical transition is proved: admissible error sign/history of stress seeds is unknown.
- The 1e-9-hour seeds and 2^-80-hour seed are numerical fixtures, not measured clocks/equipment or demonstrated long-run histories.
- No corrected model is generated; model release remains 0.40 and its earlier acceptance stays scoped.
- Near-tie fixtures are assessed within existing energy/time resolution; exhaustive exact real-input ordering remains open.
- Normal-mode host planner executes analytic intra-macro segments; generated code/solver-clock event execution untested.
- No measured physical validation/article replication or new primary-text signoff; research remains 0/31 full signoffs.
- Independent algorithms in same agent, not independent personnel. Separate synthetic reviewer checks are not simulations.
- Inherited formal-argument shadow warnings and failed sandbox startup are retained in timestamped logs.
- Broad fixtures missed BACKUP; initial commentary misidentified missing mode as HEAT_RECOVERY. Targeted BACKUP supplement closes coverage. Initial reviewer assumed physical-cutoff precedence and aborted; failed attempts preserved.

Next actionable task: Implement additive Stateflow v42 uncertainty-aware dwell decisions in planner, saved supervisor and runtime gate: require physical-age lower endpoint hi+lo-bound >= minimum dwell using cancellation-safe comparisons; schedule a conservative wait with certified post-add enclosure or explicitly reject unresolvable progress. Retain ON-dwell safety overrides and all v41 seeds/ties, then execute new SLX with independent interval timing, six-mode/reference, actual fault and saved-MAT QA. Preserve v40/v41 evidence. Then resume primary equipment traceability.
