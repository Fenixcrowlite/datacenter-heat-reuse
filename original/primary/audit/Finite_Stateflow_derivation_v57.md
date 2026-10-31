# Compiled finite-water Stateflow boundary v57

This is an additive executable implementation of the previously host-only v53
interface. It preserves v52's dispatch, canonical TES endpoints, HP supervisor,
physical-hour dwell checks, and fixed tank capacity/cutoff. It does **not** solve
the continuous tank-linked charge/event endpoint blocker documented in v56.

## Evidence and scope

All topology, heat-capacity rates, efficiencies and test inputs are synthetic
engineering assumptions. No primary article was retrieved or newly verified in
this run. Inherited primary signoffs remain 0/31; this is neither article
replication nor measured physical validation. Saturation temperatures and water
temperatures have separate ports. No UA, hydraulics, minimum-flow law, equipment
map, standby load or pump calibration is inferred.

The macro input is the ordered v53 boundary vector (16 fields) followed by
demand. The From Workspace block holds each vector without interpolation.
Source/hot water temperatures, approaches, capacity rates, cooling factor and
auxiliary ratio may change at the next macro boundary. Within a macro interval
they are fixed. Tank maximum, cutoff, heat capacity and ambient reference are
frozen per simulation; attempts to redefine them through the input reject.
Condenser temperature supports the specified maximum tank temperature throughout
the interval. It is not computed from evolving TES energy.

## Independent derivation

Temperatures are in degrees C, differences in K. Define source glide gL > 0,
evaporator approach aL >= 0, condenser approach aH >= 0, charge approach aC >= 0,
direct approach aD >= 0 and discharge approach aS >= 0. Then

```
source_out = source_in - gL
evap = source_out - aL
hot_out = max(tank_max + aC, delivery + aD)
cond = hot_out + aH
cutoff = delivery + aS
gH = hot_out - hot_in > 0
TL = evap + 273.15; TH = cond + 273.15
EER = cooling_factor * TL / (cond - evap)
COP_H = 1 + EER
eta_H = ((cond - evap) + cooling_factor*TL) / TH
```

The conversion follows QH = QL + W, so COP_H = EER + 1. With heating Carnot
COP TH/(TH-TL), eta_H is COP_H divided by that bound. It lies in (0,1] when
0 < cooling_factor <= 1 and TH > TL > 0. The heating-side planner receives
eta_H, zero part-load penalty, and bounds that contain this COP without clipping.

Let CL and CH be maximum water heat-capacity rates in MW/K. The source budget is
CL*gL, hot budget is CH*gH, and effective heating capacity is the lesser of the
hot budget and nameplate capacity. For any authorized request R >= 0,

```
QH = min(R, nameplate, CH*gH, CL*gL*COP_H/(COP_H-1))
W = QH/COP_H
QL = QH-W
required_CL = QL/gL
required_CH = QH/gH
```

These are feasibility constraints for variable flows, not a finite-UA exchanger
solution. Actual segment outputs, not rated capabilities, determine required
water rates and energy totals.

TES energy is relative to the fixed ambient temperature: E = C*(Ttank-Ta),
capacity = C*(Tmax-Ta), cutoff_energy = C*(cutoff-Ta). For each physical segment
of duration tau hours and fixed charge/discharge powers qc, qd,

```
P = eta_charge*qc - qd/eta_discharge
dE/dt = P-lambda*E
Eend = Ebegin*exp(-lambda*tau) + P*(1-exp(-lambda*tau))/lambda
```

The lambda=0 limit is Ebegin+P*tau. Inherited v52 uses expm1 for the integration
kernel and a canonical endpoint protocol, with a declared 64-ULP normalization
budget. Strict zero-span padding and exact energy handoff remain unchanged.
Independent review allows 72 ULPs for endpoint comparison to exact-input
80-digit arithmetic, as in the accepted v52 protocol. It does not enlarge
production tolerances or authorize a discrete coupled-branch crossing.

Auxiliary electricity is assumed proportional to compressor electricity and
is fully rejected to the environment: A = aux_ratio*W. The expanded per-segment
first law, integrated in MWh, is

```
Ebegin + (QL + W + A + boiler - delivered)*tau
       - Eend - standing_loss - charge_loss - discharge_loss - A*tau = 0
```

There is no auxiliary heat credit to demand or TES. Nonzero hot-credit input
rejects in the compiled boundary. The accounting trace records compressor,
auxiliary, rejected auxiliary and total electric energies, residual, and maximum
required source/hot capacity rates. Auxiliaries do not alter dispatch decisions.

## Execution and QA requirements

The builder creates a new SLX and refuses to overwrite a saved version. Two
actual Stateflow charts execute guarded thermal modes and persistent HP latch/
clock updates. The new boundary and accounting blocks are compiled MATLAB
Function blocks. The analytic segment planner remains a normal-mode host
extrinsic; standalone generated-code deployment is not accepted.

The acceptance harness executes the six required modes, finite-approach and
limiter scenarios, multi-interval mode/dwell sequences, changing water inputs,
and twelve actual runtime faults including a delayed fault. Representative
physical outputs compare with verified MATLAB simulate_dispatch_v30, excluding
only its attempted-request diagnostic (column 22) when the HP is OFF.

Independent Python QA imports no production implementation. It reads row-major
little-endian binary64 exports produced from reopened original MAT files, checks
80-digit boundary/HP/TES/service/auxiliary equations, exact padding/handoff,
exact Fraction dwell authorization and clock increments, model contents,
source hashes and preservation. Synthetic reviewer mutations are counted
separately. This is independent algorithmic QA by the same agent.

The continuous tank-linked model remains a separate acceptance target: bounded
propagated endpoints, one-sided equality protocol and variable-power compressor/
source integrals are still required before its coupled planner is integrated.
