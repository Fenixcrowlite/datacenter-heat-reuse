# Annual coupled model: data centre, district heating and swimming pool

*Independent MATLAB R2026a simulations with 2025 weather reanalysis, 23 October 2026*

> **Research scenario only. Not a certified system design or monitored operating plant.**

Goal: evaluate data-centre waste-heat utilisation for a district-heating network with an additional swimming-pool consumer. External air temperature comes from the NASA POWER hourly gridded reanalysis. IT electrical load, equipment characteristics and pool environment remain engineering assumptions.

## Methodology and energy balances

Pool: 25 m × 12.5 m × 1.6 m, volume 500 m³, water area 312.5 m². Initial temperature 16 °C, thermostat switching 27.25/27.60 °C, model safety ceiling 27.80 °C. Maximum pool heat input 150 kW; 08:00-20:00 local Bratislava opening hours, covered overnight.

Governing equation: C·dT/dt = Q_heating - Q_evaporation - Q_convection - Q_radiation - Q_structure - Q_makeup - Q_other, with C = ρ·V·cp. Pool integration uses a 300-second step nested within one-hour district dispatch.

Heat pump partition: Q_HP,out = Q_DC,source + W_compressor. Compressor electricity is not recovered IT waste heat. The reported ERF_source_proxy is only a source-extraction indicator, not the EU 2024/1364 metered energy-reuse factor.

To avoid double allocation, the maximum 5-minute pool source draw within every hour is reserved before assigning the remaining source to district heating. This conservative hourly interface can underutilise heat within individual subintervals.

## Annual simulation results

| Case | Pool MWh | DC source MWh | Gas MWh | DC to pool MWh |
|---|---|---|---|---|
| 35°C source without pool | 0.0 | 38,107.5 | 9,085.9 | 0.0 |
| 35°C direct pool exchanger | 250.1 | 38,238.7 | 9,234.4 | 250.1 |
| 25°C source without pool | 0.0 | 36,689.7 | 7,218.9 | 0.0 |
| 25°C pool heat pump | 250.1 | 36,793.7 | 7,331.1 | 187.6 |

## Operating-energy comparison

Additional modelled savings versus independent gas-boiler heating of an equivalent pool load at 90% efficiency: direct exchanger 10,920 EUR/year, COP=4 pool heat pump 3,542 EUR/year. The displacement of heat from district heating and additional gas/HP electricity are included. CAPEX, pumps, service and natatorium HVAC are excluded.

## Pool-parameter sensitivity

500 m³ with overnight cover: 250.1 MWh/year; 1000 m³ with cover: 388.8 MWh/year; 500 m³ uncovered: 324.0 MWh/year. The structure UA is scaled geometrically, not calibrated from a building-envelope design.

## Verification and limitations

The pool-disabled branch exactly reproduced the original dchr.simulate_system heat pump, gas and storage results. Pool-energy conservation and exclusive DC source allocation passed. Peak model pool water temperature was 27.62 °C. This does not validate real sensor uncertainty, valve lag or pool safety compliance.

## Authoritative datasets and references
- [NASA POWER 2025, 8760h Bratislava, gridded reanalysis](https://power.larc.nasa.gov/docs/services/api/temporal/hourly/)
- [Eurostat non-household electricity nrg_pc_205, Slovakia 2025](https://ec.europa.eu/eurostat/databrowser/view/nrg_pc_205/default/table)
- [Eurostat non-household gas nrg_pc_203, Slovakia 2025](https://ec.europa.eu/eurostat/databrowser/view/nrg_pc_203/default/table)
- [EU Commission Delegated Regulation 2024/1364 PUE & ERF](https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj)
- [Slovak Decree 308/2012 §8 swimming pools published text](https://static.slov-lex.sk/static/SK/ZZ/2012/308/vyhlasene_znenie.print.html)
- [STN EN 15288-1+A1 pool safety design](https://normy.normoff.gov.sk/norma/139372/?lang=en)

Outstanding: actual hourly IT power, manufacturer partial-load COP tables, coolant temperatures and flows, natatorium occupancy and dehumidification, boundary metering for ERF, contracted tariffs, hydraulic losses and complete currently effective standards. Concurrent pool Simulink files were not modified.

Reproducibility: run_coupled_annual_SK.m, simulate_coupled_pool_SK.m, coupled_scenarios_2025.csv, four 8760-hour CSVs and pool_volume_cover_sensitivity_2025.csv.

![[coupled_annual_SK.png]]
