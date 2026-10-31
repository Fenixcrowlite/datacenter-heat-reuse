---
tags: [datacentrum, bazen, simulink, Stateflow, poruchy, FMEA]
status: VERIFIED_SYNTHETIC
date: 2026-10-23
language: sk
---
# V06: model fyzikálnych porúch a nezávislého chladenia

## Hlavná dokumentácia

- [[Matematika_a_fyzikalne_poruchy_v06_SK]] - rovnica vody, onskorenie snímačov, ventil, odvod IT, bilancie a nezávislé overenie
- [[DC_Bazen_Fyzikalne_Poruchy_v06_SK.slx]] - vykonaný model Simulink so Stateflow
- [[DC_Bazen_Fyzikalne_Poruchy_v06_SK.pdf]] - slovenská technická správa
- [[DC_Bazen_Fyzikalne_Poruchy_v06_EN.pdf]] - English report
- [[DC_Bazen_Fyzikalne_Poruchy_v06_RU.pdf]] - русский отчёт
- [[povel_vs_prietok_v06_SK.png]] - ochranná západka vs. skutočný únik vody
- [[teplota_IT_riziko_v06_SK.png]] - vývoj hypotetického IT tepelného rizika
- [[vysledky_v06_SK.json]] - KPI siedmich scenárov
- [[QA_NEZAVISLA_V06_SK.json]] - 84 801 PASS
- [[POOL_FAILURE_V06_HANDOFF_20261023]] - handoff a nedostatky
- [[spusti_poruchove_scenare_v06_sk.m]] - spustenie simulácií

## Dôležité
V06 dokazuje, že nulový regulačný povel nezaručuje nulové fyzikálne teplo, ak je ventil zaklinený. REJECT chyba môže viesť k modelovému rizikovému prehriatiu IT bufferu. Žiadna z teplôt IT nie je reálnym meraním serverov. Všetky vstupy sú syntetické.

## Reprodukcia

MATLAB R2026a, adresár:
C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\matlab\pool_failure_v06

Spustenie:
    spusti_poruchove_scenare_v06_sk

Nezávislý QA:
    python qa_v06_sk.py

Podkladová originálna v85 ostáva samostatná a bez úprav.
