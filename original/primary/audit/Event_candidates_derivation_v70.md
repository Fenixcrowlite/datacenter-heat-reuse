# Mode-conditioned prospective event interface v70

This additive release repairs the v69 observer interface in the same six-mode
Stateflow chart. It preserves the v66 sampled dispatch/inventory/energy policy.
Candidates execute inside the chart but do not split a held interval or switch
at an event. This is executable interface acceptance, not earliest-event control
acceptance, measured validation, article replication or equipment calibration.

For an eligible prospective segment, E' = B - lambda E, with
B = etaC charge - discharge/etaD. The independent solution is
E(t) = B/lambda + (E0-B/lambda) exp(-lambda t), or E0+B t
for zero loss. A threshold root is
tG = -log((G-B/lambda)/(E0-B/lambda))/lambda, or (G-E0)/B.
Restart readiness is max(tG, max(0,minOFF-age)). All numerical input values
are exact represented binary64 engineering fixtures, not verified paper values.

Candidate allocation precedes sampled whole-horizon port withholding:

- Bound HP heat by nameplate, refrigerant source capacity and water capacity.
  Direct demand has first priority. Surplus can charge only with a charge sink,
  inventory certainly below stop, and an effective ON latch. HP initially OFF
  can turn ON at the segment start only with both certified OFF age and restart
  threshold. ON-to-OFF sink/source safety overrides and external-disable dwell
  match the sampled policy.
- Discharge only the residual demand, with no simultaneous charge, and only
  when incoming inventory is certainly above cutoff. A cutoff root is enabled
  only for this positive discharge. Charging stop is enabled only for positive
  charge. The allocation is prospective: energy limits are events rather than
  full-horizon sampled throttles. It must not be used for unsegmented service.
- An effective OFF latch with source and a future direct/charge sink enables
  restart. Use the same segment forcing, including TES discharge. A future
  charge sink remains relevant even if incoming inventory is above stop.
- Preserve E/age hulls, boundary, threshold identities, selected ports, B hull,
  eligibility flags and latch reason. Root records retain strict before/after
  witnesses from the inherited v68 certifier. No midpoint is consumed.
- Compare enabled readiness hulls only. Strict boundary/contact ambiguity or
  overlapping cutoff/restart readiness rejects. If cutoff precedes restart,
  the restart prediction is valid only for the pre-cutoff hypothetical forcing;
  a consumer must recompute after cutoff. Pair code 1=cutoff first,
  2=restart first, 3=unresolved, 0=no competing reached/interior events.
- An enabled path with unresolved derivative sign at its threshold retains an
  unresolved root record (status/order 2); strict mode rejects. Skip a root only
  when the complete derivative hull proves the threshold is unreachable in its
  required direction. This may conservatively reject a near-equilibrium path
  with no actual finite crossing. It makes no existence or order claim there.

The trace is 283 values: unchanged plant 1:205, then candidates 1:78.
Candidate 1:45 are three 15-field root records, 46:51 per-root B hulls,
52:54 enablement flags, 55:60 HP/direct/charge/discharge/B,
61:62 held duration, 63:66 initial/effective latch, potential charge and reason,
67 pair order, 68:73 stop/cut/restart hulls, 74:77 E/age, 78 interface schema 70.
Disabled roots are all zero. Enabled roots with certified non-crossing monotonicity need
not call the certifier; eligibility and threshold provenance remain recorded.

QA separately checks sampled first-law/SOC/service/source/work enclosures against
exact-binary Fraction and 160-digit closed exponential/logarithmic solutions;
candidate allocation, enablement and roots against independent equations and
all root-box corners; original MAT reopened/exported by MATLAB; saved SLX scripts;
baseline preservation; runtime faults; six modes; delayed witnesses; repeated
dt=0.25/0.5/1 schedules; the v68 represented lambda*duration=1 boundary.
Reviewer corruptions are separate self-checks. This is same-agent algorithmic
independence, not independent personnel; no independent MAT/HDF5 parser.

Limitations: normal-mode conditional interval arithmetic, engineering equipment
and conservative hull eligibility, no generated-code acceptance. Earliest-event
segments must carry correlated inventory/source/work/loss/service/clock offsets
and recompute forcing after each event before event-controller acceptance.
