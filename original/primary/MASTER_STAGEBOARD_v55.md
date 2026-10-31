# Conservative coupled branch checkpoint v55

UTC 2026-10-11T06:51:25.104084+00:00. Instantaneous gate implementation and independent QA PASS.
Accepted model stays 0.52; no new SLX or coupled Stateflow acceptance.

MATLAB 466 PASS / 0 FAIL. 249 vectors:
199 resolved accepted, 50 unresolved
rejected, six invalid-domain rejections. All twelve retained v54 exact-branch
misclassifications are reproduced and safely rejected. The original witness has
exact gap -5/3602879701896397 K (-1.3877787807814457e-15 K).
No guard/tolerance was weakened. Exact equality deliberately rejects.

Independent exact rational interval/sign/limiter algebra, original-MAT binding,
80-digit held-input ODE/first-law/port/clock checks and preservation evidence:
4750 PASS / 0 FAIL. Five separately counted reviewer mutations detected.
Two actual normal-mode saved-v52 simulations execute two positive charging
segments (mode 2): source-limited and hot-flow-limited sampled controls. Exact
energy handoff and zero-span padding remain preserved. This is not continuous
coupling or fresh six-mode coupled acceptance.

Evidence: `results/branch_guard_v55_20261011T064903_468947Z`. Independent QA: `results/branch_guard_v55_20261011T064903_468947Z/independent_QA_v55_20261011T065027_511186Z.json`.
Derivation: `audit/Branch_guard_derivation_v55.md`.
Source/model snapshots, original SimulationOutputs/MAT reopens, binary inputs,
timestamped MATLAB/reviewer logs and startup-failure receipt retained.

Limitations:

- No new SLX or accepted coupled Stateflow controller. Accepted saved v52 unchanged; two fresh held-boundary charge controls execute only mode 2. Prior six-mode acceptance remains STATUS_stateflow_v52.json.
- The v55 wrapper conservatively rejects intervals including zero, including exact equality and some resolvable near-kink signs. It certifies exact binary instantaneous inputs under IEEE binary64 round-to-nearest/gradual-underflow assumptions; it is not a certified event endpoint or general active-limiter selector.
- Instantaneous source uniqueness is diagnostic only. General charge-side limiter regimes, direct/discharge coupled service, earliest events, propagated exponential endpoint-error enclosure and variable-power integrals remain unimplemented; new coupled model acceptance stays blocked by these prerequisites.
- Synthetic tank-return variable-flow engineering topology; no UA, hydraulics, minimum/standby-flow/pump law, calibrated equipment map, article replication or independent measured physical validation. No new literature or primary text was retrieved in this focused implementation run; inherited source signoffs remain 0/31.
- Independent QA means exact Fraction equations plus separately implemented 80-digit Decimal saved-trace checks by the same agent; not independent personnel, universal floating-point proof or continuous-coupling validation.
- Stateflow license, two actual charts and normal-mode execution observed. ver(Stateflow) is empty; no installed Stateflow version fabricated. Inherited shadow warnings and 64-slot host-planner/standalone deployment limits persist.
- Sandbox MATLAB startup failed with filesystem inconsistency; failure log retained. Authorized local batch passes. No production/model tolerance, saved controller or prior evidence was modified.

Next actionable task: Derive all charge-side request/nameplate/hot-flow/source limiter regimes and their earliest branch, limiter and capacity events. Use the v55 conservative instantaneous gate, explicitly resolve equality/event endpoints, and bound propagated endpoint energy error. Only then build an additive energy-linked condenser/COP/variable-port Stateflow release with demand, cutoff/restart/dwell memory, strict padding/handoff, six required modes, fault tests and independent equations/original-MAT QA. Preserve saved v52 and v53/v54/v55 controls; avoid unchanged annual matrices. Primary calibration remains OPEN.
