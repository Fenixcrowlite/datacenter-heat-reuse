# A59: Import SCADA exportu do kalibračného reťazca A55–A58

**Účel:** Prevod existujúceho CSV exportu zo SCADA/MQTT/FUXA na kanonický formát meraní pre A55. Program nevytvára chýbajúce kanály ani kalibračné dokumenty. Nepripája sa k SCADA a nič neposiela do zariadení.

## Pracovný postup

1. Exportovať skutočné namerané dáta do samostatného CSV s časom UTC, identifikátorom zariadenia, referenciou kalibrácie, teplotou, čistým tepelným tokom, príkazom a skutočným výkonom kompresora, stavom ochrany, zvyškovým a nominálnym tepelným tokom.
2. Pripraviť JSON mapu schémy a59.1: source_kind musí byť explicitne real_telemetry alebo synthetic_test; asset_id, calibration_ref, provenance_notes; objekt columns mapuje všetkých 10 cieľových polí na pôvodné názvy stĺpcov; objekt units uvádza jednotky šiestich fyzikálnych kanálov.
3. Spustiť: python -B a59_scada_ingest.py RAW.csv MAPPING.json NOVY_ADRESAR. Výstupný adresár nesmie existovať.
4. Program vytvorí telemetry.csv, metadata.json, provenance.json. Kontroluje integritu CSV, jedinečnosť mapovania, konečné čísla, UTC, monotónny čas s intervalom najviac 3600 s, identitu zariadenia, jednotky a minimálne 20 vzoriek.
5. A55 môže spracovať výstupné telemetry.csv a metadata.json. Na A57/A58 treba osobitne pridať reálne údaje o neistote, originálne kalibračné certifikáty, synchronizačný protokol a mapu výrobcu. Program ich nevymýšľa.

## Jednotky a model

T_C: degC alebo K, prevod T[°C] = T[K] - 273,15. Výkonové kanály: W, kW, MW; prevody 1, 1000, 1 000 000. Q_net_W môže byť záporný, ostatné výkonové kanály musia byť nezáporné. Stav ochrany musí byť presne RUN alebo TRIPPED. Žiadne zaokrúhlenie časových pečiatok ani doplnenie chýbajúcich hodnôt.

## Reprodukovateľný príklad

python -B build_demo_a59.py vytvorí len označené syntetické dáta. python -B -m unittest -v test_a59 vykoná 17 testov vrátane prechodu do skutočného kódu A55 na syntetickej vzorke. Predpoklad testu: 30 bodov po 60 s, efektívna kapacita 8 000 000 J/K, časová konštanta 300 s, zvyškový tok 12 % nominálneho.

**Bezpečnostné hranice:** source_kind=real_telemetry je tvrdenie operátora, nie nezávislé overenie pravosti. SHA256 dokazuje zhodu bajtov, nie kalibráciu ani fyzickú bezpečnosť. physical_release=false vždy. Reálne merania a dokumenty zatiaľ chýbajú, preto fyzická validácia ostáva BLOCKED.

**Ďalší krok:** Získať export z existujúcej SCADA, priložiť mapu stĺpcov a originálne kalibračné doklady, spustiť A59 → A55 → A56 → A57 → A58; až potom posudzovať hranice modelu Stateflow.
