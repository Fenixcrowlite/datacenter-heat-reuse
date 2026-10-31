# Closed-loop model: data centre, swimming pool and district heating
**MATLAB/Simulink R2026a | 2025 weather | 23 October 2026**

**Status: numerically verified engineering model, not a certified installation or regulatory compliance assessment.**

## Model architecture
A distinct file, **DC_Pool_Coupled_ClosedLoop_20261023_SK.slx**, implements true feedback using three Unit Delay states: pool water temperature, TES energy and thermostat state. Every 300 seconds, the pool draws its actual heat from the data centre source; the remaining source capacity is then allocated to district heating.

- Pool: 500 m³, 25 × 12.5 × 1.6 m, maximum useful heat input 150 kW.
- Thermostat: ON at 27.25 °C, OFF at 27.60 °C; numerical upper bound 27.80 °C.
- Pool equation: **C × ΔT / Δt = Q_pool − Q_losses**.
- Joint source balance: **Q_DC,pool + Q_DC,district ≤ Q_DC,available**.
- Heat pump partition: **Q_HP,out = Q_DC,source + W_compressor**. Compressor electricity is not IT waste heat.

## Executed annual simulations
Four 2025 cases with **105,120 five-minute intervals each** using NASA POWER hourly reanalysis and a still-synthetic IT load profile.

| Case | Pool heat, MWh | DC waste heat to pool, MWh | District gas heat, MWh |
|---|---:|---:|---:|
| 35 °C source, no pool | 0 | 0 | 9,085.89 |
| 35 °C, direct heat exchanger | 250.125 | 250.125 | 9,189.27 |
| 25 °C, pool HP with COP=4 | 250.125 | 187.594 | 7,296.99 |
| 35 °C, 24-hour source outage | 250.000 | 250.000 | 9,404.84 |

An independent Python audit checked **420,480** CSV intervals for source exclusivity and energy conservation. During the simulated data-centre outage, pool heat input was zero. Maximum modeled pool temperature was **27.62 °C**.

## Operating-cost sensitivity
With selected Eurostat Slovakia 2025 industrial-band prices (electricity **€152.07/MWh**, gas **€55.63/MWh fuel**), modeled incremental energy OPEX savings compared with separate gas-boiler pool heating are **€12,306.50/year** for the direct exchanger, and **€4,279.76/year** for the pool HP. CAPEX, additional pumping, HVAC, service and building operation are not included.

## Equipment-performance evidence
Eurovent certified **Carrier 61XWH-ZE07** at the W10-7 water source condition: COP 5.48 with sink outlet 35 °C, 4.71 at 45 °C, 3.92 at 55 °C and 3.17 at 65 °C. The original 0.50 Carnot-factor surrogate differs by **−12.8% to +0.4%** at these points. Such ratings do not validate a 25–35 °C source / 70 °C district supply operating point; out-of-range interpolation is refused.

## Standards and outstanding work
The published Slovak decree 308/2012 identifies 28 °C as a maximum swimming-pool water temperature, pending confirmation of the legally effective current version. The full STN EN 15288-1+A1 text, sensor uncertainty, equipment failure modes, water treatment and independent IT cooling remain unverified. Under EU 2024/1364, a reportable ERF requires boundary-metered reused heat, not these simulated source allocations.

**Sources:** [EU 2024/1364](https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj), [Slov-Lex 308/2012](https://static.slov-lex.sk/static/SK/ZZ/2012/308/vyhlasene_znenie.print.html), [Eurovent Carrier](https://www.eurovent-certification.com/en/catalog/program/certificate/participant/model/show/199588446), [NASA POWER](https://power.larc.nasa.gov/docs/services/api/temporal/hourly/).

**Technical files:** SLX model, Slovak mathematical analysis, reproducible MATLAB scripts, yearly CSVs, independent QA JSON.