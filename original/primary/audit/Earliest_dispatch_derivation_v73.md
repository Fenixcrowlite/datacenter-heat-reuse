# Numerical-admissibility repairs and symbolic passive contact v73r2

This is a reduced-model implementation derivation using synthetic engineering
fixtures. No new article equation, equipment value, primary-text signoff,
calibration or measured performance is claimed. The original v14, accepted
legacy v57/v66, v71, v72 evidence and first saved v73 model are preserved.

## Stable affine inventory image

The held storage equation is E' = B - lambda E, with E in energy units,
B in energy/hour and lambda in 1/hour. Its independently derived solution is

    E(t) = E0 exp(-lambda t) + B t phi1(-lambda t)
    integral(E,0,t) = E0 t phi1(-lambda t) + B t^2 phi2(-lambda t)

where phi1(x)=(exp(x)-1)/x and phi2(x)=(exp(x)-1-x)/x^2,
with continuous values 1 and 1/2 at zero. Production active singleton corners
use the equivalent E0+(B-lambda E0)t phi1(-lambda t), preserving small active
increments. The uncertain initial inventory is evaluated at monotone corners,
rather than reused as two independent interval operands. For fixed E0 and B,
the derivative (B-lambda E0)exp(-lambda t) keeps its sign, so the extrema over
the time box occur at its endpoints. The solution increases with E0 and B;
the lower/lower and upper/upper operand corners suffice. Passive B=0 uses
the positive product E0*exp(-lambda t), so uncertainty contracts with inventory.

Production bounds exp(+lambda*t) by a positive Taylor sum through degree 30
and then takes its reciprocal. On the private expanded domain 0<=lambda*t<=2,
the remainder is bounded by 8*2^31/31!, since exp(2)<8. The negative phi sums
retain the inherited 24-term bound 8*2^25/26! (also conservative for phi2).
Every arithmetic operation expands by two binary ulps. The public held-span
limit lambda*dt<=1 remains. This is conditional finite-domain arithmetic,
not an arbitrary-scale, subnormal, overflow or generated-code certification.

## Correlated inclusive ON-age proof

The retained age hull remains authoritative for event-derived durations.
For a full macro hold without an uncertain event, an additional compensated
identity records age = hi + err. Error-free binary64 TwoSum supplies the exact
addition residual, and an outward interval encloses their accumulated sum.
Minimum ON dwell is certified either by the age-hull lower bound or by the
lower bound of the correlated difference (hi-minimum)+err. Uncertain event
segments invalidate this optional certificate; it never replaces their hull.
Singleton additive inverses are recognized as the exact zero identity in r2,
so canceling TwoSum residuals do not create a spurious negative lower endpoint.

Trace header fields 62..65 (MATLAB indices) retain valid flag, hi and residual
lower/upper endpoints. Tests include ordinary binary equality, compensated
equality (.1+.2+.19999999999999998 equals exactly .5 in binary-input real
arithmetic), a compensated admissible margin, and .1+.2+.7, whose exact binary
sum is strictly below 1 although its rounded cumulative display equals 1.
The last disable must still reject. This is exact-binary input semantics,
not a claim that nominal decimal schedules should always be interpreted so.

## Selected source/water limiter provenance

Let a=factor*(Te+273.15)>0, Lfloor=hotFloor+approach-Te>0,
and S=sourceFlow*glide. The reduced source extraction is q*a/(a+L), with
L>=Lfloor. Thus q<=S*(1+Lfloor/a) implies source rate<=S.
The selected HP power comes from the lower source/water limiter endpoints and
the nominal HP capacity, minus eight ulps of allocation room. The sum of
separately rounded direct/charge ports is then explicitly checked against all
three bounds. This changes conservative power selection; it does not relax
a capacity guard. Header fields 66..71 retain source-capacity, source-limiter
and water-limiter hulls. The source-rate hull intersects the independently
proved [0,S.upper] interval; independent QA verifies the exact source formula
and the original selected binary powers against the actual capacity.

## Positive correlated compressor work

The reduced work rate is q*L/(a+L), derived directly from
q-q*a/(a+L). Both q>=0 and L>0 are certified. Production integrates this rate
using the same outward time rectangles as source extraction, rather than
subtracting independently widened heat and source energy totals. Auxiliary
electricity is a nonnegative factor times that work. The separate independent
reviewer still checks work=heat-source using the closed source integral.
Neither energy conservation nor source/work containment is replaced by a
nonnegativity tolerance.

## Additional symbolic STOP-to-RESTART contact in r2

The first saved v73 repairs the earlier compressor-work refusal, but the
2^-42 K band next rejects an unresolved passive event boundary. At the STOP
tag, the exact incoming inventory is the symbolic threshold C*(Tstop-Ta),
and B=0. Retaining this contact identity cancels the common C:

    tau = log((Tstop-Ta)/(Trestart-Ta))/lambda
        = log1p((Tstop-Trestart)/(Trestart-Ta))/lambda.

The numerator is the small temperature difference itself; no difference of
two independently widened large inventories is formed. For 0<x<=1/2,
the alternating log1p series through degree 32 has positive remainder at most
x^33/33. All terms and tau are enclosed by outward arithmetic. The result is
a time hull with the same target and dwell/ready fields used by the segment
planner. It is a symbolic analytic certificate, distinct from the generic
before/after inventory witnesses. It applies only to retained STOP, zero B,
positive lambda and the declared log-series domain. Header field 72 records
its use. Other roots keep the generic strict-witness certifier.

The symbolic contact and root-time box survive the segment; no midpoint is
used. Forcing is recomputed after restart. A true enabled collision, unresolved
boundary and the sixteen-segment resource limit remain explicit refusals.

## Verification boundary

Actual saved-model simulations execute the SAME six-mode Stateflow chart in
normal mode; solver ticks are protocol calls containing analytic segments,
not solver-clock thermal events. The independent reviewer converts original
MAT binary exports to exact Fractions and uses 120/160-digit closed exp/log
inventory, event times and piecewise source integrals. Actual containment has
no tolerance. Allocation diagnostics/v30 retain their labelled 1e-12 budget;
matched-partition closed trajectories use a separate 1e-90 comparison budget.
Mutation checks are reported separately. This is same-agent algorithmic QA,
not independent personnel. MAT reopening/export is performed by MATLAB;
no independent HDF5 parser or measured validation is claimed.
