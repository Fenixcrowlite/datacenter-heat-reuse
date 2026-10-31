# Charge-event isolation v59 and the correlated Stateflow handoff blocker

This is a new MATLAB event-isolation prerequisite and a documented blocking
defect, not a new coupled Stateflow release. The accepted plant is saved v57.
Its finite-water boundary, six modes, cutoff/restart/dwell, runtime faults and
reference comparisons are executed afresh in this checkpoint. No new primary
article text, equipment map, calibration or measured validation is asserted.
All charge topology and test fixtures remain synthetic engineering assumptions.

## Equations, signs and dimensions

For the fixed initial branch and active limiter, q(E)=alpha E+beta [MW],
E [MWh], alpha [1/h], beta [MW], k=eta alpha-lambda [1/h] and B=eta beta
[MW]. The exact initial-binary-input ODE is E'=kE+B. The continuation is

    E(t)=E0+(k E0+B) t phi1(kt).

v59 constructs all coefficients outward from the source inputs, independently
of v56's nominal event times. The latter only supplies the initially certified
branch/limiter and proposes harness horizons. The finite 24-term phi1 series
and outward 3/26! tail are inherited from the v58 derivation. Every outward
node requires |kt|<=1. IEEE binary64 round-to-nearest and gradual underflow
remain explicit conditions; basic arithmetic expands by two local eps values.
Overflow, uncertain starting guards and excessive spans reject.

Define eight positive affine guards g_i(E)=a_i E+b_i:

- E>0 and Ecap-E>0 [MWh].
- Ta+E/C+d-F>0 for TANK; its negative for FLOOR [K].
- q_active(E)>0 [MW].
- q_j(E)-q_active(E)>0 for the four other limits [MW].

The first zero of any guard ends the current strict regime. This includes an
active limit becoming zero, both inventory bounds, branch crossings and every
competing limit. There is no arbitrary minimum-time epsilon. Because
E'(t)=(k E0+B) exp(kt), every exact trajectory and every affine guard is
monotone or stationary. Positivity at both endpoints certifies the entire
physical prefix, including stationary and decreasing-energy trajectories.

For each guard, outward positivity at the horizon certifies no event there.
Otherwise bisection retains a lower endpoint with certified positive guard
and an upper endpoint with its enclosed sign. A negative upper sign certifies
a crossing. A midpoint whose interval contains zero stops refinement without
choosing either side. Iteration exhaustion and adjacent time doubles also stop
refinement. They cannot authorize a transition. No requested width/relative
accuracy guarantee is provided; uncertainty may leave a broad window.

The safe prefix is the minimum of all candidate lower endpoints. The upper
bound for the first event is the smallest certified-negative upper endpoint,
when one exists. Every guard whose candidate lower endpoint is no later than
that upper bound remains a contender. Overlapping windows retain all contenders;
in particular a simultaneous branch/hot-flow event is never arbitrarily ordered.
Without a certified-negative upper endpoint the result is conservatively
HORIZON_UNRESOLVED_BLOCKED, not a claim that an event occurred before the horizon.

The fixed-regime ODE may be evaluated past its first zero solely to bracket a
mathematical root. That continuation is NOT a physical dispatch or heat credit.
The harness integrates source/compressor/standing/charging/auxiliary energy
with v58 on half the certified safe prefix, comfortably inside the regime.
No interval between the safe prefix and the event is silently served or lost.
The original exact inventory and HP clock must remain correlated with any future
event-time representation. v59 explicitly refuses both transition and memory
handoff authorization.

## Independent equations and QA

Python imports no production component or interval implementation. Fraction
reconstructs exact coefficients and affine guards directly from original MAT
binary64 exports. A guard root has E*=-b/a. If k=0, t*=(E*-E0)/(k E0+B).
Otherwise t*=ln((k E*+B)/(k E0+B))/k when the ratio is positive and the time
is positive. Stationary, unreachable and asymptotic roots are handled separately.
120- and 160-digit Decimal evaluations independently check energy, all endpoint
guard signs, all isolated windows and earliest-event coverage. Separate analytic
integrals check physical-prefix ports, following the v58 independent derivation.
Binary binding, reopened MAT equality, prior source/model preservation and actual
batch receipts are mandatory. Synthetic reviewer mutations are reported separately.
This is independent algorithmic QA by the same agent, not independent personnel.

## Concrete exact-endpoint blocker and one-sided policy

The simultaneous fixture uses C=the binary64 value of 0.2 MWh/K, Ta=20 C,
F=47 C, d=2 K, hot capacity rate=0.5 MW/K, request=1 MW. Its exact branch
energy is

    E*=25 C=90071992547409925/18014398509481984 MWh.

It lies strictly between adjacent doubles 5 and 5+eps(5). No binary64 scalar
can equal this exact threshold. At the exact symbolic event, REQUEST and
HOT_FLOW tie at 1 MW. For the subsequent TANK branch, that tie persists:
HOT_FLOW=H*d=1 MW. Both adjacent scalar continuations reject in the current
strict branch/unique-limiter API. This is an executed representation/equality
blocker, not a claim of a newly proved physical error in the accepted v57 model.

The proposed mathematical one-sided policy is precise:

1. At exact branch equality, use the sign of E' for the right-hand branch:
   positive enters TANK, negative enters FLOOR; zero retains equality and
   requires a stationary contact policy. Numeric overlap is not exact equality.
2. Among equal affine limits at an exact event, choose the smallest right
   derivative alpha_j*E'. When E' is nonzero, equal values and equal derivatives
   imply identical affine power laws throughout that branch; record the tied
   limiter set. At E'=0, equal derivatives alone do not establish equivalent
   affine laws: retain the stationary contact and compare exact slopes and
   intercepts separately. A stable index may name a set only after exact
   equivalence is established.
3. At simultaneous boundaries, compute the right branch and all limiter guards
   together, rather than sequentially normalizing the energy. Capacity and
   safety constraints override continued charging. HP dwell must use physical
   time uncertainty, not a rounded event instant.
4. An event record must carry the exact threshold constraint, incoming trajectory,
   time bracket, correlated energy/source/work/loss enclosures, HP clock interval
   and right-hand branch/tied-limit set. The same mathematical energy feeds both
   incoming and outgoing flows. An arbitrary midpoint, capacity snap, zero-span
   memory reset or unintegrated-time heat credit is inadmissible.

The policy is derived here; its correlated representation and executable
Stateflow handoff are NOT implemented or accepted by v59. The scalar v55/v56
API cannot express this event manifold and rejects persistent exact ties.
The next task is an additive endpoint record and interval/correlated initial-
condition propagator with exact equivalent-limiter classification. It must then
drive a new continuously coupled saved Stateflow model while preserving v57
water guards and v52 supervisor/endpoint behavior, and pass actual six-mode,
fault, reference and original-MAT QA. Do not re-run unchanged annual matrices.
