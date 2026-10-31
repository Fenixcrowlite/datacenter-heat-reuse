# C128: competing thermal source priorities with command transport delay

## Change
An isolated 15-minute synthetic heat-dispatch model now compares water-first
and air-first policies at **20 and 25 kW** source caps, with **0 or 30 minutes**
of command transport delay. Also replays a 150 kW zero-delay baseline.
Ten scenarios, 672 quarters each (7 days), total **6720 transitions**.
Thermal source kW is not electrical draw; no COP has been modeled.

## Observed results at 20 kW (7 days)
| Priority | Delay | Final pool C | Air heat MWh | Binding quarters |
|---|---:|---:|---:|---:|
| Water-first | 0 min | 28.000000 | 0.315071 | 364 |
| Air-first | 0 min | 27.972717 | 0.500401 | 494 |
| Water-first | 30 min | 28.000285 | 0.282282 | 364 |
| Air-first | 30 min | 27.963519 | 0.497373 | 498 |

Priority now changes allocation and pool temperature; 150 kW replay does not.
Delay uses a cold-start FIFO of two 15-minute commands; **not** measured actuator
inertia. Air heating has a live-temperature safety interlock, so stale air commands
are clipped by the current air request. Pool commands can remain active after
a thermostat switch, explicitly exposing possible delay overshoot.
Cooling remains independent of recovered source.

## Verification
Six embedded tests; 6720 independent CSV row checks with energy/mass,
FIFO, source-cap, thermostat, priority and continuity reconstruction;
nine negative controls. Separate regression matched 1344 baseline
C127 quarters across 6720 numeric fields, max difference 0.
The energy/mass balances verify implementation consistency, not field validity.

## Limitations and next step
All parameters and weather are synthetic; no validated HVAC curves, electrical
COP, intra-step switching or field instrumentation. Primary source signoffs
remain 0/31. Next: implement finite thermal actuator slew-rate and explicit
electrical input/COP, then run robust sensitivity on cap and delay without
altering SCADA/MATLAB or shared runtime.
