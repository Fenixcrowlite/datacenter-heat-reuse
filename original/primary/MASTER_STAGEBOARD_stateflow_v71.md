# Scoped executed earliest-event segment acceptance v71

UTC 2026-10-12T03:04:12.782319+00:00. Saved `matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v71.slx` actually executes all six modes,
50 earliest events and eleven stop/restarts in one physical held interval.
MATLAB 2385/0; independent 31346/0;
closure 1309/0; eight runtime rejections and eight reviewer
mutations detected. 396 held intervals, 446 positive segments,
21 v30 comparisons; matched dt=0.25/0.5/1 invariance passes.

Evidence `results/earliest_dispatch_v71_20261012T030016_337397Z` and audit/Earliest_dispatch_results_v71.md are authoritative.
Root hulls, symbolic threshold contacts, forcing/port offsets and OFF age
survive each event. Candidate forcing is recomputed after cutoff/stop/restart.
No root midpoint is consumed; unresolved event and boundary order rejects.
Legacy models and evidence preserved. Scope is macro analytic event segments
inside Stateflow, not solver-clock event firing, annual v71 or calibrated
physical validation. Same-agent closed-form QA; full primary signoffs 0/31.

Next actionable task: Audit saved-v71 earliest-segment numerical admissibility and conservation under long repeated service, small restart bands, finite source/water limiter ties, external-disable ON dwell and segment-budget exhaustion. Execute original-MAT counterexamples or scoped acceptance with closed-form QA; preserve v57-v71. Then adapt a held-boundary annual input/reporting interface for v71 before any annual earliest-event claim. Primary calibration and measured validation remain OPEN.
