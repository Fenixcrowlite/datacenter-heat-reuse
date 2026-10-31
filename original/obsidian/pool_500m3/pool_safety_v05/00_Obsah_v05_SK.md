---
tags: [datacentrum, bazen, bezpečnost, simulink, stateflow, FMEA, senzorika]
status: VERIFIED_SYNTHETIC_SIMULATION
language: sk
created: 2026-10-23
---
# V05 - bezpečnostná nadstavba bazéna 500 m³

## Úvod

Nový model v05 obsahuje senzorickú blokovaciu slučku a sedem skutočne vykonaných 7-dňových Simulink simulácií. Každá má 672 vzoriek s krokom 900 s. Originálne v85 a v04 neboli prepísané.

## Navigácia
- [[Bezpecnost_a_poruchy_bazena_v05_SK]] - fyzika, modelové limity, hysterezné blokovanie, FMEA, matematické bilancie
- [[DC_Bazen_Bezpecnost_v05_SK.slx]] - nový model Simulink/Stateflow
- [[Bezpecnost_bazena_v05_SK.pdf]] - slovensky
- [[Bezpecnost_bazena_v05_EN.pdf]] - English
- [[Bezpecnost_bazena_v05_RU.pdf]] - русский
- [[interlock_timeline_v05_SK.png]] - časový záznam blokovania pre 7 scenárov
- [[teplota_poruchy_v05_SK.png]] - porovnanie T vody
- [[resultaty_v05_SK.json]] - primárne výstupy Simulink
- [[QA_V05_SK.json]] - nezávislý QA, 32 928 skupín
- [[POOL_SAFETY_V05_HANDOFF_20261023]] - obmedzenia a ďalší krok
- [[spusti_poruchy_v05_sk.m]] - skript na spustenie
- [[pool_safety_gate_v05.txt]] - matematická a bezpečnostná funkcia

## Skutocne výsledky
Bazén pri bezporuchovom behu: 10,393 MWh tepla/168 h, Tmax 27,58°C. Pri poruche a aktivovaní bezpečnostnej západky je Q_pool=0 až do odstránenia chyby a ručného resetu. Model nedokazuje bezpečnosť skutočného fyzického snímača; oba kanály sú generované ako T_model + simulovaný bias.

## Spustenie
Aktuálny adresár MATLAB R2026a:
C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\matlab\pool_safety_v05

    spusti_poruchy_v05_sk

Kontrola:
    
    python QA_v05_sk.py

PDF/archív sú tiež v OneDrive/Projects/DataCenter_Heat_Reuse/results/pool_safety_v05.
