# Results v0.2

## Reference experiment

The annual model uses 8760 hourly points, a 10 MW IT reference data centre and synthetic Bratislava-like weather. Economics remain scenario assumptions, not current Slovak market data.

| Scenario | COP | Coverage | HP electricity | Gas backup |
|---|---:|---:|---:|---:|
| Air25_Fixed70 | 3.10 | 78.1% | 14.96 GWh | 13.03 GWh |
| Liquid35_Weather | 4.70 | 82.2% | 10.62 GWh | 10.55 GWh |
| Warm45_Weather | 6.19 | 81.1% | 7.85 GWh | 11.26 GWh |
| Warm45_Storage100 | 6.21 | 82.3% | 7.97 GWh | 10.54 GWh |
| Liquid35_LowTempDH | 6.41 | 78.9% | 7.36 GWh | 12.55 GWh |

## Main conclusions

1. Temperature lift is the central coupling variable between the data-centre cooling architecture and the district-heating network.
2. Higher COP substantially reduces compressor electricity, but does not automatically maximize annual heat coverage when recoverable source heat is fixed.
3. Storage improves temporal matching. In the reference case, 25 MWh already raises coverage from 81.06% to 82.14%; increasing storage to 1000 MWh raises it only to 83.64%, while the screening LCOH proxy rises strongly under the assumed CAPEX.
4. Therefore the project must be treated as a multi-objective problem: electricity, gas backup, curtailment, CAPEX, CO2 and exergy must be evaluated together.

## Important limitation

These numbers are not a forecast for Bratislava and are not a reproduction of a single published plant. They are a reproducible reference experiment used to test architecture and dependencies before real-data calibration.

## Reproduce

```matlab
cd('C:/Users/Lysda/OneDrive/Projects/DataCenter_Heat_Reuse/matlab')
run_tests_v2
summary = run_experiment_v2
run_sensitivity_v2
```
