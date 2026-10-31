# v35 restart/dwell admissibility and dimensional defect audit

This checkpoint tests the preserved saved v34 Stateflow model. It does not
release a corrected SLX. The v34 acceptance record covers its tested fixtures;
the newly reproduced clock-tolerance defect limits broader acceptance.

## Independent derivation (engineering assumptions)

Let ambient-reference energy E and capacity M be MWh, lambda be h^-1,
cutoff K and restart R be MWh, and all dwell/age/segment quantities be hours.
For held internal power P in MW, E'=P-lambda E. Its solution is
E(t)=E0 exp(-lambda t)+P(1-exp(-lambda t))/lambda, with E0+Pt at lambda=0.
These are our reduced-model equations, not equipment calibration or a paper
replication. The inherited ambient-loss provenance is recorded in
TES_standing_loss_primary_v28.md; the lumped-store reduction remains assumed.

To remain below M for an ON duration tau when Pmax>lambda M, restarting
at R requires

`R <= Pmax/lambda + (M-Pmax/lambda) exp(lambda tau)`.

At lambda=0 this is R<=M-Pmax tau. This is sufficient even for changing
P(t)<=Pmax, by comparison of the scalar linear ODE. It assumes HP operation
remains feasible; source loss or a screening cutoff can override ON dwell.
For the assumed charge bound, Pmax=etaC*chargeLimit. If Pmax<=lambda M,
the upper capacity boundary is invariant and this growth constraint is
unnecessary. Negative upper bounds mean the requested dwell is infeasible.

While OFF, usable TES supply is limited by dischargeLimit and boilerLimit.
For discharge dmax MW, internal depletion B=dmax/etaD MW, and remaining OFF
dwell tau, the sufficient reserve condition is

`E0 >= -B/lambda + (K+B/lambda) exp(lambda tau)`.

At lambda=0 this is E0>=K+B tau. It bounds changing discharge up to dmax,
including standing loss. The bounds are checked independently by RK4 forward
integration from each inverted initial energy, including zero and small loss.
They are mathematical sufficient conditions for the assumed coefficients.

A full robust OFF period beginning at M also requires that reserve(M,tau)
not exceed M. A restart band cannot repair an arbitrary initial OFF state below
the required reserve. Nor can stored energy repair an instantaneous port limit:
with HP OFF and demand D>dischargeLimit+boilerLimit, unmet demand is at least
D-dischargeLimit-boilerLimit while energy remains above cutoff. Source
unavailability can extend OFF beyond its minimum dwell indefinitely, so finite
reserve cannot guarantee service for an unbounded outage. Restart additionally
requires available HP output for the held input, not just energy and age guards.

Fixture values are assumptions: M=10, K=5, etaC=.9, etaD=.8, lambda=.1,
chargeLimit=3, dischargeLimit=4, boilerLimit=.5, ON/OFF dwell=.25 h.
The independently generated specification records R=8.827220821345797 MWh,
ON upper bound=9.56964295108471 MWh and OFF reserve=6.392331628843586 MWh.
The overload control starts OFF at E=9.9, D=8 MW; .25 h of binding OFF dwell
produces (8-4-.5)*.25=.875 MWh unmet before restart. This is an expected
policy limitation, not a failure of the energy balance.

## Confirmed implementation defect

The saved v34 supervisor guard sets `tol=1e-10*max(1,p(2))` from TES capacity
in MWh, then uses that same number in an age comparison in hours. The runtime
monitor sets `tol=1e-9*max(1,cap+(...)*dt)` from an energy scale and applies it
to segment offsets, age increments and final clocks. These are dimensionally
inappropriate comparisons. The monitor also reuses energy-derived tolerances
for power and dimensionless COP; that wider tolerance audit remains a handoff.

The numerical stress cases hold durations and flows fixed while varying M
over 10, 1e4, 1e6 and 1e9 MWh. These capacities are adversarial numerical
scales, not plausible installations or calibrated equipment values. At 1e9,
guard tolerance is .1 numerically, and monitor tolerance is approximately 1.
An OFF age of .24 h is admitted against a .25 h minimum in a direct guard
probe. This probe calls the guard component; it does not prove the host planner
caused an early transition in a clean simulation. Separately, an executed
in-memory allocator mutation adds .01 h to the reported segment end age and
is incorrectly accepted by the saved-model monitor at the largest scale.
Smaller tested scales reject it. Independent QA uses hour-based checks to
reject every accepted corrupted segment, including padding.

The mutation is temporary, restoration is executed and compared to baseline,
and the saved SLX hash is preserved. A coherent next release must introduce
separate energy, power, temperature, dimensionless and time tolerances, embed
the corrected guard and monitor in a new versioned model, and demonstrate
actual scale-independent runtime rejection. Preserve this counterexample.
Define floating-point time resolution explicitly: adding energy capacity to
clock tolerance is never justified by large-energy cancellation.

## Evidence boundaries

Copeland AE4-1431 R2, PDF page 20, Minimum Run Time, was visually checked from
the acquired PDF render. It addresses ZB*KAU R-290 scroll compressors (title on
PDF page 1): maximum 10 starts per hour, recommended 2-3 minute run time for
oil return, and no minimum OFF time for that equipment. It does not calibrate
our HP or justify .25 h dwell. The PDF header says October 2024 and footer
copyright 2025; no publication-date inference is made from that discrepancy.

EnergyPlus 26.2 engineering reference, Plant Loop Heat Pumps, Part Load Ratio
Calculations, Eqs (16.459)-(16.463), describes a user-specified minimum PLR and
cycling ratio below it. The local full HTML and extracted relevant section were
read. This is primary engineering documentation, not a research article or
measured startup-loss model. Minimum PLR and minimum COP are distinct
constraints. Our linear part-load COP and unavailable-below-COP policy remain
engineering assumptions. No startup/cycling-loss parameter is adopted.

Public acquisition URLs, errors, timestamps, source hashes and verification
classifications are retained in equipment_evidence_v35_20261010T031109285Z.
Full primary article signoffs remain 0/31. Independent algorithm/artifact QA
is not separate human/agent review or physical validation. The model uses
normal-mode host planning and analytic segment offsets within a macro solver
sample; it is not solver-clock event scheduling or standalone deployment.
