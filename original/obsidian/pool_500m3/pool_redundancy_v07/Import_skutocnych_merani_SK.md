---
tags: [datacentrum, bazen, merania, kvalita-dat, reprodukovatelnost]
status: PREPARED_NOT_CONNECTED
language: sk
date: 2026-10-23
---
# Import časových meraní do ďalšej kalibračnej fázy

## Dôležité rozlíšenie

V07 je už overená uzavretá simulácia so **syntetickými** vstupmi. Súbor kontroly_vstupnych_merani_v07.py iba kontroluje a pripravuje *skutočné* alebo zdrojovo podložené časové rady. **Dnes nie sú dodané žiadne originálne prevádzkové údaje**, preto kontrolér v07 ešte skutočné merania nespracúva. Tento adaptér sa nesmie prezentovať ako dokončená fyzická kalibrácia.

## Povinný vstup

Dva súbory:

- merania_15min_SABLONA.csv - presne predpísané hlavičky a jednotky; doplniť skutočné údaje.
- metadane_merania_SABLONA.json - správna trieda dôkazu a zdroj.

Časové body majú mať ISO 8601 UTC, napríklad 2026-10-23T11:00:00Z, každých 900 s bez vynechaných ani duplicitných bodov. Výkony sú vo W, teploty v °C, RH v 0..1, prietok bazéna v m3/h, stav chladiča 0..1.

Základné stĺpce: timestamp_utc, Q_DC_available_W, T_DC_C, Q_DH_request_W, T_air_C, RH, T_pool_sensor1_C, T_pool_sensor2_C, pool_flow_m3h, P_IT_W, Q_REJECT_measured_W, main_reject_ok, backup_reject_ok.

## Pôvod a kvalita zdroja

- A = originálne fyzické meranie zariadenia, s ID snímačov a kalibračným dokumentom.
- B = dáta publikovanej odbornej štúdie s jej konkrétnou citáciou a identifikáciou prevzatých meraní.
- C = výrobné katalógové dáta konkrétneho zariadenia a testovacích podmienok.
- D = generované alebo predpokladané syntetické hodnoty (nikdy nezamieňať za A).

Validator odmietne nepovolenú časovú medzeru, nefinitné číslo, záporné výkony, nesprávne poradie stĺpcov, interval iný než 900 s a dáta A bez identifikácie fyzických prístrojov a kalibrácie. Každý úspešný import uloží hash SHA-256 pôvodného súboru. Vytvorenie cieľového adresára odmietne prepísanie existujúceho importu.

## Spustenie na PC

V priečinku matlab/pool_redundancy_v07:

    python kontrola_vstupnych_merani_v07.py --input merania_SKUTOCNE.csv --metadata metadane_SKUTOCNE.json --output staged_merania/dataset_001

Test kontextu (syntetický D prijatý, falošné A odmietnuté):

    python test_schema_merani_v07.py

**Ďalší krok:** fyzické hodnoty po overení zdroja treba previesť na časové vstupy Simulink a zmeniť v budúcej verzii syntetické meracie kanály na skutočné dva fyzicky nezávislé snímače, s dostupnými neistotami, oneskorením a protokolom kalibrácie. Kým to nie je vykonané, nasledujúci článok reťazca má status BLOCKED_REAL_DATA.
