# Coupled branch certificate v55

Engineering implementation prerequisite for a coupled Stateflow release. All
fixtures use the inherited synthetic tank-return topology. No new paper claim,
equipment calibration, SLX, or continuous-coupled dispatch acceptance is made.

The exact-input branch gap is

    g = ambient + E/C + charge_approach - delivery - direct_approach.

Each finite binary64 input denotes its exact rational value. A basic interval
operation evaluates the extreme endpoint combinations and expands its rounded
lower/upper extrema by two `eps` values at the respective extrema. IEEE binary64
round-to-nearest with gradual underflow is required. One spacing covers the
operation rounding; the second covers expansion rounding and binade changes.
Zero uses the minimum subnormal spacing. Nonfinite intermediates, an interval
denominator including zero, and expansion overflow reject. Exact input points
receive no uncertainty until an operation is performed. No user tolerance or
production Stateflow guard is changed.

Only `lower(g)>0` certifies TANK and `upper(g)<0` certifies FLOOR. An interval
containing zero is UNRESOLVED, including an exactly equal branch. The v55 wrapper
rejects UNRESOLVED with a dedicated identifier rather than assigning a branch.
It deliberately may reject well-defined signs near the kink. Equality handling
and event endpoints will need an exact or explicitly one-sided event protocol.

The certificate also encloses all four instantaneous heat limits, retaining
request/nameplate as exact input points. It certifies a unique source limiter
only when the source upper bound is strictly below all other lower bounds.
This is diagnostic evidence, not a general active-limit/event selector. Kelvin
conversion uses the exact binary value of MATLAB's literal 273.15; the rational
reviewer uses that same explicit input convention. Physical equations with a
decimal Kelvin offset differ by representation error and are not exact-input
branch assertions.

The known witness E=5 MWh, C=binary 0.2 MWh/K, ambient=20 C, charge approach=2 K,
delivery=45 C, direct approach=2 K has rounded g=0 while exact g is negative.
The new gate must reject it. Original v54 vectors, including all twelve recorded
branch disagreements, are replayed with exact rational QA. Additional ULP
neighbors, translations, capacity-rate ties, wide positive-C scales and gradual
underflow exercise the enclosure independently.

The instantaneous certificate does not enclose the exponential propagator's
roundoff, produce certified continuous endpoint energy, solve all charge-side
limiter regimes, or provide event times. Consequently it is not sufficient to
integrate a new coupled Stateflow controller. Saved v52 can still run a sampled
held-boundary control; that evidence must remain labeled as an approximation.
The next release requires the general piecewise charge dynamics, conservative
endpoint/event protocol, variable-power port integrals, and then six-mode,
fault, reference, and independent trace QA. Preserve v52/v53/v54 evidence.
