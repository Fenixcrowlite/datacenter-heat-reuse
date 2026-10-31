# DCHR C34: kontrola skutočnej kapacity modelu v85

## Overený kontrakt
Uložený súbor `DCHR_Electrical_Dispatch_Stateflow_v85.slx` má SHA256 `2a9de22c0c55e8c4a87f7b0e0cfe9cd97db08c991f09d98361b009de310adde7`, zhodný so stavom v86. Jeho priložený testovací predpis obsahuje **27 prípadov**. Vo všetkých platí `C = 0,2 MWh/K`, `T_min = 20 °C`, `T_max = 70 °C`, teda `E_max = C (T_max - T_min) = 10 MWh`. Zdrojová funkcia `electrical_policy_v85.m` používa presne tento vzťah a pôvodné jadro v75 ho používa pri kontrole energetických hraníc.

## Kritická hranica porovnania
Predchádzajúci izolovaný výpočet C33 predpokladal **100 MWh**. To však nie je hodnota preukázaná v 27 uložených testoch v85. Preto **nesmieme tvrdiť**, že C33 reprodukuje dynamiku uloženého modelu v85 alebo že 100 MWh je kapacita týchto testov. Ani údaj 10 MWh nie je automaticky objem reálnej nádrže: parameter C je agregovaná tepelná kapacita, chýba potvrdenie fyzikálneho objemu, stratifikácie a hydrauliky.

## Dôkaz a hranice
Kontrolovaný SHA modelu, zdrojové funkcie, generátor Stateflow, uložený testovací predpis a pôvodné C33 JSON sú v `C34_V85_CONTRACT.json`. Archív SLX bol skontrolovaný na integritu a prítomnosť Stateflow XML. **Bez spustenia MATLAB/Simulink**, bez úpravy pôvodných súborov, bez overenia primárnych zdrojov. Údaje sú modelové, nie merané.

## Ďalší krok
Nájsť skutočný pôvod predpokladu 100 MWh v dátach alebo inom modeli, overiť definíciu SOC a teploty, následne vykonať porovnanie oboch modelov pri rovnakých vstupoch a počiatočných podmienkach. Dovtedy ponechať porovnanie C33 ako `NOT_PARITY_VERIFIED`.
