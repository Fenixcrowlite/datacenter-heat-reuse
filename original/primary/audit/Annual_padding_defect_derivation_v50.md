# Zero-duration padding identity defect — v50

The planned nine one-coordinate annual sensitivities produced seven complete
actual saved-v42 annual runs and two actual runtime rejections. Failed variants
are restart49 MWh and minimum ON dwell0.5h. Both passed8760-row static preflight.
The harness records60 passed checks and2 failed execution checks; no complete
nine-case matrix or repaired controller is accepted.

Actual SimulationOutputs retain2896 and2415 valid-prefix samples respectively.
Reconstructing each first uncommitted interval from its exact previous MAT
inventory/clock reproduces the padding predicate failure. Two isolated
one-interval saved-SLX simulations also reject with the same runtime message.
Prefixes alone do not expose the rejected segment: the failing timestep is not
committed to the original trace. Isolated replay evidence and standalone
function witnesses are explicitly separate from retained prefix outputs.

At zero duration, the reduced physical identities require

    E1=E0; integral(power)dt=0; standing/conversion loss=0;
    residual=E0-E1=0.

This must hold exactly for numerical padding, because padding represents no
physical process. Padding inherits the terminal state of the last physical
segment and must not independently clip/reset that state.

The production planner's padding energy in both witnesses is the next binary
double above capacity50 MWh. The production allocation function computes the
zero-duration endpoint and then applies its unconditional capacity clip. Thus
E0=50+ulp(50), E1=50 and residual=ulp(50), although every heat power, standing
loss, conversion loss and delivered heat is zero. The runtime gate requires
both E1==E0 and zero residual and correctly refuses this inconsistent padding.
Its combined assertion message says "Zero-span segment has service." The
witnesses prove a padding identity/roundoff handoff error, not nonzero service.

Exact IEEE-754 evidence, decoded independently in Python:

    capacity/end: 4049000000000000
    padding start: 4049000000000001
    difference: 7.10542735760100185871124267578125e-15 MWh.

This is one ULP at capacity and well within the preceding physical-bound
roundoff allowance. CSV formatting rounds both energy values to50, so exact
binary witness fields and original MATs are essential; residual alone is still
visible in CSV. Python decodes the bits rather than calling MATLAB or trusting
a rounded text equality. No material physical-capacity violation or unserved
energy is attributed to this tiny discrepancy. It nevertheless prevents an
admissible annual policy from executing to completion.

The first independent physical-time review also produced152 dwell flags in the
completed OFF0.5h trajectory when summing15-digit CSV spans. Exact binary spans
and clocks reopened from original SimulationOutputs resolve all152 with
nonnegative lower-age dwell margins (minimum about1.0842e-19h). Maximum CSV
age discrepancy is about5.139e-16h. The final reviewer uses exact binary spans
for threshold proofs, binds each to its original CSV value, and retains the
failed review and a152-decision serialization-resolution artifact. No production
guard, physical criterion or dwell tolerance is changed. This is a reviewer
serialization defect, separate from the actual Stateflow padding blocker.

The confirmed scope is planner/allocation padding state disagreement. The
specific floating-point path that generates the overshoot before padding
requires a repair audit; it must not be assumed to occur only after one event
kind or one macro remainder. Preserved production planner, allocation,
collector and contract-gate code determine the corrective work.

Next repair: additive v51 model/builder and helpers with a shared canonical
physical end state before padding. Derive how capacity/cutoff clipping and
roundoff correction propagate through physical endpoint, next inventory and
all zero-duration slots. Keep zero-span identity and first-law checks strict;
do not solve this by discarding the assertion, crediting tiny padding losses,
or permitting nonphysical inventory changes. Ensure macro summary/memory
stays within capacity and no phantom clock/latch transition occurs. Retest both
exact isolated counterexamples, all nine fresh annual policies and the required
six-mode acceptance fixtures, with independent binary/ODE/dwell/port/report QA.
Preserve v42 and all v50 failed/control evidence. Prior v42/v49 acceptance is
unchanged within its tested policy scope. Broader thermal-interface studies
follow this concrete execution blocker.
