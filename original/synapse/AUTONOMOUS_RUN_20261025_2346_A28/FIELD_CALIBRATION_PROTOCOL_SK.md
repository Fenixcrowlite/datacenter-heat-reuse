# DCHR A28 | Protokol pre meranie kovariancie chýb

**Stav:** izolovaný nástroj QA; nie je nasadený do SCADA ani MATLAB. Všetky dodané príklady sú **syntetické**, nie sú to merania zariadenia.

## Prečo nestačia prevádzkové dáta

Kovariancia prietoku a teplôt počas bežnej prevádzky obsahuje skutočné zmeny procesu. Z nej nemožno bez referencie určiť kovarianciu **chýb snímačov**. Preto každá vzorka vyžaduje synchronizované odčítanie snímača a referencie: `e_F = F_read - F_ref`, `e_H = T_hot_read - T_hot_ref`, `e_C = T_cold_read - T_cold_ref`.

Odhad systematického posunu: `b_i = (1/n) sum(e_i,k)`. Odhad kovariancie náhodných rezíduí: `S_ij = sum((e_i,k-b_i)*(e_j,k-b_j))/(n-1)`. Tieto dve zložky sa **nesmú zamieňať**. Pri výpočte neistoty tepelného výkonu sa následne použije `J S J^T`, kde `J = (rho*c_p/3600) * (DeltaT, F, -F)` pre prietok v m3/h a teploty v °C.

## Vstupný kontrakt

CSV musí mať presne stĺpce: `flow_time_utc,hot_time_utc,cold_time_utc,flow_read_m3h,flow_ref_m3h,hot_read_C,hot_ref_C,cold_read_C,cold_ref_C`. Časy musia obsahovať časové pásmo, vzorky musia byť monotónne, bez duplicít a veľkých výpadkov. Vyžaduje sa najmenej 12 trojíc a kladný prietok.

JSON metadáta: `source_class` (`SYNTHETIC_TEST` alebo `FIELD_CALIBRATION`), `units` (`flow=m3/h`, `hot=degC`, `cold=degC`), `sample_period_s`, `max_skew_s`. Pre `FIELD_CALIBRATION` sú povinné pre všetky tri kanály údaje `certificates.{flow,hot,cold}.{instrument_id,reference_id,file,sha256,expires_utc}`. Súbory certifikátov sa kontrolujú podľa SHA256 a deklarovanej expirácie. **To nie je overenie pravosti certifikátu ani metrologickej nadväznosti.**

## Spustenie (bez zmeny prevádzky)

`python field_calibration_gate.py --csv paired.csv --metadata metadata.json --output evidence.json`

Príklad: `example_synthetic/paired.csv` a `example_synthetic/metadata.json`. Vždy skončí `SYNTHETIC_ONLY_NOT_FIELD_VERIFIED`. Aj pri formálne vyhovujúcich terénnych vstupoch zostáva `release_allowed=false`, kým nezávislý odborník neoverí kalibráciu, stabilitu, reprezentatívnosť a porovnanie s referenčným kalorimetrom.

Autokorelácia prvého rádu a odhad efektívneho počtu vzoriek sú **len diagnostika s predpokladom AR(1)**, nie spoľahlivý interval. Systematický posun sa nesmie zmenšiť delením odmocninou z počtu meraní.

## Akceptácia pred nasadením

1. Dodať skutočné spárované merania a súbory kalibrácie s overiteľným pôvodom.
2. Nezávisle overiť platnosť kalibrácie a metrologickú nadväznosť, jednotky, časovú synchronizáciu, rozsah prevádzky a stabilitu rezíduí.
3. Porovnať odvodenú neistotu s nezávislým kalorimetrom na oddelených dátach.
4. Integrovať PSD-validátor A27 len po kontrole vlastníka; následne spustiť regresné testy A26+A27+A28.
5. Až potom rozhodnúť o použití vo výpočte reálnej tepelnej bilancie. Žiadny výstup tohto balíka nedokazuje fyzickú bezpečnosť dátového centra alebo bazéna.
