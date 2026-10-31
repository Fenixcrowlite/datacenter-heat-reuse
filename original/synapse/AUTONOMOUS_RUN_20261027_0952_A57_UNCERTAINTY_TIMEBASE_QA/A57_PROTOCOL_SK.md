# A57 | Kontrola neistoty merania a časovej synchronizácie

**Stav:** softvérový kontrolný modul s nezávislým syntetickým príkladom. **Nie je to fyzikálna kalibrácia, certifikácia bezpečnosti ani prevádzkové povolenie.** Vstupy A55/A56 zostávajú nezmenené. Údaje z reálneho zariadenia zatiaľ neboli overené.

## 1. Účel a vstupy

A55 odhaduje efektívnu tepelnú kapacitu `C_eff`, časovú konštantu kompresora `tau` a podiel zvyškového tepla. A56 odhaľuje vybrané chyby energetickej bilancie a prechodovej charakteristiky. A57 k nim pridáva **konzervatívne medze chyby** teploty, výkonu a času.

Príkaz: `python run_a57.py telemetry.csv metadata.json uncertainty.json --output report.json`. Existujúci report sa neprepisuje. Základné CSV a metadata majú formát A55. `uncertainty.json` musí obsahovať zhodné `asset_id`, `source_kind`, `source_csv_sha256`, `calibration_ref`, `timebase=UTC`, `time_sync` a štyri záznamy `sensors`: `T_C`, `Q_net_W`, `P_cmd_W`, `P_actual_W`.

Pre každý snímač sa zadáva `abs_error_bound` v jednotke veličiny a bezrozmerný `relative_error_bound`. Každý záznam obsahuje referenciu kalibrácie a SHA256 dokumentu. **Samotný hash nie je dôkazom pravosti ani nezávislej kontroly certifikátu.** Pri syntetickom príklade sú použité nulové zástupné hashe.

## 2. Rovnice a fyzikálne predpoklady

Pre interval `i`: `E_i = Q_net,i Δt_i` [J], `ΔT_i = T_i - T_(i-1)` [K], `C_eff ≈ E_i/ΔT_i` [J/K].

Najhoršia zadaná chyba merania `x` je `u_x = u_abs + u_rel |x|`. Pre rozdiel teplôt `u_ΔT = u_T(i) + u_T(i-1)`. Pre intervalový čas `u_Δt = 2 (u_clock + u_timestamp)` [s]. Pre energiu `u_E = u_Q Δt + (|Q| + u_Q) u_Δt` [J]. Pri známom znamienku `E` a `ΔT` sú konzervatívne medze `C_min = (|E| - u_E)/(|ΔT| + u_ΔT)`, `C_max = (|E| + u_E)/(|ΔT| - u_ΔT)`. Interval s nejednoznačným znamienkom sa nepoužije.

Kompresor prvého rádu: `r = |P_actual,i - P_cmd| / |P_actual,i-1 - P_cmd|`, `tau = -Δt/ln(r)` [s]. A57 počíta dolnú/hornú medzu `r` z absolútnych chýb `P_actual` a `P_cmd`; `tau_min = (Δt-u_Δt)/(-ln(r_min))`, `tau_max = (Δt+u_Δt)/(-ln(r_max))`. Platí iba pri stabilnom príkaze, `0<r_min≤r_max<1` a identifikovateľnom prechode.

Zadané chyby sa interpretujú ako **deterministické horné medze**, nie ako štandardné odchýlky. Výstupný interval je obálka všetkých použiteľných intervalov, nie 95 % interval spoľahlivosti. Predpokladá sa zodpovedajúci kontrolný objem a synchronizované meranie príkazu a odozvy. Pre reálne zariadenie je potrebné overiť koreláciu chýb, drift, odozvu snímačov, fyzikálnu bilanciu a hranice platnosti prvého rádu.

## 3. Časová synchronizácia

`time_sync.method` musí byť zdokumentovaná metóda (PTP/NTP/GPS/spoločné hodiny, alebo syntetické hodiny). Zaznamenávajú sa horné medze absolútneho posunu hodín, neistoty synchronizácie, chyby časovej pečiatky a latencie akčného člena. Softvérová kontrola odmietne nejednoznačné intervaly alebo príkazové prechody. Tieto interné prahy (10 % a 25 % najkratšieho intervalu) sú **inžinierske pravidlá A57**, nie normové bezpečnostné limity.

## 4. Reprodukovateľný príklad

`build_demo_a57.py` vytvorí `DEMO_SYNTHETIC`: 65 vzoriek v 60-sekundových intervaloch, `C_eff=8 MJ/K`, `tau=300 s`, nulové fyzické uvoľnenie. Nezávislý `Decimal` výpočet kontroluje 64 energetických bilancií.

Pri zadaných **syntetických** medziach vychádza `C_eff` približne **7.456–8.622 MJ/K** a `tau` približne **207–538 s**. Rozsahy platia výlučne pre demonštračné údaje a zadané modelové chyby. Nesmú sa použiť ako limity skutočného zariadenia.

## 5. Blokujúce podklady a ďalší krok

Pre skutočnú identifikáciu treba získať zhodné ID zariadenia, merania `T, Q_net, P_cmd, P_actual` s UTC časom, metódu synchronizácie, odhad presnosti a kalibračné certifikáty všetkých snímačov, definíciu kontrolného objemu a katalógové údaje kompresora. Potom vykonať A55+A56+A57 na **nezmenených originálnych súboroch**, nezávislú revíziu neistôt a až následne izolovanú Stateflow regresiu. `physical_release=false` zostáva záväzné.
