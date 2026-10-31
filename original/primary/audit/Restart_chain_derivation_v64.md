# Retained interval restart chain v64

This is an engineering derivation and a scoped executable component, not a
paper equation, calibrated equipment model or accepted six-mode replacement.
The immutable v63 global charging/capacity record is embedded unchanged as a
local function. Its exact binary operands define capacity K=C(Tmax-Ta), initial
inventory and event roots. Its conditional outward series and port hulls remain.

After capacity safety OFF, inventory at an exact binary sampled horizon tr is
Er=K exp[-lambda(tr-tc)]. The capacity root tc remains an interval with retained
operands. Restart requires OFF-age.lower >= min_off and (Ta+Er/C).upper <=
restart_C, where Ta < restart_C < Tmax. These two inequalities are conservative;
unresolved readiness rejects. No scalar thermal or capacity root is selected.
The sampled horizon is a control policy, not earliest-event physical firing.

At restart, retain the entire Er interval and each cumulative port/loss interval,
plus exact binary horizon tr. For tau=t-tr, B=eta_charge*q,
E(t)=Er exp(-lambda*tau)+(B/lambda)(1-exp(-lambda*tau)).
At lambda=0 its limit is Er+B*tau. Monotonic interval integration keeps all
possible original capacity-event trajectories. The independent reviewer evaluates
the correlated exact original trajectory rather than an interval midpoint.

Additional heating is q*tau, charge loss (1-eta_charge)q*tau and standing loss
lambda integral(E dt). All cumulative energies add retained offsets. For tank
charging above the floor branch, Te=source-glide-evaporator_approach,
a=cooling_factor*(Te+273.15), l0=Ta+charge_approach+condenser_approach-Te.
Source rate is q*a/(a+l0+E/C), compressor rate q-source and auxiliary rate
aux_per_compressor*compressor. The compiled component uses 128 outward rectangles
per resumed trajectory and rejects source/hot-water infeasibility. Hot capacity
rate q/charge_approach is checked, including inherited host exact tie certificates.

For the independent closed form, let y=a+l0+E/C and cc=B/C+lambda*(a+l0).
The resumed source integral is q*a*[log(y1/y0)+lambda*tau]/cc.
The reviewer uses exact binary Fractions and 120-/160-digit Decimal exp/log.
First law is E0+heating-E-standing-charge_loss=0 across all three trajectories.

The restart origin is a known sampled horizon, so new ON age is outward tau.
Prior OFF age is retained, not discarded or replaced by a guessed event time.
This legitimate latch transition is distinct from v63's uncertain capacity OFF.
Memory slots 1:80 retain the legacy v63 schema; 81 is restart horizon, 82:83
restart inventory hull, 84:95 cumulative offsets, 96:97 certified preceding OFF
age, 98:99 restart temperature, 100:101 new ON age, 102:103 retained inventory,
104:111 resumed heat/source/work/standing loss, 112 outer schema=64, 113 restart
threshold and 114 outer phase. No scalar service-credit authorization is added.

Scope: constant request; strictly increasing active trajectory; one capacity OFF,
passive cooling and one certified sampled restart; resumed tank branch only;
outward arithmetic subject to inherited |lambda*span|<=1. Further capacity
crossings reject. Zero-loss passive cooling cannot reach a strictly lower thermal
restart threshold and is not presented as a successful restart. Six modes remain
in the separate accepted v57 model. Coupled dispatch, demand/discharge/backup
allocation, multiple event cycles, other limiters, cooling below branch floor,
standalone generated code, calibration and measured physical validation remain
open. Same-agent independent algorithms do not imply independent personnel.
