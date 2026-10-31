# Exact-state protocol verification for resumed v52 acceptance

The saved v52 candidate predates this run. Its acceptance was unfinished. All
earlier models, partial execution evidence and failed v51 runs are preserved.
This run completes execution in a new timestamped folder; it does not claim
to have rebuilt the candidate.

For held net tank power P = eta_charge Q_charge - Q_discharge/eta_discharge,
the reduced model is dE/dt = P - lambda E. Independent integration gives
E(t) = E(0) exp(-lambda t) + P (1-exp(-lambda t))/lambda, with the lambda=0
limit E(0)+Pt. Integrated standing loss is E(0)+Pt-E(t). Units are MWh, MW
and hours. These are derived engineering equations, not article replication.

The existing endpoint kernel normalizes a positive integration result within
64 eps(max(1,capacity)) of capacity/cutoff. That bounded floating-point
correction is left in the first-law residual, not booked as physical loss.
Zero duration remains exact state identity with zero ports/loss/residual.

The added exporter reopens original SimulationOutputs and asserts exact
planner-target/allocated-end equality, exact planner-start/allocated-start
equality and exact consecutive energy handoff for all 64 slots. Positive-span
start, end, target, charge, discharge, duration, standing loss and residual
are exported as hexadecimal IEEE-754 doubles.

The independent Python reviewer decodes those doubles and evaluates the ODE
at 70-digit Decimal precision without importing production dispatch code.
Its equation-error budget is 72 ULPs at capacity: 64 for the existing bounded
normalization and eight for comparing floating-point evaluation with exact
arithmetic. This is an explicit scoped audit criterion, not a universal error
bound. The measured maximum errors are recorded. Exact target equality and
capacity/cutoff event identity use no tolerance. Separate one-ULP and material
equation-error self-checks demonstrate sensitivity; they are not simulations.

This review supplements the inherited independent per-segment HP/port/ODE,
dwell, annual-report and exact-padding QA. It is independent algorithmic QA
by the same agent, not separate personnel or calibrated physical validation.
