# Conservative compressor ceiling in saved Stateflow v83

The new backend adds a finite nonnegative compressor electrical ceiling Pmax
(MW), policy operand 26. It is a synthetic engineering rating, not a coefficient
from the unacquired 2025 commercial-device supplement. The reduction and primary
evidence boundary recorded in HP_approach_derivation_v82.md remain unchanged;
no new primary text or calibration is claimed this run.

For the preserved constant cooling-factor reduction, with k the binary64
operand 273.15, define exact operand expressions:

    TeC = Tsource - source_drop - evaporator_approach
    A = eta_cooling * (TeC + k)
    L(E) = max(Tfloor, Ta + E/C + water_rise) + condenser_approach - TeC
    W(E,q) = q * L(E)/(A + L(E))
    Lmax = max(Tfloor, Tmax + water_rise) + condenser_approach - TeC
    COPmin = 1 + A/Lmax
    effective_thermal_cap = min(original_thermal_cap, Pmax * COPmin)

E is MWh, C is MWh/K, temperatures and rises are C/K, q and W are MW.
The physical reduction assumes E < C*(Tmax-Ta). The numerical kernel checks
the upper endpoint against its outward capacity upper endpoint Ucap. The final
v83r2 implementation therefore replaces nominal Tmax in Lmax by an outward
enclosure of Ta+Ucap/C, using the same capacity operations as the kernel. This
covers both the physical domain and the kernel's rounded numerical guard;
the first nominal-Tmax v83 candidate and its passing fixture evidence remain
preserved, and are not the accepted release. The exact Fraction fixture QA
also checks each segment's actual maximum endpoint lift against nominal Lmax,
which is a stronger fixture condition than required by this revised cap.
For A>0 and 0<L(E)<=the conservative revised Lmax,
L/(A+L) is increasing: its derivative is A/(A+L)^2>0. Thus the exact
inequality q<=Pmax*COPmin proves W(E,q)<=Pmax throughout every accepted
segment, even when temperature, root brackets and source/work quadrature vary.
This is an instantaneous bound, not an average-energy test.

The production adapter uses outward binary interval operations (two epsilon
steps at each operation), takes the lower product endpoint, and intersects
with the original thermal cap. It never increases the thermal rating. Zero
Pmax gives exact zero thermal cap and safety OFF. Nonfinite/negative ratings,
invalid axes and nonfinite intermediate expressions reject. No tolerance or
production guard is relaxed. Subnormal underflow conservatively clamps to
zero. Overflow rejects even if the original thermal rating would bind.

The SAME six-state chart embeds this adapter before every mode decision and
dispatch. Its standing-loss/HP/energy/temporal monitor receives the effective
25-operand policy. Raw 26-operand policy is immutable across a schedule, with
separate retained raw memory; changing a nonbinding ceiling also rejects.
A second chart output records all raw operands plus the effective thermal cap.
The thermal trace remains schema 75 and binds the effective policy, allowing
the preserved v76 reporter and independent thermal equation reviewer to operate.
They do not themselves authenticate the raw electrical policy; the certificate
output and v83 independent reviewer provide that additional evidence.

Predeclared tests: six required modes with a nonbinding ceiling and bitwise
saved-v80 reference comparison; ceiling 0/.01/.05/.2 MW at cold/hot tank
states and approach pairs (1,1)/(10,10); repeated stop/restart event histories;
negative/NaN/Inf and delayed nonbinding-ceiling mutation runtime refusals.
Independent exact Fraction algebra checks the cap and every segment worst
electrical rate, and independent 120/160-digit closed exp/log trajectories check
original-MAT binary exports, inventory, losses, event/dwell timing and reports.
Reviewer corruptions must detect excessive cap and excessive heat allocation.

Limitations: this global Tmax ceiling is safe but can underuse compressor
capacity at colder operating temperatures. It is not an instantaneous maximal
electrical limiter, calibrated part-load map, startup-current model, total site
electricity limit, variable rating, annual acceptance, generated-code acceptance
or physical validation. Auxiliary electricity remains separate, so total external
electricity may exceed Pmax by the configured auxiliary fraction. The existing
finite-span, event-collision, clock and segment-count domains remain. Independent
QA means a distinct same-agent algorithm, not independent personnel; MATLAB
reopens MAT for binary export, not an independent MAT parser.
