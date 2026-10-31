# A67: Bezpečné opakované overenie zaregistrovaného checkpointu

Pri opakovanom spustení pôvodného A66 finalizátora sa odhalila chyba: generoval nový časový údaj v nemennom `FINAL_HANDOFF.md`, preto druhý beh zlyhal na `IMMUTABLE_CONFLICT`. Prvé zaregistrovanie A66 zostáva platné, manifest a udalosť neboli zmenené.

A67 je nezávislá read-only kontrola. Nemení A66 ani databázu; overuje všetky SHA256 z manifestu, SHA256 evidence/handoff v existujúcej udalosti Synapse, presne jednu udalosť daného aktéra a `physical_release=false`. Pri opakovaní vracia rovnaký `ALREADY_RECORDED` bez vedľajších účinkov.

Regresné testy kontrolujú poškodený artefakt, duplicitnú udalosť, nesúlad digestu, pokus o prechod mimo priečinka, chýbajúci súbor a nepravdivý príznak fyzickej validácie. Testy používajú dočasnú SQLite databázu, ktorá sa po každom teste riadne zatvorí.

Obmedzenie: A67 nie je náhradou fyzickej validácie ani univerzálnym finalizátorom. Ďalší krok je upraviť šablóny budúcich finalizátorov tak, aby čas checkpointu bol stabilný a opakovaný beh neprepisoval historické dôkazy.
