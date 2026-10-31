# DataCenter Heat Reuse | Stratifikovaný zásobník vody, fyzikálna kontrola

**Stav:** VERIFIED izolovaný výpočtový kandidát, nie validovaný návrh zariadenia. Dátový vstup tvorí **8760 syntetických hodinových záznamov** z `best_scenario_v2_timeseries.csv`, SHA256 `8125719923bae97901f37cf0f5354df77b46544df0477f863172255748873f25`. Pôvodný model Simulink, súbory OneDrive a existujúci zásobník **100 MWh** zostali bez zmien.

## Fyzikálny model

Zásobník je rozdelený na **8 vrstiev rovnakej hmotnosti**; každá má tepelnú kapacitu `C_i = rho * cp * V / (N * 3.6e9)` v MWh/K. Použité konštanty: `rho = 1000 kg/m3`, `cp = 4180 J/(kg K)`. V každej hodine je 8 explicitných podkrokov s podmienkou advekcie `alpha <= 0.5`.

Pri nabíjaní vstupuje teplá voda z tepelného čerpadla hore a rovnaký prietok sa odoberá zdola. Pri vybíjaní odchádza teplá voda zhora do výmenníka CZT a ochladená vratná voda vstupuje zdola. Schéma zachováva celkovú hmotnosť a energiu; tepelná energia výstupu sa odpočíta od zásobníka. Výstup je povolený len pri `T_horna > T_privod_CZT + 3 K`. Výpočet zároveň rešpektuje tepelný výkon, obmedzenie elektrického príkonu tepelného čerpadla a dostupnosť odpadového tepla.

Tepelné straty: `Q_strata = UA * max(T_vrstva - T_okolie, 0) * dt`. Pre ilustračnú valcovú geometriu výšky 10 m je `UA = U * (2*pi*r*h + 2*pi*r^2)`, `r = sqrt(V/(pi*h))`. **Predpoklad**, nie meranie: `U = 0.15 W/(m2 K)`, teplota okolia 15 °C, vratná voda 35 °C, medzi-vrstvová vodivosť 0.5 kW/K. COP pri vyššom teplotnom zdvihu je heuristicky znížený, nie odvodený z katalógovej mapy výrobcu.

Nezávislá bilančná kontrola pre každý podkrok a rok:
`E_koniec = E_zaciatok + Q_nabijanie - Q_dodane - Q_straty`.
Samostatne platí `Q_nabijanie = Q_elektrina_HP + Q_odobrane_zo_zdroja`. Všetky veličiny sú v MWh; uvedené ročné hodnoty sú výsledkom **tretieho opakovania** syntetického roka.

## Výsledky tretieho modelového roka

| Objem vody | Nabíjacia teplota | UA | Dodané do CZT | Dodatočná elektrina HP | Tepelné straty |
|---:|---:|---:|---:|---:|---:|
| 10 000 m³ | 72 °C | 0.468 kW/K | 341.04 MWh | 226.47 MWh | 176.22 MWh |
| 10 000 m³ | 80 °C | 0.468 kW/K | 437.11 MWh | 331.55 MWh | 192.78 MWh |
| 305 485.8 m³ | 72 °C | 10.094 kW/K | 3460.15 MWh | 3413.14 MWh | 2970.36 MWh |
| 305 485.8 m³ | 80 °C | 10.094 kW/K | 3004.79 MWh | 3413.14 MWh | 2600.14 MWh |
| 10 000 m³ | 80 °C, bez strát a miešania | 0 | 456.07 MWh | 234.10 MWh | 0 |

**Interpretácia:** V tomto modelovom nastavení neplatí, že vyššia nabíjacia teplota vždy zvýši dodané teplo. Pri veľkom objeme môže vyšší zdvih zhoršiť COP a znížiť dostupné nabíjanie. Rozdiely medzi variantmi sú citlivé na **predpokladanú** izoláciu, geometriu, vratnú teplotu a zdrojové limity. Model nedokazuje ekonomickú návratnosť, fyzickú realizovateľnosť stavby ani úsporu zemného plynu.

## QA a hranice platnosti

Automatické testy **21/21 PASS**; nezávislý kontrolný skript bez importu modelu: **15 ročných energetických bilancií, 15 elektrických rozkladov, 5 výpočtov UA a 5 finálnych teplotných profilov PASS**. Celkový počet syntetických intervalov 8760, päť konfigurácií, tri opakované roky. Súčasný Simulink už obsahuje **100 MWh** zásobník, preto tieto výsledky **nie sú inkrementálnou úsporou** voči existujúcej prevádzke.

**Otvorené:** porovnanie s reálnym dispečingom 100 MWh zásobníka; prechodné hydraulické prietoky a tlaky; kalibrácia UA, stratifikácie, vratnej teploty a COP z výrobcu; teplotná dynamika výmenníka; náklady a hodinové tarify; 31/31 kontrol primárnych zdrojov (aktuálne 0/31). Žiadne merané dáta ani experimentálne overenie sa netvrdia.

**Nasledujúci krok:** vytvoriť samostatný integračný kontrakt s existujúcim modelom Simulink, najprv porovnať bilančné hranice pôvodného 100 MWh zásobníka, potom až prípadne vykonať izolovanú simuláciu MATLAB bez prepísania v85.
