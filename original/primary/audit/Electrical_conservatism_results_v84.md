# Saved-Stateflow electrical conservatism experiment v84

UTC 2026-10-13T10:57:16.506408+00:00.

Preserved saved v83r2 actually executes 19 complete schedules / 56 held intervals / 67 positive segments / 11 interior events, with all six required modes. MATLAB 79 PASS / 0 FAIL; independent equation/artifact QA 12063 PASS / 0 FAIL; 3 separate reviewer corruptions detected. One fresh nonbinding saved-v80 reference comparison and clean saved-v83r2 reopening are bitwise equal.

The global maximum-temperature electrical cap is safe but leaves useful capacity unused on every one of twelve tested service/charging histories. A new independently derived temperature-conditioned comparator quantifies the gap on identical raw policies, initial conditions and four 0.25-hour inputs. It is a hypothetical reduced-model calculation, not a saved Stateflow dynamic controller. No hull midpoint is used: actual totals are reconstructed from original-MAT binary exports and checked against reporting hulls.

| Case | Global HP heat (MWh) | Conditioned HP heat (MWh) | Additional recovered source (MWh) | Additional delivered service (MWh) | Additional final TES (MWh) | Heat increase (%) |
|---|---:|---:|---:|---:|---:|---:|
| service_E3.0_a1.0 | 0.2216761364 | 0.4475657895 | 0.2006542957 | 0.2258896531 | 0 | 101.9007534 |
| service_E3.0_a10.0 | 0.1682056452 | 0.2480743243 | 0.06377094729 | 0.07986867916 | 0 | 47.48275784 |
| service_E4.95_a1.0 | 0.2216761364 | 0.4475657895 | 0.2006542957 | 0.2258896531 | 0 | 101.9007534 |
| service_E4.95_a10.0 | 0.1682056452 | 0.2480743243 | 0.06377094729 | 0.07986867916 | 0 | 47.48275784 |
| service_E8.5_a1.0 | 0.2216761364 | 0.2569520548 | 0.0284116187 | 0.03527591843 | 0 | 15.91326834 |
| service_E8.5_a10.0 | 0.1682056452 | 0.1844724771 | 0.01185781866 | 0.0162668319 | 0 | 9.67080022 |
| charge_E3.0_a1.0 | 0.2216761364 | 0.4475657895 | 0.2006542957 | 0 | 0.2033006878 | 101.9007534 |
| charge_E3.0_a10.0 | 0.1682056452 | 0.2480743243 | 0.06377094729 | 0 | 0.07188181125 | 47.48275784 |
| charge_E4.95_a1.0 | 0.2216761364 | 0.4327021812 | 0.1861140359 | 0 | 0.1899234404 | 95.19565268 |
| charge_E4.95_a10.0 | 0.1682056452 | 0.2463130016 | 0.0621335841 | 0 | 0.07029662083 | 46.43563324 |
| charge_E8.5_a1.0 | 0.2216761364 | 0.2537676976 | 0.02570033293 | 0 | 0.02888240508 | 14.47677758 |
| charge_E8.5_a10.0 | 0.1682056452 | 0.1834623063 | 0.01107785522 | 0 | 0.013730995 | 9.070243211 |

For service-only cold E=3 MWh and approaches 1/1 K, delivered service rises from 0.2216761364 to 0.4475657895 MWh in one hour. The extra heat is supported by both more recovered source and more compressor work. At hot E=8.5 MWh the gap is smaller. Charging near the hot-water floor at E=4.95 MWh crosses that floor on both compared paths; the nonlinear comparator uses a separated logarithmic solution and explicit crossing time, independently checked by RK4 at 1024/2048 steps. The dynamic endpoint stays strictly below the stop threshold in every comparator case.

Model `matlab/simulink/DCHR_Electrical_Dispatch_Stateflow_v83r2.slx`, SHA256 `6c3923c30e7058ec07e8d6f1667a5b9aae4db012775cba52bb0fb8d9cd98e1dd`. No production model or prior checkpoint changed. Evidence `results/electrical_conservatism_v84_20261013T105537_783028Z` contains timestamped MATLAB/Simulink and Python logs, execution receipt, 19 individual original MAT files and a reopened aggregate MAT, binary exports, comparison/trajectory CSV, predeclared specification, source snapshots and preservation hashes. Derivation: `audit/Electrical_conservatism_derivation_v84.md`. Prior failed scope attempts: `results/electrical_conservatism_v84_20261013T105044_893030Z` and `results/electrical_conservatism_v84_20261013T105247_497281Z`.

Limitations:

- Checkpoint 0.84 is a fresh saved-v83r2 experiment and independent hypothetical comparator; no new SLX or dynamic-cap Stateflow implementation is accepted.
- Twelve comparison histories are zero-loss, HP initially ON, service-only or charge-only, with disabled boiler/TES discharge and no stop/restart on the dynamic paths. Six modes and an interior event control execute separately.
- Dynamic heat/source gains use increased compressor work. Service-only gains are delivered service; charging gains are stored inventory, never delivered district heat or equal-electricity savings.
- Reduced constant cooling-factor/refrigerant proxy equations, approach values, storage efficiencies and 0.05 MW compressor ratings are synthetic engineering assumptions. No new primary text/signoff or commercial supplement was acquired; full signoffs remain 0/31.
- Same-agent algorithmic independence: Fraction/binary inputs and 120/160-digit closed equations call no production MATLAB solver; a separate RK4 integrates the comparator ODE. MATLAB reopens MAT for binary export; no independent personnel or independent MAT parser claim.
- Independent comparator budgets are 1e-100 precision agreement, 1e-110 primitive residual and 1e-10 MWh RK4 endpoint agreement, not relaxed production guards or measured accuracy.
- No positive-loss dynamic comparator, mixed service/charge optimization, source-map calibration, annual performance, article replication, measured physical validation or generated-code acceptance.
- Inherited saved-model span, clock, segment-count and event-collision domains remain. Its protocol ticks are not solver-clock event times.
- Initial restricted MATLAB startup failed. Two complete candidates each passed MATLAB 79/79 and 11008 independent checks but failed the interior-event coverage gate at 0.2/0.5 MW. Both attempts and original snapshots are preserved; only the corrected 1000 MW nonbinding event-fixture batch and QA count as checkpoint acceptance.

Next actionable task: Derive and independently verify a temperature-conditioned ON charging backend with positive passive loss, hot-water floor crossing and TES stop events before integration into an additive six-mode Stateflow model. The affine held-power kernel cannot accept a start-temperature electrical cap safely while charging. Choose a certified whole-segment constant cap or a certified nonlinear flow/event solver explicitly, bind raw and effective policies with versioned trace/report provenance, and regress v84 histories plus zero/nonbinding ratings and stop/restart/dwell/refusal controls. Preserve v80-v84. Keep primary equipment supplement acquisition/calibration open; synthetic Pmax is not a commercial rating.

Stop after this coherent executed deliverable and clear handoff.
