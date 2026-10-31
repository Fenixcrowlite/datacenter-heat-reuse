# Correlated earliest-event segment controller v71

This additive model consumes the v70 mode-conditioned candidate policy, rather
than preserving the v66 sampled service policy. It implements repeated analytic
event segments **inside the same executed six-mode Stateflow chart**. Simulink
solver ticks remain protocol calls for held physical intervals; they are not
solver-clock thermal events. The original v57/v66/v70 models are preserved.
All equipment constants are synthetic engineering assumptions inherited from
the existing fixtures, or explicit synthetic cycle controls. No paper equation,
calibration, article replication or measured validation is claimed.

## Physical and mathematical contract

E is ambient-reference tank energy; time is hours, powers are the existing
project heat-power units, C is the corresponding energy per kelvin, lambda is
inverse hours. Held ports obey E' = B - lambda E, with
B = etaC charge - discharge/etaD. The controller gives direct demand priority,
then charges surplus while certainly below stop; discharge meets residual
demand while above cutoff. Boiler output is bounded and residual unmet demand
has no delivered-energy credit. Charge and discharge are exclusive.

The HP limit is the lower bound of nameplate, source-side capacity and finite
hot-water approach capacity. The source bound uses the lowest hot temperature,
giving a conservative uniform admissible heat rate throughout the segment.
The inherited refrigerant model uses Te = sourceIn - glide - evapApproach and
a = factor * (Te + 273.15). Delivered condenser heat q has source extraction
q*a/(a+lift), compressor work q-source, and auxiliary electricity aux*work.
Auxiliary electricity is excluded from useful condenser/storage heat. Fixed
approaches and this cooling-factor law remain uncalibrated assumptions.

Stop is enabled only while charging, cutoff only while discharging, restart
only while OFF with source, enable and a present/future direct or charge sink.
Restart readiness is max(thermal-root, max(0,minOFF-age)). Root forcing is
recomputed after **every** cutoff, stop, restart and held-input boundary.
Stop and no-source/no-sink OFF are safety overrides of minimum ON dwell.
External disable requires certified ON age. OFF dwell is certified either by
its complete lower-age bound or the symbolic wait identity, never a tolerance.

For positive lambda the independent closed solution is
E(t)=B/lambda+(E0-B/lambda)*exp(-lambda*t), with root
-log((G-B/lambda)/(E0-B/lambda))/lambda. For zero lambda,
E(t)=E0+B*t and the root is (G-E0)/B. Production instead uses outward Taylor
flow and separate strict-before/strict-after bisection witnesses inherited
unchanged from v70. Public held spans require lambda*dt<=1; expanded private
Taylor arguments permit |x|<=2 with tail <=8*2^25/26!.

## Correlation and event consumption

A segment retains the full root duration hull, incoming inventory/age, forcing,
symbolic threshold identity, local start/end time hulls and every cumulative
energy offset. For a certified thermal contact, the outgoing energy is the
**symbolic policy threshold**, and the duration remains the root hull. This
represents the exact manifold E(tG)=G; it is not a floating midpoint, clipping
operation or scalar state restart. All ports are integrated over the complete
duration box from the incoming trajectory. First-law enclosures must include
zero at every segment and cumulatively. Cartesian interval evaluation widens
the dependent quantities; records preserve their defining relationship.

The outgoing clock is start+duration. A dwell-limited restart retains
wait=minOFF-age, proving age+wait=minOFF symbolically. A thermal-limited restart
requires root.lower > wait.upper and lower-age certification. Overlapping
thermal/dwell order is refused. The exact held-boundary identity
tStart+(dt-tStart)=dt is recorded and used after the terminal segment, while
inventory, age, source/work/service and their offsets retain their enclosures.
No root midpoint is consumed anywhere. Roots at unresolved held boundaries,
overlapping enabled events, unresolved derivative signs, zero progress and
more than sixteen segments per held interval reject explicitly.

Only enabled reachable candidates compete. Root witnesses are evaluated over
the original scalar macro span; if a witness at that larger span is unresolved,
it can be ignored only when the entire actual remaining trajectory is
certainly before its threshold. A root after cutoff is recalculated with the
new passive forcing; the hypothetical pre-cutoff restart is not reused.

## Saved-model trace schema

The output/retained memory has 1380 doubles. Header 1:100:

| Fields (MATLAB indices) | Meaning |
|---|---|
| 1,2 | final positive segment mode; schema 71 |
| 3:6 | macro incoming/outgoing inventory hulls |
| 7:12 | outgoing HP latch, age, cumulative clock, symbolic contact tag |
| 13,14 | segment count; interior event count |
| 15:30 | macro heat/source/work/standing/charge-loss/discharge-loss/service/boiler energy hulls |
| 31:50 | cumulative ten energy hulls, adding unmet and auxiliary |
| 51:54 | original inventory; cumulative first-law residual hull |
| 55:57 | macro unmet hull; conservative HP heat limit |
| 58:61 | incoming/held-boundary physical clock hulls |
| 62:75 | reserved zero |
| 76:100 | immutable 25-element equipment/policy vector |

There are sixteen fixed 80-double segment records. Unused records are zero.
Contact tags: 0 no symbolic contact, 1 stop, 2 cutoff, 3 restart.
Events: 0 held boundary, 1 stop/OFF, 2 cutoff, 3 restart/ON.

| Segment fields | Meaning |
|---|---|
| 1:4 | slot, six-mode code, event, thermal-contact flag |
| 5:10 | local start, duration and end time hulls |
| 11:18 | incoming/outgoing inventory and effective/outgoing age hulls |
| 19:23 | effective/outgoing latch, incoming/outgoing tag, boundary transition reason |
| 24:31 | HP/direct/charge/discharge/boiler/unmet powers and B hull |
| 32:51 | heat/source/work/standing/charge-loss/discharge-loss/service/boiler/unmet/aux energy hulls |
| 52:71 | corresponding macro-start energy offsets |
| 72:77 | selected thermal-root, wait and symbolic-threshold hulls |
| 78:80 | latch/age before any segment-start boundary transition |

Modes 0..5 are IDLE, HEAT_RECOVERY, STORAGE_CHARGE, STORAGE_DISCHARGE,
BACKUP and UNMET_DEMAND. The Stateflow state at a protocol tick is the final
positive segment mode; internal physical segments additionally record every
mode and transition. No claim of Stateflow solver-clock event firing is made.
The legacy correlated capacity/restart prefix protocol is not accepted as a
v71 input; only held-service kind=1 is supported.

## Independent QA contract

Original MATLAB MAT reports are reopened, compared and exported little-endian
binary. The separate reviewer consumes these binary operands as exact Fraction
values and solves the event trajectory with Decimal closed exp/log formulas
at 120 and 160 digits. Selected heat powers are independently checked against
admissible maximal allocation within a labelled 1e-12 relative/absolute
comparison budget for conservative binary64 limiter rounding; trajectory and
energy enclosure checks use **no numeric acceptance tolerance**. The reviewer
then uses the observed exact-binary powers as the executed forcing, rather
than silently substituting ideal powers. It verifies earliest candidate
selection, root/contact/dwell identity, all offsets, source/work/service/TES
balances and clocks across repeated cycles.

Source energy is independently integrated analytically. Where hot=max(floor,
Ta+E/C+approach), split at the exact floor-branch crossing. Above the floor,
write the denominator as K+R*exp(-lambda*t). Its integral is
t/K + log((K+R*exp(-lambda*t))/(K+R))/(lambda*K), with its K=0 and lambda=0
limits treated separately. Below the floor the rate is constant. Production
uses 32 outward source rectangles per segment; this algorithm is distinct.
Scalar v30 comparisons are made only for exact singleton starts/durations;
no interval midpoint is sent to that reference. Reviewer corruption controls
are synthetic self-checks and are counted separately from actual evidence.

Limitations: conditional normal-mode binary64/outward arithmetic, conservative
interval eligibility, finite segment budget and explicit unresolved-order
rejection; no generated-code or general arbitrary-domain acceptance. QA is
same-agent algorithmic independence, not independent personnel. MAT reopening
uses MATLAB, not an independent HDF5 parser. The model is reduced engineering
physics and full primary source signoffs remain 0/31.
