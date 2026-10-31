# Charge regime and endpoint blocker checkpoint v56

UTC 2026-10-11T11:14:43.860859+00:00. Saved model remains **0.52**; no new SLX or coupled model acceptance.
This run resumed pre-existing unfinished v56 code and executed it in fresh immutable evidence.

The five charge limits (request, nameplate, hot flow, source, TES port) are derived
on both FLOOR and TANK branches: all ten affine regimes pass independent exact-input
coefficient, event-completeness/time, reachability and min-envelope RK4 checks.
146 cases: 137 accepted interiors and 9 expected domain/endpoint rejections.
Candidate event times are explicitly **nominal**, never production certificates.

MATLAB 727 PASS / 0 FAIL (694 main, 33 temporal).
Saved v52 actually executes 13 intervals / 14 positive segments / all six required
modes. Six fixtures compare with verified MATLAB v30; one actual negative-source fault
rejects. The seven-interval sequence has 6 macro mode transitions;
3 actual HP latch changes have separately checked reason/dwell authorization.
Flow/SOC/first-law, cutoff, exact state handoff and zero-duration identity pass.
This held-input acceptance does not establish continuously coupled behavior.

Independent equation/trace QA: 6695 PASS / 0 FAIL.
Separate provenance/binary/dwell gate: 650 PASS / 0 FAIL;
43148 original binary64 values in 85 records reopened from seven original
SimulationOutput MATs bind exactly to the reviewed JSON values. 7 separate synthetic
reviewer self-checks pass. Complete source/reviewer/exporter snapshots and observed
MATLAB batch receipts are required by the release gate. Same agent, separate algorithms.

## Concrete blocker

The FLOOR trajectory's nominal branch target is 5 MWh. Original binary inputs
C=0.2 MWh/K, Ta=20 C, charge/direct approaches=2 K and delivery=45 C yield the
exact endpoint branch gap **-5/3602879701896397 K**, not zero. Actual v56 replay at
the nominal endpoint rejects with `DCHR:v55:UnresolvedBranch`. This proves the
nominal event descriptor cannot yet advance through the kink using the strict
instantaneous gate. No production guard was weakened and no invalid coupled
controller was saved. Prior fixed-temperature v52 acceptance remains intact.

Derivation: `audit/Charge_regime_derivation_v56.md`.
Evidence: `results/charge_regimes_v56_20261011T111230_427402Z`.
Equation QA: `results/charge_regimes_v56_20261011T111230_427402Z/independent_QA_v56_20261011T111430_667933Z.json`.
Release QA: `results/charge_regimes_v56_20261011T111230_427402Z/release_QA_v56_20261011T111435_176759Z.json`.
Original model SHA256: `3d12602aeebcb80585ecfd16e13b0e9ea9cffe091348883b620923e468954e12`.

## Limits and handoff

- No new SLX or continuously coupled Stateflow acceptance. Actual saved v52 freshly executes six held-input fixtures and a seven-interval sequence; previously accepted v52 remains unchanged.
- v56 certifies a unique instantaneous minimum, but coefficients, candidate energies and event times are nominal binary64. Branch/limiter equality, propagated endpoint error and variable-power port integrals remain OPEN. Exact equality and unresolved minima reject.
- Actual nominal branch-endpoint replay rejects with DCHR:v55:UnresolvedBranch. The rounded kink energy 5 MWh differs from the exact binary-input kink; exact gap is -5/3602879701896397 K. This is a new-interface prerequisite blocker, not a defect in accepted v52 fixed-temperature scope.
- Charge-only event landscape has no direct-demand/discharge or HP dwell dynamics. Dwell checks and temporal traces in this checkpoint verify held-input saved v52, not a coupled v56 controller.
- Synthetic tank-return variable-flow topology, without calibrated UA, hydraulics, pumps/minimum-flow law or equipment map. No new literature/primary text retrieved; inherited full signoffs remain 0/31. No article replication or measured physical validation.
- Independent exact Fraction algebra, 80-digit Decimal equations, min-envelope RK4, original-MAT binary binding and separate reviewer mutations by the same agent; not independent personnel or a universal numerical-domain proof.
- Stateflow license, two charts and actual normal-mode execution observed; ver(Stateflow) empty, so no installed version claimed. Inherited host planner/64-slot/standalone deployment limits and shadow warnings remain.
- Pre-existing unfinished v56 files and earlier successful/failed evidence preserved. Their incomplete late-harness/reviewer snapshots are superseded by this fresh complete snapshot; prior results were not overwritten.

Next actionable task: Implement a bounded-error charge propagator and compressor/source energy integrals for all ten charge regimes. Resolve the exact branch/limiter equality endpoint with an explicit one-sided protocol; nominal roots and log1p event times are diagnostics, not controller certificates. Then integrate an additive coupled Stateflow model with demand/cutoff/restart/dwell, strict padding/handoff, six modes, faults, verified-reference comparison and independent original-MAT binary/equation QA. Preserve saved v52 and v53-v56 evidence; do not repeat unchanged annual matrices. Primary equipment calibration remains OPEN.
