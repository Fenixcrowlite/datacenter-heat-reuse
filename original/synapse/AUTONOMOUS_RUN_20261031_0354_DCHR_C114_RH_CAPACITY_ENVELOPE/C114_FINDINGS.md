# C114 · Synthetic pool-room RH equipment-capacity envelope

**Scope:** independent, task-local continuation of C112. Source model and C111/C106 datasets are SHA-pinned; shared OneDrive/SCADA/Simulink files were not modified. This is not a manufacturer's equipment selection.

## Model and criterion

- Room air inventory: 3540 kg dry air; ventilation: 3540 kg dry air per hour.
- Indoor temperature: 29 °C, ideal outdoor coil pretreatment from C112, one-hour exact well-mixed response.
- Acceptable **hour-end** RH band: 45–65% for every one of 8760 synthetic hours.
- Search tolerance: 0.01 kg/h, using failed lower and passing upper capacity brackets.
- Two controls: symmetric capacity (same maximum dehumidification and humidification) and asymmetric pair (each actuator independently minimized while the other is unconstrained, then the pair jointly rechecked).

## Numerical results

| Source dispatch | Symmetric minimum passing (kg/h) | Dehumidification minimum passing (kg/h) | Humidification minimum passing (kg/h) | Joint band violations |
|---|---:|---:|---:|---:|
| Water first | 45.6543 | 45.6543 | 29.6973 | 0 / 8760 |
| Air first | 45.6543 | 45.6543 | 29.6875 | 0 / 8760 |

The independently minimized pair is sufficient **only within this one-way synthetic model**. For water-first, joint min/max RH are approximately 45.006% / 64.996%. For air-first, approximately 45.001% / 64.996%.

The symmetric 45.65 kg/h capacity should **not** be presented as the required humidifier capacity; the asymmetric search finds roughly 29.69 kg/h under these assumptions.

## QA

- C112 base self-tests: 21/21 PASS.
- Independent second implementation of the room-mixing recurrence, **without calling C112.step**, replayed 140,160 hourly reference steps and performed 94 numeric checks.
- Three negative controls caught malformed capacity, altered expected result and nonfinite value.
- Initial QA defects corrected before acceptance: missing second actuator argument and a Pa-versus-kPa pressure mismatch. The pressure unit is kPa (101.325), matching C104; the QA now passes.

## Limits and next engineering step

This is a synthetic sizing *sensitivity*, not field validation. It checks hour endpoints, not within-hour transients; outdoor coil drying is unlimited; RH does not feed back into evaporation, COP or heat dispatch. The 3540 kg inventory and 3540 kg/h ventilation are assumptions, not measured geometry or flow. Primary source confirmations remain **0/31**.

**Next:** implement a physically consistent two-way RH → evaporation → latent heat → pool temperature/heat dispatch iteration, with a conservation test and baseline regression. Obtain real pool dimensions, airflows and equipment curves before selecting hardware.
