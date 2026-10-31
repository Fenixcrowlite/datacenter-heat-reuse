# v33 capacity fallback audit and restart-policy handoff

Checkpoint v33 executes the preserved accepted **model v32**. No new SLX, changed
plant controller, article replication or measured validation is claimed. Status,
stageboard, acceptance, frontier, primary TES audit and relevant production/oracle
code were read first. Fixtures are engineering assumptions in MW, MWh and hours.

## Evidence provenance

Inherited verified primary article evidence: Cadau (2019), DOI
10.3390/en12224275, p4 Eq (4), ambient heat-transfer term; local PDF/hash/locators
remain in `TES_standing_loss_primary_v28.md`. Its stratified plant is not reproduced.
Full primary article signoffs remain 0/31. No new paper values/equations are adopted.

Primary engineering documentation reopened 2026-10-10:
[EnergyPlus 9.5 mixed thermal tanks](https://bigladdersoftware.com/epx/docs/9-5/engineering-reference/water-thermal-tanks-includes-water-heaters.html),
Mixed Water Thermal Tank / Energy Balance and Water Heater Control Algorithm.
The page gives the constant-coefficient temperature ODE, its exponential solution
and inverse target-time calculation. It describes cycling versus modulation and
piecewise integration as control conditions change. This supports the mathematical
method, not our HP screening map, tank parameters or selected dwell times.

[MathWorks temporal logic](https://www.mathworks.com/help/stateflow/ug/using-temporal-logic-in-state-actions-and-transitions.html),
Define Time Delays / Best Practices: discrete actions occur at solver sample
instants; absolute-time delays use elapsed simulation time while tick delays count
chart awakenings. Retrieved page identifies R2026b; installed runtime is separately
observed as R2026a. No new temporal API is executed or version equivalence asserted.
In v32, iterator activations share one solver timestamp while analytic segments
carry physical durations. Counting two iterator ticks as two elapsed physical
intervals would be incorrect. Future dwell must accumulate accepted segment
durations explicitly, or use a verified solver-time scheduler with consistent units.
Current model numeric solver time is interpreted as hours by the experiment;
`after(...,sec)` cannot be added without resolving that hours/seconds convention.

## Mechanism to test

Define E as ambient-reference TES energy, M as capacity, lambda as loss coefficient,
etaC/etaD as port efficiencies, D as demand, B as finite backup. For a held segment,
`E'=P-lambda*E`, `P=etaC*Qc-Qd/etaD`. For lambda>0 set A=P/lambda:

`E(t)=A+(E0-A)*exp(-lambda*t)`.

v32 normally requests HP heat `D+chargeLimit`. At capacity it reduces request to
`D+min(chargeLimit,lambda*M/etaC)`. Its screening COP is
`C(Q)=alpha+beta*Q`, alpha=nominal*(1-penalty), beta=nominal*penalty/HPcapacity.
When beta>0, minimum admitted load is `Qmin=max(0,(COPmin-alpha)/beta)`.
If the reduced request is below Qmin, HP becomes unavailable.

With M=10, lambda=.1, etaC=.9, chargeLimit=3, D=3, nominal=4, penalty=.3,
HPcapacity=8, COPmin=3.5: alpha=2.8, beta=.15, Qmin=4.6666667 MW.
High request 6 MW is feasible (COP=3.7, required source=6-6/3.7 MW < 6 MW).
Capacity request 4.1111111 MW is below Qmin. This is a mathematical cutoff in an
assumed screening map, not a manufacturer minimum compressor-load measurement.

Before capacity: internal power 2.7 MW, equilibrium A=27 MWh. For E0<M:

`tHit=log((27-E0)/(27-10))/.1`;
`on=min(h,tHit)`; `off=h-on`.

If off>0, v32's capacity tail has **both HP and TES discharge off**:
`E_next=10*exp(-.1*off)`; electricity `=(6/3.7)*on`;
backup energy `=.5*off`; unmet energy `=2.5*off`.
For off=0, `E_next=27+(E0-27)*exp(-.1*h)`.
This independent logarithmic recurrence is compared with both the independent
Decimal/bisection fixture and actual saved-model traces. At initial E=M the planner
instead enables 3 MW TES discharge when HP is unavailable. The branch difference
is explicitly exercised; after-capacity cooling must not be described as the
initial-capacity policy. Total first-law closure can pass despite preventable
service failure in the capacity tail.

## Source-limited hold: distinguish reachability from fallback

For admitted COP C>1, source extraction is `S(Q)=Q-Q/C(Q)` and
`S'(Q)=1-alpha/C(Q)^2>0`: alpha<=C, so alpha/C^2<=1/C<1.
Thus a feasible higher HP output implies sufficient source for every lower
**admitted** output under the same source/temperature/map conditions.
Reaching capacity by charging requires etaC*Qc>lambda*M. Consequently, a reduced
loss-replacement operating point cannot become source-limited following a
reachable capacity event with constant inputs if it remains in the admitted
domain. It can lose availability at the part-load cutoff. Source shortage at an
initial capacity state can cause cooling; source changes between samples are a
separate case. Do not infer a reachable source-limited capacity tail from an
initial-capacity cooling fixture.

The constant-COP source-limited fixture has source=.5 MW, COP=4, HP heat=2/3 MW,
etaC=.9, demand=0. Internal power=.6 MW, equilibrium 6 MWh:
`E(t)=6+(10-6)*exp(-.1*t)`. It never reaches capacity again. Passive and feasible
modulation controls distinguish this smooth cooling from low-load cutoff pulses.

## Derived candidate hysteresis and dwell constraints

These are design equations for a **future controller**, not executed v33 control.
Let HP ON use an admitted feasible heat Qon and charge surplus Qc; require
Pon=etaC*Qc>lambda*M so Aon=Pon/lambda>M. Let HP OFF serve demand from TES at
constant feasible Qd, giving Poff=-Qd/etaD and Aoff=Poff/lambda<=0. Define restart
energy R with cutoff<R<M. Then

`tOn=log((Aon-R)/(Aon-M))/lambda`;
`tOff=log((M-Aoff)/(R-Aoff))/lambda`.

For assumed minimum physical dwell Ton, Toff:

`R <= Aon+(M-Aon)*exp(lambda*Ton)`;
`R <= Aoff+(M-Aoff)*exp(-lambda*Toff)`.

Both are energy upper bounds, not arbitrary percentage SOC deadbands. Feasibility
requires the smaller bound to exceed cutoff and require admissible Qon/source,
port limits and nonnegative finite dwell. At lambda=0 with positive Pon and
negative Poff, replace them with `R<=M-Pon*Ton` and `R<=M+Poff*Toff`.
Zero loss and zero off draw never naturally reach a lower restart threshold;
zero/nonpositive ON net charging power cannot support the proposed cycle.

Illustration only: Qon=6 MW, Qd=3 MW, etaD=.8 and Ton=Toff=.25 h.
The constraints yield R<=9.569642951 MWh and R<=8.827220821 MWh. Choosing the
smaller gives tOn=.667114809 h and tOff=.25 h, above cutoff=5 MWh. Separate RK4
integration checks both endpoints. These times are deliberately assumed; they
do not represent calibrated hardware requirements or prove economic superiority.

Future supervisor must persist HP ON/OFF latch and accumulated physical dwell
across macro samples, distinct from the six instantaneous service modes. OFF
service must allocate TES/backup/unmet at every segment and stop TES at cutoff.
Capacity/cutoff safety and input-domain failures take precedence over dwell;
changing source/demand may invalidate a previously feasible cycle. Two segment
slots cannot represent arbitrary multiple ON/OFF cycles in a coarse interval.
Add a bounded multi-event integrator with explicit failure on exhaustion, or a
verified smaller-step scheduler; never silently truncate events. Prove invariance
of physical timers and service across tested partitions, including exact-capacity
initialization, input changes and finite backup. Do not use HP-off tail cooling
as a complete dwell controller.

## Acceptance boundary and next task

Executed counts/results belong to the timestamped v33 QA, results report and status.
v32's six-mode/domain/corruption acceptance is inherited and preserved; targeted
v33 simulations do not repeat or expand that fault coverage. Independent algorithm
and artifact review is not separate human/agent review or physical validation.
Normal-mode host planner, constant-coefficient mixed store, reservoir temperature
proxies and uncalibrated HP screening remain. Sensitivity is a finite four-hour
assumed fixture sweep, not an annual optimum or universal controller comparison.

Next: implement additive model v34 with persistent HP hysteresis/dwell supervisor,
physical-duration timers, TES service during HP OFF and enough event slots. Retain
v32 as the counterexample baseline and execute the independent recurrence,
cutoff/finite-backup and clock/unit tests before declaring controller acceptance.
