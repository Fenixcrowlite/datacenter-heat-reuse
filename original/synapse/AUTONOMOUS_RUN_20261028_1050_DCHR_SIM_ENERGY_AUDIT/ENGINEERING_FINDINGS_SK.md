# DCHR: energetický audit hodinovej simulácie (2026-10-28)

**Typ údajov:** SIMULOVANÉ, nie namerané údaje z elektromerov/SCADA. Zdroj je existujúci `results/best_scenario_v2_timeseries.csv` (8 760 hodinových riadkov za rok 2026). Zdrojový CSV nebol upravený.

## Metóda a výsledky

Pre výkon `P_i` v MW a interval `Δt = 1 h` platí `E = Σ P_i Δt` v MWh. Posledný interval sa predpokladá hodinový; časové značky nemajú uvedenú časovú zónu. Hodnoty sa sčítali s desatinnou aritmetikou a nezávisle skontrolovali `math.fsum`.

| Ukazovateľ simulácie | Výsledok |
|---|---:|
| IT elektrina | 71 832,833 MWh |
| Celková elektrina DC | 86 199,400 MWh |
| **Simulované PUE** | **1,2000** |
| Teplo získané zo zdroja pre HP (`HP_Source_Used`) | 39 645,173 MWh |
| Elektrina tepelného čerpadla | 7 364,648 MWh |
| Skutočne využité teplo HP (`HP_Heat_Used`) | 47 009,821 MWh |
| Potenciálne vyrobené teplo HP (`HP_Heat`) | 69 555,243 MWh |
| Obmedzené/nevydané teplo (`Curtailed_HP_Heat`) | 22 545,421 MWh |
| Podiel obmedzeného tepla | **32,414 %** |
| Hodiny s nenulovým obmedzením | **4 587 / 8 760** |
| Plynové teplo | 12 549,051 MWh |

**Dôležité rozlíšenie:** prvotná kontrola `HP_Heat = HP_Source_Used + HP_Electric` zlyhala v 4 587 intervaloch. Nešlo o chybu simulácie, ale o chybný predpoklad auditu: `HP_Heat` je potenciálne vyrobené teplo pred obmedzením. Správne identity sú:

1. `HP_Heat_Used = HP_Source_Used + HP_Electric`.
2. `HP_Heat = HP_Heat_Used + Curtailed_HP_Heat`.

Po oprave a pridaní regresného testu pre nenulové obmedzenie: **0 porušení** oboch identít; najväčšia absolútna chyba prvej identity približne `1e-14 MW`. Nezávislý audit potvrdil všetkých deväť energetických súčtov.

## Hranice a otvorené otázky

**PUE je len modelová hodnota.** Bez meracích hraníc nie je možné tvrdiť, že zodpovedá skutočnému dátovému centru. Treba overiť, či `DC_Total_MW` zahŕňa elektrinu tepelného čerpadla alebo je HP mimo hranice DC.

`HP_Source_Used` je **diagnostická tepelná veličina, nie certifikovaný E_REUSE ani ERF**. `HP_Heat_Used` obsahuje aj elektrickú prácu HP, preto ju nemožno automaticky vykázať ako odpadové teplo DC. Chýbajú namerané časové rady obnoviteľnej elektriny a vody: **ERF, REF a WUE sa nevypočítali**.

Tento audit **nepotvrdzuje fyzikálnu kalibráciu, legislatívny súlad ani primárne zdroje**. Počet úplne overených literárnych zdrojov zostáva **0/31**.

## Ďalší vykonateľný krok

Získať zdokumentované meracie hranice a vierohodné časové rady `E_DC`, `E_IT`, `E_REUSE`, `E_RES`, `W_IN`; až potom rozšíriť tento výpočet o metered-mode a prepojiť ho so SCADA. Zatiaľ nepovažovať modelový pomer 0,459924 za ERF.
