# Spätné využitie tepla dátového centra

Projekt zahŕňa pôvodné výpočty MATLAB/Simulink/Stateflow, dokumentáciu a prenosnú aplikáciu Python. Prenos je rozpracovaný: overené sú ročný model v2 a uzavretý model bazéna v04. Ostatné historické modely majú samostatný stav v katalógu.

## Spustenie

```sh
docker compose up --build
```

Otvorte **http://localhost:8080** a zvoľte jazyk SK. Vyberte model a scenár, upravte parametre a spustite nový výpočet. Schéma zobrazuje aktuálne toky tepla a stav zásobníka. Posuvník mení časový okamih, graf zvolenú veličinu. Výsledok možno uložiť do CSV alebo JSON.

Bez Dockeru stačí Python 3.11 alebo novší; v koreňovom priečinku repozitára spustite:

```sh
python -m heat_reuse serve
python -m heat_reuse verify
```

Pôvodné modely a správy zostávajú v `original/`. Katalóg pôvodných blokov a stavov odlišuje overený výpočet Python od samotnej extrakcie schémy. Všetky scenáre sú numerické výskumné modely; zhoda s MATLAB nepredstavuje overenie skutočnej teplárne.

## Úplný archív

Úplný archív obsahuje jedinečné pôvodné súbory, výsledky a historické verzie. Manifest uchováva všetky cesty a kontrolné súčty SHA-256, aj keď sa rovnaký obsah ukladá iba raz. Pri obnove použite nový prázdny priečinok:

```sh
python -m tools.snapshot restore heat-reuse-source-2026-10-30.zip obnovene
```

Lokálne heslá, tokeny, cookies a nainštalované závislosti sa neprenášajú. Vlastné prihlasovacie údaje pre voliteľné MQTT/FUXA služby nastavte samostatne podľa ich pôvodnej dokumentácie. Vypočítané experimenty sa v Dockeri zachovávajú v pomenovanom volume `experiments`.
