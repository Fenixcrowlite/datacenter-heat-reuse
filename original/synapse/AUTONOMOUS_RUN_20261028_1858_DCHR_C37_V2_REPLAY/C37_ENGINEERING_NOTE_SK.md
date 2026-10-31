# DCHR C37 — reprodukovateľný hodinový priebeh Warm45_Storage100 (v2)

**Rozsah:** samostatný výpočtový kandidát v izolovanom priečinku. Pôvodné súbory MATLAB/Simulink ani CSV v OneDrive sa nemenili. Údaje predstavujú syntetický modelový rok 2026 (8760 h), nie meranie prevádzky.

## Pôvod a výpočtový postup

Zdrojové definície: `matlab/run_experiment_v2.m`, `default_config.m`, `default_config_v2.m`, `+dchr/simulate_system_v2.m`, `+dchr/+components/*.m`. Pôvodný MATLAB driver exportuje posledný scenár `Liquid35_LowTempDH` pod zavádzajúcim názvom `best_scenario_v2_timeseries.csv`. Preto sme samostatne rekonštruovali hodinový priebeh **Warm45_Storage100** bez zmeny originálnych dát.

Pre každý hodinový interval sa vypočíta teplota siete podľa počasia, dostupné teplo zdroja, účinnosť výmenníka, COP Carnotovho modelu, priamy prenos tepla, nabíjanie/vybíjanie akumulátora, elektrický príkon TČ a plynový dohrev. Akumulátor má **100 MWh**, nabíjací/vybíjací limit **5 MW**, účinnosti **0,95**, hodinovú stratu **0,0001**. Ide o **jednouzlový energetický model** bez teplotného profilu vody.

## Overenie

Najprv bol rovnaký Python algoritmus použitý na referenčný scenár Liquid35_LowTempDH. **192 720** porovnaní s pôvodným MATLAB CSV: najväčšia absolútna odchýlka **8,53 × 10⁻¹⁴**; priebežný stav akumulátora maximálne **3,91 × 10⁻¹³ MWh**. Rekonštrukcia Warm45_Storage100 následne reprodukovala päť ročných metrík z pôvodného `scenario_summary_v2.csv` s maximálnou odchýlkou **1,24 × 10⁻⁹ MWh**.

Nezávislý test s `decimal.Decimal` preveril **8760/8760** hodinových energetických bilancií akumulátora (maximálne rezíduum **2,41 × 10⁻¹⁴ MWh**) a šesť ročných súčtov. Vstupné syntetické časové rady a časové značky sú rovnaké pre v1 a v2.

## Ročné výsledky a interpretácia

| Ukazovateľ | v1 Warm45_Storage100 | v2 Warm45_Storage100 | Rozdiel v2 − v1 |
|---|---:|---:|---:|
| Plynové teplo [MWh] | 10 413,416 | 10 542,548 | +129,132 |
| Elektrina TČ [MWh] | 7 161,767 | 7 969,876 | +808,109 |
| Potreba tepla [MWh] | 59 429,977 | 59 429,977 | ≈0 |

**Rozdiely nie sú preukázané úspory.** v1 a v2 používajú odlišné komponentové modely, hoci vstupné časové rady sú zhodné. Samotný scenár v2 Warm45_Storage100 má modelové pokrytie **82,2606 %** a potrebu plynového tepla **10 542,548 MWh/rok**.

## Obmedzenia a ďalší krok

Výsledok je Python replay podľa zdrojových rovníc, **nie nový beh MATLAB-u**. Neoveruje zhodu so Stateflow v85 (10 MWh), stratifikovaným fyzikálnym zásobníkom ani s meranou prevádzkou. Primárne literárne zdroje zostávajú **0/31**. Ďalej vytvoriť izolovaný natívny MATLAB export `Warm45_Storage100` (bez prepísania spoločných CSV), porovnať ho po hodinách s týmto replay a až potom riešiť hranice v85 a fyzikálneho modelu.
