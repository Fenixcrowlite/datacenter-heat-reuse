# Engineering research release: data centre, pool, district heating and independent IT cooling

**23 October 2026 | Model status: VERIFIED NUMERICAL STUDY**
> Numerical MATLAB/Simulink and Python results only. NOT a commissioned or compliance-certified installation.

### 1. Energy model perimeter
The IT facility is a 10 MW nominal heat scenario, not metered equipment. IT demand remains synthetic; Bratislava 2025 weather comes from NASA POWER gridded reanalysis. PUE is an assumption rather than metered site data.

### 2. Annual IT cooling heat balance
Across 105,120 five-minute Simulink points: 71,833 MWh IT heat, 38,275 MWh actually used IT source heat, 33,558 MWh residual IT heat to reject. Mean rejected load 3.831 MW. When both district and pool reuse are absent, independent backup cooling must support 10 MW design-rated IT heat.

### 3. Hydraulic and ride-through screening
For liquid water rho=997 kg/m³ and cp=4182 J/(kgK), 10 MW across 5K needs roughly 1727 m³/h; a single line at 2 m/s requires 553mm inside diameter. Actual glycol fluid, network layout, pressure drops and hydraulic pump selection are not available.

### 4. Executed Simulink failure tests
New saved IT_Independent_HeatRejection_20261023_SK.slx: six one-hour runs with 5-second steps, all pool and district consumers disabled, water buffer 10m³, T initial 35°C, protection threshold 40°C.

| Scenario | Model max T °C | Did not trip? |
|---|---:|:---:|
| 6 units, 0% derating, 30s | 36.44 | PASS |
| 7 units, 10% derating, 30s | 35.72 | PASS |
| 7 units, 10% derating, 300s | 42.20 | TRIP |
| 6 units, 10% derating, persistent | 122.76 | TRIP |
| 7 units, 20% derating, persistent | 70.74 | TRIP |
| 7 units, 10s pump failure | 37.88 | TRIP |

**Note / Poznámka / Примечание:** Results ABOVE the configured trip threshold are invalid for physical equipment; no IT load shedding or boiling model is included.

### 5. Minimum safety architecture
Independent IT heat rejection must not depend on the heat reuse business. Every nominally 2MW net cooler needs manufacturer proof at the site's maximum outdoor design condition. With 10MW IT, 6 installed units N+1 cover full design only without derating; with 10% derating, 7x2MW would leave 10.8MW after one failure. A 30-second 2MW cooling deficit and 5K buffer interval requires a minimum theoretical 2.88m³ water; this does NOT provide IT chip coolant flow. UPS-supported pumps, independent actuators, hardware safety relays and dual power feeds remain P0.

### 6. Equipment envelopes and unknowns
Carrier 61XWH-ZE17 up to 1570kW nominal at W20/15 source and W70/75 sink, not the target conditions. Oilon ChillHeat P30-P450 max 450kW at B0/W35; S series up to 2000kW at other conditions. Alfa Laval offers industrial gasketed plate pool exchangers. Güntner and Kelvion provide data center recooling systems. Actual 25/20 and 35/30 to 50/70C COP/PLR and effective duty are not confirmed.

### 7. Pool/standards boundary
A 500m³ pool (25×12.5×1.6m) using direct 150kW low-temperature exchanger has preliminary design UA=37.63kW/K with an assumed fouling allowance. Slovak Decree 308/2012 published §8(7) specifies a 28°C maximum for swimming pools, but effective consolidated legislation and licensed STN EN15288-1+A1 require review. Reportable ERF under EU 2024/1364 requires a boundary heat meter.

### 8. RFQs and unresolved work
Created four engineering RFQ drafts for Carrier, Oilon, Alfa Laval and recooler manufacturers. NOT SENT and no vendor quotes obtained. Obtain certified COP/PLR maps, capacity/flow/pressure loss, fault recovery, N+1, commissioning and budget prices, then actual IT/BMS logs, hydraulic schematics, electrical SLD, qualified legal review and safety commissioning test results.

### Source material

- [Carrier 61XWH-ZE 2025, published 1570 kW W20/15 / W70/75](https://brandportal.carrier.com/m/7e93b9e9f7e9d2a2/original/10191_PSD_02_2025_61XW_ZE_Short_version.pdf)
- [Oilon ChillHeat product data](https://oilon.com/wp-content/uploads/2024/04/Oilon_ChillHeat-EN.pdf)
- [Alfa Laval Slovakia plate heat exchangers](https://www.alfalaval.sk/produkty-a-riesenia/prenos-tepla/doskove-vymenniky-tepla/plate-heat-exchangers/)
- [Güntner data center cooling](https://guntner.com/applications/data-centers)
- [Kelvion data center cooling](https://www.kelvion.com/industry-solutions/data-center)
- [ASHRAE Data Centers engineering](https://handbook.ashrae.org/Handbooks/A23/SI/A23_Ch20/a23_ch20_si.aspx)
- [EU delegated regulation 2024/1364 ERF](https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj)
- [Slov-Lex swimming pool requirements, decree 308/2012 original edition](https://static.slov-lex.sk/static/SK/ZZ/2012/308/vyhlasene_znenie.print.html)

### Reproducible outputs
- `independent_cooling_design_scenarios.json` and `cooling_nplus1_derating.csv`
- `IT_Independent_HeatRejection_20261023_SK.slx`
- `test_IT_cooling_failure_SK.m` and `IT_cooling_failsafe_simulink_results.json`
- `cooling_fault_second_scale.csv`, `cooling_failover_sensitivity.csv`
- `RFQ_Carrier_EN.md`, `RFQ_Oilon_EN.md`, `RFQ_AlfaLaval_EN.md`, `RFQ_DryCooler_EN.md`
- `cooling_resilience_calculator.html`
- `FMEA_engineering_gaps.csv`

**No procurement, email delivery, commissioning or operating safety certification has occurred.**
