# v38 executed Stateflow numerical-domain repair

UTC 2026-10-10T08:19:30.779040+00:00. PASS_SCOPED_IMPLEMENTATION, model release 0.38.

Actual new saved v38 executes 80 scenarios (69 complete, 11 intended domain
rejections), 3725 intervals, 3910 positive segments and all six modes.
MATLAB 2110/2110 PASS, 219 HP probes, 30 actual runtime fault rejections;
independent actual checks 128974/128974, synthetic reviewer checks 3/3,
zero failures. Ten fresh saved-v36 comparisons and independent references pass;
1792 prior immutable entries preserved.

v37 drift/band-progress/HP-slope defects repaired in tested fixtures. Clock
high error <=5.817381143570185e-11 h; retained expansion matches exact-input
Decimal clocks in the executed fixtures. Implementation QA only; no calibrated
physical validation or paper replication. Broader clock seed/event and HP
numerical domains retain explicit audit limits.

Evidence: STATUS_stateflow_v38.json; audit/TES_numerical_repair_derivation_v38.md;
audit/TES_numerical_repair_results_v38.md; results\stateflow_v38_20261010T081205294Z\independent_QA_v38_20261010T081552_920975Z.json.

Next: Audit the normalized HP solver near the COP cutoff and across extreme source/output ratios, and verify compensated-clock initial residual/bound and event-guard domains before broadening acceptance. Use independent analytic/exact-input counterexamples rather than repeating the current suite. Then return to primary heat-pump/equipment evidence and physical parameter traceability; no calibrated or article-derived control values are accepted yet. Preserve all prior models/evidence.
