# C127: bounded quarter-step thermostat and shared thermal source (synthetic)

## Engineering change
Independent task-local 15-minute pool thermostat replaces C125's frozen hourly
pool-heat replay. At each step the pool requests feedforward losses plus proportional
temperature correction; heating is bounded by a shared thermal source. Positive
air-HVAC heating competes for the same source, dispatched either water-first or
air-first. Negative air-HVAC cooling is independent and excluded from source heat.
Pool evaporation and moist-air temperature/humidity continue to feed back.

## Measured simulation outputs
- 150 kW thermal source, water-first: 35040 quarters, final pool 28.0000 C,
  delivered pool 123.375 MWh, air 26.143 MWh,
  saturated quarters 0.
- 150 kW air-first: 35040 quarters, final pool 28.0000 C,
  saturated quarters 0. Identical to water-first
  because the shared cap never binds in this synthetic scenario.
- 10 kW water-first, 7 days: 672 quarters, final pool 27.6946 C,
  saturated quarters 644, air heat delivered
  0.0180 MWh.
- Zero source heat, 7 days: 672 quarters, final pool 25.4674 C,
  pool heat delivered 0.0000 MWh.
- Total 71424 quarter steps, 13 embedded tests, independent QA 71424
  row checks and 6 negative controls PASS.

## Scientific limitations and interpretation
All inputs are synthetic. The ideal 150 kW thermostat holds exactly 28 C because
it can match the same loss law used by the simulator; this is NOT field performance.
The column pool_unmet_kJ measures unserved controller REQUEST (including feedback
catch-up), not observed heat leakage or equipment rating. Source caps are thermal
power, not electrical draw; no COP, cycling, actuator delay, calibrated dehumidifier,
weather measurements, physical validation or 31 primary-source signoffs are supplied.
Room air RH >65% persists even when pool temperature is controlled. Energy/mass
conservation tests prove accounting consistency, not real-world model accuracy.

## Next executable step
Introduce actuator delays, hysteresis switching costs and uncertain weather/COP,
then test constrained water-vs-air priority with a source cap that binds in both
directions. Independently verify all source and equipment assumptions before SCADA
or MATLAB deployment. Preserve original C116/C124/C125 and all shared runtimes.
