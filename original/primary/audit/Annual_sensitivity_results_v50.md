# Annual sensitivity and padding defect — v50

2026-10-10T23:05:51.924740+00:00. **Defect CONFIRMED OPEN; no corrected model accepted.**

Actual saved-v42 matrix:9 attempted years,7 complete,2 reject. Harness60PASS/2FAIL and matrix batch exit1. Successful controls total61320 intervals/125776 positive segments. Independent evidence/equation QA 1773125PASS/0FAIL with 6 separate mutations; that QA acceptance confirms the defect record and passing controls, not a repaired controller.

| Policy | Annual execution | Unmet MWh | Delta vs baseline MWh | Usable MWh | Terminal MWh |
|---|---|---:|---:|---:|---:|
| baseline | Complete | 2851.571488 | +0.000000 | 3.846154 | 46.122381 |
| cutoff_81 | Complete | 2874.801394 | +23.229906 | 3.076923 | 46.891083 |
| cutoff_82 | Complete | 2901.242883 | +49.671395 | 2.307692 | 47.659786 |
| restart_47 | Complete | 2895.632761 | +44.061273 | 3.846154 | 46.122381 |
| restart_49 | REJECTED at interval 2897 | — | — | — | — |
| on_0 | Complete | 2851.571488 | +0.000000 | 3.846154 | 46.122381 |
| on_05 | REJECTED at interval 2416 | — | — | — | — |
| off_0 | Complete | 2851.571488 | +0.000000 | 3.846154 | 46.122381 |
| off_05 | Complete | 2875.650633 | +24.079145 | 3.846154 | 46.122381 |

Cutoff81C adds23.229906MWh unmet and cutoff82C adds49.671395MWh relative to baseline. Restart47MWh adds44.061273MWh; OFF dwell0.5h adds24.079145MWh. ON dwell0 and OFF dwell0 reproduce baseline annual integrated results on this profile. These are measured synthetic model effects conditional on the baseline, not physical/equipment benefits. Restart49 and ON0.5h have no accepted annual quantities. Their missing rows must not be interpolated or credited.

Both failed configurations pass every static input row. Restart49 stops after2896 committed samples (first rejected interval2897); ON0.5h stops after2415 (first rejected interval2416). Two exact original-MAT-seeded one-interval simulations reproduce the actual runtime rejection. Binary padding witnesses show start4049000000000001, capacity/end4049000000000000 and residual7.1054273576010019e-15MWh. All heat powers/losses/delivery are zero; unconditional allocation clipping changes padding energy by one ULP. The combined runtime message “Zero-span segment has service.” identifies the zero-span identity predicate, not actual nonzero service.

Baseline reproduces preserved v49; original SimulationOutputs and MAT reports reopened. Seven complete trajectories independently pass every segment HP quadratic, ODE, port/mode/cutoff/capacity/clock/dwell check and annual energy/equal-delivered-service report. Maximum independent macro first-law residual1.4962e-13MWh. Fresh paired v48 annual reports and deltas are independently recomputed; differences remain joint policies, not integration error. Terminal inventory is unpriced.

Initial full-success reviewer/finalizer/checker drafts remain preserved and unused. A separate scoped defect reviewer retains the numerical equations and changes only execution/scope/receipt handling. No production controller, monitor, numeric artifact or failed evidence was changed to obtain QA. No successful nine-year release is claimed.

First scoped review produced152 dwell flags from15-digit CSV physical spans. Original-MAT binary spans/clocks were reopened and independently decoded. All152 flags resolve with exact nonnegative lower-age margins (minimum1.08420217248550443400745280086994171142578E-19h); maximum CSV age discrepancy5.138777878078144567552953959E-16h. The final reviewer uses exact binary physical spans for dwell and binds each to its original CSV. No dwell guard or proof criterion was relaxed. First failed QA/source/log are retained; targeted resolution: results/annual_sensitivity_v50_20261010T225436_641700Z/dwell_serialization_resolution_v50_20261010T230502_129033Z.json.

Evidence: results/annual_sensitivity_v50_20261010T225436_641700Z; results/annual_sensitivity_v50_20261010T225436_641700Z/independent_QA_v50_20261010T230421_605866Z.json; spec/source snapshots; nine preflight/adapter MATs; original annual SimulationOutputs;7 complete dispatch/segment/clock/port traces; failed-prefix MAT reopen; exact binary witnesses and2 isolated replay SimulationOutputs; timestamped logs/receipts. 1716 prior artifacts and accepted SLX hash/CRC unchanged. See audit/Annual_padding_defect_derivation_v50.md for mathematical identity/counterexamples and repair handoff.

Limitations:

- Nine annual scenarios attempted; seven complete and two reject. Harness60PASS/2FAIL. This is an OPEN saved-model padding defect checkpoint with scoped passing controls, not a complete sensitivity release or a repaired-controller acceptance.
- Accepted saved model remains0.42 and its SLX hash is unchanged. No new SLX/controller/component changes. Prior v42/v49 acceptance remains limited to tested policies.
- Failed prefixes2896 and2415 samples are preserved but not treated as completed annual reports. First failing intervals are separately reconstructed and replayed in the actual saved model; isolated binary witnesses are distinct from committed prefix traces.
- Zero-span failure is a one-ULP inventory/residual identity mismatch from clipping, with zero physical service. It is not evidence of material energy loss or invalid primary physics. Broader roundoff/event origins require the corrective audit.
- Seven passing annual policies share synthetic fixed85C condenser/tank,20C ambient, identical deterministic source/load, zero initial inventory and initial HP ON at zero age. One coordinate varies per policy; interactions/alternate inputs/calibration/economic optimality are untested.
- Annual mode coverage is recorded for completed scenarios. All-six-mode acceptance is inherited from preserved v42/v49 fixtures; no six-mode annual coverage or fresh six-mode fixture execution is claimed here.
- Matched paired v48 is recomputed MATLAB loss-first dispatch with same source/load/lift and different cutoff/latch/active-port integration. Deltas against it remain joint policy effects, not numerical error.
- Independent QA uses same-agent Decimal closed-form HP/ODE and physical-time sums plus exact binary decoding. It is not independent personnel, universal floating-point proof, measured physical validation or primary-paper replication.
- Physical segments execute through64 bounded intra-macro slots, not solver-clock events; normal-mode planner uses host MATLAB. Standalone generated-code deployment and alternate extreme numerical domains are untested.
- Usable inventory is K-Ecut; terminal inventory is reported and unpriced. Auxiliary electricity/pumping/HX finite approach/network transients/CAPEX/equipment maps and primary calibration remain unspecified. Full primary signoffs0/31.
- Native seasonal condenser/fixed-tank envelope remains unsupported. Fixed85C zero tank approach is synthetic reduced-model policy, not finite-HX validation.
- Initial sandbox MATLAB startup exit1 is retained; local matrix run exits1 because of the two actual defects. Reopening/inspection and isolated-replay batches exit0 while correctly observing those failures. Inherited Stateflow shadow warnings remain.
- Initial independent CSV-only review had152 dwell flags. Exact binary spans/clocks reopened from original MATs resolve all152 with strictly nonnegative lower-age margins; no guard/time tolerance was relaxed. Failed QA/source/log and targeted152/0 serialization-resolution evidence remain preserved.

Next actionable task: Derive and implement an additive v51 Stateflow padding repair with a consistent canonical physical end state across planner/allocation, zero-duration slots and macro inventory memory. Preserve saved v42 and all v50 evidence. Keep zero-span identity/first-law assertions strict; do not weaken the guard or count padding as physical loss. Audit the one-ULP overshoot source, capacity/cutoff roundoff and clock/latch handoffs. Reproduce and repair exact MAT-seeded restart49 interval2897 and ON0.5h interval2416, then rerun all nine matched annual policies and required six-mode executable acceptance with independent binary/ODE/port/dwell/report QA. Only accept a new versioned SLX after every required test passes. Defer variable-temperature interface work until this concrete execution blocker is resolved; primary equipment calibration/auxiliaries/physical validation remain open.
