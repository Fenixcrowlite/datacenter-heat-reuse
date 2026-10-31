# v39 saved-v38 HP defect checkpoint

UTC 2026-10-10T12:36:56.411250+00:00. DEFECT_REPRODUCED_OPEN. No new SLX.

Executed 22 scenarios / 45 intervals / six modes;
MATLAB 122/122 execution checks PASS and 78 HP probes.
Independent evidence QA 4040/4040 PASS; synthetic 3/3 PASS.
Analytic implementation comparisons 202 PASS / 234 FAIL.
Fixed 80-step search falsely returns OFF or nonmaximal output at extreme
request/source ratios; same-source tight-request controls serve demand.
No physical validation or article replication; prior models/evidence preserved.

Evidence: STATUS_stateflow_v39.json; audit/HP_dynamic_range_derivation_v39.md;
audit/HP_dynamic_range_results_v39.md; results\stateflow_hp_domain_v39_20261010T123256940Z\independent_QA_v39_20261010T123637_591117Z.json.

Next: Implement additive Stateflow v40 with a source-relative bracket or stable scaled HP root, explicit unsupported-resolution rejection, and source-limited request invariance. Execute v39 dynamic-range/cutoff counterexamples plus all six modes and prior v38 representative references; independently verify analytic maximal output, nonzero electricity, SOC/port limits and first-law closure. Preserve v38 and all v39 evidence. Do not broaden clock seed/bound/event-order acceptance or claim equipment calibration; those audits and primary parameter traceability remain open.
