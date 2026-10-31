# Canonical positive-segment endpoint and padding identity — v51

Engineering derivation, with no new primary-source calibration claim.
For frozen parameters and held ports, dE/dt = P - lambda E,
P = etaC Qcharge - Qdischarge/etaD. Thus

    E(t) = E0 exp(-lambda t) + P phi(t)
    phi(t) = -expm1(-lambda t)/lambda, or t when lambda = 0
    Lstanding = E0(1-exp(-lambda t)) + P(t-phi(t)).

Use the small-x series for t-phi to avoid cancellation. Event times solve the
same equation. Capacity/cutoff are numerical boundary representatives, and a
bounded correction of at most 64 eps(max(1,capacity)) is applied only after
positive-duration integration. It is not a physical loss or a service port.
First-law residuals retain this roundoff rather than inventing heat credits.

The v42 planner used one endpoint arithmetic path and set analytic boundary
events directly to capacity/cutoff; allocation independently integrated and
clipped. It also extended the final span by a roundoff remainder using a second
advance from an already normalized event endpoint. The last remainder advance
could exceed capacity by one ULP, leaving padding with a different initial
state than the allocated physical endpoint. v50 exact MAT seeds reproduce it.
The new endpoint kernel is shared by host planning and embedded Stateflow
allocation. Final remainders recompute from the original segment start over the
complete final span. The planner classifies near-boundary initial inventory
without silently changing it. No segment-start normalization creates inventory.

For zero duration, E1=E0 exactly, all integrals/losses vanish and no latch/time
change is allowed. The kernel returns identity and rejects an out-of-domain
initial state. The strict zero-span gate is preserved; segment handoff now
requires exact energy equality. The macro inventory memory consumes this same
canonical physical endpoint through all padding slots.

Validation required before acceptance: original saved-v42 replays, exact seeded
v51 repairs, all six modes, reference comparisons, actual corruption rejections,
nine annual policies, exact binary endpoint/padding/clock evidence and independent
Decimal ODE/HP/port/report/dwell review. This is scoped numerical implementation
QA, not measured thermal validation, universal floating-point proof, independent
personnel review, or primary-article replication.
