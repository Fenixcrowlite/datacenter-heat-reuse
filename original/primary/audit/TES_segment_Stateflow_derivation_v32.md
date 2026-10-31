# v32: executed segment dispatch with separate HP operating points

This implementation follows the executed v31 event-comparison handoff. Existing
v14/v24/v28/v30 saved models and immutable evidence are retained. Project STATUS,
MASTER_STAGEBOARD, acceptance contract, frontier, progress and relevant production
and independent-reference sources were read before changes. No unrelated project
or Jarvice file is accessed or edited.

## Evidence and assumptions

Inherited article evidence is restricted to Cadau (2019), DOI
10.3390/en12224275, article p4 Eq (4), the ambient heat-transfer term. The verified
primary-text record and PDF hash remain in `TES_standing_loss_primary_v28.md`.
Its stratified multi-node plant is not reproduced here. The v31 primary engineering
documentation check of the EnergyPlus 9.5 mixed-tank energy balance and target-time
inversion is inherited, not a newly verified article equation. All numerical
fixtures, constant ambient/heat capacity/loss coefficient, reservoir temperatures,
HP screening map and capacity/cutoff control decisions are engineering assumptions.
No new article result, parameter calibration or primary signoff is claimed.

Newly consulted primary software documentation on 2026-10-09:
[MathWorks For Iterator](https://www.mathworks.com/help/simulink/slref/foriterator.html)
and [iterator execution](https://www.mathworks.com/help/simulink/ug/iterate-subsystem-execution.html).
The subsystem repeats execution **within the current simulation timestep**.
Accordingly v32 records analytic physical offsets and durations, and executes
Stateflow once for each of two ordered segments at the macro sample's Simulink
clock time. It does not claim solver-clock activations at the analytic event times.
The local MATLAB API probe verifies installed version/license and actual iterator
parameters; its original failed library-path probe is retained.

## Segment physics and scheduling

For ambient-referenced energy A [MWh], net internal held power
P=etaC*Qc-Qd/etaD [MW], loss coefficient lambda [h^-1] and span s [h],

`A_next=A*exp(-lambda*s)+P*phi(s)`;
`phi=-expm1(-lambda*s)/lambda`, with phi=s at lambda=0.

Standing loss is `A*(1-exp(-lambda*s))+P*(s-phi)` MWh. The external
inefficiency integrals are `(1-etaC)*Qc*s` and `(1/etaD-1)*Qd*s`. Temperature
is `Ta+A/C`, C in MWh/K. Capacity M and delivery cutoff Ac are distinct.
The v31 log1p event kernel sets the first span at the earlier capacity/cutoff
boundary or interval end. Its independent oracle finds that boundary by
60-digit Decimal trajectory bisection. At capacity, the second HP request is
`D+min(chargeLimit,lambda*M/etaC)`; at cutoff, discharge is disabled and the
remaining store cools. Ports are nonnegative and mutually exclusive.

Before a boundary, the HP request is D+chargeLimit (at initial capacity use the
loss-replacement request immediately). HP output Q is bounded by that request,
condenser capacity and available evaporator heat. Its part-load COP is the v14
screening relation `COP(Q)=nominal*(1-penalty+penalty*Q/capacity)` above the
operating cutoff, with heat/electric/source closure `Q=W+Qev` and W=Q/COP(Q).
The host planner re-evaluates HP for the capacity tail. If that operating point
is unavailable or source-limited, charge can fall below loss replacement: the
store cools, and the controller waits for the next macro input sample to
redispatch. It does not invent sustained capacity hold or implement instantaneous
restart/cycling. A fixture explicitly exercises unavailable low-load hold.
This sampled fallback can depend on macro timestep; no universal partition
invariance or event-policy superiority is claimed.

For each executed segment j:

`direct_j=min(D,Q_j)`;
`gas_j=min(B,max(0,D-direct_j-Qd_j))`;
`unmet_j=max(0,D-direct_j-Qd_j-gas_j)`.

The six-state chart selects and authorizes ports separately for both segments.
The runtime gate independently checks segment ODE, losses, bounds, mode, COP,
condenser allocation, demand service and first laws, then integrates totals.
Energy is carried between macro samples through an outer Unit Delay. The chart
stores both segment outputs in a fixed 50-element trace; the zero-duration
second slot has no service. Positive-duration segments alone define coverage.

Interval powers are integrated energies divided by h. Electricity is
`sum(Q_j/COP_j*s_j)/h`; it is not evaluated using average condenser power.
Reported interval COP is `sum(Q_j*s_j)/sum(W_j*s_j)` when electricity is positive,
otherwise undefined. Interval Mode is the highest executed service condition;
individual chart modes remain in the segment trace. No average mode or average
power is used to authorize ports. With finite B, calculating gas/unmet from
average TES power is invalid, as the inherited v31 timing counterexample shows.

## Verification boundary

Independent Python specification reuses only independent v30/v31 Python oracles:
analytic source-constrained HP root, Decimal event-root bisection and temperature
RK4 equation checks. It imports no production MATLAB code. Actual saved-v32
simulations, positive-duration modes/transitions, MATs and numeric CSVs are tested,
and representative scenarios freshly execute the preserved v30 reference.
The read-only exporter reconstructs outputs/diagnostics from saved MATs separately
from the harness; the reviewer inspects saved SLX XML and source/hashes. Actual
domain, delayed-domain and in-memory allocator corruption runs test runtime
rejections. Synthetic reviewer corruptions are reported separately. Independent
algorithm/evidence QA is not a separate human/agent review or physical validation.

Remaining model scope: normal-mode host HP; no standalone code generation,
hydraulics, stratification, calibration, time-varying ambient, sensor/equipment
faults, hysteresis, minimum dwell, cycling, pumping/fuel/exergy or annual-system
integration. A macro sample at StopTime represents a complete following interval.
Full primary article signoffs remain 0/31. Executed counts and failures belong to
the timestamped acceptance and QA reports; this derivation alone is not acceptance.
