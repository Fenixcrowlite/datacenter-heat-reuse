# Horizon dependence and proposed renewal contract v86

This checkpoint executes the unchanged accepted saved v85 chart. It does not
claim a renewable-cap Stateflow implementation. All input ratings, approaches,
cooling factors and storage efficiencies are synthetic engineering operands.
No primary article equation, equipment coefficient or measured result is added.

Let A>0 and L(E)=max(Lf,b+E/C)>0 be the inherited reduced refrigerant proxy axes.
Compressor work rate is W(q,E)=q L(E)/(A+L(E)). Its inventory derivative is
nonnegative; therefore a cap certified at an upper inventory bounds work at
every point of a monotone held-power segment. Heat and work are MW; inventory
is MWh, C is MWh/K and H is hours. Auxiliary work is outside this ceiling.

For a fixed raw policy define Quniv=Pmax(1+A/Lf) and
Qch=max(0,min(charge_port,thermal_cap,Quniv)). Since
E'=eta_ch qch-qdis/eta_dis-lambda E <= eta_ch Qch for E>=0,

    B(H)=min(Ecapacity,Einitial+eta_ch Qch H)
    Qeff(H)=min(thermal_cap,Pmax(1+A/L(B(H)))).

B is nondecreasing and Qeff is nonincreasing in H. In the absence of competing
limits the HP heat over an identical ON history is Qeff times its duration.
There can be a flat region below the hot-water floor and another after capacity
saturation. Positive loss makes the reachability bound conservative, while the
actual held-power thermal kernel still integrates loss and interior events.
Changing only input partition does not change Qeff or the exact trajectory for
constant physical forcing and no switching. Floating-point reporting hulls may
change width. Partition comparisons use independently reconstructed exact-binary
closed equations and overlap of the original reported hulls, never midpoints.

Predeclared execution: all twelve v84 service/charge histories at nominal
H=1,2,4 hours with 0.25-hour partitions; the cold service and floor-crossing
charge histories also at 0.125 and 0.5 hours. Actual H for nominal 1 is
1+2^-40 hours, an explicit certificate margin, not a longer simulated history.
The same exact one-hour endpoint with H=1 is probed separately and its actual
acceptance/refusal is retained. H=2 and 4 are exact. Six modes, positive-loss
charging, stop/cutoff/restart, zero rating and seven prior refusal controls
execute as regression fixtures. The v84 nonlinear comparator is recalculated
at 120/160 digits with its original zero-loss/nonbinding/no-switch scope and
RK4 floor-aware endpoint check; it is hypothetical, not a saved model.

## Proposed additive renewal contract (not implemented here)

1. Keep the raw 25 thermal operands and compressor rating immutable. Renewal
   may replace only the certified effective heat cap at a held-input boundary.
   Store origin, generation, physical renewal-clock hull, expiry-clock hull,
   reachable inventory upper bound, raw-policy digest and effective cap in a
   versioned certificate. The current 29-column certificate is insufficient.
2. Start each renewal from the retained inventory **upper endpoint**, never
   an arbitrary midpoint or the first-call initial inventory. For a renewal
   window of duration h, set B=min(Ecapacity_upper,Eretained_upper+eta_ch Qch h)
   with directed outward arithmetic; derive the cap from that B. An interval
   renewal requires h to cover the certified duration upper endpoint, including
   clock uncertainty. Reject an unresolved expiry before committing outputs.
3. Preserve retained physical clock, HP latch, ON/OFF age, threshold identity,
   root hulls and correlated service/source/work/loss offsets. A cap update is
   not a reset, switch or new simulation. Existing dwell constraints still
   govern actual switching. Do not change forcing inside an already certified
   event segment. Recompute enabled candidates after renewal with the new cap.
4. Authenticate each input/thermal trace/report against its renewal generation
   and certificate. Replace the current effective-policy immutability check
   with a narrow authenticated renewal rule in an additive kernel/schema;
   permit no other policy mutation. Reporting must validate all generations.
5. Predeclare saved-model tests: v86 paired histories/partitions, positive loss
   and floor crossing, stop/restart/cutoff and dwell, zero/nonbinding ratings,
   retained-hull sensitivity, corrupted origin/generation/expiry/raw operands,
   early renewal, unresolved collision and clock/segment refusal controls.
   Independently reconstruct each certificate and complete physical trajectory
   from original-MAT binary exports before accepting the new version.

A cap computed only at the current temperature is unsafe for charging when
E subsequently rises above the floor. Qstart=Pmax(1+A/L(Estart)) implies
W(Qstart,Eend)>Pmax whenever L(Eend)>L(Estart). This strict rational witness
is checked separately. Restarting the current model each interval would also
discard clock and latch/dwell provenance; it is not an implementation of renewal.

Same-agent algorithmic independence only: Fraction and Decimal closed equations
call no production MATLAB solver. MATLAB reopens MAT for binary export; neither
independent personnel nor an independent MAT parser is claimed. No annual,
generated-code, equipment calibration, article replication or physical-validation
acceptance is possible from this synthetic one-hour sensitivity experiment.
