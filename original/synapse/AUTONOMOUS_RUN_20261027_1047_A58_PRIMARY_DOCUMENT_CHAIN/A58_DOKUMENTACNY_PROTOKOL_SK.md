# A58: Overenie reťazca primárnych dokumentov merania

**Účel:** Zamedziť tomu, aby sa samotný textový SHA-256 odkaz v A57 považoval za existujúci a overený kalibračný certifikát. A58 vyžaduje skutočný súbor a porovnáva jeho bajty s manifestom aj so záznamom neistoty A57.

## Vstupy a väzby

Balík obsahuje `telemetry.csv`, `metadata.json`, `uncertainty.json`, `document_manifest.json` a podadresár `docs/`. Manifest viaže všetky tri dátové súbory ich SHA-256, ID konkrétneho zariadenia, typ dát a presne šesť dokumentov: štyri kalibrácie (T_C, Q_net_W, P_cmd_W, P_actual_W), protokol časovej synchronizácie a mapu prevádzkových parametrov výrobcu.

Každý dokument má ID, relatívnu cestu, SHA-256, vydavateľa, dátum vydania a koniec platnosti. Záznam kalibrácie musí obsahovať jednotku, identifikátor kalibrácie a absolútnu i relatívnu hranicu chyby. Časový protokol musí uvádzať metódu a štyri hranice časovej chyby zhodné s A57. Mapa výrobcu deklaruje teplotný interval v °C a maximálny výkon vo W. Program overuje, či namerané body spadajú do **deklarovaného** rozsahu. Nie je to potvrdenie, že rozsah je autentický.

## Bezpečnostné obmedzenia

Kontrola je lokálna, len na čítanie. Cesty mimo `docs/`, `..`, symbolické odkazy a chýbajúce či prázdne súbory sa odmietajú. Duplicitné JSON kľúče, nesúlad SHA-256, jednotiek, kalibračných referencií, dátumov a neistôt vedú k chybe. Dátum vydania musí predchádzať začiatku merania a platnosť pokrývať koniec merania.

**SHA-256 dokazuje iba zhodu bajtov, nie pravosť certifikátu.** Podvrhnutý dokument s novým SHA-256 môže byť interne konzistentný. Preto ani úspešný beh A58 nikdy nenastavuje `physical_release=true`, `independent_issuer_authentication=true` alebo `safe_operating_limits_certified=true`.

## Skutočné meranie a nezávislá kontrola

Pred fyzikálnou validáciou je potrebné získať originálne záznamy pre konkrétne ID zariadenia, kalibračné certifikáty s overiteľným vydavateľom a nadväznosťou na etalón, protokol synchronizácie času a originálnu mapu výrobcu s verziou a pracovným rozsahom. Nezávislý hodnotiteľ musí potvrdiť identitu vydavateľa, prístrojov, časovú platnosť a aplikovateľnosť mapy na zariadenie.

Potom spustiť A55, A56, A57 a A58 na **nemenených** vstupoch, zapísať SHA-256, vykonať nezávislé porovnanie parametrov a až následne izolované skúšky v Stateflow. Samotný úspech Python testov nie je certifikácia bezpečnosti.

## Reprodukovateľný syntetický príklad

`python -B build_demo_a58.py` vytvorí explicitne označené fiktívne dokumenty. `python -B a58_document_gate.py DEMO_SYNTHETIC` overí väzby. `python -B -m unittest -v test_a58` spustí regresné testy vrátane zámerne poškodených dokladov.

**Stav:** VERIFIED pre syntetický QA reťazec; BLOCKED pre fyzikálne overenie a autentickosť originálnych dokladov.
