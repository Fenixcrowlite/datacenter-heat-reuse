# v34 HP hysteresis and physical-hour event model

This is an engineering controller for the assumed mixed TES/HP screening plant.
The existing STATUS/stageboard v33, research STATUS/stageboard v25, acceptance,
research frontier, primary TES audit and relevant MATLAB/oracle code were read
before edits. Model v14/v24/v28/v30/v32 and earlier evidence remain preserved.

## Evidence and assumptions

Inherited relevant primary text is Cadau (2019), DOI 10.3390/en12224275, PDF p4
Eq (4), ambient term `-UA(T_i-T_amb)`, documented with the local source hash and
locators in `TES_standing_loss_primary_v28.md`. Its stratified implementation is
not reproduced. The lumped constant-coefficient reduction, port efficiencies,
HP screening map, restart band and dwell values are engineering assumptions.
No new paper equation, measured value, article replication or full signoff is
claimed. Full primary signoffs remain 0/31.

Primary engineering documentation inherited from v33 is EnergyPlus 9.5
[mixed water thermal tanks](https://bigladdersoftware.com/epx/docs/9-5/engineering-reference/water-thermal-tanks-includes-water-heaters.html).
Its held-coefficient ODE, inverse target time and piecewise control integration
support the method, not project parameter calibration. MathWorks
[diagnostic diary](https://www.mathworks.com/help/simulink/slref/sldiagviewer.diary.html)
was checked during this run and executed in installed R2026a to capture the
initial indexing compile defect. This is API evidence, not physical evidence.

## Equations and units

Ambient-reference energy E is MWh, port power is MW, and all segment durations,
elapsed ages and dwell parameters are **physical hours**. For constant ambient,
heat capacity, losses and held powers, `E'=P-lambda*E`, where
`P=etaC*Qc-Qd/etaD`, lambda is h^-1. Hence

`E(h)=E0*exp(-lambda*h)+P*(1-exp(-lambda*h))/lambda`.

At lambda=0 use `E(h)=E0+P*h`. The integrated standing loss is
`L=E0+P*h-E(h)`. Port conversion losses are
`Lc=(1-etaC)*Qc*h`, `Ld=(1/etaD-1)*Qd*h`.
TES closure is `E0+(Qc-Qd)*h=E(h)+L+Lc+Ld`.
HP closure is `Qhp=Welectric+Qsource`; service closure is
`D=Qdirect+Qdischarge+Qbackup+Qunmet`.

For a reachable target Et, lambda>0, solving the energy expression gives
`t=log1p(lambda*(Et-E0)/(P-lambda*Et))/lambda`.
At lambda=0 use `(Et-E0)/P`. The production planner uses this logarithmic form;
the independent Python specification instead brackets the monotonic energy
trajectory and bisects it with 60-digit Decimal coefficients. Separate RK4
integration verifies endpoints and integrated loss. A closed periodic recurrence
additionally verifies the low-load cycle without the generic event algorithm.

## Executed policy specification

Control vector is `[restart_MWh,minOn_h,minOff_h,maxPositiveSegments]`.
Require cutoff < restart < capacity, finite nonnegative dwell, and integer
event budget from 1 to 64. HP state `[ON,elapsed_h]` persists across macro samples.
HP ON normally requests `D+chargeLimit`. At capacity its feasible request is
`D+min(chargeLimit,lambda*capacity/etaC)`.

An ON mode that can charge through capacity cycles OFF at capacity once its
minimum ON age has elapsed. If it reaches capacity earlier, it holds using the
feasible reduced request until ON dwell expires. If that request is unavailable,
or changed inputs make the active request unavailable, it turns OFF immediately:
physical capacity/input feasibility overrides minimum ON dwell. Therefore ON
dwell is a conditional operating constraint, not an unconditional guarantee.
OFF dwell remains binding. OFF serves TES up to its discharge limit whenever
energy exceeds cutoff, then uses finite backup and records unmet heat.

OFF restarts when energy <= restart, elapsed OFF age >= minOff, and the high
HP request is available. Under held inputs the restart time is the later of
threshold crossing and dwell completion. Cutoff may occur first; then TES
discharge stops and passive cooling plus finite backup/unmet service continues.
Capacity, cutoff, restart and ON-dwell endpoints form a bounded multi-event
partition. Exhaustion rejects the whole interval explicitly; it never returns a
truncated trace. The 64-slot iterator pads unused slots with zero physical time,
flow and timer advancement.

Two actual Stateflow HP states authorize transitions and accumulate age by
`age += segmentDuration_h`; their clock output feeds a Unit Delay and the next
planner invocation. Six actual thermal states authorize the instantaneous ports
and independently integrate each analytic segment. A separate runtime monitor
checks state/flow, physical clock and energy continuity, capacity/cutoff bounds,
instantaneous boiler/HP/TES constraints and interval first-law closure. It rejects
actual allocation/clock corruption; saved SLX is never edited by fault injection.
The normal-mode host planner supplies screening availability and predicted event
schedule. This is an analytic co-simulation, not autonomous deployment code.

The iterator shares one macro solver timestamp. Physical events occur at the
logged offsets within the analytic interval; they are not separate solver-clock
events. No seconds-based `after(...)` logic is used. Replacing elapsed physical
duration with iterator ticks is deliberately injected and rejected in execution.

## Independent cycle anchor

For the v33 low-load assumed fixture: M=10 MWh, lambda=.1 h^-1,
etaC=.9, etaD=.8, HP ON output 6 MW (COP3.7), D=3 MW and backup=.5 MW.
ON internal power is 2.7 MW, equilibrium 27 MWh. OFF internal power is -3.75 MW,
equilibrium -37.5 MWh. Assumed Ton=Toff=.25 h gives the energy upper bounds
`Ron=27+(10-27)*exp(.1*Ton)` and
`Roff=-37.5+(10+37.5)*exp(-.1*Toff)`.
Their smaller value, 8.827220821 MWh, is the fixture restart threshold. It gives
steady ON .667114809 h and OFF .25 h. The first short ON from E0=9.9 cannot meet
Ton before capacity; its unavailable hold triggers the explicit safety override.
At E0=10 with age0 the same safety override enters OFF immediately.

The independent closed-cycle reviewer sums the initial ON leg, alternating
analytic ON/OFF legs and final partial leg. It compares end energy, physical
clock, HP electricity and TES service with actual saved-model traces. Six macro
partitions (4,2,1,.5,.25,.125 h) test the same four-hour held-input experiment.
These tests establish finite fixture invariance, not arbitrary input invariance,
economic optimality, actual compressor cycling counts or measured performance.

## Acceptance boundary

Executed counts, comparison numbers and pass/fail belong to the timestamped
acceptance summary, independent QA and v34 results/status records. Numerical QA
uses an independent algorithm, a separate closed recurrence, saved MAT re-export,
saved SLX graph/function bindings and previous immutable hashes. It is not a
separate human/agent review or physical validation. Synthetic reviewer challenges
are counted separately from actual model faults and traces.

Remaining limits: fixed mixed-store coefficients, reservoir temperature proxies,
no calibrated minimum compressor load/dwell, cycling startup losses, ramping,
hydraulic/network model, measured validation or standalone code generation.
The band requires positive usable TES capacity; zero-capacity or zero-width-band
control is rejected. Source/demand are held per macro interval; varying-input
partition equivalence requires preserving the same physical input timeline.
ON dwell can be overridden for safety. Host-planned HP infeasibility is trusted
as a screening result; this run does not add physical equipment/sensor faults.
Nonfatal Stateflow formal-argument shadow warnings are retained in logs.
