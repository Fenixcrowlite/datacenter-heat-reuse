# DataCenter Heat Reuse: normative baseline / calibration lane (23.10.2026)
**Owner:** Independent standards-and-synthetic-data workstream. **DO NOT modify** `matlab/pool_500m3` or `docs/pool_500m3` (the other chat owns the dynamic pool model).
## Deliverables
- `sources_and_benchmarks.json`: traceability links, valid-as-of date, confidence classes and explicit incomplete verifications.
- `benchmark_calculator.py`: reproducible parameter-dependent heat/PUE/ERF screening with units and normative warning.
- `interactive_calculator.html`: standalone interactive RU interface, no dependencies or Internet needed to compute. Editable pool dimensions, water temperatures, thermal power/loss, COP, source temperature, IT capacity/utilization, recovery and PUE. Exports JSON.
- `test_benchmark_calculator.py`: independent unit tests.
- `comparison_result.json`: automatically produced by the CLI after execution.

## Research values actually sourced
- **PUE**: Uptime 2026 sample mean **1.52**, n=644 (not a mandatory limit, not a particular site's value). Original scenario 1.20 is more efficient than sampled mean; do NOT automatically replace 1.20 with 1.52 inside old simulation. Run both and document cohort comparability.
- **PUE method**: ISO/IEC 30134-2:2026; EU 2024/1364 specifies PUE and ERF=E_REUSE/E_DC with waste heat at data centre boundary. Do not count extra compressor electricity as reused DC waste heat.
- **Pool max**: published Slov-Lex 308/2012 §8(7) says **28°C swimming pool maximum**. Original thermostat OFF 28.2°C crosses it. This is a design stop-warning, pending verification of currently consolidated legal version. The default calculator changes to target 27.5°C / OFF 27.8°C only; it does NOT silently alter the other chat's Simulink model.
- **Design**: STN EN 15288-1+A1:2024 valid safety standard for public pool design; its full licensed body is not audited. Reference **25×12.5×1.6m = 500m³** is illustrative and must NOT be called a World Aquatics-compliant competition pool. Alternative **25×20×2m=1000m³** is likewise only a geometry scenario until detailed compliance.
- **Geometry scaling**: the 31.45 kW mean holding loss from the concurrent synthetic 312.5m2 scenario is scaled by open water area for preliminary comparison, not as a validated enclosure heat-loss model.
- **Evaporation**: US DOE Pool Efficiency notes evaporative losses dominant and potential overall pool-heating savings 50–70% with covers. The other model's 90% evaporation reduction is a separate scenario assumption, not an empirically proven total saving.
- **Weather**: official Copernicus ERA5 hourly dataset selected but **not downloaded/calibrated**.
- **Tariffs**: Eurostat nonhousehold nrg_pc_205 selected but consumption-band/country-period numbers **not downloaded/calibrated**.
- **Heat pump**: fixed COP 4 remains synthetic until manufacturer COP(T_source,T_sink,PLR) grid and appropriate test condition (EN 14511) are secured.
- **Cooling fractions**: 0.7/0.85/0.9 not measured, never interpret as normative values.

## How to execute on Windows
```powershell
$dir = 'C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\calibration\standards_20261023'
Set-Location $dir
python -m unittest -v test_benchmark_calculator.py
python benchmark_calculator.py --output comparison_result.json
python benchmark_calculator.py --length-m 25 --width-m 20 --depth-m 2 --pue 1.52 --target-C 27.5 --switch-off-C 27.8 --output comparison_1000m3.json
Start-Process (Join-Path $dir 'interactive_calculator.html')
```
Each CLI output refuses to overwrite existing results. For calibration/reality check import and timestamp real records; first 2025/2026 ERA5 temperatures, Eurostat tariff after selecting actual industrial consumption-band/tax regime, manufacturer heat-pump map and DC metering.

## Measurement and comparison contract
A = measured on nominated installation, B = published primary study/dataset, C = manufacturer specs/provider, D = assumed scenario.
Dataset row must contain variable, value, SI unit, source URL/DOI, observation year, aggregation window, location/facility, source confidence, model mapping, uncertainty and reference conditions. Reject comparing unmatched denominators/boundaries (IT vs facility; pool heating only vs natatorium HVAC; source vs HP delivered heat).

## Integration contract for pool workstream
1. Keep existing baseline v85/v86 and pool files untouched.
2. Pool Stateflow control should have hard `T_water <= T_max` safety interlock with hysteresis and measurement error allowance; introduce a **new model version** rather than overwriting existing.
3. Add mode-dependent thermal source allocation, HP source partition and direct-exchanger approach; always preserve independent IT cooling.
4. Export `time[h],Twater[C],Q_pool[kW],Q_source_dc[kW],W_HP[kW],mode,flags`; verify interval energy residual and consumption at DC boundary.
5. Distinguish ideal first heatup from 7-day model and 8760 h yearly totals. Hourly seasonal source/weather requires independent measured profiles.

No legal compliance or scientific validation is claimed by running the supplied tests.
