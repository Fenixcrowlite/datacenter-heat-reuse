---
tags: [datacentrum, bazen, integracia, MATLAB, simulink, stateflow, v85]
status: VERIFIED_ONE_WAY_REPLAY
language: sk
created: 2026-10-23
---
# Most v85 → bazén (v03) - obsah a spustenie

**Uložený model je reálne spustiteľný, a pôvodný Stateflow v85 zostal nezmenený.** v03 používa skutočne spustenú výstupnú stopu v85, nie falošný ročný profil. Toto nie je obojsmerný dispečing a nejde o dodatočné vyrobené teplo. Úloha je len presmerovať časť už dodanej priamej HP služby do bazéna a zvyšok ponechať pôvodnému odberateľovi.

## Dokumentácia a správy

- [[Prepojenie_v85_bazen_v03_SK]] - rovnice od prvých princípov, 9 skutočných behov, limitácie
- [[Most_v85_bazen_v03_SK.pdf]] - technický prehľad po slovensky
- [[Most_v85_bazen_v03_EN.pdf]] - English technical appendix
- [[Most_v85_bazen_v03_RU.pdf]] - техническое приложение
- [[Bazen_Prepripojenie_Sluzby_v85_v03_SK.slx]] - nový funkčný Simulink model
- [[most_v85_bazen_v03_SK.json]] - výsledky 9 vykonaných behov
- [[QA_NEZAVISLA_V85_BRIDGE_SK.json]] - 99 nezávislých kontrol
- [[spusti_skutocne_v85_a_bazen_sk.m]] - spustenie oboch modelov a archivácia výsledkov
- [[krok_bazen_v85.txt]] - fyzikálne jadro simulácie pre kontrolu

## Interpretácia príkladu

V85 pri servise poskytol 0,447565789 MWh počas 1 h. Pri štarte bazéna z 16 °C sa 0,150000 MWh presmerovalo do bazéna; pôvodnému odberateľovi zostalo 0,297565789 MWh. Pri teplej vode 27,70 °C alebo pri STOP bazéna sa nepresmerovalo nič.

**Bilancia: 0,447565789 = 0,150000000 + 0,297565789 MWh.**

Dve ďalšie pôvodné stopy nesmú vykazovať TES nabíjanie ako voľné teplo pre bazén.

## Spustenie MATLAB/Simulink

Otvoriť MATLAB R2026a. Prejsť do adresára:

C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\matlab\pool_v85_bridge_v03

V Command Window vyvolať:

    spusti_skutocne_v85_a_bazen_sk

Samostatný QA nad výstupmi:

    python qa_most_v85_sk.py

Pri potrebe kontroly slx otvoriť model Bazen_Prepripojenie_Sluzby_v85_v03_SK.slx. Výstupy sa ukladajú do OneDrive/Projects/DataCenter_Heat_Reuse/results/pool_v85_bridge_v03.

## Čo nie je vyriešené

- V85 nerozhoduje podľa dopytu bazéna. Ide o jednosmerné presmerovanie služby po pôvodnom dispečingu.
- Originál v85 má overené krátke časové okná, nie meraný 8760 h profil.
- Stále chýba hydraulický výmenník, údaje výrobcu COP, pomocné pohony a merania.
- Normové a právne odkazy sú podklady pre audit, nie vyhlásenie o certifikovanej zhode.

Pre syntetickú 8760 h simuláciu sa pozri do susedného adresára [[Matematika_a_rocna_simulacia_SK]] v02.

## Grafické simulácie

- [[priebeh_bazen_v85_SK.png]] - voda, tri režimy
- [[rozdelena_sluzba_v85_SK.png]] - vykon bazéna a zvyšok DH
- [[POOL_V85_BRIDGE_HANDOFF_20261023]] - handoff a otvorené hranice

