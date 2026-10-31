# Carrier sizing correction and closed-loop N+1 simulation
**23 October 2026 | MATLAB/Simulink R2026a | Engineering simulation, not commissioned equipment**

## Seven executed annual simulation scenarios

A new versioned `DC_Pool_Capacity_Fault_20261023_SK.slx` includes a time-dependent district heat pump output cap at **every 300-second step**. The water temperature controller, thermal storage and backup gas are dynamically recalculated, instead of clipping prerecorded output.

| Scenario | Annual district gas MWh |
|---|---:|
| No pool, 12 MW HP limit | 9085.895 |
| No pool, 10 MW HP limit | 9088.579 |
| Pool, 10 MW HP limit | 9191.507 |
| Pool, 24 hours with one 2-MW module unavailable | 9207.071 |
| Pool, N+1 replacement available after 30 minutes | 9191.637 |
| Pool, HP output limited to 9.42 MW | 9256.806 |
| Pool, HP output limited to 10.99 MW | 9189.267 |

All seven scenarios ran for 8760 hours and 105120 steps. Thermal balance, source exclusivity and the modeled pool water ceiling of 27.8 °C passed. Peak pool temperature: **27.62 °C**.

## Manufacturer correction

The **Carrier 61XWH-ZE 2025 product data** reports a maximum **1570 kW** nominal heat output for model 17. Its documented test conditions are evaporator entering/leaving water **20/15 °C**, condenser **70/75 °C** according to EN14511. This is NOT a validated 35/30 °C waste-heat source to 50/70 °C district heating rating.

- 6 operating model 17 units: 9.42 MW nominal + 1 spare: **7 total**.
- 7 operating model 17 units: 10.99 MW nominal + 1 spare: **8 total**.
- The Simulink difference is 67.538 MWh/year of backup gas and 14.145 MWh/year higher electricity demand with the larger bank.
- At selected Eurostat Slovakia 2025 electricity/gas prices, the bigger bank saves **€2,023.92/year** in modeled variable energy expenditure.

## Investment implication and boundaries

With 2% of extra CAPEX as annual fixed maintenance, a 6% discount rate and 20-year model lifetime, the break-even incremental investment for the seventh operating (eighth installed) unit is only **about €18,883**. That is a screening threshold, not a supplier quote, and does not price reliability or standby service.

**Critical missing evidence:** Manufacturer selection report for the exact 35/30 °C source and 50/70 °C network (also 25/20 °C source), including full/part-load thermal output, COP, pressure losses, minimum turndown, start current and N+1 recovery time. The model's 30-minute failover is a scenario assumption, not real hardware certification.

IT waste-heat reuse does **not** replace independent critical cooling. Size independently to reject approximately **10 MW of rated IT heat** under full IT demand, with redundancy, electrical autonomy and safe failure modes established in engineering design.

**References:** [Carrier 2025 catalogue](https://brandportal.carrier.com/m/7e93b9e9f7e9d2a2/original/10191_PSD_02_2025_61XW_ZE_Short_version.pdf), physical ratings on PDF page 8, indicative single/multi-unit COP plot on page 9; [Eurovent Certified Carrier model 07](https://www.eurovent-certification.com/en/catalog/program/certificate/participant/model/show/199588446).

**Reproducible data:** `capacity_fault_simulink_2025.csv`, `capacity_fault_simulink_2025.json`, `Carrier_2025_nominal_vs_Nplus1_options.csv`, `Carrier_2025_rated_vs_simulated_economics.json`.
