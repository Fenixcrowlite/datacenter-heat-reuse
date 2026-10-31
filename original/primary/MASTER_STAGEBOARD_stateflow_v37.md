# v37 saved-Stateflow numerical-domain defect checkpoint

UTC 2026-10-10T08:01:23.118491+00:00. Defect reproduction PASS; repair OPEN.

Saved v36: 24 scenarios, 19 complete, 5 runtime rejections, 3382 completed intervals; four HP component probes. Six baseline modes pass. MATLAB harness 3/3; independent QA 15924/15924; 6730 equation checks; prior immutable entries 1781 preserved. No new SLX.

Clock cumulative bias 1.6809289550781246e-8 h; bands <=64 energy ulps fail progress; subnormal host HP slope yields Inf COP, rejected by runtime gate. These are numerical stress defects; no early clean dwell or physical validation claim.

Evidence: STATUS_stateflow_v37.json; audit/TES_resolution_results_v37.md; audit/TES_resolution_derivation_v37.md.

Next: Implement additive saved Stateflow v38: reject unresolved capacity/restart/cutoff bands before planning; replace overflow-prone HP slope arithmetic with a finite normalized-load component; implement compensated persistent physical-hour clocks with declared cumulative accuracy and reset/guard semantics. Execute six modes, v36 changing-input references, preserved v37 stress/counterexamples, clock partitions, cutoff overlap and source/request-limited HP cases; independently export MAT and compare exact-input Decimal clocks and normalized/analytic HP laws. Preserve every prior model/evidence; do not claim physical calibration.
