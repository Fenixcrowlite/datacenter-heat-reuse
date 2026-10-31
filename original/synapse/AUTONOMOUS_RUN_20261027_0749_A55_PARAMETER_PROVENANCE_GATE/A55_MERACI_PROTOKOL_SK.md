# A55: Merací a kalibračný protokol pre tepelný okruh DataCenter

**Stav:** implementovaný validačný nástroj; fyzikálna kalibrácia **BLOKOVANÁ**. Žiadne údaje z reálneho zariadenia neboli dodané tomuto behu. Výsledky A54 sú syntetické, trieda D, nie bezpečnostné limity.

## 1. Pas premenných a rovnice

| Premenná | Jednotka | Význam | Identifikácia |
|---|---|---|---|
| `C_eff` | J/K | efektívna tepelná kapacita sledovaného okruhu | `Q_net Δt = C_eff ΔT` |
| `Q_net` | W | meraný čistý tepelný tok do definovaného kontrolného objemu | bilancia kalibrovaných prietokov a teplôt |
| `T` | °C | teplota v rovnakom kontrolnom objeme | kalibrovaný snímač |
| `P_cmd` | W | požadovaný tepelný výkon kompresora | log riadenia |
| `P_actual` | W | skutočný tepelný výkon | nezávislé meranie |
| `tau` | s | časová konštanta prvého rádu | `P_i=P_cmd+(P_(i-1)-P_cmd) exp(-Δt/tau)` |
| `f_res` | 1 | podiel zvyškového tepla po odstavení IT | `Q_residual/Q_nominal` |

**Identifikácia kapacity:** pre intervaly s dostatočnou zmenou teploty sa odhadne
`C_eff = Σ(ΔT_i · Q_net,i · Δt_i) / Σ(ΔT_i²)`.
Znamienka teplotnej a energetickej zmeny musia súhlasiť. Predpokladá sa homogénna teplota a časovo priemerný tok; pri silnej stratifikácii treba viacuzlový model.

**Identifikácia kompresora:** pri stabilnej požiadavke je
`r_i=(P_actual,i-P_cmd)/(P_actual,i-1-P_cmd)`, `tau_i=-Δt_i/ln(r_i)`.
Prípustné je iba `0<r_i<1`. Pri veľkej variabilite odhadov prvý rád nepostačuje.

**Zvyškové teplo:** konštantný `f_res` je iba lokálny model. Ak sa po odstavení mení o viac než 20 % vzhľadom na medián, nástroj odmietne konštantný model. Treba identifikovať časový priebeh.

## 2. Prevod scenárovej kapacity A54 na ekvivalent vody

Pri predpoklade vody okolo 20 °C: `rho=998 kg/m³`, `cp=4182 J/(kg·K)`, `V_eq=C_eff/(rho·cp)`.
Pre A54 `C_eff = 6/8/10 MJ/K` je `V_eq ≈ 1.438/1.917/2.396 m³`.
**Nejde o zmeraný objem okruhu.** Kov, glykol, tepelný výmenník, nehomogénna teplota a hranice kontrolného objemu môžu ekvivalenciu zmeniť.

## 3. Požadované vstupy

CSV: `timestamp_utc,asset_id,calibration_ref,T_C,Q_net_W,P_cmd_W,P_actual_W,trip_state,Q_residual_W,Q_nominal_W`.

Samostatný JSON: `asset_id`, `source_kind` (`real_telemetry` alebo `synthetic_test`), `sensor_calibration_record`, `original_csv_sha256`, `provenance_notes`.

Časové pečiatky musia byť v UTC, monotónne; potrebných je aspoň 20 vzoriek. Pre reálnu skúšku sa musia zaznamenať hranice kontrolného objemu, presnosť snímačov, metóda výpočtu `Q_net`, definícia času príkazu, identifikácia konkrétneho tepelného čerpadla a režim ochrany. Metadata v JSON nie sú náhradou za nezávislé overenie kalibračného certifikátu.

## 4. Pravidlá prijatia

Nástroj odmieta chýbajúce metadáta, zmenu SHA256, časové chyby, nekonečné hodnoty, nesúlad energie, neidentifikovateľný `tau` a nestacionárne zvyškové teplo. Uvádza empirické percentily p10/p90, **nie štatistické intervaly spoľahlivosti**.

Aj pri reálnom CSV je stav iba `MEASURED_CANDIDATE_REQUIRES_INDEPENDENT_QA`. Bez nezávislej kontroly senzorov, datasheetu a prevádzkových hraníc sa parametre nepovyšujú na certifikované a fyzické riadenie sa nepovoľuje.

## 5. Ďalší krok

Získať merania a datasheet konkrétneho zariadenia, spustiť `calibrate(csv_path, metadata_path)`, overiť identifikovateľnosť a chyby, následne preniesť **iba schválené** intervaly do samostatnej grafickej Stateflow regresie. Žiadna zmena pôvodných modelov A48–A54.
