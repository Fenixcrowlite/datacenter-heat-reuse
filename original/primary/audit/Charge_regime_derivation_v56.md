# Charge limiter dynamics and event landscape v56

This is an additive mathematical prerequisite to continuous coupled Stateflow.
The accepted saved model remains v52. No new SLX, coupled dispatch acceptance,
paper equation, equipment calibration or physical validation is claimed.
The topology and parameters are synthetic engineering assumptions inherited
from v54/v55; this run does not retrieve new primary article text.

Let E denote ambient-referenced tank energy [MWh], C thermal capacity [MWh/K],
T=Ta+E/C, d charge approach [K], F delivery plus direct approach [C],
Te evaporator saturation [C], dc condenser approach [K], a=f(Te+273.15) [K],
S available evaporator heat [MW], H maximum hot-side heat-capacity rate [MW/K].
All finite double inputs denote their exact binary values for independent QA.
The local Kelvin offset is the binary value of 273.15, as in v55.

The outlet is max(T+d,F). E_k=C(F-Ta-d) is the branch kink. On FLOOR (E<E_k),
L=F+dc-Te is constant; on TANK (E>E_k), L=Ta+d+dc-Te+E/C. Heating COP is
1+a/L. Heat output in this zero-demand, charge-only scope is the minimum of:

| Limit | FLOOR q(E) [MW] | TANK q(E) [MW] |
|---|---|---|
| Request | R | R |
| HP nameplate | Qmax | Qmax |
| Hot flow | H(F-Ta)-HE/C | Hd |
| Source | S(1+(F+dc-Te)/a) | S(1+(Ta+d+dc-Te)/a)+SE/(aC) |
| TES charge port | Qcharge | Qcharge |

The fifth limit is essential: an HP-only minimum is insufficient for a TES
charging regime. v55 certifies the branch; the new selector certifies a unique
active limit only if its interval upper endpoint is below every other lower
endpoint. Zero request, equal minima, unresolved kinks, initial capacity,
nonfinite derived coefficients and inadmissible policy values reject.
Exact equality is deliberately unresolved; no tolerance is used to select it.

For one active affine q=alpha E+beta, E'=eta q-lambda E=kE+B, with
k=eta alpha-lambda [1/h], B=eta beta [MW]. FLOOR hot-flow k is negative unless
H=lambda=0; FLOOR source and all constant limits have k=-lambda. TANK source
allows positive, negative or zero k. A stationary initial state never reaches
an event. With v0=kE0+B, the mathematical event time to target Et is

    t = (Et-E0)/v0                         if k=0
    t = log1p(k(Et-E0)/v0)/k               otherwise.

A target is reachable only in the velocity direction with the target velocity
of the same sign. An equilibrium target takes infinite time; a target beyond
the equilibrium is unreachable. Candidate targets are zero, capacity, the
branch kink, and intersections of the active limit with each competing affine
limit. Parallel unequal limits never meet. Parallel equal limits were already
rejected by the strict selector. Filter candidates to the current branch and
physical tank interval, then choose the earliest time. Exact coincident
nominal candidates retain all labels. These rules also cover cooling from
large standing loss while the HP remains charging, and branch departure in
either direction. They do not model direct demand/discharge or HP dwell.

Continuity at the kink holds algebraically for hot and source limits. Roots,
coefficients and log1p times in the MATLAB descriptor use ordinary binary64;
they are NOMINAL candidates, not outward certified event times or endpoints.
The instantaneous v55 certificate does not certify propagated E. In particular,
the exact mathematical kink often cannot be represented as a double and the
v55 gate rejects its rounded endpoint. Therefore this descriptor is intentionally
not wired into the saved controller. Release remains blocked until an explicit
one-sided equality protocol, propagated exponential energy enclosure and
variable-power compressor/source integrals are independently verified. A
comparison tolerance in QA is not a production certificate.

Independent QA derives all coefficients and candidate intersections using
Fraction arithmetic from original binary inputs; computes times and endpoint
equations at 80 decimal digits; checks event-free trajectories with a separately
programmed min-envelope RK4 method. MATLAB results are reopened from their
original MAT file. Fresh saved-v52 six-mode/reference runs remain held-input
controls and cannot establish continuous-coupled correctness. Independent means
separate algorithms by the same agent, not independent personnel.
