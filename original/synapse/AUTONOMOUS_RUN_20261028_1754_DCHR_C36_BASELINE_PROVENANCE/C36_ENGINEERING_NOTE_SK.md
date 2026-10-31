# DCHR C36: pôvod 100 MWh a nesprávne označený časový rad

## Preukázané zo zdrojov
Staršie skripty `run_experiment.m` a `run_experiment_v2.m` explicitne nastavujú `capacity_MWh = 100` pre scenáre. Zásobník je **jednou energetickou veličinou E [MWh]** so stratami, limitmi nabíjania/vybíjania a účinnosťou 0,95; bez dynamickej teploty vody a bez stratifikácie. Toto je pôvod hypotézy 100 MWh, nie overená fyzická nádrž.

## Kritická chyba označenia
`run_experiment_v2.m` zapisuje `O{end}` ako `best_scenario_v2_timeseries.csv`. Posledný scenár je **Liquid35_LowTempDH**, nie Warm45_Storage100. Má pokrytie **78.884 %** a potrebuje **12549.051 MWh** plynového tepla. Najvyššie pokrytie v uloženej tabuľke má **Warm45_Storage100**: **82.261 %**, plyn **10542.548 MWh**. Rozdiel v plynovom teple je **2006.503 MWh**.

## Nezávislé overenie
Oba uložené hodinové CSV majú po **8760** riadkov. Počas každého kroku sme z CSV zrekonštruovali zákon energie zásobníka, nabíjacie/vybíjacie limity, bilanciu tepla, obmedzenie 100 MWh a súlad ročných súčtov s tabuľkami scenárov. Originálne zdrojové súbory boli iba čítané; MATLAB sa nespúšťal.

## Hranica interpretácie
Uložené testy Stateflow v85 s kapacitou **10 MWh** sú iný kontrakt. Výpočty C29–C35 nad `best_scenario_v2_timeseries.csv` treba označovať ako **Liquid35_LowTempDH**, nie ako automaticky najlepší scenár a nie ako v85. Vzniká požiadavka na reprodukovateľný export **Warm45_Storage100** pre korektné porovnanie.
