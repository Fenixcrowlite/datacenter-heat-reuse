# C92 | ASHRAE evaporation reference sensitivity, isolated DataCenter pool model

## Primary reference inspected
ASHRAE Handbook 2023, HVAC Applications, Chapter 6, *Indoor Swimming Pools* (official publisher):
https://handbook.ashrae.org/Handbooks/A23/SI/A23_Ch06/a23_ch06_si.aspx
Reviewed 2026-10-30. The official chapter provides the empirical evaporation relation (Eq. 2), SI coefficient terms 0.089 and 0.0782 times air speed, and activity factors: unoccupied 0.5; public/school 1.0; wave pool at least 1.5. It recommends measuring actual operating air/water temperatures and relative humidity. This review does **not** sign off any of the existing 31 project sources, because their identifiers and validation requirements have not been reconciled.

## Dimensional calculation
Using the chapter's Equation (2) with vapor pressure difference Δp in kPa, latent enthalpy Y in kJ/kg and air speed V in m/s:

`m_evap [kg/s] = A [m²] * Δp [kPa] * (0.089 + 0.0782 V) / Y [kJ/kg] * F_a`.

At water 28 °C and assumed V=0.1 m/s, Y≈2434.892 kJ/kg:

`K_ref = 3600*(0.089+0.0782*0.1)/2434.892 ≈ 0.1432 kg/(m² h kPa)`.

Effective reference coefficients are ≈0.0716 for unoccupied and ≈0.1432 for public-pool occupancy. Previous C90/C91 assumptions were 0.12 for unoccupied and 0.18 for occupied, **higher** than these reference examples. A 0.15 nighttime-cover multiplier is still assumed, not validated by the chapter or a measured cover specification.

## Same 8760-hour synthetic source, same thermostat, same hypothetical COP
| Variant | Hypothetical recoverable fraction | Minimum water °C | Hours below 27.5 °C | HP heat MWh/year |
| --- | ---: | ---: | ---: | ---: |
| C91 original assumed evaporation | 10% | 27.468 | 2 | 252.76 |
| ASHRAE-informed evaporation | 10% | 27.653 | 0 | 197.36 |
| C91 original assumed evaporation | 25% | 27.782 | 0 | 258.63 |
| ASHRAE-informed evaporation | 25% | 27.796 | 0 | 201.76 |

The approximate 22% decrease in modeled annual heat-pump heat is a **sensitivity to the chosen evaporation model**, not an experimentally verified efficiency gain. It illustrates why the unvalidated C90 evaporation coefficient is a critical assumption.

## QA and boundaries
- C92 implementation compile PASS, self-tests **7/7 PASS**.
- Independent output/reference QA **29/29 PASS**, including source and C91 script SHA pins, equation unit conversion, official activity factors, exact C91 baseline reconciliation, 4 scenarios, energy conservation, source split, and no false signoff.
- C91 baseline source CSV and scripts remain untouched. C92 outputs are task-local only.
- Air velocity 0.1 m/s, occupied hours, public-pool classification, cover factor, water/air conditions, heat-exchanger source availability and COP are still assumed.
- HVAC air-side load and dehumidification were not integrated. Source/sink temperature pinch and heat allocation are not verified.
- No MATLAB/SCADA/SLX/shared GUI modifications, no new Codex or GPU job.

## Exact next executable step
Map this official ASHRAE chapter to the project's 31-source checklist without claiming approvals prematurely. Then calibrate actual pool classification, air speed, nighttime cover effectiveness, hourly occupancy, measured temperatures and RH. Re-run coupled pool + ventilation + dehumidification loads, and validate HX temperature pinch/COP using real plant data.
