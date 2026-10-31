# Temperature-conditioned compressor comparator v84

This checkpoint executes the preserved v83r2 Stateflow artifact. It does not
implement or accept a temperature-conditioned Stateflow controller. The new
comparator is an independently derived synthetic engineering experiment.
No new primary paper text, coefficients or equipment rating is claimed.
The evidence limits in HP_approach_derivation_v82.md still apply.

Use the exact binary policy operands, including the binary operand 273.15:

    Te = source_temperature - source_drop - evaporator_approach
    A = eta_cooling*(Te + 273.15)
    L(E) = max(Tfloor, Ta + E/C + water_rise) + condenser_approach - Te
    W(q,E) = q*L(E)/(A+L(E))
    q_electric(E) = Pmax*(1 + A/L(E))

For A>0, L>0, W is linear and increasing in q. Hence q_electric is the
unique electrical boundary. In a constant-temperature service case the
admissible maximum is min(demand, thermal_limit, water_limit,
source_floor_limit, q_electric). The source_floor_limit is the retained
kernel's conservative allocation rule, not a newly optimized source rule.
We test cases where the electrical boundary is strictly below all other
limits and demand. Charge, TES discharge, boiler and passive losses are
disabled for these cases. Then service=q*t, work=Pmax*t, source=(q-Pmax)*t.
The colder state gives more service AND more recovered source with more
compressor work; no equal-electricity efficiency claim is made.

For charging-only cases lambda=0, initial HP ON, backup/discharge disabled,
and q_electric below charge/thermal/source/water limits:

    dE/dt = eta_charge*Pmax*(1+A/L(E)).

Below the hot-water floor L=Lf, so inventory rises linearly. The floor
crossing is E*=C*(Tfloor-Ta-water_rise). Above it, put
b=Ta+water_rise+condenser_approach-Te and L=b+E/C. Separation gives:

    t-t0 = C/(eta_charge*Pmax) *
           [L-L0 - A*log((L+A)/(L0+A))].

The derivative of the bracket is L/(L+A)>0, so there is one endpoint.
A high-precision Decimal Newton inversion evaluates this equation; a
separate fixed-step RK4 calculation of the original ODE checks it at 1024
and 2048 steps. Floor-crossing time is explicit, and RK4 integrates each
side separately. Total heat=(Eend-E0)/eta_charge, work=Pmax*t,
source=heat-work. Charging loss=(1-eta_charge)*heat. Thus first-law closure
is derived independently, including efficiency losses. No stored heat is
reported as delivered district service.

Predeclared scopes: six required saved-model modes, one nonbinding saved-v80
reference, an interior-event history, and service/charging cases at initial
inventories 3, 4.95 and 8.5 MWh with approach pairs (1,1) and (10,10) K.
Each experiment has identical raw policy, initial conditions and four
0.25-hour held inputs for actual global-cap and hypothetical dynamic paths.
Comparisons reconstruct actual trajectory from original-MAT binary exports,
never a reported hull midpoint. 120/160-digit results must agree to 1e-100
relative; closed-equation inversion residual must be below 1e-110 at 120
digits. RK4 endpoint agreement budget is 1e-10 MWh and fine-step error must
not increase beyond 1e-12 MWh floating arithmetic noise. These are comparator
QA budgets, not relaxed production guards.

Every dynamic path must remain below the TES stop threshold, within tank
bounds, below all other power limits, source-feasible and electrically
feasible. Otherwise the fixture fails: this comparator has no stop/restart,
positive-loss or mixed service/charge event implementation. Inherited actual
Stateflow event QA remains separate. Algorithmic independence is same-agent;
MATLAB reopens MAT and exports binary, not an independent MAT parser or
independent-personnel validation. All values are synthetic, not calibrated
equipment, annual performance, generated-code acceptance or physical validation.
