# C121 | 15-minute sensor latency and actuator lag sensitivity
2026-10-31, isolated DataCenter Heat Reuse engineering scope.

## Model
Replay SHA-pinned C116 water-first/ideal hourly evaporation (8,760 synthetic hours), C106 weather, C118 exact 15-minute moisture ODE, and C120 feedback/predictive controller. Eight variants: controller {feedback, predictive} x sensor delay {0, 2 quarters = 30 minutes} x actuator time constant {0, 0.5 h}. Four quarter-hour steps per hour; 70,080 hourly records and 280,320 state transitions.

The actuator is first-order: a_new = a_old + (u-a_old)*(1-exp(-0.25/tau)), or a_new=u at tau=0. The delayed sensor reads the room humidity from two quarter-hour starts earlier. Saturation and condensate follow the exact C118 moisture balance. Controller capacity is bounded by 45.66 kg/h dehumidification and 29.70 kg/h humidification. Synthetic energy proxy is 0.5 kWh/kg removed and 0.75 kWh/kg added. This is NOT measured power.

## Results (high-RH quarters above 65% / 35,040 quarter-hours per scenario)
| Controller | Sensor delay | Actuator tau | High-RH quarters | Switches (>5 kg/h change) | Proxy kWh/year |
|---|---:|---:|---:|---:|---:|
| Feedback | 0 min | 0 h | 7,919 | 18,710 | 147,036.9 |
| Feedback | 0 min | 0.5 h | 8,602 | 16,362 | 120,142.0 |
| Feedback | 30 min | 0 h | 5,779 | 19,144 | 149,485.5 |
| Feedback | 30 min | 0.5 h | 6,798 | 16,522 | 123,434.4 |
| Predictive | 0 min | 0 h | 6,295 | 17,367 | 158,011.9 |
| Predictive | 0 min | 0.5 h | 7,494 | 18,141 | 115,468.4 |
| Predictive | 30 min | 0 h | 10,517 | 20,292 | 160,578.9 |
| Predictive | 30 min | 0.5 h | 10,254 | 21,235 | 108,969.5 |

Counterintuitive finding: delaying the naive feedback measurement lowers the number of high-RH quarters in this one stress scenario, while delaying the predictive controller raises them substantially. This is not evidence that sensor delays are desirable: the feedback gain and phase lag interact, and low-RH errors, controller stability, and overall objective have not been optimized.

## Independent QA
70,080 row checks for finite values, RH bounds, mass closure, nonnegative fluxes, switching counts and synthetic energy equation. 17,520 baseline rows independently crosschecked against immutable C120 outputs for both zero-delay/zero-lag modes (10 numerical fields per row). Five deliberate negative mutations correctly rejected. Five selftests pass. Source SHA pins verified.

## Limitations and next action
Fixed 29 °C air, no air thermal mass or enthalpy dynamics, no vendor response curves, no sensor noise or weather forecast uncertainty, no actual electricity meter data. Evaporation front-loading is a deliberately adverse synthetic profile. Physical validation and 31 primary-source signoffs remain open. Next: couple room temperature and moist-air enthalpy to 15-minute moisture model, then compare RH/temperature/electricity/switching Pareto tradeoffs with real equipment curves. Do not change shared MATLAB, SCADA or original datasets.
