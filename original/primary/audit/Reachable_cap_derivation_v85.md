# Declared-horizon reachable-temperature cap v85

This additive Stateflow model retains the accepted affine held-power thermal
kernel. It chooses one certified constant heat cap per complete schedule,
not the maximal temperature-conditioned nonlinear controller hypothesized in
v84. No new article equations, coefficients or calibrated rating are claimed.

With the exact binary operands and the axes defined in v83/v84, lift obeys
L(E)>=Lf>0. Thus every electrically admissible heat rate satisfies
q<=Pmax*(1+A/Lf)=Quniversal. Charging cannot exceed
Qcharge=min(charge_port_cap, original_thermal_cap, Quniversal).
The inventory equation is E'=eta_charge*qcharge-qdis/eta_dis-lambda*E.
For nonnegative inventory, discharge and loss, E'<=eta_charge*Qcharge.
Consequently for 0<=t<=H:

    E(t) <= min(capacity, Einitial+eta_charge*Qcharge*H) = Ebound.
    Lbound=max(Tfloor, Ta+Ebound/C+water_rise)+cond_approach-Te.
    Qeffective=min(original_thermal_cap, Pmax*(1+A/Lbound)).

The choice is self-consistent: Lbound>=Lf implies Qeffective<=Quniversal;
the original thermal/charge limits remain enforced. Since L/(A+L) increases,
q<=Qeffective proves W(q,E)<=Pmax over every full segment. Positive passive
loss only lowers the reachable inventory, so ignoring it in this bound is
safe. The kernel still integrates actual positive loss and floor crossings,
stop/restart/cutoff events and dwell, with its original interval certificates.

Production interval operations enclose the universal upper power, reachable
upper inventory and electrical lower cap. Capacity uses the retained kernel's
outward upper guard. H is raw policy operand 27 (hours), finite, positive and
immutable. Every dispatch checks its certified physical clock upper endpoint
<=H and both endpoints of every monotone affine segment <=Ebound before
committing trace/memory. Initial inventory comes from retained origin after
the first call. Raw policy and effective cap/inventory bound are bound by a
29-operand certificate; thermal trace schema remains 75 and reporter remains
76. A schedule requiring more time must be supplied a larger H at initiation.

Predeclared execution includes all v84 histories, six modes, zero/nonbinding
ratings, positive-loss charge/floor crossing, binding stop and repeated events.
Identical histories execute the preserved global-cap v83r2 for comparison.
Independent Fraction algebra proves cap/bound/pointwise power safety from
original-MAT binary exports; independent 120/160-digit exp/log trajectories
check TES flow, source/work partition, loss, event timing, dwell and reporting.
Reviewer mutations test excessive cap, selected heat and raw certificate.
Algorithmic independence is same-agent, not separate personnel or an
independent MAT parser. MATLAB reopens original MAT before binary export.

This bound grows with H and can revert to the global-cap behavior. It remains
conservative under cooling, long horizons or port limits, and does not optimize
instantaneous electrical capacity. Auxiliary electricity is separate. Equipment
calibration/supplement, physical validation, annual and generated-code acceptance
remain open; synthetic constants and ratings must not be treated as primary data.
