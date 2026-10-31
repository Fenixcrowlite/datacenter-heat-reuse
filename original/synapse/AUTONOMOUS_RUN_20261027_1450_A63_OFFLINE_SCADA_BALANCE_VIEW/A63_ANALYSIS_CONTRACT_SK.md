# A63 | Offline analýza energetickej bilancie SCADA

**Rozsah:** samostatný statický HTML prehliadač bez internetu a bez úprav existujúcej SCADA/FUXA, MATLAB/Stateflow, A60, A61 alebo A62. Otvoriť `OUTPUT/dashboard.html` v prehliadači. Prepínač umožňuje porovnanie scenárov SCADA v08 a MATLAB v09.

## Energetické veličiny

- Príkon tepla do bazéna: `Q_pool_W` [W].
- Podpísané tepelné straty: `Q_pool_loss_W` [W]. Záporná hodnota znamená prísun tepla z okolia.
- Čistý tepelný tok: `Q_pool_net_W = Q_pool_W - Q_pool_loss_W` [W].
- Diskrétna vstupná energia: `E_in[k] = Σ(i=0..k) Q_pool[i] Δt` [J].
- Podpísané straty: `E_loss[k] = Σ(i=0..k) Q_pool_loss[i] Δt` [J].
- Energia uložená vo vode: `E_store[k] = ρ V cp (T[k] - T0)` [J].
- Rezíduum: `r[k] = ρ V cp (T[k]-T[k-1])/Δt - Q_pool_net[k]` [W].

Predpoklady A62: `Δt=900 s`, `V=500 m³`, `ρ=997 kg/m³`, `cp=4182 J/(kg·K)`, `T0=16 °C`. Ide o predpoklady syntetického modelu, nie o certifikované parametre zariadenia.

**Dôležité:** 672 aktualizácií po 900 s predstavuje 168 h, ale rozdiel medzi prvou a poslednou časovou značkou je 167,75 h. Trapezoidálna integrácia A60 a diskrétna integrácia A62 preto nie sú zameniteľné.

## Kontrola pôvodu a kvality

Generátor `a63_offline_dashboard.py` kontroluje SHA256 vstupných CSV, schému A62, počet vzoriek, časovú os, jednotky, energetické súčty a numerické rezíduá. Odmieta vstupy s `physical_release=true`, s iným `source_kind`, s neplatnými alebo nekonečnými číslami. Nevytvára nový cieľ, ak už existuje.

Nezávislá kontrola `independent_qa_a63.py` porovnáva všetky číselné kanály v HTML s pôvodnými CSV, opätovne počíta energie cez `Decimal` a kontroluje JavaScript pomocou `node --check`. Samostatný headless Chrome overuje vykreslenie šiestich metrík a siedmich SVG kriviek bez zásahu do používateľského profilu.

**Stav:** `VERIFIED` len pre softvérovú offline vizualizáciu odvodených simulácií. `physical_release=false`. Fyzická kalibrácia a bezpečnostná validácia sú `BLOCKED`, pretože chýbajú skutočné merania a certifikáty.

**Ďalší krok:** doplniť do samostatnej offline vrstvy porovnanie časových integrácií A60/A62 s explicitnou voľbou konvencie a jasným označením neistoty; neprepísať existujúce výsledky.
