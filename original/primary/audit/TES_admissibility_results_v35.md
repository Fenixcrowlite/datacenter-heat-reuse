# v35 executed saved-v34 admissibility and dimensional defect audit

UTC: 2026-10-10T07:32:15.442162+00:00. **OPEN DEFECT; no new SLX or corrected-controller acceptance.**

Fresh MATLAB batch exit 0: 1205/1205 assertions PASS, 20 scenarios, 109 intervals, 136 positive segments, all six modes. Independent RK4 bound checks: 27/27. Maximum clean first-law residual 4.76837158e-08 MWh (large-energy cancellation stress; smaller-case details remain in traces).

The actual saved-v34 allocator mutation adds .01 h (36 s) to each reported end age. The monitor rejects it at 10, 1e4 and 1e6 MWh but incorrectly accepts it at 1e9 MWh. Independently re-exported MATs contain the corrupted trace; hour-based QA rejects all 128 corrupted slots. The direct guard probe also admits age .24 h against required .25 h at 1e9 MWh. Clean source/demand traces are not claimed to exhibit an early restart. The model was restored and re-executed; the original SLX hash is unchanged.

| Timeline | Step (h) | End TES (MWh) | Electricity (MWh) | Unmet (MWh) | End latch / age (h) |
|---|---:|---:|---:|---:|---:|
| demand_step | 0.5 | 9.146695605 | 2.216216216 | 0.000000000 | 0 / 0.500000000 |
| demand_step | 0.25 | 9.146695605 | 2.216216216 | 0.000000000 | 0 / 0.500000000 |
| demand_step | 0.125 | 9.146695605 | 2.216216216 | 0.000000000 | 0 / 0.500000000 |
| source_step | 0.5 | 8.808647083 | 2.027027027 | 0.000000000 | 1 / 1.000000000 |
| source_step | 0.25 | 8.808647083 | 2.027027027 | 0.000000000 | 1 / 1.000000000 |
| source_step | 0.125 | 8.808647083 | 2.027027027 | 0.000000000 | 1 / 1.000000000 |
| safe_held | 0.5 | 9.493899354 | 2.258725642 | 0.000000000 | 0 / 0.107119187 |
| safe_held | 0.25 | 9.493899354 | 2.258725642 | 0.000000000 | 0 / 0.107119187 |
| safe_held | 0.125 | 9.493899354 | 2.258725642 | 0.000000000 | 0 / 0.107119187 |

These timelines keep input change times fixed at .5 h boundaries; the finite partition comparisons pass. The separate initial-OFF overload case yields .875 MWh unmet, matching the independent power-limit calculation. A sample at StopTime executes its full following physical interval. The base six cases inherit the independently verified v34 fixture specification; no new annual simulator comparison is claimed here.

QA breakdown: `{"numeric": {"passed": 10712, "failed": 0}, "artifact": {"passed": 10310, "failed": 0}, "partition": {"passed": 9, "failed": 0}, "defect": {"passed": 141, "failed": 0}, "archive": {"passed": 6, "failed": 0}, "preservation": {"passed": 1347, "failed": 0}}`. 1347 prior unique immutable entries preserved. Supplementary source/receipt/MAT/equipment bindings: 63 PASS. These are distinct from model assertions.

Primary equipment evidence and independent equations: `audit/TES_admissibility_derivation_v35.md`. Copeland page 20 was visually inspected, and PDF page 1 establishes equipment scope. Both acquired source hashes were rechecked. No equipment values were adopted into the model. Full primary article signoffs remain 0/31.

Earlier unclosed work is preserved: MATLAB sandbox startup failures, cell/struct harness error, old reviewer failures (large-scale energy cancellation and an incorrectly placed overload expectation), and an old cleanup warning. The revised specification explicitly starts the overload control OFF. This run first rejected an incompatible old-result/new-reviewer pairing with KeyError; that log is retained. Fresh latest-spec simulation, separate MAT export and reviewer now pass; the final cleanup warning is absent. All actual Stateflow shadow warnings remain in the batch log.

Evidence: `results\stateflow_admissibility_v35_20261010T072819778Z`, `results\stateflow_admissibility_v35_20261010T072819778Z\independent_QA_v35_20261010T073002_065500Z.json`, `audit\Stateflow_completion_QA_v35_20261010T073215_442162Z.json`, `audit\Stateflow_execution_v35_20261010T072815949Z.json`, `audit\Stateflow_execution_v35_20261010T072949614Z.json`.

Remaining limitations:

- OPEN clock/guard tolerance defect at adversarial numerical capacity scale; this checkpoint accepts defect reproduction only, no corrected model.
- Guard early-age result is a direct component probe, not an observed early transition in a clean Stateflow run; allocator corruption is actual saved-model runtime evidence.
- Extreme capacities are numerical stress tests, not plausible installations; clean prior v34 fixture acceptance remains scoped to its evidence.
- Held source/demand timelines are preserved across .5/.25/.125 h partitions for three finite fixtures only.
- Binding OFF dwell can leave unmet demand from instantaneous TES/backup limits, even with ample energy; source outage can extend OFF indefinitely.
- Copeland guidance is equipment-specific primary documentation; EnergyPlus is primary engineering documentation; no new primary article signoff or parameter calibration.
- Normal-mode host planner, analytic segment offsets at macro solver timestamps; no standalone code generation or solver-clock events.
- No measured or calibrated physical validation, stratification/hydraulics, startup/cycling-loss equipment model or article replication.
- Independent algorithm/artifact QA is not separate human/agent review. Nonfatal Stateflow formal-argument shadow warnings remain visible.

Next: Implement additive Stateflow v36 with separate energy, power, temperature, dimensionless and physical-hour tolerances; embed corrected guard/monitor, preserve v34 and v35 counterexamples, execute the six modes and changing-input fixtures, and require clock corruption and early-dwell guards to reject at every tested energy scale. Audit representable time resolution and retain equipment assumptions without calibrated cycling-loss claims.
