# A61 | Diskrétna energetická bilancia bazéna (D-SYNTHETIC)

**Stav:** overená numerická konzistencia existujúcich simulácií v08/v09. Nie meranie fyzického zariadenia, nie bezpečnostná certifikácia.

## Dôvod nezávislého auditu

Export A60 počíta integrál výkonu bazéna **trapezoidovým pravidlom** medzi časovými značkami 0 a 603900 s (167,75 h). Pôvodná Simulink schéma však používa **diskrétny krok 900 s** a každý výstupný riadok obsahuje *už aktualizovanú teplotu* a tepelný výkon použitý pri tejto aktualizácii. Existuje 672 aktualizácií, teda 168 h. Tieto dva integrály zodpovedajú rôznym časovým konvenciám; nemožno ich zamieňať.

Overené zdrojové predpoklady: `matlab/pool_feedback_v04/alokuj_teplo_v04_sk.txt`, `vypocitaj_dopyt_bazena_sk.txt` a `spusti_scenare_v04_sk.m`:
- Objem vody V = 500 m³, hustota rho = 997 kg/m³, merná tepelná kapacita cp = 4182 J/(kg K).
- C = rho V cp = 2 084 727 000 J/K.
- Počiatočná teplota T_initial = 16 °C; krok dt = 900 s.
- Rovnica stavu: `T[k] = T[k-1] + dt * (Q_pool[k] - Q_loss[k]) / C`.
- Záporné `Q_loss` sú možné: pri teplejšom okolitom vzduchu konvekcia a sálanie môžu predstavovať tepelný **zisk**. Nie je prípustné automaticky meniť ich znamienko alebo ich označiť za chybu.

## Výsledky v08 (672 aktualizácií)

| Veličina | Hodnota |
|---|---:|
| Dodané teplo bazénu, diskrétne | 10,393084303 MWh |
| Podpísané tepelné straty (netto) | 3,687212453 MWh |
| Zmena energie vody C × (27,58 − 16) | 6,705871850 MWh |
| Energetická uzávierka | približne 0 J |
| Najväčšia chyba okamžitej bilancie | 2,18 × 10⁻⁷ W |
| Riadky so zápornými stratami | 91/672 |
| Integrovaný tepelný zisk zo záporných strát | 0,299636047 MWh |
| Pôvodný integrál A60 (trapezoid) | 10,373083906 MWh |
| Rozdiel A60 oproti 672 diskrétnym krokom | −20,000398 kWh |

Pre v09 je výsledok nezávisle reprodukovaný: maximálna chyba 2,16 × 10⁻⁷ W, 91 záporných strát a rovnaká energetická uzávierka v tolerancii. Samostatný kontrolný výpočet používa `decimal.Decimal`, nie funkcie z A61.

Rozdiel integrálov je vysvetliteľný presne: `E_discrete - E_trapezoid = dt × (Q_pool[0] + Q_pool[N−1]) / 2` pri konštantnom kroku. Nejde o automatický dôkaz chyby A60; jeho výstup popisuje interval medzi časovými značkami, nie všetkých 672 aktualizácií modelu.

## QA, pôvod a obmedzenia

A61 kontroluje SHA256 pôvodného CSV a A60 exportu, klasifikáciu `derived_simulation`, zákaz `physical_release`, zhodu časových značiek, jednotiek a mapovaných kanálov. Vstupné súbory, Simulink, SCADA, pracovné vetvy a konfigurácia neboli modifikované.

A61 **nepotvrdzuje** presnosť fyzikálnych predpokladov ani kvalitu meracích kanálov. Bez skutočného kalibrovaného exportu zostávajú A55–A59 fyzikálne testy BLOCKED. V ďalšej integrácii treba explicitne rozlišovať integrál po časových značkách a integrál po aktualizáciách diskrétneho modelu a zachovať kanál podpísaných strát.
