# DataCenter Heat Reuse
## Synthetic-data validation, external evidence and standards
**23 October 2026.** Engineering research outputs, not a commissioned or certified installation and not measured data-centre telemetry.

### Evidence sources
**Weather:** NASA POWER, Bratislava (48.1702 N, 17.2127 E), **8,760 hourly values** during 2025; complete temperature, relative humidity and wind. This is gridded reanalysis rather than on-site station measurements. [NASA documentation](https://power.larc.nasa.gov/docs/services/api/temporal/hourly/).

**Electricity:** Eurostat `nrg_pc_205`, Slovakia, industrial annual electricity band **70,000–149,999 MWh**, recoverable VAT excluded (X_VAT), weighted average for 2025: **€152.07/MWh**. [Electricity source](https://ec.europa.eu/eurostat/databrowser/view/nrg_pc_205/default/table?lang=en).

**Natural gas:** Eurostat `nrg_pc_203`, Slovakia, industrial annual fuel band **100,000–999,999 GJ**, X_VAT, 2025: **€55.63/MWh fuel**. [Gas source](https://ec.europa.eu/eurostat/databrowser/view/nrg_pc_203/default/table?lang=en).

**Power Usage Effectiveness:** modeled 1.20 versus Uptime Institute 2026 industry average 1.52 and capacity-weighted average 1.36. These are distinct distributions, not equipment acceptance limits. [Uptime](https://intelligence.uptimeinstitute.com/resource/growing-pue-advantage-larger-data-centers).

### Actual MATLAB simulation comparison
The unchanged `dchr.simulate_system` core was executed with the synthetic weather generator and NASA POWER 2025 hourly reanalysis; both experiments use the **same synthetic IT demand profile**.

| Variable | Synthetic weather | NASA 2025 |
|---|---:|---:|
| Mean ambient temperature [°C] | 10.47 | 12.09 |
| Annual district heat demand [MWh] | 59,430 | 56,794 |
| Annual heat pump electricity [MWh] | 10,089 | 9,766 |
| Backup gas heat [MWh] | 10,074 | 9,086 |

Replacing the synthetic weather with NASA reanalysis reduced modeled annual heat demand by **2,636 MWh (4.44%)**.

### Indicative economic sensitivity
At Eurostat 2025 period-weighted prices and NASA 2025 weather, the model estimates annual variable energy operating savings of **€1,464,015** against a 90%-efficient gas-boiler counterfactual. The synthetic-price baseline would estimate **€1,673,853**. This is **not** a payback forecast: CAPEX, additional pumping, real contract prices, HVAC and pool loads, maintenance and demand charges are excluded.

### ERF model defect and boundary conditions
The existing `compute_metrics.m` reports ERF **0.48835** under NASA 2025 and PUE 1.36 because it counts heat delivered by the heat pump, including its compressor electricity. Subtracting electricity gives a **source-heat proxy of 0.39008**, but this is **not a compliant measured ERF**: EU 2024/1364 / EN 50600-4-6 requires metering reused heat where it crosses the data-centre boundary. [EU legal source](https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj).

### Swimming-pool standards and safety
Review [STN EN 15288-1+A1](https://normy.normoff.gov.sk/norma/139372/?lang=en), [STN EN 15288-2](https://normy.normoff.gov.sk/norma/128828/?lang=en) and the currently effective [Slovak Decree 308/2012](https://www.slov-lex.sk/ezbierky/pravne-predpisy/SK/ZZ/2012/308/20121015.html). The published §8(7) text specifies a maximum swimming-pool water temperature of **28°C**. The old thermostat cut-off of **28.2°C** is flagged for redesign, accounting for measurement uncertainty and thermal overshoot. The 25 × 12.5 × 1.6 m illustration yields 500 m³ but is not established as World Aquatics-certified geometry.

### Outstanding work
On-site data-centre IT/cooling measurement, actual heat-exchanger transfer, manufacturer COP map, legal full-text review, pool psychrometrics, ventilation/dehumidification, pump hydraulics, contractual electricity pricing and complete heat metering remain unverified. Parallel Simulink pool work was left untouched.

**Artifacts:** 8,760-row NASA CSV, 18-case sensitivity CSV, MATLAB run output, monthly chart, source matrix, standards register and tests.
