---
tags: [datacentrum, bazen, merania, Simulink, Stateflow, v08]
status: VERIFIED_SYNTHETIC_REPLAY
language: sk
date: 2026-10-23
---
# Externé merania v08 - obsah a spustenie

Hlavná zmena: dve teplotné merania T1/T2 vstupujú do bezpečnostnej funkcie Stateflow cez validovaný CSV, nie priamo z virtuálneho T_model. Nárok na reálne kalibrované údaje sa **nevyslovuje**. Všetky 8 kontrolných prípadov používajú D-syntetický replay z v07.

## Materiály

- [[Matematika_integracia_merani_v08_SK]] - fyzika, rovnice, bezpečnostné zámky, metrológia a nezávislé QA
- [[DC_Bazen_Externe_Merania_v08_SK.slx]] - model Simulink
- [[DC_Bazen_Externe_Merania_v08_SK.pdf]] - technická správa po slovensky
- [[DC_Bazen_Externe_Merania_v08_EN.pdf]] - English report
- [[DC_Bazen_Externe_Merania_v08_RU.pdf]] - технический отчёт
- [[externe_snimace_v08_SK.png]] - modelová spoločná chyba T1/T2 pri replay
- [[regresia_tepla_v08_SK.png]] - maximum rozdielov v08 vs v07
- [[QA_NEZAVISLA_V08_SK.json]] - 91 565 PASS
- [[NEISTOTY_MERANIA_V08_SK.json]] - predpokladaná metrológia
- [[vysledky_v08_SK.json]] - výsledky a regresné odchýlky
- [[D_REPLAY_INPUT_MANIFEST.json]] - klasifikácia D a pôvod súborov
- [[POOL_MEASUREMENT_V08_HANDOFF_20261023]] - technické hranice a ďalší postup

## Dôležité výsledky

8 × 672 intervalov po 15 min; všetky v08 safety latch zhodné s v07. Max rozdiel vody 3,01e-8 °C, max rozdiel tepla <0,05 W. Nezávislý QA odhalil dvojité pripočítanie biasu a v08 bola opravená. Prvý pokus nie je súčasťou overeného výsledku.

Predpokladový príklad: 30 m³/h a 3 K má tepelný tok 104,24 kW so štandardnou neistotou približne 11,12 kW, ak prietok má 5 % a oba teplomery 0,2 K nezávislú štandardnú neistotu.

## Spustenie

MATLAB R2026a v priečinku OneDrive/Projects/DataCenter_Heat_Reuse/matlab/pool_measurement_v08:

    spusti_merania_replay_v08_sk

QA v Pythone:

    python qa_nezavisla_v08_sk.py

Pri ďalšom kroku treba skutočné A merania s identifikáciou a kalibračnou evidenciou prístrojov. D-replay nesmie byť označený ako reálna validácia.
