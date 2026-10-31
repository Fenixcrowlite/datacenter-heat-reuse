# A69 | Offline prehľad normalizovanej SCADA telemetrie

## Účel
Nový samostatný nástroj `a69_telemetry_review.py` vytvorí z existujúceho balíka A59 (`telemetry.csv`, `metadata.json`, `provenance.json`) **offline HTML prehľad**, strojovo čitateľné zhrnutie a kontrolný SHA256 receipt. Nezasahuje do SCADA, MATLAB, A59 ani spoločného GUI.

## Spustenie
```powershell
python a69_telemetry_review.py FIXTURE OUTPUT_SYNTHETIC
```
Cieľový adresár musí byť nový. Pre skutočný export použite nový cieľový adresár a vstupný balík v schéme A59. Žiadny súbor v pôvodnom balíku sa neprepisuje.

## Výpočty a jednotky
Pre vzorky s časom `t_i` a výkonom `P_i` vo W sa energia počíta **iba medzi pozorovanými vzorkami**:

`E [kWh] = Σ ((P_i + P_(i+1)) / 2) · (t_(i+1) - t_i) / 3 600 000`.

Tento lichobežníkový integrál má `N-1` intervalov pre `N` časových značiek. Posledný nepozorovaný interval sa neextrapoluje. Nepravidelné časové medzery sa označia upozornením. Pre `Q_net_W` je povolený záporný výkon. Počty stavov TRIPPED a prechodov do TRIPPED sa vypočítajú oddelene.

## Demonštračný výsledok
Syntetická vzorka A59 obsahuje 30 meraní, 29 intervalov po 60 s. Nezávislá kontrola cez `Decimal` potvrdila:
- `E(Q_net) = 0.9666666666666667 kWh`
- `E(P_cmd) = 48.33333333333333 kWh`
- `E(P_actual) = 39.99755438873025 kWh`
- `E(Q_residual) = 5.8 kWh`
- Pôvodné dáta už obsahujú 6 riadkov TRIPPED a 1 prechod do TRIPPED.

## Integrita a bezpečnosť
Vstupné tri súbory musia byť pravidelné súbory bez symbolických odkazov. SHA256 CSV a metadata sa musí zhodovať s A59 provenance; metadata musí súhlasiť s identifikátormi a source_kind. Kontrolujú sa UTC značky, monotónnosť, medzera do 3600 s, konečné čísla a dovolené stavy. Neplatný vstup zlyhá pred vytvorením výstupného adresára.

HTML je samostatný súbor bez externých skriptov alebo požiadaviek. Výstup explicitne odlišuje `synthetic_test` a **deklarované** `real_telemetry`. Ani označenie `real_telemetry` neznamená overenie pôvodu, senzorov, kalibrácie alebo bezpečnosti. `physical_release=false` je nemenné.

## QA a otvorené obmedzenia
- Unit/regresia: 19 spustených, 18 PASS, 1 SKIP (Windows nepovolil vytvorenie symlinku v teste; samotná kontrola symlinku je implementovaná).
- Nezávislý prepočet Decimal, 3 vstupné a 2 výstupné SHA: PASS.
- Chrome headless v izolovanom profile cez CDP, **skutočný CSS viewport** 320/390/1440 px: 3/3 PASS, bez horizontálneho overflow, 2 SVG grafy a 4 série.
- Prvý QA test predpokladal nulový počet pôvodných TRIPPED stavov. Opravené na porovnanie voči baseline. Prvé Chrome CLI meranie zistilo minimálny vnútorný viewport 500 px aj pri `--window-size=320`; nahradené skutočnou CDP emuláciou.
- Žiadne skutočné kalibrované merania, certifikáty ani fyzické testy. Integrácia A55–A58 so skutočným zariadením zostáva BLOCKED.

**Nasledujúci krok:** na existujúcom exporte z FUXA/SCADA pripraviť explicitnú A59 mapu kanálov, overiť podpisy a časovú synchronizáciu, následne vygenerovať A69 prehľad; pred akýmkoľvek fyzickým záverom prejsť A57/A58.
