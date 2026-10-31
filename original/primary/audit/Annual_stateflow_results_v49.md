# Actual annual saved-Stateflow results — v49

2026-10-10T22:48:55.585281+00:00. Scoped implementation acceptance PASS.

MATLAB 61/0; independent actual 258635/0 and five separate reviewer self-checks. Actual annual saved v42: 8760 intervals/18495 positive segments/11434 thermal-mode transitions. Annual modes [2, 3, 4, 5]; all six modes passed in six actual acceptance fixtures. Three-day cold prefix72 plus six fixtures gives total 8838 intervals/18573 positive segments. 9588 actual latch changes checked. Maximum independent macro first-law residual 1.3866e-13 MWh.

All 8760 direct seasonal condenser rows reject the specified fixed tank. Explicit separately admitted 85C condenser supports original scheduled delivery up to80C; this is a new engineering boundary, not calibration. The full original scenario is unsupported in the fixed-temperature model. Static admissibility is distinguished from actual trajectory acceptance.

| Actual integrated quantity | Saved v42 annual | Paired loss-first v48 |
|---|---:|---:|
| heat_demand_MWh | 59429.976769254 | 59429.976769254 |
| total_delivered_MWh | 56578.405281424 | 56946.974121320 |
| unmet_heat_MWh | 2851.571487832 | 2483.002647937 |
| hp_heat_MWh | 53152.617059507 | 53646.061859844 |
| hp_electric_MWh | 17761.456196742 | 18107.959728995 |
| gas_heat_MWh | 4533.711886950 | 3421.858594944 |
| storage_charge_MWh | 10536.430527944 | 947.693056745 |
| storage_discharge_MWh | 9428.506862910 | 826.746723277 |
| hp_heating_COP_integrated | 2.992582166 | 2.962567990 |

Stateflow unmet minus paired v48 unmet is 368.568839895 MWh. Both comparisons use actual delivered service. The tank cutoff reduces usable inventory; the controller also cycles HP and trades storage losses/electricity against boiler/unmet. These are joint policy effects, not a claim of improvement or an isolated integration-error estimate.

Evidence: STATUS_v49.json; spec.json, immutable source_snapshot and snapshot_revisions_v49.json; original SimulationOutputs/MAT, reopened exports, numeric dispatch/segment/clock traces, reports; timestamped execution receipts/logs; independent QA JSON and reviewer source snapshots. 1397 prior artifact hashes and accepted SLX CRC/hash pass. Initial sandbox startup and first failed independent review remain saved. No controller/model/numeric artifact changed to obtain revised independent acceptance. Pre-existing unaccepted derivation draft is preserved in the first source snapshot, with a hashed final revision record.

Limitations:

- Actual saved model remains version 0.42 and its accepted SLX hash is unchanged; v49 versions the explicit annual input adapter and executed harness, not a new SLX/controller.
- Original weather-scheduled condenser/delivery boundary is unsupported by a fixed cutoff/tank maximum. All 8760 rows are explicitly rejected for the specified tank; no annual simulation of that boundary is claimed.
- Fixed 85C condenser, 85C tank maximum, 80C delivery cutoff, 48 MWh restart, 0.25h ON/OFF dwell and 20C ambient are synthetic engineering assumptions, not primary equipment calibration. Zero condenser/tank approach is permitted by the reduced model but has no finite-HX/hydraulic validation.
- Nominal 50 MWh tank has only 3.8461538462 MWh above the 80C cutoff. Cold initial E=0 is initially unusable. Passive heat loss can cool below cutoff; discharge cannot cross it.
- Static preflight checks every input with saved v42 physical-domain validation but does not guarantee state-dependent event progress or clock/event budgets for unexecuted scenarios. Adapter scope is the weather/Carnot boundary only.
- Annual trajectory executes modes 2,3,4,5; all six required modes are executed in separate preserved six-case fixtures. Annual transitions and positive segments are actual trace counts, not six-mode annual coverage.
- Physical segments execute within macro timesteps through 64 bounded Stateflow slots, not at solver-clock event times. Normal-mode HP planner uses host MATLAB calls; standalone generated-code deployment is not tested.
- Independent QA is same-agent algorithmic/evidence QA with 60-digit Decimal equations and independent physical-time sums from serialized numeric traces. It is not independent personnel, binary-interval proof for all arithmetic domains, measured physical validation or article replication.
- Paired v48 comparison holds HP lift/source/demand fixed and matches passive retention only. Temperature cutoff/usable inventory, active-port integration and hysteresis/dwell differ jointly. Cost/CO2 use equal actually delivered service; policy differences are not isolated causal effects or an economic optimum.
- Initial/terminal inventory provenance/value, auxiliaries, pumping, network transients, CAPEX and calibrated weather/load/equipment maps remain unspecified. Full primary signoffs remain 0/31; no new research-text claim this run.
- Sandbox MATLAB startup failed before project execution and is retained. Normal local retry passed all 61 MATLAB checks. Inherited Stateflow shadow warnings remain.
- Initial independent review had three evidence-check failures: JSON-versus-CSV exact equality, a legitimate unnamed MATLAB assert, and a preserved pre-existing unaccepted draft derivation. Revised QA uses numeric serialization tolerance, retained rejection messages and a hashed explicit draft revision record; original numeric/model evidence is unchanged and first failed QA remains preserved.

Next actionable task: Execute a matched annual sensitivity matrix on saved v42 at fixed 85C condenser/source/load and identical initial inventory. Vary delivery cutoff, resolved restart band and ON/OFF dwell separately; retain runtime domain/event-budget failures and independently verify actual ports, dwell, inventory and energy reports. Compare each with the paired v48 loss-first policy and report usable inventory K-Ecut, terminal inventory and joint policy differences without attributing them to numerical error. Use this evidence to decide whether an additive variable-temperature TES/HP interface is justified. Primary equipment calibration, auxiliaries and measured physical validation remain open.
