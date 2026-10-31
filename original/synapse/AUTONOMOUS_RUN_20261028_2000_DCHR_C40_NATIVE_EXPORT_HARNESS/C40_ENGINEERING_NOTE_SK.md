# DCHR C40 — izolovaný natívny MATLAB export Warm45_Storage100 v2

## Účel
Predchádzajúci výpočet C37 reprodukoval 8760 syntetických hodín v Pythone, ale **nebol natívnym behom MATLAB-u**. Pôvodný `run_experiment_v2.m` zapisuje zdieľané súbory `scenario_summary_v2.csv`, `best_scenario_v2_timeseries.csv` a obrázky. Jeho spustenie by preto porušilo izoláciu a mohlo prepísať výsledky iných úloh.

## Implementácia
`c40_export_warm45_v2.m` volá priamo `default_config_v2`, `dchr.make_inputs`, `dchr.simulate_system_v2` a `dchr.compute_metrics_v2`. Používa scenár **Warm45_Storage100**: 45 °C zdroj, 90 % rekuperácia, 100 MWh energetický akumulátor, režim `weather`, 5 MW nabíjanie/vybíjanie a RNG seed 42. Výstup smeruje výlučne do vlastného C40 priečinka. Existujúci export sa nesmie prepísať.

`c40_compare_native.py` porovná budúci natívny CSV so samostatným C37 replay: rovnaká schéma 23 stĺpcov, rovnaké časové značky, presne 8760 riadkov a **192 720 číselných hodnôt** s toleranciou 2 × 10⁻⁸. V prípade rozdielu skončí s chybou; nedokáže falošne označiť chýbajúci MATLAB export za úspech.

## QA a stav
**16/16 statických kontraktových kontrol PASS.** **6/6 testov komparátora PASS** vrátane negatívnych testov odlišnej hodnoty, času a počtu riadkov. Kontrola identického C37 súboru (192 720 porovnaní) je **iba test komparátora**, nie dôkaz MATLAB parity.

MATLAB R2026a je nainštalovaný, ale natívny beh sa **nespustil**: pri kontrole zostávalo iba **1,891 GiB voľnej RAM**, pod konzervatívnym limitom 5 GiB. Nezmenili sa žiadne zdrojové MATLAB/Simulink súbory, spoločné výsledky ani worktrees.

## Ďalší presný krok
Po overení STOP/ownership a po uvoľnení aspoň 5 GiB RAM vykonať v izolovanej MATLAB relácii:

`addpath('C:\Users\Lysda\Desktop\SynapseControlCenter\recovery\AUTONOMOUS_RUN_20261028_2000_DCHR_C40_NATIVE_EXPORT_HARNESS'); c40_export_warm45_v2`

Následne spustiť `python c40_compare_native.py --native Warm45_Storage100_v2_MATLAB_NATIVE.csv` a skontrolovať všetkých 8760 riadkov. Natívny export zatiaľ **BLOCKED_BY_RESOURCE_GATE**, Stateflow v85 a fyzikálna validácia zostávajú otvorené. Primárne vedecké zdroje: **0/31** podpísaných.
