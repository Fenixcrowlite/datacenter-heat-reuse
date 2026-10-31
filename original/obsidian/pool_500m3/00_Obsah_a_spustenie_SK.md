---
aliases: [Bazen DC 500m3, Ohrev bazena datacentrum]
tags: [datacentrum, matlab, simulink, bazen, tepelnacinnost]
status: VERIFIED_MATLAB_SIMULINK_REFERENCE
created: 2026-10-23
---
# Dátové centrum → ohrev bazéna (500 m³)

> [!summary] Pripravené výstupy
> Výpočet v Pythone (7 variantov), reálny MATLAB/Simulink (4 varianty), sedemstranové správy v troch jazykoch, analytický rozbor a integračné rozhranie. Ide o **referenčné scenáre**, nie o reálny projekt zariadenia.

## Technické správy

- [[Bazen_500m3_SK.pdf|Slovenská technická správa (SK)]]
- [[Bazen_500m3_EN.pdf|English technical report (EN)]]
- [[Bazen_500m3_RU.pdf|Русский технический отчёт (RU)]]

## Matematika a metodika

- [[Matematicky_rozbor_a_simulacia_SK|Matematický rozbor: tepelné bilancie a všetky použité rovnice]]
- [[Vypocty_a_simulacie_bazen_500m3_SK|Tabuľka scenárov a stručný postup]]
- [[Rozhranie_integracie_DC_Bazen_SK|Rozhranie pre budúcu integráciu s DCHR v85/v86]]

## Skutočné grafy MATLAB/Simulink

![[simulink_porovnanie_scenarov_SK.png]]

![[priebeh_teploty_simulink_SK.png]]

## Kľúčové čísla

| Parameter | Výsledok |
|---|---:|
| Objem / plocha | 500 m³ / 312,5 m² |
| Ohrev vody z 16 °C na 28 °C bez strát | 6,949 MWh |
| Teplo na udržanie pri 28 °C, prevádzka | 52,13 kW |
| Teplo na udržanie pri 28 °C, pod plachtou | 10,77 kW |
| Simulink 75 kW: prvý prechod 28 °C | 97,883 h |
| Simulink 150 kW: prvý prechod 28 °C | 47,317 h |
| Simulink 300 kW: prvý prechod 28 °C | 23,350 h |
| Simulink 150 kW bez plachty | 46,833 h |
| Energetické rezíduum modelu 150 kW | 0,0117 % |

## Spustenie v MATLAB-e

Pracovný adresár:

C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\matlab\pool_500m3

Skripty v Command Window:

    run('C:/Users/Lysda/OneDrive/Projects/DataCenter_Heat_Reuse/matlab/pool_500m3/spusti_simulaciu_bazena_sk.m')
    run('C:/Users/Lysda/OneDrive/Projects/DataCenter_Heat_Reuse/matlab/pool_500m3/spusti_scenare_bazena_sk.m')

Samostatná schéma:

    Bazen_DC_Ohrev_500m3_SK.slx

Uložené výsledky a CSV:

    C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\results\pool_500m3_v01

**Rozsah modelu:** tepelné straty, energia v bazéne, termostat a časovo nastaviteľný užitočný tepelný prívod. Zdrojové IT heat recovery, COP, výmenník a elektrina sú v matematických scenároch; v samotnom SLX zatiaľ nie je prepojený pôvodný Stateflow dispečing v85/v86.

## Pre učiteľovu kontrolu

1. Overiť jednotky v každom člene rovnice $C\,dT/dt = Q_{in}-Q_{loss}$.
2. Nezamieňať $Q_{IT}$, využiteľné odpadové teplo a $Q_{pool}$.
3. Pri TČ platí $Q_{out}=Q_{source}+W_{electric}$.
4. Oddeliť vykurovanie vody od spotreby HVAC celého objektu.
5. Parametre geometrie, tepelných odporov, plachty a COP označiť ako scenárové.
6. Ďalšia etapa: reálna charakteristika výmenníka a tepelného čerpadla, integrácia do dispatch.

Zdroj: ASHRAE Handbook 2023 (Indoor Swimming Pools) a EnergyPlus Engineering Reference.
