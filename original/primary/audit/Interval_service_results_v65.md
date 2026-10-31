# Executed six-mode interval-service Stateflow checkpoint v65

UTC 2026-10-11T21:28:46.143877+00:00. New saved `DCHR_Interval_Dispatch_Stateflow_v65.slx` executes
all six modes in the SAME chart, including each retained v64 restart chain and
subsequent direct heat, discharge, bounded boiler, unmet demand, IDLE and charge.
The scalar-service interface blocker is resolved for this conservative sampled
policy: use lower inventory for service and upper inventory for capacity;
retain the entire inventory, cumulative ports and age hulls. No midpoint reset.

MATLAB 194 PASS / 0 FAIL; 12 actual runs /
56 protocol ticks / 36 service intervals;
10 specific runtime fault rejections, two valid samples before
delayed rejection; 20 verified-v30 comparisons.
Independent QA 4141 PASS / 0 FAIL and
8 separate synthetic corruptions detected.
Exact-binary 120/160-digit original-trajectory and whole-inventory-box solutions,
piecewise source-energy integrals, finite water/source capacities, HP latch/dwell,
first law, auxiliary exclusion, service bounds and artifact hashes all checked.
Unit discharge efficiency/zero loss and near-cutoff no-credit fixtures execute.

Immutable reopened original MAT/binary exports, numeric CSV, MATLAB/Python logs,
receipts and source snapshots: `results/interval_dispatch_v65_20261011T212742_987732Z`.
All v57-v64 models/status/stageboards and earlier MATLAB sources are unchanged.
Legacy dispatch acceptance remains v57. V65 is a scoped additional sampled model;
general repeated exact-event coupling remains OPEN. No new primary-source or
physical-validation claims.

Development scaffold recovery is recorded in
`results/v65_scaffold_recovery_20261011T211923092Z`.
Original builder was restored from the earlier saved snapshot; unused draft
generator stopped before changing the existing kernel. Startup/configuration,
absolute-horizon subtraction, coverage fixtures and stale reviewer-manifest
failures remain in the timestamped development results. Final execution uses
the saved model bound to a fresh sealed source manifest.

Limitations:
- Scoped conservative sampled dispatch. Legacy accepted v57 remains preserved; general repeated exact-event replacement is OPEN.
- One retained v64 analytic capacity-OFF/restart prefix; subsequent service uses held-power sampled decisions and conservative capacity/cutoff budgets.
- Common hot-water return at tank temperature, fixed water/refrigerant approaches and cooling factor are engineering assumptions without equipment calibration.
- Source/compressor energies are enclosures from 128 outward rectangles; service is conservative, may leave capacity unused, and is not optimized.
- Authoritative held dt and cumulative physical-clock enclosure differ from solver protocol ticks; no earliest-event thermal firing is claimed.
- Inherited exact equivalent-limiter host certificate trust boundary and |lambda*duration|<=1 outward arithmetic domain remain.
- MATLAB normal-mode Stateflow chart executed and license observed; empty ver(stateflow) retained; standalone generated code not accepted.
- Same-agent independent Fraction and 120/160-digit algorithms, not independent personnel. Original MAT reopened/exported by MATLAB; independent Python HDF5 parser unavailable.
- Synthetic fixtures only; no new primary article text, equipment calibration, article replication or measured physical validation.
- Startup, compile, fixture, cumulative-clock and stale reviewer-manifest failures are preserved in timestamped development folders.

Next actionable task: Test and implement repeated capacity/cutoff/HP restart chains for the new v65 interval-service policy. Derive explicit sampled-vs-earliest-event comparison using identical exact-binary inputs, demand timing and finite backup limits; retain correlated inventory/ports/clocks and reject unresolved event ordering. Extend the SAME chart only with justified guards, then independently check original-MAT bounds and energy/service consequences. Preserve v57-v65; physical calibration and primary evidence remain OPEN.
