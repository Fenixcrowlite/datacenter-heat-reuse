# Correlated capacity termination and OFF dwell v63

Engineering assumptions only; no article equations, calibration or measured
validation are claimed. This additive Stateflow component extends v62, preserving
the original global constant-request trajectory and exact operand expression.
Accepted six-mode dispatch remains v57. This is not full coupled dispatch.

Let B=eta*q [MW], lambda [1/h], C [MWh/K], E [MWh]. Before capacity,
E'=B-lambda E. The branch expression is C*(delivery+direct-ambient-charge).
Capacity is the distinct exact expression K=C*(Tmax-ambient). Neither expression
is rounded into an initial scalar inventory. Strict monotonicity B-lambda K>0
is required. For lambda>0 the capacity root is
tc=-ln((B-lambda K)/(B-lambda E0))/lambda; for lambda=0,
tc=(K-E0)/B. Host log supplies only a candidate bracket. The compiled chart
certifies E(tlo).upper<K.lower and E(thi).lower>K.upper using its outward series.
The bracket must follow the branch bracket. Unsupported spans reject.

At capacity, HP switches OFF as a safety override, independent of ON dwell.
No new heating is authorized after tc. Cumulative heating is q*tc; source and
compressor energies are the same global-time quadrature integrated to tc.
The quadrature bracket may include a conservative mathematical extension past
capacity, solely as an enclosure; no such extension is physical service credit.
Heat, source, compressor, auxiliary and charge-loss enclosures remain bitwise
unchanged during passive cooling. No midpoint or selected scalar root is used.

For a later exact binary horizon t>thi, OFF age is [t-thi,t-tlo], expanded
outwards. Inventory is K*exp(-lambda*(t-tc)), computed by the outward flow series
on the retained capacity expression and duration interval. Passive standing loss
is K-E(t). At lambda=0 it is exactly zero and inventory is the same K expression.
Total standing loss includes charge-phase loss and passive loss. The first law
E0+heat-E-standing-chargeLoss encloses zero. These marginal hulls remain correlated
through the retained root/operands; they cannot authorize scalar service credit.

ON age at capacity is initial age+[tlo,thi] and freezes after switch OFF. OFF age
starts at exact zero at the symbolic capacity event, not at a guessed solver time.
Readiness is 1 only if OFF-age.lower>=minimum OFF dwell; 0 if upper<dwell;
2 if unresolved. Readiness alone is not a restart authorization. Every restart
command rejects: thermal restart/cutoff hysteresis and subsequent event-chain
integration remain open. The input has phase, physical horizon and restart flag.

The 80-double memory preserves v62 slots 1-64 (tag becomes 63; ON latch becomes
0 at capacity; water ports are exactly zero while OFF). Slots 65-67 retain
capacity-time bracket and dwell; 68-69 expose the bracket; 70-71 OFF age; 72
three-way readiness; 73 capacity safety reason=3; 74-75 initial ON age;
76-77 branch bracket; 78-79 capacity expression enclosure; 80 restart=0.
Original input has 34 doubles: v62's 31 with schema 63, then tlo,thi,minimum dwell.

Five guarded chart phases execute on seven protocol solver ticks. Solver ticks
are not physical event times. Branch/capacity ordering, delayed immutable-memory
faults, passive horizons, finite ports, SOC, first-law and OFF readiness must be
checked in actual normal-mode simulations. Independent Python Fraction and
120/160-digit analytic exponential/log integrals review original reopened-MAT
binary exports. Separate synthetic reviewer mutations are not experiments.
Same-agent algorithmic independence is not independent personnel validation.
The separately accepted v30 storage kernel also executes one pre-capacity active
and three passive scalar comparisons per fixture. Its rounded capacity and
nominal-root duration are scalar reference inputs, not production event resets.
Their energies must lie in the compiled enclosures. The Python reviewer separately
checks the v30 outputs from their own exact binary inputs, including standing loss.

Scope: constant REQUEST, scalar exact initial E, strict increasing charge branch,
host-certified exact equivalent limiter mask, one capacity safety OFF event,
passive cooling, conditional outward binary64 and |lambda*span|<=1. Source/hot
limits remain feasible on the upward request branch. Six-mode integration,
actual restart, thermal cutoff, other limiters, arbitrary interval initial
inventory, calibrated HP equipment and measured physical validation remain OPEN.
