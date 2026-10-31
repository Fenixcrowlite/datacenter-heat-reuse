# Constitutive TES standing-loss monitor v80

This is a check of the existing engineering model, not a paper equation,
equipment calibration or measured validation. The preserved v75 kernel uses
E' = B - lambda E, with held constant B, lambda >= 0 and E >= 0. E is inventory
above ambient in MWh, B is MW, lambda is h^-1, and duration is h.

Differentiating gives E'' = -lambda E'. Therefore E' keeps its sign on a held
segment (including the affine lambda=0 case). All inventories lie between the
initial and final inventory. The standing loss L = integral(lambda E dt) obeys

lambda d Emin <= L <= lambda d Emax,

where Emin is the minimum lower endpoint and Emax is the maximum upper
endpoint. With duration uncertainty, use its lower/upper endpoints in the
respective bound. These inequalities are dimensionally MWh. For lambda=0,
L is exactly zero, irrespective of duration, forcing, or inventory.

The saved runtime monitor builds the positive bound with outward binary
arithmetic and requires overlap with the recorded loss hull. It calls no
production flow, exponential, event root or quadrature routine. Exact zero
coefficient requires an exact zero loss record. Python Fraction arithmetic
independently checks the inequalities directly from binary operands; separate
120/160-digit closed exp/log QA verifies actual trajectories and integrals.

v79 already checks balance, endpoints, forcing and copied totals, but those
checks can accept a coordinated wrong inventory/loss pair. Test controls alter
only one passive segment's endpoint, loss, copies and residual, after kernel
evaluation in unsaved chart copies. They are adversarial records, not physical
trajectories. v80 must reject them before trace emission and memory commit;
v79 acceptance and exact bypass traces establish the new guard's necessity.

Scope: necessary constitutive overlap only. Endpoint monotonicity is an
assumption of the held reduced ODE. Wide hulls and wrong values that still
overlap this rectangle can pass; no full ODE certificate or event/dwell proof
is claimed. Existing nonlinear independent QA remains mandatory. No change
to thermal kernel, control policy, trace schema 75 or reporting API 0.76.
