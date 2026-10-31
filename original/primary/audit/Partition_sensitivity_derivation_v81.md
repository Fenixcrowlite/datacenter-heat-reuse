# Held-input partition sensitivity on actual saved Stateflow v80

This is synthetic implementation evidence for the reduced engineering model.
No new SLX, controller repair, calibrated equipment or primary paper equation is claimed.

For constant forcing B (MW), loss lambda (h^-1), and inventory E (MWh),
the model uses E'=B-lambda E. Its exact flow is
E(t)=B/lambda+(E(0)-B/lambda) exp(-lambda t), or E(0)+Bt at lambda=0.
Therefore F(t+s,E)=F(s,F(t,E)) while forcing remains held. Source and work
integrals, standing losses and service also add over subintervals. Threshold
events and persistent dwell timers should preserve the same physical trajectory
when an unchanged hold is split. Extra protocol calls are not new physical inputs.

Experiments split every original hold into 1, 2, 4 and 8 equal dyadic pieces,
keeping demand, source capacity, HP/charge enable, policy and initial state fixed.
Exact Fraction checks verify that split durations sum to the original binary
duration and input histories match. Rounded cumsum labels follow the existing
adapter contract; they are not differenced to reconstruct durations.

Finite binary arithmetic and conservative power selection mean bitwise thermal
equality across different partitions is not a justified requirement. We compare
reported enclosures and independently reconstructed closed exp/log trajectories:
energy and inventory changes must fit 1e-10 times max(1, absolute quantity)
in their own units (MWh); corresponding event times have the same relative
budget in hours. These are experiment acceptance budgets, not production guard
tolerances. We separately report hull widths and overlap; no midpoint is treated
as an exact result. Width monotonicity is measured, not imposed: extra calls
can widen accumulated binary roundoff even as source quadrature tightens.

All original-MAT numeric arrays are reopened/exported by MATLAB and checked
against JSON and exact binary operands. Independent 120/160-digit closed
exponential/log solutions call no production MATLAB kernel or root finder.
Same-agent algorithmic independence is claimed; independent personnel and
independent MAT parsing are not. Unexpected runtime refusals are retained and
reported as domain blockers, never discarded as successful simulations.

Scope: six required mode fixtures plus passive decay, repeating stop/restart,
discharge/restart, 48-hour seasonal changes and enable changes. This is not
annual, generated-code, hydraulic or measured physical validation.
