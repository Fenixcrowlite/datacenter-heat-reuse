---
date: 2026-10-23
status: VERIFIED_SIMULATION_NOT_CERTIFIED
tags: [datacentrum, bazen, standardizacia, Simulink, use-cases]
---
# Observability DC - bazen: normy, grafy, testy
> [!warning] PUE a ERF sú len scenárové; platná zhoda so všetkými normami NIE JE preukázaná.

## Interaktívny dashboard a správy
- [[Engineering_Dashboard_2026.html]] (otvoriť externým prehliadačom)
- [[Standards_Graphs_Usecases_SK.pdf]]
- [[Standards_Graphs_Usecases_RU.pdf]]
- [[Standards_Graphs_Usecases_EN.pdf]]
- [[kpi_catalog_2025.csv]] - 34 KPI, definície, jednotky, proveniencia
- [[standards_traceability_2026.csv]] - 56 normových požiadaviek
- [[use_case_catalog_2026.csv]] - 36 testovacích scenárov: 22 PASS, 14 BLOCKED
- [[requirements_tests_metrics_traceability.csv]] - naviazanie normy, testu a KPI
- [[signal_dictionary_300s.csv]] - 14 časových signálov

## Grafy modelového roku 2025
### 01_pool_warmup
![[charts/01_pool_warmup.png]]
[Otvoriť SVG](charts/01_pool_warmup.svg)
### 02_monthly_energy
![[charts/02_monthly_energy.png]]
[Otvoriť SVG](charts/02_monthly_energy.svg)
### 03_monthly_HP_electric
![[charts/03_monthly_HP_electric.png]]
[Otvoriť SVG](charts/03_monthly_HP_electric.svg)
### 04_load_duration
![[charts/04_load_duration.png]]
[Otvoriť SVG](charts/04_load_duration.svg)
### 05_IT_heat_allocation
![[charts/05_IT_heat_allocation.png]]
[Otvoriť SVG](charts/05_IT_heat_allocation.svg)
### 06_pool_geometry_sensitivity
![[charts/06_pool_geometry_sensitivity.png]]
[Otvoriť SVG](charts/06_pool_geometry_sensitivity.svg)
### 07_HP_capacity_gas
![[charts/07_HP_capacity_gas.png]]
[Otvoriť SVG](charts/07_HP_capacity_gas.svg)
### 08_COP_reference
![[charts/08_COP_reference.png]]
[Otvoriť SVG](charts/08_COP_reference.svg)
### 09_pool_temperature_distribution
![[charts/09_pool_temperature_distribution.png]]
[Otvoriť SVG](charts/09_pool_temperature_distribution.svg)
### 10_recovery_dispatch_week
![[charts/10_recovery_dispatch_week.png]]
[Otvoriť SVG](charts/10_recovery_dispatch_week.svg)
### 11_thermal_storage
![[charts/11_thermal_storage.png]]
[Otvoriť SVG](charts/11_thermal_storage.svg)
### 12_weather_monthly
![[charts/12_weather_monthly.png]]
[Otvoriť SVG](charts/12_weather_monthly.svg)
### 13_gas_pool_comparison
![[charts/13_gas_pool_comparison.png]]
[Otvoriť SVG](charts/13_gas_pool_comparison.svg)
### 14_independent_cooling_Nplus1
![[charts/14_independent_cooling_Nplus1.png]]
[Otvoriť SVG](charts/14_independent_cooling_Nplus1.svg)
### 150_cooling_fault
![[charts/150_cooling_fault.png]]
[Otvoriť SVG](charts/150_cooling_fault.svg)
### 151_cooling_fault
![[charts/151_cooling_fault.png]]
[Otvoriť SVG](charts/151_cooling_fault.svg)
### 17_hydraulic
![[charts/17_hydraulic.png]]
[Otvoriť SVG](charts/17_hydraulic.svg)
### 18_scenario_COP_lift
![[charts/18_scenario_COP_lift.png]]
[Otvoriť SVG](charts/18_scenario_COP_lift.svg)
### 19_heat_pump_energy
![[charts/19_heat_pump_energy.png]]
[Otvoriť SVG](charts/19_heat_pump_energy.svg)
### 20_metric_provenance
![[charts/20_metric_provenance.png]]
[Otvoriť SVG](charts/20_metric_provenance.svg)

## Potrebné vstupy
- Skutočné 8760h E_IT, E_DC, E_REUSE a spotreba vody
- Certifikované výkony tepelného čerpadla Q(Tsource, Tsink, PLR), COP
- Reálna hydraulika, čerpadlá, nezávislé záložné chladenie
- Úplné STN a účinné právne predpisy, overenie autorizovaným projektantom

## BLOCKED testovacie prípady
- UC-004: Overtemperature sensor offset -> Independent hardware trip keeps actual T<28C
- UC-010: Full heat-reuse system unavailable -> 10MW independent full IT cooling operates
- UC-011: Direct HX thermal approach -> Manufacturer delivers 150kW 35/32 vs 27.5/29.5
- UC-014: Manufacturers thermal map -> Actual signed COP and capacity rated at site PLR
- UC-015: Vendor-certified 10MW duty -> Nameplate at required water source and sink is adequate
- UC-025: UPS pump ride through -> Pump flow sustained, redundant electrical supply validated
- UC-026: Cooling switchgear single fault -> Power selectivity and N+1 UPS verified
- UC-027: DC energy efficiency reporting -> Report official PUE not model 1.36
- UC-028: Regulated energy reuse reporting -> Report E_REUSE/E_DC compliant with regulation
- UC-029: Water resource KPI -> Calculate WUE with meter and unit
- UC-033: Pool chlorinated water chemistry -> Corrosion rating signed by OEM and sampling
- UC-034: Pool water failsafe FAT/SAT -> Independent hardware trip before 28C
- UC-035: IT cooling all sinks lost -> Critical cooling hardware bypass start and server flow maintained
- UC-036: ASHRAE W class selection -> Choose compatible W17/W27/W32/W40/W45 or W+ from actual IT design

## Verejné zdroje
- [ISO/IEC 30134-2:2026](https://www.iso.org/standard/30134-2)
- [EU 2024/1364](https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj)
- [STN EN 15288-1+A1](https://normy.normoff.gov.sk/norma/139372/?lang=en)
- [ASHRAE liquid cooling classes](https://www.ashrae.org/technical-resources/topics-and-initiatives/ai-data-center/introduction-and-purpose)
