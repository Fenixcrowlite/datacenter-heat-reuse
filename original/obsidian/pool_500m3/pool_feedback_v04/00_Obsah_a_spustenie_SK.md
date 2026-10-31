---
tags: [datacentrum, bazen, stateflow, simulink, regulačný-uzol]
status: VERIFIED_SYNTHETIC_CLOSED_LOOP
language: sk
created: 2026-10-23
---
# Uzavretá regulácia v04 | obsah a spustenie

V tomto priečinku je nová funkčná Simulink + Stateflow regulačná slučka pre bazén 500 m³, termodynamiku TČ, sieť DH a akumulátor TES. Simulácia sa vykonala pri 8 syntetických 7-dňových scenároch. Nie sú to merania, rok ani pôvodný v85 kontrolér.

## Hlavné súbory

- [[Popis_a_rovnice_Stateflow_v04_SK]] - matematika od prvých princípov, všetky bilancie, ochrany, predpoklady, význam signálov, výsledky
- [[Dispecer_Bazen_v04_SK.pdf]] - technická správa po slovensky
- [[Dispecer_Bazen_v04_EN.pdf]] - English report
- [[Dispecer_Bazen_v04_RU.pdf]] - отчёт на русском
- [[DC_Bazen_Uzavreta_Regulacia_v04_SK.slx]] - model Simulink s reálnymi stavmi Stateflow
- [[priebeh_teploty_v04_SK.png]] - skutočný 7-dňový graf
- [[vysledky_dispecer_v04_SK.json]] - KPI
- [[QA_NEZAVISLA_V04_SK.json]] - 65493 nezávislých PASS
- [[spusti_scenare_v04_sk.m]] - hlavný launcher MATLAB
- [[alokuj_teplo_v04_sk.txt]] - jadro alokácie DC/TČ/DH/TES
- [[vypocitaj_dopyt_bazena_sk.txt]] - výpar, konvekcia a teplotný termostat
- [[volba_rezimu_v04_sk.m]] - výber prevádzkových režimov Stateflow

## Výsledok referenčného syntetického testu

- Bazén: 10,393 MWh za 168 h, horná teplota 27,58 °C.
- DH: 16,101 MWh, nevykrytá potreba 1,539 MWh.
- Kompresor: 4,764 MWh, pomocné motory scenárovo 0,297 MWh.
- Q_DC_available: 28,560 MWh -> priamy HX 3,051 MWh + zdroj TČ 19,263 MWh + REJECT 6,246 MWh.
- Dopyt bazéna i energia TES sa vracajú do riadenia nasledujúceho kroku.

## Reprodukcia na PC

MATLAB R2026a, aktuálny adresár OneDrive/Projects/DataCenter_Heat_Reuse/matlab/pool_feedback_v04

    spusti_scenare_v04_sk

Python QA:

    python qa_nezavisla_v04_sk.py

PDF regenerácia:

    python vytvor_pdf_v04_3jazyky.py

## Technické hranice

Pôvodná v85 nebola menená a nie je v novom v04 chart. Tieto dva kontroléry zatiaľ nemajú dokázanú funkčnú ekvivalenciu. Bez nameraných profilov, hydrauliky, osušovania bazénovej haly, certifikovaných COP máp a poruchového testovania senzorov nie je fyzická alebo normatívna validácia hotová.
