# C91 | Dynamic 500 m³ pool thermostat, isolated synthetic model

## Purpose and provenance
This is an independent continuation of C90, **not** an update to the shared MATLAB/Simulink/SCADA implementation. Input: C90_POOL_HOURLY.csv (8760 synthetic hours for the `covered_no_extra` scenario), SHA256 `0a5e674d316e1d4e223861f1e728ff095a84485b0a4b99da6e38b67af81be8e7`. The C90 hourly heat-source field is `HX_rejected_MW`, **not** a measured or validated physically recoverable waste-heat stream. No source-standard approvals were added; 0/31 primary-source signoffs.

## Physical and control model
- Water volume 500 m³, area 250 m², initial water temperature 28.0 °C. Thermal capacity `C = 500 * 997 * 4.186 / 3,600,000 = 0.5796447222 MWh/K`.
- At every 1-hour step, recompute pool heat loss `Q_loss(T,t)` using the *same assumed* evaporation, makeup, convection, radiation and envelope coefficients as C90, but with the evolving water temperature. Signed ground heat flow allows ground-to-pool heat gain at low water temperatures. Convection/radiation are clamped to nonnegative losses as in C90.
- Thermostat switches ON when `T <= 27.85 °C`, OFF when `T >= 28.05 °C`, otherwise retains its previous state. Active heating targets at most 28.05 °C per hour.
- Hypothetical auxiliary heat pump: `Q_HP,max = min(HX_Rejected * f * COP/(COP-1), 0.075*COP, 0.300)` MW, COP=4 (assumed), recovery fraction `f` scenario-specific. Actual dispatch never exceeds requested heat. Source/electric split `Q_HP = Q_source + P_elec`.
- Optional 50 kW backup operates only when the predicted post-HP water temperature would fall below **27.60 °C**; it does not run merely to force the upper thermostat target.
- Explicit Euler energy balance per hour: `C*(T_next-T) = Q_HP + Q_backup - Q_loss`, where powers in MW are numerically MWh for a one-hour interval.

## Synthetic results
| Counterfactual fraction of HX_Rejected | Backup cap | Min water °C | Hours below 27.5 °C | HP heat MWh/year | Backup heat MWh/year |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0% | 0 kW | 18.173 | 8748 | 0.00 | 0.00 |
| 10% | 0 kW | 27.468 | 2 | 252.76 | 0.00 |
| 10% | 50 kW | 27.600 | 0 | 248.61 | 5.06 |
| 25% | 0 kW | 27.782 | 0 | 258.63 | 0.00 |
| 25% | 50 kW | 27.782 | 0 | 258.63 | 0.00 |
| 50% | 0 kW | 27.782 | 0 | 258.80 | 0.00 |

In this particular synthetic time series, 25% nominal availability keeps the water above the *chosen* 27.5 °C threshold, while 10% misses it for two hours. This is **not a threshold for actual feasibility**. The 25% case has 64.66 MWh/year of *assumed additional HP electricity*, which is not a measured tariff or plant operating cost. Ventilation air heat from C90 remains separate and is not silently included.

## QA and outputs
- C91 model compile PASS; **11/11 self-tests PASS**.
- Independent output-only QA **28/28 PASS**, covering 52,560 hourly rows, 72 monthly rows, 6 scenarios, pinned source, chronological completeness, thermal/electrical/source balances, equipment caps, thermostat-off zero dispatch, comfort hours and annual/monthly reconciliation.
- Adversarial QA **8/8 PASS**, including synthetic STOP flag in a temporary directory, source-hash drift, negative/nonfinite source, invalid recovery fraction and water temperature.
- Plot: `C91_TEMPERATURE_YEAR.png`, 6 daily-sampled trajectories × 365 days. The original first-pass outputs are preserved in `draft_v1_pre_comfort_backup_fix/` to document why a naive backup strategy was rejected. Only the corrected root-level files are accepted.
- No Codex, MATLAB, GPU job, GUI manipulation, source repo edit, remote publishing, OAuth change, or shared SCADA/SLX write.

## Open limitations and exact next engineering step
C90 evaporation and air-flow coefficients are illustrative and uncalibrated. The source/sink temperature levels, heat-exchanger pinch, measured COP, real incremental heat allocation, stratification, dynamic occupancy, water mixing, HVAC coupling and weather are not validated. The 1-hour Euler thermostat is an engineering demonstration, not a calibrated plant controller.

**Next:** obtain independently sourced evaporation/ventilation parameter bounds and measured pool temperatures; build temperature-dependent COP and HX pinch constraints, then compare with the current model using the same 8760-hour timestamps. Keep 31 source signoffs open until primary sources are actually reviewed.
