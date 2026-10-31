# DataCenter Heat Reuse
## Validácia syntetických dát a normatívny audit (SK)
**Dátum:** 23.10.2026 | **Stav:** inžinierska simulácia s reálnymi externými údajmi, nie certifikácia zariadenia.

### 1. Datové zdroje
- **Počasie:** NASA POWER, súradnice Bratislava 48,1702 N a 17,2127 E; rok 2025, **8760 hodinových pozorovaní reanalýzy**, 100 % dostupnosť. Nie sú to merania priamo na objekte. [NASA POWER](https://power.larc.nasa.gov/docs/services/api/temporal/hourly/).
- **Elektrina:** Eurostat `nrg_pc_205`, Slovensko, pásmo **70 000-149 999 MWh/rok**, bez vratnej DPH (X_VAT), rok 2025: **152,07 EUR/MWh** ako časovo vážený priemer dvoch polrokov. [Eurostat](https://ec.europa.eu/eurostat/databrowser/view/nrg_pc_205/default/table?lang=en).
- **Plyn:** Eurostat `nrg_pc_203`, Slovensko, pásmo **100 000-999 999 GJ/rok**, X_VAT, rok 2025: **55,63 EUR/MWh paliva**. [Eurostat](https://ec.europa.eu/eurostat/databrowser/view/nrg_pc_203/default/table?lang=en).
- **PUE:** Uptime Institute 2026: priemer 1,52, kapacitne vážený priemer 1,36; hodnota 1,20 je pôvodný efektívny modelový scenár. [Uptime Institute](https://intelligence.uptimeinstitute.com/resource/growing-pue-advantage-larger-data-centers).

### 2. MATLAB - reprodukovateľný experiment
Na rovnakom fyzikálnom jadre `dchr.simulate_system` bolo spustené syntetické počasie a skutočný meteorologický reanalytický rok 2025. Profil elektrického zaťaženia IT je v oboch prípadoch **rovnaký a stále syntetický**.

| Výstup | Syntetická teplota | NASA POWER 2025 |
|---|---:|---:|
| Ročná priemerná teplota [°C] | 10,47 | 12,09 |
| Potreba tepla [MWh/rok] | 59 429,98 | 56 793,70 |
| Elektrina tepelného čerpadla [MWh/rok] | 10 088,95 | 9 765,80 |
| Záložné plynové teplo [MWh/rok] | 10 074,39 | 9 085,91 |

**Zmena potreby tepla: -2 636,28 MWh (-4,44 %)**. Je to zmena výsledku modelu, nie chyba meracieho prístroja.

### 3. Finančná citlivosť a hranice
Pri počasí NASA 2025 a pri štatistických cenách Eurostat vychádza **modelová ročná prevádzková úspora 1 464 015 EUR** oproti alternatíve s plynovým kotlom pri účinnosti 90 %. Pri starých syntetických cenách bola modelová úspora **1 673 853 EUR**.

**Výhrady:** hodnota neobsahuje CAPEX, distribučné a prevádzkové náklady na čerpadlá, skutočný kontrakt ceny, daňové podmienky, náklady plavárne, ani spotrebu vody. Zhodnotenie nie je štúdiou návratnosti.

### 4. Kontrola ERF a legislatívy
Pôvodný `compute_metrics.m` vypočítal ERF 0,48835 pre NASA 2025 pri PUE 1,36 ako všetko teplo dodané do siete delené energiou DC. Takto však započítava aj energiu kompresora. Po odpočítaní spotreby kompresora vychádza **orientačný pomer 0,39008**, stále však **NIE je meraním ERF podľa EN 50600-4-6**. Nutný je merač na hranici dátového centra. [EU 2024/1364](https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj).

Bezpečnosť verejného plaveckého bazéna: [STN EN 15288-1+A1](https://normy.normoff.gov.sk/norma/139372/?lang=en), [STN EN 15288-2](https://normy.normoff.gov.sk/norma/128828/?lang=en). Podľa publikovaného § 8 ods. 7 vyhlášky [308/2012 Z. z.](https://www.slov-lex.sk/ezbierky/pravne-predpisy/SK/ZZ/2012/308/20121015.html) je najvyššia teplota plaveckého bazéna 28 °C. Pred riadiacou implementáciou je potrebné overiť aktuálne účinné znenie predpisu. Starý výstup termostatu **28,2 °C** nesmie zostať neovereným návrhom.

### 5. Výpočtové vzťahy
- Bilancia potreby tepla: `Q_demand(t) = (2 MW + 18 MW × clamp((16 - T_air)/(16 - (-12)), 0, 1.15)) / 0.94`.
- Energetický pomer dátového centra: `PUE = E_DC / E_IT`.
- Normatívny ERF: `ERF = E_REUSE / E_DC`, s E_REUSE meranou na hranici DC.
- Modelové OPEX: `(Q_demand - Q_gas)/eta_boiler × price_gas - W_HP × price_electricity` (kladná hodnota znamená úsporu oproti plynovej referencii).

### 6. Rozpracované úlohy
Nedokončené: meraná spotreba IT, meraná teplota a prietok chladiaceho média, mapa COP tepelného čerpadla, zúčtovanie skutočných cien, presná hydraulika, rok prevádzky bazéna, vzduchotechnika a preukázanie aktuálnej normovej zhody. Existujúci Simulink bazéna spravuje paralelná vetva a nebol prepísaný.

**Prílohy:** `NASA_2025_weather_summary.json`, `matlab_weather_compare.csv`, `weather_pue_price_sensitivity_18_cases.csv`, `normative_compliance_matrix_SK.csv`, `monthly_weather_vs_synthetic_SK.png`.