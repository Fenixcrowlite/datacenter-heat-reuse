# Saved-v75 temporal trace continuity and additive reporter v76

The saved model remains version 0.75. Reporting version 0.76 consumes its exact
schema; this work neither builds a new SLX nor changes thermal dispatch.

## Defect hypothesis and executed controls

The v75 reporting gate reconstructs energy totals and binds held operands, but
does not link every clock, latch, age and contact record to adjacent segments or
held intervals. A cumulative first-law enclosure alone cannot certify those
links. Fresh actual saved-model traces are the source of separate single-field
reporting controls. Mutated records are never described as physical simulation.
The results checkpoint records actual acceptance/rejection, not this hypothesis.

## Structural identities

Let an interval contain ordered segments with incoming TES hull E, HP latch b,
latch-age hull A, threshold tag g and elapsed hull t. Initial values come from
the canonical adapter; subsequent incoming values must equal the immediately
preceding endpoint records bit for bit. At a held boundary, inventory, latch,
age and contact survive; the local elapsed offset resets to [0,0].

For duration hull d, segment elapsed = outward(t + d). A boundary reason of
zero preserves b and A. Reason 1 changes OFF to ON; reasons 2/3 change ON to
OFF; these transitions alone reset A to [0,0]. The record before this boundary
transition must still retain the original incoming b and A.

The stop event (1) resets b to OFF and A to zero, with stop contact g=1.
The cutoff event (2) preserves b, advances A by d and records g=2.
The restart event (3) resets b to ON and A to zero; g=3 only for an actual
thermal contact, otherwise g=0 for readiness limited by OFF dwell. A non-event
segment advances A by d and records g=0. These statements describe the existing
v75 protocol, including its explicit contact/correlation semantics.

Every interior segment must end in an event. The final segment must have event
zero and duration outward([held_duration, held_duration] - t). This preserves
the exact symbolic held remainder, rather than assuming that the independent
elapsed hull endpoints equal the binary duration. The header endpoint E, b,
A and g must exactly match the last segment endpoint.

Physical clock start equals the preceding held interval clock endpoint, starting
at zero. Physical boundary equals outward(clock_start + held_duration); both
copies of this boundary in header columns 10:11 and 60:61 must match. Header
58:59 retains the original incoming physical clock. The existing v75 gate also
binds authoritative duration/source/enable operands and cumulative energy.

The production checker uses the saved kernel's deterministic outward binary64
operations, including zero-operand and scalar-cancellation identities. Exact
equality is appropriate for stored protocol copies; it is not a tighter thermal
accuracy tolerance. No existing controller tolerance is changed.

## Independent checks and scope

Python reads the binary64 exports of the reopened original MAT. Fraction
arithmetic independently checks exact-binary clock and age enclosure sums and
differences, temporal memory links, event/reset identities and all demonstrated
reporting controls. It does not call production MATLAB or reproduce the
production eps-based outward operator. The inherited closed exp/log reviewer
independently verifies full original trajectories and energy/report totals at
120 and 160 digits. Separate synthetic reviewer faults test both lanes.

This is same-agent algorithmic independence; it is not independent personnel or
an independent HDF5 reader. The MATLAB reopening and binary-export dependency is
explicit. Coordinated replacement of a complete internally consistent record
is outside this gate. Nonlinear trajectory validation remains required.
Synthetic bounded normal-mode schedules only; no annual, calibrated, primary
article replication, measured physical or generated-code acceptance follows.
