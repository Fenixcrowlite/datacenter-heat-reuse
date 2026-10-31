# Repeated sampled thermal stop and earliest-event comparison v66

Engineering derivation only. No paper equation or calibrated equipment value is
claimed. All fixtures extend the exact binary inputs used in v65.

The v65 capacity budget checks K (Tmax), while its lower stop temperature is
checked only at the start of a sample. Consequently a held charge can cross that
stop while remaining below K. This is a limitation of v65's accepted sampled
policy; its original capacity-safety acceptance is preserved. V66 adds the
explicit requirement that every authorized charging interval stay below stop.

For E' = etaC*qcharge - lambda*E, lambda>=0 and E>=0, E(t) is bounded above by
E.upper + etaC*qcharge*t. Let S.lower be the outward lower stop inventory.
Authorize a proposed held charge only if the outward upper growth bound is
strictly less than the outward lower difference S.lower-E.upper. Otherwise
withhold charging for the whole sample. This conservative guard is applied
before HP request/latch and mutually exclusive TES service decisions. It can
turn the HP OFF early when there is no direct demand. A direct heat sink can
keep the HP ON without charging. No thermal-root midpoint is selected.

The upper envelope is nondecreasing, so checking its held-duration endpoint
certifies the entire interval. Existing lower-inventory discharge/cutoff budget,
physical-age dwell bounds, source/water limits and cumulative energy accounting
are retained. The saved v64 analytic prefix is unchanged. The new chart still
contains and executes the six dispatch states. The guard does not implement
general repeated earliest-event Stateflow dispatch.

Independent trajectory QA uses exact Fractions for binary64 operands and
120/160-digit exp/log solutions for storage and piecewise source energy. It
checks the original trajectory and the full retained initial-inventory box,
first-law closure, ports, age, physical-clock enclosure and no midpoint reset.
The saved-v65 witness is separately evaluated with its unchanged v65 reviewer.
Original MAT files are reopened by MATLAB and exported as binary64; the Python
reviewer verifies their exports. Same-agent algorithmic independence is claimed,
not independent personnel or measured validation.

Three four-cycle schedules use dt=0.25,0.5,1 hour. Each cycle holds charge-only
source availability for 10 hours, source absence/demand 6 MW for 2 hours, then
zero demand/source for 1 hour. Boiler capacity is 2 MW. These are synthetic
engineering fixtures; they share identical binary equipment and demand-change
times across the three sampled resolutions.

The independent earliest-event comparator uses maximum admissible held HP charge
until stop, passive OFF cooling until both restart temperature and OFF dwell,
and maximum TES discharge until cutoff with finite boiler/unmet service.
For a constant port B, Eeq=B/lambda and
E(t)=Eeq+(E0-Eeq)*exp(-lambda*t). A reachable threshold has
t_event=-log((Ethreshold-Eeq)/(E0-Eeq))/lambda. The passive restart event and OFF
dwell readiness combine with max; the next physical boundary combines with min.
The comparator refuses a nonzero ordering gap below its stated 1e-90 relative
clock threshold and is checked at two precisions. Boundary target identities are
carried at high precision; sub-1e-100 arithmetic residuals are retained in first
law checks. These are numerical analytic comparisons, not certified binary64
event brackets or executed earliest-event Stateflow. Event/source energy maps
and hardware calibration remain outside this comparator's scope.

Do not compare port quantities as if the policies were equivalent: earliest
charging can use more heat, and delayed demand fixes the usefulness of that
inventory. The saved numeric comparisons record HP heat, delivered service,
boiler and unmet energy separately; source/compressor enclosures are independently
checked for actual sampled execution only. Auxiliary heat remains external.
