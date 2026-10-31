---
tags: [datacentrum, bazen, Simulink, Stateflow, redundancia, bezpecnost]
date: 2026-10-23
status: VERIFIED_SYNTHETIC_V07
language: sk
---
# V07: dvojité uzávery, redundantné REJECT a IT odľahčenie

Toto je skutočne spustená, ale výhradne syntetická simulácia, **nie certifikované fyzické zariadenie**. Pôvodné v85, v04, v05 a v06 zostávajú uložené oddelene. Aktuálny nový Simulink v07 obsahuje päťstavový Stateflow dispečer, dva sériové modelové ventily, dve modelové vetvy odvodu tepla a podmienené odľahčenie tepelného vstupu IT.

## Materiály

- [[Matematika_redundancia_a_bilancie_v07_SK]] - podrobná matematika, energetické invarianty, výsledky ôsmich prípadov
- [[Import_skutocnych_merani_SK]] - presný vstupný kontrakt pre A/B/C/D dáta a limitácie
- [[DC_Bazen_Dvojita_Ochrana_v07_SK.slx]] - nový skutočne spustený model
- [[DC_Bazen_Dvojita_Ochrana_v07_SK.pdf]] - slovenská technická správa
- [[DC_Bazen_Dvojita_Ochrana_v07_EN.pdf]] - English report
- [[DC_Bazen_Dvojita_Ochrana_v07_RU.pdf]] - русский отчёт
- [[ventily_a_redundancia_v07_SK.png]] - prvý verzus dva zaseknuté ventily
- [[IT_riziko_v07_SK.png]] - porovnanie prehriatia s/bez odľahčenia
- [[vysledky_v07_SK.json]] - výsledky Simulink
- [[QA_NEZAVISLA_V07_SK.json]] - 129 251 nezávislých kontrol
- [[POOL_REDUNDANCY_V07_HANDOFF_20261023]] - otvorené limity a ďalší krok

## Hlavné výsledky

Pri jednom zaklinenom ventile nedošlo v tomto modeli k úniku tepla. Pri oboch došlo k 0,490 MWh úniku. Ak vypadol hlavný REJECT, záložný v skúške prevzal 0,080 MWh. Pri poruche oboch vetiev a povolení IT odľahčenia klesol modelový rizikový teplotný indikátor z 47,06°C na 40,33°C. Nejde o skutočné teploty serverov.

## Spustenie

MATLAB R2026a, aktuálny priečinok:
C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\matlab\pool_redundancy_v07

    spusti_scenare_v07_sk

Nezávislá kontrola:

    python qa_nezavisla_v07_sk.py

Kontrola metadát a CSV meraní:

    python test_schema_merani_v07.py

Skutočné merania ešte nie sú dodané ani priamo zapojené ako vstupy Stateflow v07. Validačná schéma je pripravená, nie dokončená kalibrácia.
