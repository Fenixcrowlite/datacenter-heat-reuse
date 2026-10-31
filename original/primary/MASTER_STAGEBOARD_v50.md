# v50 actual saved-Stateflow defect handoff

2026-10-10T23:05:51.924740+00:00. Padding identity defect CONFIRMED OPEN. Model remains0.42, no new SLX or repaired acceptance.

Nine annual variants attempted:7 complete/2 runtime reject; MATLAB60PASS/2FAIL. Independent scoped evidence QA1773125/0 with6 separate reviewer mutations. Two exact one-interval actual model replays reject; one-ULP clipping changes zero-span energy. Prior v49 baseline reproduces and model/evidence hashes are preserved.

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

Evidence: STATUS_v50.json; audit/Annual_padding_defect_derivation_v50.md; audit/Annual_sensitivity_results_v50.md; results/annual_sensitivity_v50_20261010T225436_641700Z; results/annual_sensitivity_v50_20261010T225436_641700Z/independent_QA_v50_20261010T230421_605866Z.json.

Next actionable task: Derive and implement an additive v51 Stateflow padding repair with a consistent canonical physical end state across planner/allocation, zero-duration slots and macro inventory memory. Preserve saved v42 and all v50 evidence. Keep zero-span identity/first-law assertions strict; do not weaken the guard or count padding as physical loss. Audit the one-ULP overshoot source, capacity/cutoff roundoff and clock/latch handoffs. Reproduce and repair exact MAT-seeded restart49 interval2897 and ON0.5h interval2416, then rerun all nine matched annual policies and required six-mode executable acceptance with independent binary/ODE/port/dwell/report QA. Only accept a new versioned SLX after every required test passes. Defer variable-temperature interface work until this concrete execution blocker is resolved; primary equipment calibration/auxiliaries/physical validation remain open.

Stop this coherent defect-audit run with handoff.
