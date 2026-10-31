# Executed numerical-admissibility repair v73r2

UTC 2026-10-12T07:44:02.667485+00:00. Saved `matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v73r2.slx` was built and actually simulated.
All six final chart modes execute. The original v72 passive, inclusive ON-dwell,
source-limiter and correlated-work witnesses pass in this tested scope.

MATLAB **2804 PASS / 0 FAIL**; independent original-MAT
closed-form QA **112144 PASS / 0 FAIL**;
10 separately counted reviewer corruptions detected.
58 probes, 50 saved accepted/prefix runs,
1226 completed held intervals, 1316 positive segments,
90 interior events, 34 exact-singleton v30 comparisons.
11 actual runtime refusals are the expected domain/early-disable/
collision/boundary/resource controls, rather than acceptance failures.

The positive passive product and monotone affine corners repair the 91/23-hour
wrapping witnesses. Full 256-hour lambda=.2/h, 80-hour lambda=1/h and 256-hour
lambda=.01/h controls execute. The 208-hour repeated schedule executes.
Exact .25h and compensated .5h ON-dwell equality accept; true early disable,
including a displayed-but-inexact 1h binary sum, rejects. Source-limited,
rounded water/source tie, below/above tie and finite-water controls pass.
The 2^-42 K band executes with positive independently checked compressor work.
Matched dt=.25/.5/1 schedules retain independently equal physical trajectories.

The first saved v73 model is preserved. Its initial suite yielded 2759 passing
checks and one acceptance failure: after repairing positive work, the narrow
band next refused an unresolved passive root boundary. Additive v73r2 retains
the exact STOP-to-RESTART manifold and cancels the common heat capacity in
the log1p root equation. It records 34 macro calls using that symbolic
certificate. No root midpoint, capacity relaxation or energy tolerance was used.

Evidence `results/earliest_repair_v73r2_20261012T073823_950801Z` contains timestamped MATLAB logs/exit receipts, diagnostics,
original/reopened MAT, little-endian binary exports, numeric closed trajectories,
source/model snapshots and prior preservation hashes. Independent numeric CSV:
`closed_event_traces_v73_20261012T074352_249993Z.csv`. Derivation: `audit/Earliest_dispatch_derivation_v73.md`.
All fixture values are synthetic model units, not measured or paper data.

Development evidence is retained in the earlier v73 folders, including the
pre-existing startup/JSON-shape failures, this session's restricted MATLAB
startup refusal and first generated-v73 failed acceptance suite. An unexecuted
alternative scaffold refused to overwrite the existing v73 builder and was
archived under `results/v73_alternative_draft_*`; it is not production evidence.
No failed run is counted as acceptance.

Limitations:

- Scoped synthetic normal-mode implementation acceptance only; analytic event segments execute inside macro Stateflow protocol calls, not at solver-clock thermal events. No generated-code acceptance.
- Public lambda*heldDt<=1 and sixteen-segment limits remain. Generic unresolved boundary/root/dwell/collision decisions still reject. Symbolic passive contact applies only to retained STOP, B=0, lambda>0 and the declared log1p domain.
- Compensated ON-age certificate is optional and invalidated by uncertain event segments. Source limiting is conservative with eight ulps of allocation room. Arbitrary-scale, subnormal, overflow and arbitrary-policy acceptance are untested.
- Same-agent algorithmic independence using exact binary Fraction and 120/160-digit closed exp/log/source equations, not independent personnel. Original MAT reopening/export uses MATLAB; no independent HDF5 reader.
- Original v72 numerical witnesses repaired in the executed scope. This does not establish equipment calibration, measured performance, primary article replication or a full annual earliest-event simulation. Full primary signoffs remain 0/31.

Next actionable task: Develop an additive held-boundary input/reporting adapter for the saved v73r2 earliest-event model. Begin with a bounded representative seasonal schedule and source/demand/enable changes, preserve held physical timestamps and uncertainty hulls, explicitly surface collision/span/segment/clock refusals, and independently audit service/source/work/TES/backup/unmet aggregation from original MAT. Compare identical schedules with verified v57/v66 and equal delivered-service reporting before any full annual claim. Primary calibration, article replication and measured validation remain OPEN.
Stop after this coherent executed deliverable and handoff.
