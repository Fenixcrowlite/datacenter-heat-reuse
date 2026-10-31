# Fixed-size compiled correlated charge memory v62

This is an executed Stateflow prerequisite for the still-open continuously
coupled six-mode plant. It does not replace accepted dispatch v57. No new primary
article evidence, equipment calibration or measured physical validation is used.
All fixtures and the cooling-factor law remain synthetic engineering assumptions.

## Exact expression and compiled memory

The source doubles denote their exact binary rationals. The event is the
nonrepresentable energy manifold

`E*=C*(delivery+direct_approach-ambient-charge_approach)`.

Instead of choosing a binary64 endpoint, the saved chart retains every defining
operand and an expression/schema identifier (62). These operands define the same
exact expression before, at and after contact. Its outward runtime enclosure is
diagnostic; it never becomes a scalar initial condition. The host v61 rational
adapter certifies the branch, the isolated time bracket and exactly equivalent
right limiter mask. Compiled code independently checks bracket signs, domain,
constant limiter feasibility, port bounds and immutable operands. Interval
overlap at a limiter is not itself an exact-equality proof. The host certificate
is an explicit trust boundary, not replaced by a compiled BigInteger engine.

The chart's fixed 64-double retained memory is as follows (MATLAB indexing):

| Slots | Meaning |
| --- | --- |
| 1–23 | E0, request, eta, lambda, C, ambient, delivery, direct approach, charge approach, condenser approach, source inlet, source glide, evaporator approach, cooling factor, hot capacity rate, HP nameplate, source capacity rate, TES charge limit, tank maximum, auxiliary ratio, initial HP-age lower/upper, total horizon |
| 24 | Expression/schema identifier 62 |
| 25–26 | Root-time bracket, retained across every continuation |
| 27–31 | Exact host-certified equivalent mask: REQUEST, NAMEPLATE, HOT_FLOW, SOURCE, TES_PORT |
| 32–33 | Outward enclosure of symbolic E* |
| 34 | Protocol phase 0 FLOOR, 1 CONTACT, 2 TANK |
| 35–36 | Physical horizon enclosure |
| 37–38 | Inventory enclosure |
| 39–40 | HP-age enclosure |
| 41–52 | Cumulative heating, evaporator/source, compressor, standing loss, charge loss, rejected auxiliary energy, each lower/upper |
| 53–54 | First-law residual enclosure |
| 55–57 | ON latch=1; scalar authorization=0; memory schema=62 |
| 58–59 | Capacity enclosure |
| 60–61 | Instantaneous finite hot-water capacity-rate enclosure |
| 62–63 | Tank-linked hot-water inlet enclosure |
| 64 | Quadrature cell count=128 |

The input has a phase and physical horizon; it contains no output inventories,
physical port energies, temperatures or HP ages. Those are computed by the
embedded compiled function. After contact, three successively later horizons
execute from persistent chart memory. Every original operand, bracket, equivalent
mask and initial age must remain unchanged. No branch reset or scalar service
credit is authorized.

The solver's five discrete ticks are protocol phases. The time of the physical
event is an enclosure carried in memory, not a solver-clock event. Physical
horizons and solver time are recorded separately. This distinction limits the
integration claim.

## Inventory, clock and tank-linked ports

With constant REQUEST heat q [MW], eta [-], lambda [1/h], C [MWh/K],
`E'=B-lambda*E`, `B=eta*q`. Both sides have this same global trajectory:

`E(t)=E0+(B-lambda*E0)*t*phi1(-lambda*t)`.

The inventory integral is
`E0*t+(B-lambda*E0)*t^2*phi2(-lambda*t)`.
No outgoing segment is initialized at a rounded event state. The compiled
function bounds these expressions at global physical time using 24 series terms
and a 3/26! remainder allowance, conditional on outward `|lambda*t|<=1`.
Basic operations expand both bounds by two local eps under binary64
round-to-nearest and gradual underflow; nonfinite expansions reject. This is a
conditional arithmetic contract, not arbitrary-range formal verification.

The compiled flow certifies `E(tlo).upper < E*.lower` and
`E(thi).lower > E*.upper`. At CONTACT, inventory is the same symbolic expression
E*, with root time in `[tlo,thi]`; first-law and port hulls retain that correlation.
At later horizons, inventory is the global flow at that horizon. The supported
trajectory is strictly increasing throughout the admissible capacity domain,
certified by `B-lambda*capacity > 0`, and must remain below capacity. No other
capacity, dwell, cutoff or limiter event is handled.

Temperature evolves as `Ttank=ambient+E/C`. The hot-water inlet is
`max(delivery+direct_approach,Ttank+charge_approach)`.
Let `Te=source_in-glide-evaporator_approach`,
`a=cooling_factor*(Te+273.15)`, and
`L(E)=max(Lfloor,L0+E/C)` with the condenser approach included. The evaporator
source power is `q*a/(a+L(E))`; compressor power is q minus that power.

Source energy is integrated over the ENTIRE global horizon using 128 outward
rectangles. Monotone inventory and monotone lift provide bounds on each cell.
Taking an interval max includes every part of the uncertain branch window.
There is no omitted unresolved-time energy and no chosen event midpoint.
The width of each uncertain cell is horizon/128, avoiding artificial widths
from subtraction of independently bounded nodes. Heating is q*t, standing
loss is lambda times the inventory integral, charge loss is (1-eta)*q*t, and
auxiliary electricity is rejected outside the hot thermal boundary.

First-law residual is `E0+heat-E-standing_loss-charge_loss`; its enclosure must
contain zero. All cumulative physical energy bounds are nonnegative.

The water capacity rate is q/(hot_inlet-Ttank). At/after contact the SAME symbolic
approach gives q/charge_approach directly; subtracting decorrelated tank/inlet
intervals would lose the constant-temperature-difference constraint. Exact
host-certified hot-flow ties are retained; non-ties require a strict compiled
upper capacity bound. No eps-based tie choice is made.

HP stays ON across this thermal event. Age is original age interval plus global
physical horizon; neither an event inventory nor event age is used as a new
scalar initial condition. This chart authorizes no HP switch. Uncertainty-aware
dwell switching remains work for integration with the full supervisor.

## Independent equations and executable evidence

Python imports no production component. Fraction reconstructs the exact manifold,
limiter mask and physical coefficients from binary exports of the reopened
original MATLAB MAT. At 120 and 160 Decimal digits it independently computes
the root `-ln((B-lambda*E*)/(B-lambda*E0))/lambda` (linear expression at zero loss)
and equilibrium/exponential inventory and its integral. For the outgoing source
integral, `y=a+L0+E/C`, `c=B/C+lambda*(a+L0)` gives
`integral(1/y)=[ln(y_end/y_event)+lambda*duration]/c`.
The floor-source integral is constant power times exact event duration.
Their sum independently checks compiled source bounds at every physical horizon.
HP ages, water rate, hot temperatures, exact operand continuity and port closure
are independently checked as well. Separate synthetic mutations check reviewer
sensitivity to snapping, missing ties, source corruption, timer reset, provenance
change and scalar authorization. These are not physical experiments.

Actual saved-chart runtime faults include skipped/repeated contact, reversed and
excess horizons, invalid source/domain, delayed operand/age change, corrupted
bracket/mask/schema and NaN. Prior models and data must retain their hashes.
Final acceptance requires sealed source/model hashes and a successful batch
receipt; development startup/snapshot/warning evidence remains preserved.

## Integration blocker and next task

This model solves fixed-size compiled provenance/enclosure retention and executes
continuous tank-linked charge continuation in the specified constant-request
upward branch. It is not a six-mode dispatch model. Initial interval inventory,
other limiters, general event chains, HP switching/dwell uncertainty, source and
hot-water fault monitors for every full-plant topology, and finite-capacity event
termination remain open. The accepted six-mode plant is still saved v57, under
its held-boundary assumptions and its existing independently verified fixtures.

Next: integrate this fixed-size trajectory/provenance memory into a new additive
six-mode dispatch version, beginning with a capacity/cutoff event chain and
uncertainty-aware HP supervisor. Reject unsupported regimes explicitly. Execute
the six mandated cases, fault timing and verified-reference comparisons, then
perform independent original-MAT equation/port/clock QA. Preserve v52–v62;
do not repeat unchanged annual matrices. Equipment calibration and measured
physical validation remain open.
