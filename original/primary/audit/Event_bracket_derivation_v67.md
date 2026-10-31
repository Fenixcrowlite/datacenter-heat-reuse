# Held-trajectory event certificates v67

Engineering mathematics and synthetic fixtures only. No new article text,
equipment calibration, article replication or physical validation is claimed.

The versioned observer executes inside the SAME six-mode sampled chart. The
embedded v66 dispatch source and its 205-element retained memory remain exact.
The 51 appended observer values do not allocate heat, select event times, reset
inventory or change ports. Service kind `u(4)=1` requests strict certification
and rejects any active unresolved contact/order. Existing fixtures use zero.

For held affine input B (MW), thermal inventory E (MWh) and loss rate lambda
(1/h), dE/dt=B-lambda E. E=C(T-Ta), with C in MWh/K. Threshold inventory uses
the exact binary input expression C*(Tthreshold-Ta), enclosed by outward
arithmetic. For lambda>0,

    Eeq=B/lambda
    E(t)=Eeq+(E0-Eeq)*exp(-lambda*t)
    troot=-log((Eth-Eeq)/(E0-Eeq))/lambda

For lambda=0, E(t)=E0+B*t and troot=(Eth-E0)/B. These formulas describe reachable
monotone roots; equilibrium, zero forcing and nonpositive logarithm ratios
require separate reachability classification. Compiled certificates require a
strict derivative sign at both incoming and threshold interval endpoints.
That sign propagates over the monotone segment. Unsupported derivative signs
reject; no event existence is inferred from a logarithm alone.

The certifier reuses the already derived *algorithmic form* of the outward
Taylor flow, with a fresh versioned implementation. For x=-lambda*t and |x|<=1,

    E(t)=E0+(B-lambda*E0)*t*phi1(x)
    phi1(x)=sum_{n=0}^24 x^n/(n+1)! + remainder
    |remainder| <= 3/26!

The exponential tail bound follows from e<3 on this domain. Every ordinary
binary64 arithmetic endpoint expands by two eps increments, with explicit
zero identities. Finite expansion, positive division and outward span guards
reject unsupported inputs. This is conditional binary64 engineering arithmetic;
standalone generated-code rounding and subnormal environments are not accepted.

Each root starts with a full incoming inventory hull and candidate B hull. An
interior certificate requires a certainly-before initial state and a
certainly-after held-duration endpoint. Two independent 48-step searches locate
the latest certainly-before and earliest certainly-after witnesses. An ambiguous
evaluation never chooses a side. The stored interval [tlo,thi] retains all box
roots; interval width includes incoming uncertainty and arithmetic expansion.
The full inventory box remains available. No scalar-root midpoint is state
authority. Status 0 means no crossing during this horizon, status 1 is a strict
interior bracket, status 2 means contact/horizon unresolved, and status 3 means
the whole incoming box is already on the reached side. Status 2's [0,H] is a
search window, **not a claim that a physical root lies in that interval**.

For OFF dwell D and incoming age [alo,ahi], remaining wait is

    W=[max(0,D-ahi),max(0,D-alo)]
    ready=[max(tlo,Wlo),max(thi,Whi)]

Outward subtraction retains arithmetic uncertainty. Classify ready strictly
before H, strictly after H, or unresolved. Root contacts and boundary collisions
are never ordered with a tolerance. Direct probes include exact E0=8, B=1,
lambda=0, threshold=9, H=1: an exact root at the held boundary. Actual chart
fixtures include a nearby binary boundary with conservative water-limited
forcing, and a delayed counterpart after two valid samples. Do not call that
compiled candidate's small nonzero binary gap an exact collision.

The three observer lanes describe alternative held candidate trajectories:
full HP charge to stop, full demand-limited TES discharge to cutoff, and passive
OFF cooling to restart with OFF dwell. They are potential trajectories, not
simultaneously executed ports. Restart observations are restricted to incoming
OFF state with an enabled source and charging sink. General interacting events,
direct-demand changes and repeated event segmentation are still open.

Observer output after the original 205 plant values:

| Positions (MATLAB) | Meaning |
| --- | --- |
| 206–220 | Potential thermal-stop certificate |
| 221–235 | Potential cutoff certificate |
| 236–250 | Potential passive-restart / OFF-dwell certificate |
| 251–252 | Stop affine forcing B hull |
| 253–254 | Cutoff affine forcing B hull |
| 255–256 | Passive restart forcing B=0 |

Each 15-value certificate stores status, root lower/upper, two endpoint inventory
witness hulls, wait lower/upper, ready lower/upper, ordering code, direction and
threshold hull. Ordering codes: 0 no event, 1 ready strictly before held boundary,
2 unresolved, 3 ready strictly after held boundary. Inactive lanes are all zero.

Independent QA evaluates all eight E/B/threshold box corners with exact binary
Fractions and 160-digit closed exp/log mathematics. It verifies root containment,
strict witness separation, derivative signs, threshold-expression enclosure,
OFF wait and readiness, original retained trajectories, source/work integrals,
first law, ports and clock handoffs. Original MAT is reopened/exported by MATLAB,
then binary traces and archive-embedded sources are verified. Reviewer mutations
test corrupt roots, order, witnesses, readiness, threshold and OFF wait. This is
same-agent algorithmic independence, not independent personnel.

The blocking interface remains concrete: a bracket certifies existence and order
but cannot be passed as one scalar duration to v66 service allocation. The
earliest switch requires a symbolic threshold identity plus correlated event-time,
elapsed OFF age and every port offset; post-event integration must carry those
dependencies. Root observation is accepted separately, never earliest switching.
Next implementation must retain the event-time box across both segments and
prove source/work and first-law enclosure before controlling a repeated cycle.
