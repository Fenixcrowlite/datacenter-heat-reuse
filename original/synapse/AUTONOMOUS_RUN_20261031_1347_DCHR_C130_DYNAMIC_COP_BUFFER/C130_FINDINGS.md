# C130 | Finite data-center waste heat, thermal buffer, and temperature-dependent COP

## Scope
An isolated seven-day synthetic extension of C129/C128. It does **not** edit the operating SCADA, MATLAB/Simulink, GUI, worktrees, or vendor settings. Six scenarios at 15-minute resolution (4032 state transitions). The existing Synapse DataCenter task remains queued.

## Assumptions and equations
- Thermal source available: scarce profile 5 kW at night, 12 kW otherwise; abundant profile 25 kW. Source heat is added to a 0 or 30 kWh buffer.
- Source temperature: 15 or 22 °C base plus 2 °C daily sinusoid; sink temperature: 40 + 0.3(28 - pool temperature) °C.
- **Illustrative, not manufacturer-calibrated:** COP = clamp[0.32 (T_sink + 273.15)/(T_sink - T_source), 1.5, 6.5].
- Thermal output = electrical input + recovered source heat; recovered heat = thermal output (1 - 1/COP).
- Conservation every interval: source inflow + buffer before = recovered heat + buffer after + spilled heat.
- Source shortage overrides commanded output and may cause a faster downward change than the nominal 2 kW/15 min actuator ramp.
- The existing C128 room and pool models, 30-minute command delay, and 20 kW output cap are preserved.

## Measured synthetic results (seven days)
| Scenario | Heat delivered (MWh) | Electricity (MWh) | Waste heat spilled (MWh) | Final pool °C | RH>65% intervals |
| --- | ---: | ---: | ---: | ---: | ---: |
| Water priority, scarce/cold, no buffer | 2.0574 | 0.5202 | 0.0868 | 28.0008 | 442 |
| Water priority, scarce/cold, 30 kWh buffer | 2.1602 | 0.5439 | 0 | 28.0006 | 368 |
| Water priority, scarce/warm, 30 kWh buffer | 1.9856 | 0.3616 | 0 | 27.9914 | 523 |
| Air priority, scarce/cold, no buffer | 2.1399 | 0.5421 | 0.0262 | 27.1186 | 316 |
| Air priority, scarce/warm, 30 kWh buffer | 1.9889 | 0.3649 | 0 | 26.9270 | 315 |
| Water priority, abundant/warm, 30 kWh buffer | 2.2694 | 0.4146 | 0 | 28.0000 | 364 |

**Interpretation:** A finite thermal buffer captures source heat otherwise spilled in the scarce/cold case. Higher COP does not guarantee more thermal delivery under a fixed **waste-heat availability** constraint: the recovered-heat share rises, so thermal output can become more constrained by the available source energy. The observed humidity/temperature trade-offs depend on synthetic room, pool and heat-source assumptions.

## QA and provenance
- 8 embedded tests PASS; 4032 independent CSV-row validations and 9 deliberately corrupted-row controls PASS.
- Independent recomputation checks source-buffer conservation, electrical and heat-pump balance, COP formula, thermal cap, buffer capacity, state continuity and scenario aggregates.
- First simulation attempt failed on surplus output during down-ramp. Corrected to prohibit thermal output exceeding live demand. Initial independent QA negative-control selection also corrected; only final successful QA is accepted.
- No equipment datasheet calibration, no field validation, no primary-source signoffs added (0/31).
- Do not infer compressor electrical ratings, real savings, or real pool performance from these values.

## Next
Use manufacturer COP(T_source,T_sink,part-load) maps and measured data-center waste-heat availability; then run an independently checked interval-wise source/storage/electricity balance with thermal buffer losses, charge/discharge limits and equipment minimum run times. Keep all original OneDrive models immutable until explicit integration approval.
