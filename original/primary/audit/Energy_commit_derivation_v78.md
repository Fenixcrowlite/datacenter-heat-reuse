# Candidate energy and flow monitor v78

This is an engineering consistency contract for the existing reduced thermal
model, not a newly verified paper equation or equipment calibration. Release
0.78 preserves the v75 kernel, trace schema 75 and v76 reporting interface.
The new embedded monitor calls the unchanged v77 temporal monitor, then checks
the completed candidate before either trace emission or retained-memory commit.
Both entry and during actions of every required mode call it.

For each positive segment, HP heat power equals direct service plus charge;
held demand equals direct plus TES discharge plus backup plus unmet power.
Flows are nonnegative, charge/discharge are mutually exclusive, and HP, TES
port and boiler capacities hold. The HP latch constrains HP power. Final mode
priority is unmet, backup, discharge, charge, direct recovery, idle.

The inventory equation is dE/dt = eta_c Q_charge - Q_discharge/eta_d - lambda E.
The forcing record must match eta_c Q_charge - Q_discharge/eta_d. For duration
hull d, heat=(direct+charge)d, service=(direct+discharge+backup)d,
backup=Q_backup d and missing=Q_unmet d. Charge loss is (1-eta_c)Q_charge d;
discharge loss is (1/eta_d-1)Q_discharge d. Auxiliary electricity equals the
configured multiplier times compressor electricity. Heat must overlap the sum
of recovered source and compressor electricity, under interval uncertainty.

The segment first law is
E_start + heat + backup - service - E_end - standing - charge_loss - discharge_loss = 0.
The cumulative first law uses the bound initial inventory and cumulative
energies. Both interval residuals must contain zero. Every energy hull must
be nonnegative and ordered. Segment offsets, interval totals, cumulative totals,
origin and stored residual are reconstructed and bound to the candidate.
Units are MW for port powers, h for duration and MWh for inventory/energy.

Deterministic binary64 consistency uses the existing outward operator with two
eps on each side and exact zero/cancellation identities. Equality binds copies
of operations, not physical accuracy. The independent Fraction reviewer checks
exact operand enclosure arithmetic without emulating that operator. A separate
120/160-digit exponential/logarithmic reviewer checks full nonlinear TES/event
trajectories, source/work integrals and energy totals without MATLAB calls.

The planned harness freshly simulates six modes, variable holds, stop/cutoff/
restart and repeated cycles. Every valid output must match fresh saved v77
execution. Unsaved chart copies inject isolated post-kernel candidate faults:
v77 temporal monitoring accepts them, v78 must reject each with its specified
energy assertion, and the monitor-bypass trace must reproduce the exact fault.
These are instrumentation controls, not physical plant trajectories. The clean
saved v78 artifact is reopened and rerun after instrumentation. Original MAT
is reopened by MATLAB and exported as binary64; Python is not an independent
MAT parser or independent personnel.

The monitor establishes candidate consistency, not proof against coordinated
replacement or all nonlinear physical/event inequalities. Source/work interval
overlap is necessary, not sufficient physical validation. Standing loss is
checked by balance here and independently by the nonlinear closed-form lane.
Synthetic normal-mode implementation only; calibration, annual performance,
primary article replication, measured validation and generated code remain open.
