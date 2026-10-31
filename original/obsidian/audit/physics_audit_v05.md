# Independent physics audit v0.5

Original outputs untouched.

## Residual checks
| Check | Worst residual | Count > 1e-6 |
|---|---:|---:|
| network | 1.0658141e-13 | 0 |
| HP_first_law | 1.0214052e-13 | 0 |
| HX_balance | 9.980905e-14 | 0 |
| source_overuse | 0 | 0 |
| storage_step | 1.0231815e-12 | 0 |
| gas_capacity_20MW | 0 | 0 |
| HP_capacity_37MW | 0 | 0 |

## Annual energy totals [MWh]
- demand_MWh: 144,000.000
- gas_MWh: 3,600.000
- hp_heat_MWh: 140,993.659
- HP_electric_MWh: 33,946.590
- HX_MWh: 196,400.796
- HP_source_MWh: 107,047.069
- charge_MWh: 3,883.275
- discharge_MWh: 3,289.616

## Issues requiring model changes
- 20 MW gas-boiler limit is declared in the paper but never enforced in dispatch.
- Storage sweep varies both energy capacity and charge/discharge power limits.
- Recovery fraction fitted to reproduce 97.5 percent; this is calibration, not independent validation.
- Source temperature, 300 MWh storage, synthetic weather and electricity prices are assumptions.
- ERF numerator counts delivered heat with HP electricity; check the mandated reporting boundary.
- No hourly unmet-demand output if finite gas boiler capacity is enforced.
- Exergy and economics require paper-by-paper physical-boundary validation.
