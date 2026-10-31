# Correlated constant-request branch record v61

Engineering prerequisite for continuously tank-linked Stateflow, not a new
accepted SLX. Saved v57 retains its held-macro finite-water acceptance. This
run uses synthetic fixtures and no new primary article evidence. The immediate
Stateflow priority governs this work; no unrelated research or annual reruns.

## Exact contact, assumptions and scope

All source doubles denote their exact binary rationals, including the stored
273.15 K offset. In the zero-demand charge topology let C [MWh/K], Ta [C],
F=delivery+direct approach [C], d=charge approach [K]. The branch manifold is
E*=C(F-Ta-d) [MWh]. Java BigInteger host arithmetic retains this reduced
rational as numerator/denominator strings. No Symbolic Toolbox is required.
It is not a code-generation-compatible memory implementation.

v61 deliberately supports increasing FLOOR/REQUEST to TANK/REQUEST with
constant q [MW] on both sides. Initial strict guards are inherited from v56;
the first-event time enclosure is inherited from v59. Only BRANCH and an
exactly simultaneous LIMIT_HOT_FLOW contender are supported. Different events
whose numerical windows overlap reject. Decreasing, stationary, capacity,
other initial limiters and non-equivalent contacts are unsupported and reject.

At E*, right limits are request q, nameplate, H*d, S(1+Lfloor/a), and TES port.
a=f_c(Te+273.15) [K], S=source capacity rate times glide [MW], and Lfloor [K]
is the floor condenser minus evaporator temperature. REQUEST must be minimal.
Constant limiters exactly equal to q are retained as a set. Equality is tested
by integer cross multiplication, never by tolerance or rounded values. Source
equality rejects because its right slope S/(aC)>0 is nonzero and the limiter
law is not equivalent. Increasing right motion and a strictly interior endpoint
are required. No saturation snap or scalar memory handoff is authorized.

## Correlation and bounded physical ports

E'=eta*q-lambda*E, k=-lambda [1/h], B=eta*q [MW]. Both sides have the same
inventory ODE. E(t)=E0+(kE0+B)t*phi1(kt); its integral is
E0*t+(kE0+B)t^2*phi2(kt). The unique incoming root defines t_event at the
exact rational E*. Outgoing duration is total-t_event, not a separately chosen
point. Outgoing initial inventory is that SAME rational. The record stores
this constraint and trajectory, time bracket, exact manifold, port enclosures
and HP-age enclosures. Interval hulls are bounds of correlated quantities, not
a declaration that every independent combination is physically reachable.

phi series and outward 3/26! tail follow the verified v58 derivation, requiring
outward |lambda*t|<=1. Two local eps expansions enclose basic operations under
binary64 round-to-nearest and gradual underflow. Exact zero identities are
preserved. Rational-to-double bounds are checked by exact integer comparisons;
nonrepresentable E* uses adjacent doubles. Estimate overflow or failure to
bracket within 16 neighbor steps rejects; this is not an arbitrary-range API.

Heating input is exactly q*total [MWh]. FLOOR evaporator energy is
q*a/(a+Lfloor)*t_event. TANK lift is L0+E/C; source power is q*a/(a+L0+E/C).
Outward rectangles on uncertain outgoing duration enclose this integral;
each exact member's affine ODE is monotone. Cell width is duration/cells,
avoiding artificial negative widths from independently subtracted time nodes.
Compressor energy is heating minus source; charge loss is (1-eta)*q*total;
standing loss is lambda times the two inventory integrals. Auxiliary energy
is rejected outside the hot thermal boundary. Nonnegative port bounds and
an inventory first-law enclosure containing zero are mandatory.

HP remains ON across this thermal branch transition; its age is NOT reset.
Age_event=age_initial+t_event; age_end=age_initial+total. These are interval
enclosures, not a scalar timer or permission for a dwell-sensitive switch.
There is no midpoint, boundary snap, omitted event-window energy or scalar
service credit. All source/work/loss results across uncertain time are bounds.

## Independent verification

The Python reviewer imports no production algorithm. Fraction reconstructs
the manifold and coefficient/tie laws from original reopened-MAT binary exports.
For lambda>0 the independent root is
-ln[(B-lambda E*)/(B-lambda E0)]/lambda; for lambda=0 it is (E*-E0)/B.
The global inventory and integral are evaluated independently as equilibrium
plus exponential (or a linear polynomial), spanning the full physical time.

For outgoing source energy let y=a+L0+E/C, k=-lambda, and
c=B/C-k(a+L0)>0. Then integral(1/y)=[ln(y_end/y_event)-k*duration]/c.
Thus source_out=q*a*integral(1/y). Independent 120- and 160-digit Decimal
evaluations verify all reported physical enclosures and precision stability.
Exact numerator mutation, missing tie, inventory/source corruption, timer reset
and scalar-authorization corruption are separate synthetic reviewer checks.
No independent personnel or measured physical validation is claimed.

## Remaining executable Stateflow blocker

The exact branch/tie fixture can continue in this HOST representation, including
the original E*=90071992547409925/18014398509481984 between adjacent doubles.
Saved v57's TES and HP memories still accept scalar binary64 values and held
macro condenser boundaries. Feeding a midpoint/adjacent endpoint into those
memories would discard the constraint and its time/port correlation. v61 does
not do that, does not modify v57, and does not accept a new continuously coupled
model. General limiter/event chains, arbitrary interval initial inventory,
compiled correlated memory, uncertainty-aware dwell transitions, and compiled
finite-water guards on changing tank-linked temperatures remain integration
work. Equipment calibration and measured validation remain open.

Next: define a fixed-size compiled correlated memory/port schema with validated
manifold provenance and event clock uncertainty, then build an additive SLX
that executes this branch fixture without scalar reset. Extend guarded events
before accepting all six modes, faults and reference comparisons. Preserve
v52-v61 and the failed development evidence; do not repeat annual matrices.

