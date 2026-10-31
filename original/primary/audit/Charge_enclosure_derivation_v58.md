# Bounded single-regime charging prerequisite v58

This is an additive prerequisite to the open continuous-coupled Stateflow task.
The actual accepted model remains saved v57; no v58 SLX or continuously coupled
controller is claimed. All prior models and evidence are preserved. Equations
below are independently derived for the synthetic v54–v57 topology. No new
primary article text, equipment calibration or measured validation is used.

Within each of v56's ten branch/active-limiter combinations, hot heat is affine:
q(E)=alpha E+beta [MW]. E is ambient-referenced tank energy [MWh]. With charging
efficiency eta and loss coefficient lambda [1/h], E'=kE+B, k=eta alpha-lambda,
B=eta beta. Every coefficient is enclosed directly from the exact binary inputs,
including the binary constant 273.15; the nominal v56 coefficients are not used
as certified coefficients. v56 only proposes the starting branch/limiter.

With v0=kE0+B, x=kt and phi1(x)=sum(x^n/(n+1)!),
phi2(x)=sum(x^n/(n+2)!),

    E(t) = E0 + v0*t*phi1(kt)
    integral(E dt) = E0*t + v0*t^2*phi2(kt)
    heat = alpha*integral(E dt) + beta*t.

The formulas remain valid at k=0 and avoid subtraction of nearly equal
exponentials. Production evaluates terms n=0..24 with outward arithmetic.
For every outward evaluation node |x|<=1 is enforced. Each omitted tail is
bounded by 3/26!: the phi1 tail is at most |x|^25 exp(|x|)/26!, exp(1)<3,
and phi2's tail is smaller. The tail is itself computed outward. Production
does not call exp/log or presume correctly rounded library transcendental
results. Each finite basic operation expands by two local eps values, including
subnormal endpoints. Overflow rejects. This is conditional on IEEE binary64
round-to-nearest with gradual underflow; no universal deployment proof is claimed.

Every exact trajectory in the coefficient box is monotone or stationary:
its velocity is v0*exp(kt), so its sign cannot change. The hull of initial energy
and the enclosed final energy therefore bounds the full interval. Exact branch
sign, physical energy bounds and the strict unique affine minimum are then
certified over that hull. A hull touching a branch, capacity or competing limiter
rejects. This is deliberately a conservative single-regime gate; accepted steps
cannot authorize a transition at an event. No tolerance picks a side of a kink.

Let L(E)=l0+l1 E be saturation lift [K], a=f(Te+273.15) [K]. Heating COP is
1+a/L. Compressor and evaporator power are qL/(L+a) and qa/(L+a). For SOURCE
limiting, evaporator energy is exactly S*t. On FLOOR, L is constant and source
energy is heat*a/(L+a). Other TANK regimes use interval rectangles: enclose E
at both endpoints of each partition, use monotonicity to enclose E throughout,
enclose qa/(L+a), and multiply by the outward partition width. Both time nodes
and widths are enclosed, so rounded partition gaps cannot omit service.
Compressor energy is heat minus source energy. The intervals are rigorous
outer bounds under the stated arithmetic assumptions, not point estimates or
an adaptive tolerance guarantee. Refinement reduces rectangle uncertainty in
tested fixtures; it does not imply universal nesting or a fixed relative accuracy.

Standing loss is lambda*integral(E dt), charging loss is (1-eta)*heat, and
fully externally rejected auxiliary electricity is aux_factor*compressor.
The balance E0+heat-E1-standing_loss-charge_loss encloses zero. There is no
direct demand, discharge, cutoff/restart/dwell event execution in this kernel.

Independent QA reconstructs coefficients with exact Fraction arithmetic and
evaluates analytic energy equations at 80 and 120 decimal digits. The reviewer
does not use production interval algorithms or rectangle integration. For the
non-source TANK limits q is constant. Put y=L+a, c=l1 B-k(l0+a); y'=ky+c:

    integral(1/y dt) = (log(y1/y0)-k*t)/c        when c != 0
    integral(1/y dt) = (1-exp(-k*t))/(k*y0)     when c = 0, k != 0
    integral(1/y dt) = t/y0                    when stationary.

Thus source energy=q*a*integral(1/y dt). Degenerate/stationary cases are
handled separately. Original MAT files are reopened for binary input/output
exports, and both precision levels must lie within each production interval
with no added comparison tolerance. Precision stability is checked separately.
Reviewer mutations remain explicitly separate synthetic self-checks.

The original nominal E=5 MWh endpoint has exact branch gap
-5/3602879701896397 K. Its rejection is reproduced rather than normalized
away. One-sided branch/limiter equality, outward event-time isolation, energy
enclosure handoff, demand/discharge coupling and HP supervisor integration
remain the concrete blocker before an additive continuous Stateflow model.
