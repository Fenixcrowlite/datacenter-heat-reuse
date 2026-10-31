# v43 primary heat-pump traceability checkpoint

2026-10-10T13:19:12.453065+00:00. PASS_SCOPED_EQUATION_TRACEABILITY_AUDIT; calibration blocker OPEN.
Actual saved model remains0.42; no new SLX. Four new focused saved-model cases,
324 synthetic vectors/972 HP calls; MATLAB1638/0,
independent actual6389/0, separate reviewer self-checks3/0.
Local source20 p8 Eqs4-7 and p10 verified visually. Cooling EERII cannot be
copied into heating h(2); refrigerant saturation and reservoir-proxy boundaries
differ. Full primary signoffs0/31; physical validation/article replication untested.

Evidence: STATUS_v43.json; audit/HP_primary_boundary_derivation_v43.md;
audit/HP_primary_boundary_results_v43.md; audit/literature_traceability_v43.csv;
results/hp_traceability_v43_20261010T131612_418934Z/independent_QA_v43_20261010T131754_326049Z.json.

Next actionable task: Acquire and audit source20 upstream reference [62] (Rocchetti and Socci, TSEP 2025, 61, 103513; DOI 10.1016/j.tsep.2025.103513) and its performance-correlation supplement, then public CoolSelector [61] equipment data when accessible. Verify exact coefficients, both refrigerant-temperature axes, compressor versus auxiliary power, units and admissible operating range. If no complete map is public, record the specific access/data blocker. Do not calibrate heating h(2) from the article cooling EERII, adopt a lift-only polynomial, or replace the accepted v42 assumptions without new evidence. Design a separate refrigerant-temperature/cooling-efficiency backend only after evidence supports it; preserve v42 and all v43 diagnostics.
Stop after this coherent task and handoff; do not repeat regression absent a change.
