---
tags: [datacentrum, odpadove-teplo, bazen, simulink, matlab, validacia, closed-loop]
created: 2026-10-23
status: VERIFIED_SIMULINK_8760H_NOT_REAL_WORLD_VALIDATION
owner: calibration_closed_loop
---
# Skutočná spätná väzba: DataCenter → Bazén + Teplovodná sieť (Simulink)

> [!important] Pôvod modelu a bezpečnosť
> Nový nezávislý model `DC_Pool_Coupled_ClosedLoop_20261023_SK.slx`. Pôvodné `matlab/pool_500m3/Bazen_DC_Ohrev_500m3_SK.slx` a `DCHR_*v85/v86` zostali nezmenené. Údaje o IT, COP, bazénovej hale a vykurovaní sú inžinierske scenáre. Bez zodpovedného projektanta a úplného overenia normy nejde o certifikovaný bezpečnostný systém.

## 1. Čo teraz pracuje v Simulinku

Každých **300 s** sa vykonáva jeden časovo diskrétny krok so skutočnou vzájomnou väzbou:

1. Výstupné stavy predchádzajúceho kroku cez bloky **Unit Delay (T vody, energia TES, stav termostatu)**.
2. MATLAB Function blok `DC_bazen_spatna_vazba` vypočíta skutočne dodané teplo bazénu s ohľadom na teplotu, výpar, plachtu a dostupný DC zdroj.
3. Odpočítané teplo DC už nie je dostupné tepelnému čerpadlu pre teplovodnú sieť.
4. Zvyšný výkon zohľadní zásobník TES a pomocný plynový zdroj, stav akumulátora sa vráti cez Unit Delay.
5. Žiadne predpočítané `Pool_Q` sa do pôvodného bazénového regulátora nereprezentuje ako nezávislý vstup.

Tým je rozdelenie zdroja **na každom kroku fyzikálne uzatvorené**, nie iba hodinová rezervácia maxima ako v predchádzajúcej kalibračnej vetve.

## 2. Základné matematické rovnice

$$
C=\rho Vc_p = 997\cdot500\cdot4182=2\,084\,727\,000\ \mathrm{J/K}
$$

$$
T_{k+1}=T_k+\frac{\Delta t}{C}\left(\dot Q_{pool,k}-\dot Q_{loss,k}\right), \qquad \Delta t=300\ \mathrm{s}
$$

$$
\dot Q_{pool} = \dot Q_{DC,pool}+W_{HP,pool}
$$

$$
\dot Q_{DC,pool}+\dot Q_{DC,DH}\leq\dot Q_{DC,available}
$$

$$
\dot Q_{DH,HP}=\dot Q_{DC,DH}+W_{HP,DH}
$$

$$
\dot Q_{DH,demand}=\dot Q_{DH,HP}-\dot Q_{TES,charge}+\dot Q_{TES,discharge}+\dot Q_{gas}
$$

Pre zdroj 35 °C a vodu < 28 °C režim priamy výmenník vyžaduje $T_{source}\geq T_{pool}+3$ K. Je to **nutná teplotná podmienka**, nie katalógovo overený výkon výmenníka. Zdroj 25 °C používa bazénové TČ so scenárovým COP=4.

Termostat zapína pri 27,25 °C a vypína pri 27,60 °C. Výkon sa obmedzuje tak, aby ďalší modelový krok neprekročil **27,80 °C**. Konečný limit 28 °C vychádza z publikovaného §8 ods. 7 vyhlášky 308/2012 Z.z.; aktuálnu účinnú verziu právnej normy je ešte nutné oficiálne verifikovať. Pred fyzickou realizáciou treba merať neistotu snímačov, teplotnú zotrvačnosť a oneskorenia ventilov.

## 3. Validácia: ročná simulácia a blackout test

Použité vstupy: NASA POWER, hodinová reanalýza 2025 Bratislava (8760 hodín), syntetická záťaž IT a modelové tepelné pomery. 8760 × 12 = **105 120 Simulink krokov na scenár**.

| Scenár | Bazén MWh | DC zdroj do bazéna MWh | Elektrina bazénového TČ MWh | Plyn pre teplovodnú sieť MWh |
|---|---:|---:|---:|---:|
| Zdroj 35 °C, bez bazéna | 0 | 0 | 0 | 9 085,895 |
| Zdroj 35 °C, bazén priamo | 250,125 | 250,125 | 0 | 9 189,267 |
| Zdroj 25 °C, bazén cez TČ | 250,125 | 187,594 | 62,531 | 7 296,988 |
| Zdroj 35 °C, 24h blackout v hodine 48–72 | 250,000 | 250,000 | 0 | 9 404,845 |

Blackout: v hodinách 48 až 72 je $\dot Q_{DC,available}=0$. Simulácia potvrdila nulový odber zdroja a nulové vykurovanie bazéna z DC počas odstávky, pričom plynový záložný zdroj pokrýva požadované teplo siete. **Nejde o potvrdenie reálnej ochrany serverov pri zlyhaní chladenia.**

Nezávislý Python QA čítal všetky štyri 105 120-riadkové CSV. Otestoval $Q_{pool}=Q_{DC,pool}+W_{pool}$, $Q_{DH,HP}=Q_{DC,DH}+W_{DH}$ a $Q_{DC,pool}+Q_{DC,DH}\leq Q_{DC,available}$ pre každý krok. Najvyššia vypočítaná teplota bola **27,620 °C**. Rezíduá bilančných rovníc sú na úrovni numerickej presnosti.

## 4. Ekonomika: nový uzatvorený model

V porovnaní s variantom rovnakého bazéna vykurovaného samostatným plynovým kotlom (modelový $\eta_{gas}=0,90$) a pri Eurostat 2025 SK tarifách 152,0726 EUR/MWh elektrina a 55,6348 EUR/MWh plyn:

- Priamy 35 °C výmenník: **12 306,50 EUR/rok** modelovej dodatočnej úspory.
- Bazénové TČ pri 25 °C (COP=4): **4 279,76 EUR/rok** modelovej dodatočnej úspory.

Zohľadňuje sa zníženie tepla pre sieť a potrebný dodatočný plyn a kompresor. Bez CAPEX, projektovania, čerpadiel, distribučných poplatkov a nákladov na klimatizáciu plavárne.

## 5. Overenie modelového COP voči certifikácii

Na základe [Eurovent Carrier 61XWH-ZE07](https://www.eurovent-certification.com/en/catalog/program/certificate/participant/model/show/199588446), skúšobná voda zdroja W10-7:

| Teplá voda (výstup) °C | Výrobcom certifikované COP |
|---|---:|
| 35 | 5,48 |
| 45 | 4,71 |
| 55 | 3,92 |
| 65 | 3,17 |

Nezávislý test `run_manufacturer_cop_comparison_SK.m` porovnával pôvodný model Carnot/0,5 s týmito štyrmi bodmi. Rozdiel bol medzi **-12,8 % až +0,4 %**. Rozhodnutie: pri fyzicky netestovanej kombinácii (zdroj 25/35 °C a dodávka 70 °C) **NEEXTRAPOLOVAŤ**. Funkcia `manufacturer_cop_reference_SK.m` vracia NaN a stav UNVERIFIED mimo zverejneného rozsahu; táto séria nie je zatiaľ dosadená ako COP reálneho modelu.

## 6. Skutočné výstupy a vlastníctvo

Súbory v tomto adresári: `DC_Pool_Coupled_ClosedLoop_20261023_SK.slx`, `build_closed_loop_simulink_SK.m`, `dc_pool_coupled_step_SK.m`, `run_closed_loop_cases_SK.m`, `simulink_closed_loop_summary_8760h.json`, `closed_loop_independent_QA_2025.json`, `closed_loop_incremental_opex_2025.json`, `manufacturer_certified_points_carrier.csv`, `carrier_cop_certified_vs_scenario.csv`.

Každý `*_8760h.csv` predstavuje priamo výstup uloženej Simulink schémy pre 105 120 intervalov. Obrovské výpisy ostávajú v OneDrive pracovnej vetve, do Obsidianu sa kopírujú iba malé overiteľné artefakty.

## 7. Nedokončené pre inžinierske schválenie

- Úplná Stateflow šesťstavová architektúra v85/v86 a logika režimov zatiaľ nie sú integrované do tohto samostatného MATLAB Function bloku.
- Skutočný COP mapovaný podľa zdrojovej/výstupnej teploty a čiastočného výkonu, prevádzkové limity výmenníka.
- Tlakové straty, hydraulika, čerpadlá, VZT a odvlhčovanie plavárne, návštevníci, voda v obehu.
- Úplná metodika teplotných snímačov, prechodové stavy a záložné IT chladenie.
- Merania na hranici dátového centra pre reálny ERF podľa [EU 2024/1364](https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj). Používané ukazovatele zostávajú modelové.
- Či sa zadaná geometria považuje za verejný alebo závodný plavecký bazén podľa normy [STN EN 15288-1+A1](https://normy.normoff.gov.sk/norma/139372/?lang=en), a aktuálna právna účinnosť vyhlášky.

**Stav:** Numerický closed-loop Simulink overený; plne normalizovaný a kalibrovaný priemyselný projekt zatiaľ nie.
