# A62 | SCADA export so znamienkovými stratami a diskrétnou energiou

**Účel:** odstrániť informačnú medzeru A60 bez úpravy pôvodného A60, MATLAB, SCADA alebo používateľského rozhrania. Nový výstup `analysis_with_signed_losses.csv` je samostatný artefakt s verziou schémy `a62.1`.

## Pridané kanály (W a J)

- `Q_pool_loss_W`: pôvodné **podpísané** straty, môžu byť záporné (tepelný zisk z okolia).
- `Q_pool_net_W = Q_pool_W - Q_pool_loss_W`: čistý tepelný tok do vody.
- `E_pool_input_cum_J = Σ Q_pool[k] × 900 s`.
- `E_pool_signed_loss_cum_J = Σ Q_pool_loss[k] × 900 s`.
- `E_pool_stored_cum_J = 997 × 500 × 4182 × (T_pool[k] − 16 °C)`.
- `state_residual_W = C × (T[k] − T[k−1])/900 − Q_pool_net[k]`.

Pôvodné stĺpce A60 zostávajú v CSV zachované. Čas `time_s` reprezentuje časové značky 0 až 603900 s, kým kumulatívna energia obsahuje **672** aktualizácií po 900 s (168 h). A60 trapezoidový integrál medzi časovými značkami (167,75 h) sa neprepisuje.

## Pôvod a fail-closed kontrola

Pred exportom A62 používa validátor A61, ktorý kontroluje SHA256 oboch zdrojov, zhodu časov, mapovanie kanálov, fyzikálnu bilanciu a `source_kind=derived_simulation`. Zápis je do nového priečinka; existujúci cieľ sa neprepisuje. `physical_release=false`, `calibration_ready=false`.

V08 aj V09: **672 riadkov**, **91 riadkov so zápornými stratami**. Nezávislý kontrolný výpočet pomocou `decimal.Decimal` porovnal **10 752** hodnôt vrátane kumulatívnych energií a rezíduí. Žiadne reálne meranie ani kalibračný certifikát sa nepredstierajú.

## Ďalší krok

Nový CSV kontrakt možno použiť pri offline analýze a vizualizácii energetickej bilancie. Na fyzikálnu validáciu sú naďalej potrebné skutočné kalibrované merania; grafická Stateflow a SCADA release acceptance zostávajú oddelenými úlohami.
