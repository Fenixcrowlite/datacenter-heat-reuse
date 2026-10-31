# v49 actual annual Stateflow handoff

2026-10-10T22:48:55.585281+00:00. Scoped annual saved-v42 execution PASS; model release remains0.42. No new SLX.

MATLAB61/0; independent258635/0; five separate reviewer self-checks. Annual8760 intervals/18495 positive segments/11434 thermal transitions; modes2–5 in annual, all six in fixtures. 8760 native rows explicitly rejected; 8760 fixed85C rows admitted. Paired policy increases unmet by368.568840 MWh, a joint cutoff/dwell/storage effect.

Evidence: STATUS_v49.json; audit/Annual_stateflow_derivation_v49.md; audit/Annual_stateflow_results_v49.md; results/annual_stateflow_v49_20261010T224401_242369Z; results/annual_stateflow_v49_20261010T224401_242369Z/independent_QA_v49_20261010T224734_985106Z.json.

Next actionable task: Execute a matched annual sensitivity matrix on saved v42 at fixed 85C condenser/source/load and identical initial inventory. Vary delivery cutoff, resolved restart band and ON/OFF dwell separately; retain runtime domain/event-budget failures and independently verify actual ports, dwell, inventory and energy reports. Compare each with the paired v48 loss-first policy and report usable inventory K-Ecut, terminal inventory and joint policy differences without attributing them to numerical error. Use this evidence to decide whether an additive variable-temperature TES/HP interface is justified. Primary equipment calibration, auxiliaries and measured physical validation remain open.

Run complete; stop with this handoff.
