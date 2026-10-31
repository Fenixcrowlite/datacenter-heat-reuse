# Explicit annual Stateflow boundary — v49

This additive input adapter targets the preserved actual saved v42 model. It
does not create a new controller or SLX. Every parameter here is a synthetic
engineering assumption or deduction from project code. No paper equation,
equipment calibration or measured validation is claimed.

The fixed well-mixed tank stores ambient-referenced sensible energy:

    E = C (T - Ta), C = K/(Tmax-Ta), Ec = C(Tcut-Ta).

E and K are MWh, C is MWh/K; temperatures are degrees C and temperature
differences are K. The model requires Ta < Tcut < Tmax, delivery <= Tcut,
condenser >= Tmax and condenser > source. Delivery means the original weather
dependent network supply temperature, not its lower return temperature.
Its original 55–80C seasonal condenser schedule cannot satisfy a fixed tank
whose cutoff supports 80C supply. In general a direct variable schedule requires

    max(delivery) <= Tcut < Tmax <= min(condenser).

When delivery and condenser are the same varying schedule, max(schedule) is
greater than min(schedule). A direct mapping is unsupported even before event
dispatch; the adapter retains every row rejection and never lowers the delivery
requirement silently. V49 admits a separately specified fixed 85C condenser,
85C tank maximum, 80C cutoff and 20C ambient. For K=50 MWh, C=50/65 MWh/K,
Ec=600/13 MWh and restart=48 MWh. Usable discharge inventory above cutoff is
only 50-600/13=50/13 MWh, not the full nominal 50 MWh. Initial E=0 is below
cutoff and is allowed: the tank must be heated before it can discharge.

The annual source and demand remain the default deterministic engineering
profiles. Source is IT power times capture fraction, then HX efficiency/cap,
with the configured approach deducted from reservoir source temperature.
Network demand includes the existing network-efficiency factor. Upstream PUE,
pumping electricity, refrigerant/HX pinch and calibrated equipment maps are
outside this adapter. The fixed condenser increases lift relative to v48's
original weather schedule and is explicitly a changed boundary.

Minimum HP ON and OFF dwell are both 0.25 physical hours. The initial clock is
ON at zero elapsed age. Capacity/safety overrides and persistent clock bounds
retain the exact saved v42 semantics. Static preflight invokes its physical
input validator at every row; this cannot certify a trajectory-dependent event
budget or clock guarantee. Actual simulation and independent trace QA supply
those checks for the executed scenario.

To match passive loss-first retention (1-ell dt) without claiming identical
active-port physics, lambda = -log(1-ell dt)/dt. At ell=1e-4 per hour and dt=1h,
lambda=-log(0.9999) per hour. For held net internal power
P=etaC*charge-discharge/etaD, actual Stateflow integrates

    E(t) = E0 exp(-lambda t) + P(1-exp(-lambda t))/lambda.

The independent checker evaluates this with 60-digit Decimal exponentials,
using the linear limit when lambda=0. It checks every positive segment and
capacity/cutoff event, continuity, temperature, instantaneous limits and
integrated macro balance. Dwell QA sums physical spans independently of the
production clock and examines latch changes. The production monitor itself
retains compensated-clock uncertainty-aware transition guards.

HP heating COP is C(Q)=C0*(1-r+rQ/H), with reservoir proxy C0 bounded above
by the selected maximum. Its source constraint Q-Q/C(Q)<=S gives the positive
quadratic root used by preserved independent v48 Decimal QA. No production
bisection/planner is called by the Python checker. Off COP is undefined.

    E0 + integral(source_used + electricity + gas - delivered) dt
        - E1 - standing_loss - charge_loss - discharge_loss = 0.

Delivered heat is direct HP plus TES discharge plus boiler; unmet is excluded.
Reports integrate the actual ports and compare costs/emissions at equal
delivered service. Paired v48 MATLAB execution uses the same fixed 85C HP
condenser and source/demand, with its loss-first TES and no temperature cutoff
or hysteresis/dwell. Differences combine usable inventory, exact active-port
loss and controller policy; they must not be called numerical integration error
or attributed to one cause without matched sensitivity experiments. Initial/
terminal inventory provenance/value and auxiliaries remain unaccounted for.

The v49 engineering boundary is limited to weather-scheduled delivery and the
Carnot HP backend. Unsupported backends/boundaries are rejected explicitly.
Annual dispatch is not an economic optimum or physical/paper validation.
