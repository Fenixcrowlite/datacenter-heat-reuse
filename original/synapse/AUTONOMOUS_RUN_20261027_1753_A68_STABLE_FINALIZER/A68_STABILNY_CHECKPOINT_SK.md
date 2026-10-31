# A68: stabilný a opakovateľný checkpoint dôkazov

## Problém
Pri A66 sa súbor `FINAL_HANDOFF.md` pri opakovanom spustení generoval s novým časom. Zmenil sa jeho SHA256 a nemenný zápis správne odmietol konflikt. Opakované dokončenie úlohy nesmie meniť už registrovaný dôkaz.

## Riešenie
Modul `a68_checkpoint.py` vytvorí `CHECKPOINT_A68.json` len pri prvom spustení. Čas `created_at_utc` je explicitný UTC údaj a pri ďalších spusteniach sa číta z existujúceho súboru. Checkpoint je viazaný na identifikátor scope a SHA256 zdrojového balíka. Zmena vstupov, poškodený JSON alebo nekánonické bajty vedú k odmietnutiu.

Výstupné súbory sa zapisujú exkluzívne a pri opakovaní sa porovnávajú po bajtoch. Registrácia udalosti do existujúcej karty Synapse sa vykoná v transakcii `BEGIN IMMEDIATE`; pred zápisom sa kontroluje stav karty a počet predchádzajúcich udalostí rovnakého aktéra.

## Overenie
13 deterministických testov kontroluje stabilný čas, nemennosť bajtov, zmenený hash, poškodený checkpoint, chýbajúcu časovú zónu, konflikt udalosti, duplikáty a zmenu stavu karty. Testovacia databáza je izolovaná; produkčná databáza sa mení iba pri finálnej registrácii výsledku A68.

## Obmedzenia
Tento mechanizmus neopravuje pôvodný A66 finálizátor a nepovoľuje prepísanie starých dôkazov. Nezaručuje fyzikálnu správnosť dát SCADA. Pri havárii uprostred zápisu exkluzívneho súboru je potrebná manuálna diagnostika; mechanizmus radšej odmietne neúplný checkpoint, než aby ho ticho opravil.

Nasledujúci krok: použiť modul v novom samostatnom finalizátore s regresným testom opakovaného spustenia. A66 a A67 ponechať nemenné.
