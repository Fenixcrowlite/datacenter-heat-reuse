# Technický výber zariadení | DataCenter Heat Reuse
**Dátum: 23.10.2026 | Stav: technický predvýber a ekonomický screening, nie záväzná objednávka.**

## Rozhodnutie
Preferovaná vetva bazéna je **priamy nízkoteplotný výmenník pri zdroji 35 °C**, iba ak výrobca doloží výkon **150 kW** pri skutočných štyroch koncových teplotách a celkové dodané investičné náklady zostanú ekonomicky odôvodnené. Pre zdroj 25 °C tento konkrétny režim priameho výmenníka nevychádza, alternatívou je samostatné TČ bazéna alebo odber už ohriatej vody z distribúcie.

## Kľúčová oprava katalógového výkonu
Pahlén Maxi-Flo Titanium MFT680 uvádza 200 kW pri **teplotnom rozdiele 60 K**, plocha 2,11 m². Tieto údaje **nepotvrdzujú** 150 kW pri zdroji 35 °C a bazéne 27,5 °C. Musí nasledovať individuálny výber, napríklad u Alfa Laval alebo u iného dodávateľa titánových nízkoteplotných doskových výmenníkov. [Pahlén](https://www.pahlen.com/products/pool-heating/heat-exchangers/maxi-flo-titanium/), [Alfa Laval](https://shop.alfalaval.com/en-gb/pool-heating--c005).

## Návrhové parametre 150 kW
- Horúca strana: **35 → 32 °C**, potreba prietoku **43,17 m³/h**.
- Bazénová strana: **27,5 → 29,5 °C**, potreba prietoku **64,76 m³/h**.
- Protivýmenové LMTD **4,983 K**; nutné čisté UA **30,10 kW/K**; s faktorom 1,25 **37,63 kW/K**.
- Pri predpokladanom celkovom U=1500 W/(m²K) vychádza plocha približne **25,1 m²**. U nie je katalógovo overené a musí zohľadniť zanášanie a kvalitu vody.
- Pri zdroji **32 °C** ide asi o **63,9 m²** v tom istom modeli, pri **40 °C** asi **12,5 m²**. Pri 25 alebo 30 °C je daná kombinácia výstupných teplôt termodynamicky nemožná.
- Hydraulické straty 70 kPa na zdroji a 80 kPa na bazéne sú **scenárové**, rovnako ako účinnosť čerpadiel 60 %. Spolu 3,80 kW počas kúrenia; približne **8,52 MWh/rok** aj so základnou automatikou, **1 296 EUR/rok** pri zvolenej cene elektriny.

## Predvýber zariadení
| Zariadenie | Kandidát | Stav |
|---|---|---|
| Výmenník 150 kW pri malom ΔT | Alfa Laval, projektovaný doskový titánový výmenník | **RFQ**, plocha a tlaková strata musia byť doložené |
| Výmenník referenčný | Pahlén MFT680 | **NEPOUŽÍVAŤ 200 kW** pre tento teplotný režim bez výrobného prepočtu |
| Čerpadlo uzavretej čistej strany | Grundfos TPE | cca 43,2 m³/h pri 70 kPa, potvrdiť krivku |
| Čerpadlo bazénovej vody | SPECK BADU 21-80/33G alebo podobná bazénová séria | cca 64,8 m³/h pri 80 kPa, potvrdiť Q-H, chémiu vody |
| Teplota a energia | Siemens SITRANS TS500 + samostatný prietokomer/merač tepla | kalibrácia, bezpečnostná redundancia |
| Zdroj 25 °C | Oilon ChillHeat P / Carrier AquaSnap 61WH | výkon a COP **NEPOTVRDENÉ** pri 25→30 °C |

## Tepelná stanica siete
Skutočný syntetický profil pôvodného Simulinku 2025: DC zdroj **6,970 MW priemer**, **7,699 MW P95**, **8,291 MW maximum**. Výstup TČ siete: **5,477 MW priemer**, **9,396 MW P95**, **10,372 MW maximum**. Predošlý finančný príklad s 9-MW stanicou preto **NEPOKRÝVA maximum**. Predbežne treba uvažovať aspoň **12 MW menovitej použiteľnej kapacity** a N+1, napríklad 6 prevádzkových modulov po cca 2 MW + 1 záložný, avšak iba po výrobcovom prepočte pri skutočnom 35→? °C / 70 °C.

Reálne rady: [Carrier 61XWH-ZE](https://www.carrier.com/commercial/en/eu/products/heating/water-to-water-heat-pumps/61xwhze/) (do 85°C), [Oilon ChillHeat P](https://oilon.com/en-us/products/oilon-chillheat-p-30-p-450/) (do 120°C). Menovité rozsahy nie sú výkon v našom teplotnom bode. Požadovať model COP(T_source_in/out,T_sink_in/out,PLR), elektrický príkon, tlakové straty a dovolený prietok.

## Ekonomika bazéna: reálny model + hypotetické investície
Výsledok už overeného Simulinku 2025: **12 306,50 EUR/rok** energetický prínos priameho výmenníka a **4 279,76 EUR/rok** pri bazénovom TČ COP=4; obe veličiny pred čerpadlami a servisom. Elektrina Eurostat SK 2025 152,07 EUR/MWh, plyn 55,63 EUR/MWh.

| Rozpočet inštalácie | NPV 20 rokov 6 % priamy HX | Predpoklady |
|---|---:|---|
| 45 000 EUR | +70 967 EUR | čerpadlá, servis 2 % z investície |
| 75 000 EUR | +34 085 EUR | rovnaký variant |
| 110 000 EUR | −8 944 EUR | rovnaký variant |

**Hraničná investícia pre HX ~102 725 EUR**, pri TČ s COP=4 ~27 387 EUR. Tieto investície nie sú cenové ponuky, ale výpočtové scenáre. Pre 9 MW centrálne TČ a modelový COP=3,5/4,9 sa návratnosť drasticky líši; **9 MW však nepokrýva modelové maximum**, preto ho nemožno objednať iba podľa orientačnej ekonomiky.

## Povinné body dopytu dodávateľovi (RFQ)
1. Tepelný výkon, COP a elektrické pomocné spotreby pre zdroj vstup/výstup 25/20; 35/30; 45/40 °C a kúrenie 50/70, 60/70 a 70/80 °C pri PLR 25/50/75/100 %.
2. Min/max prietoky a straty tlaku, materiály v styku s upravenou vodou, požiadavky na údržbu, N+1 a bezpečnostné odpojenie.
3. Pre bazénový HX požadovať presne **35/32 °C / 27,5/29,5 °C; 150 kW; návrhové UA≥37,63 kW/K**, bezpečné oddelenie médií.
4. Ponuka vrátane inštalácie, rozvádzača, merania, VFD, uvedenia do prevádzky a dokumentácie CE/PED/EN 14511, podľa skutočnej vhodnosti a platných predpisov.
5. Záložné chladenie IT nesmie byť závislé od príjmu tepla bazénom ani od distribúcie.

**Neoverené:** skutočné IT merania, reálna teplota a prietok chladiacej vody, COP/PLR pri našom bode, presné tlaky a chémia vody, cena dodávateľa, úplné licencované normy a aktuálny právny stav. Tento predvýber **nie je stavebný ani bezpečnostný projekt**.

**Súbory:** equipment_selection_default.json, HX_low_grade_heat_default.csv, CAPEX_pool_cases_default.csv, interactive_equipment_calculator.html, screen_equipment_options.py.