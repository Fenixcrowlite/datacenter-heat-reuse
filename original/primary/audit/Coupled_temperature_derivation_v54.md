# Coupled tank-return condenser derivation v54

This checkpoint derives a new engineering interface and audits the accepted
saved Stateflow v52 against it. No new SLX or continuous-coupling acceptance is
claimed. Existing v52 fixed-temperature acceptance remains intact.

The preserved local source20 p8 Eqs4–7 was visually reinspected this run: cooling
EER uses refrigerant saturation Kelvin temperatures; compressor work plus
evaporator heat equals condenser heat. Current publisher access returned429.
[Source20 DOI](https://doi.org/10.3390/en19030800) identifies the paper. The
[upstream62 university record](https://flore.unifi.it/handle/2158/1432822) opened
but has metadata/abstract and no associated files. Its equipment equations and
supplement remain unverified. Full primary signoffs remain0/31. All temperatures,
flows, factors and topology below are SYNTHETIC_ENGINEERING; no paper replication
or calibrated equipment claim follows from the primary saturation definitions.

## Instantaneous interface and topology

The hypothetical HP hot-water inlet is the well-mixed tank return T, rather
than the fixed40C return of v53. This changes circuit topology and cannot be
interpreted as a matched retrofit efficiency improvement. A controllable
variable-flow circuit maintains its specified outlet; no UA, pump law, minimum
flow or hydraulic split is modeled. The direct-delivery temperature is only a
feasibility floor; this checkpoint's dynamic comparator is charge-only.

With C in MWh/K, fixed ambient Ta, stored energy E in MWh:

    T = Ta + E/C
    Te = source_in - source_glide - evaporator_approach
    H = max(T + charge_approach, delivery + direct_approach)
    Tc = H + condenser_approach
    hot_glide = H - T
    S = source_capacity_rate * source_glide       [MW]
    hot_budget = hot_capacity_rate * hot_glide    [MW]
    a = cooling_factor * (Te + 273.15)            [K]
    lift = Tc - Te                               [K]
    COP = 1 + a/lift
    Q = min(request, nameplate, hot_budget, S*(1+lift/a))
    W = Q/COP; QL = Q-W; auxiliary = r*W

Require finite ordered temperatures above absolute zero, positive C/source
glide/lift,0<cooling_factor<=1, nonnegative approaches/capacity rates/request,
ambient<delivery+discharge_approach<tank_max and0<=E<=C*(tank_max-ambient).
Then1<COP<=Tc_K/lift and QL<=S. Required source/hot heat-capacity rates are
QL/source_glide and Q/hot_glide. At zero hot glide the heat budget is zero:
Q=0 and the reported flow is0; no0/0 or fictitious transfer. Auxiliary heat is
entirely externally rejected, with no storage/demand credit.

## Exact source-limited charging regime

Restrict to the tank branch T+charge_approach>=delivery+direct_approach;
QL=S>0 is the unique active limiter, no demand/discharge, constant request,
all other physical inputs held and no capacity/limiter/temperature event.
Let L0=Ta+charge_approach+condenser_approach-Te. Then:

    lift(E)=L0+E/C
    Q(E)=alpha*E+beta
    alpha=S/(a*C)                    [1/h]
    beta=S*(1+L0/a)                  [MW]
    W(E)=S/a*(L0+E/C)                [MW]
    E'=eta_charge*Q(E)-lambda*E=k*E+B
    k=eta_charge*alpha-lambda        [1/h]
    B=eta_charge*beta                [MW]

For duration d in hours, phi=expm1(k*d)/k and psi=(phi-d)/k:

    E1 = E0*exp(k*d)+B*phi
    integral_E = E0*phi+B*psi         [MWh*h]
    heat = alpha*integral_E+beta*d
    compressor = S/a*(L0*d+integral_E/C)
    source = S*d
    standing_loss = lambda*integral_E
    charge_loss = (1-eta_charge)*heat
    E0+source+compressor = E1+standing_loss+charge_loss

At k=0, phi=d and psi=d²/2. A series for psi near0 avoids cancellation.
The component rejects a regime crossing rather than clipping a trajectory.
For this scalar affine ODE the solution is monotonic or stationary. The tank
branch and every limiter inequality are affine in E, so endpoint checks certify
the entire interval within this restricted regime. This proof does not apply to
general source/temperature trajectories or a multi-mode controller. Negative k,
zero k and small positive/negative k are tested separately.

## Actual saved-v52 audit and proposed handoff

The saved v52 guard requires condenser>=tank_max even while charging a cold
tank. Feeding a physically admissible instantaneous coupled condenser below
tank_max must reject. That is an unsupported new interface, not a regression
within accepted v52 scope. Above that guard, its planner/runtime COP use held
condenser and a held heating factor. A cooling-factor convention requires
etaH(E)=(lift(E)+a)/Tc_K(E); freezing etaH during temperature changes is an
additional approximation. The current trace cannot represent continuously
varying HP power while retaining its constant-port analytic TES equation.

The harness executes one cold rejection and four high-tank charging experiments
using1,2,4,8 externally restarted macro chunks over the same0.05h. Each chunk
recomputes its saturation temperatures and heating factor at the carried energy
and preserves actual HP clock/latch memory. Original SimulationOutputs and MAT
reopens are retained. These are held-input control approximations to the exact
restricted ODE, not continuous Stateflow coupling or solver-clock events.
Independent70-digit equations and an independently programmed RK4 integration
verify the propagator and actual sampled port/energy/clock evidence. Reviewer
mutation checks are reported separately; same agent, no independent personnel.

Next implementation must be additive: explicit circuit topology, energy-linked
condenser/factor/flow constraints, event splits at the max-temperature branch and
active-limit changes, conservative HP integrals, finite-boiler demand service,
cutoff/restart/dwell memory and padding protocol. Derive all limiter regimes
before building a new saved Stateflow release; preserve v52/v53 controls and
avoid another unchanged annual matrix. General dispatch, actual UA/hydraulics,
standalone generated code, primary calibration and physical validation remain
open. This single-regime component is not a complete coupled plant model.
