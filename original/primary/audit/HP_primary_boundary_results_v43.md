# v43 primary heat-pump boundary results

UTC 2026-10-10T13:19:12.453065+00:00. PASS scoped equation/traceability audit; scientific calibration blocker OPEN.
Production remains saved Stateflow 0.42. No new SLX or corrected plant acceptance.

Verified existing local primary PDF: source20, DOI10.3390/en19030800,
SHA256 `713d1ea564efacbb8813eafc474482292b167140e1b2f47d1e234d3db7302a6e`. Exact locators, definitions, dimensions,
independent conversion and code mapping: `audit/HP_primary_boundary_derivation_v43.md`.
Rendered p8/10/23/27 were visually checked; extracted p1/6/8/9/10/23/27 retained.
Newest publisher PDF identity remains unverified; direct HTML returned429.
Indexed publisher text is corroboration, not the primary verification basis.

MATLAB R2026a Update5 executed 324 synthetic vectors / 972 component calls,
then four new focused scenarios in the actual saved v42 model. Harness:
1638 PASS / 0 FAIL. Separate MATLAB batch reopened saved
MAT files and exported every compared numeric matrix/trace. Independent
80-digit Decimal quadratic roots, exact Fraction identities, dimensional checks,
MAT equivalence, receipts, source snapshots and prior-evidence hashes:
6389 PASS / 0 FAIL. Separate reviewer self-checks:
3 PASS / 0 FAIL.
177 prior sealed/source entries retain their hashes/sizes.
Evidence: `results/hp_traceability_v43_20261010T131612_418934Z`; QA: `results/hp_traceability_v43_20261010T131612_418934Z/independent_QA_v43_20261010T131754_326049Z.json`.

Direct factor substitution misses heating COP by 1-etaC: observed gaps
0.45 to 0.55.
Holding converted etaH fixed but substituting external reservoir proxies with
nonzero symmetric pinch increases COP by 0.298381017
to 4.93621157 in these engineering sweep fixtures.
This is a conditional boundary comparison, not a universal equipment error estimate.

Focused fixture: external source35C / sink75C, assumed symmetric pinch5K
giving refrigerant30C / 80C, etaC0.5, source0.5MW, demand0.68MW,
TES at cutoff5MWh, no TES port transfer or boiler, one 1h macro interval.

| Synthetic saved-v42 case | COP | Heat MW | Compressor MW | Source MW | Unmet MW | Mode |
|---|---:|---:|---:|---:|---:|---|
| same_factor_refrigerant | 3.5315 | 0.68 | 0.192552739629 | 0.487447260371 | 0 | HEAT_RECOVERY |
| converted_refrigerant | 4.0315 | 0.664934850734 | 0.164934850734 | 0.5 | 0.015065149266 | UNMET_DEMAND |
| converted_water_proxy | 4.96802607 | 0.626007236674 | 0.126007236674 | 0.5 | 0.0539927633257 | UNMET_DEMAND |
| converted_with_assumed_partload | 3.71117314 | 0.68 | 0.18323047055 | 0.49676952945 | 0 | HEAT_RECOVERY |


The factor conversion alone changes demand-met to about15.065kW unmet.
A lower COP admits more condenser heat for a fixed source budget by drawing
more electricity. The assumed part-load penalty reverses the service result
in this fixture, further demonstrating why energy balance alone cannot calibrate
performance. All four TES endpoints remain5MWh; maximum saved model integrated
first-law residual 8.881784197001252e-16MWh. These are executed synthetic comparisons,
not Varna performance predictions, paper replication or measured validation.

The initial sandbox startup failure and first harness run are retained in
timestamped logs/receipts and the earlier v43 result folder. All four initial
simulations ran, but eight harness checks addressed wrong trace columns; corrected
assertions use first-law column13, HP columns19-21 and COP column23. A new result
directory was used for the successful run. Inherited data-shadow warnings retained.
No production code/model/data was overwritten; no settings/scheduler/agent runner,
Jarvice/unrelated files, secrets or external publication touched.

Independent QA uses distinct algorithms in the same agent, not independent personnel.
Full source signoffs0/31, upstream61/62/64 and actual performance maps remain open.
New additive ledger `audit/literature_traceability_v43.csv` changes only source20's
partial review/blocker text. Read STATUS_v43.json and MASTER_STAGEBOARD_v43.md
alongside inherited STATUS_stateflow_v42.json before the next task.

Next actionable task: Acquire and audit source20 upstream reference [62] (Rocchetti and Socci, TSEP 2025, 61, 103513; DOI 10.1016/j.tsep.2025.103513) and its performance-correlation supplement, then public CoolSelector [61] equipment data when accessible. Verify exact coefficients, both refrigerant-temperature axes, compressor versus auxiliary power, units and admissible operating range. If no complete map is public, record the specific access/data blocker. Do not calibrate heating h(2) from the article cooling EERII, adopt a lift-only polynomial, or replace the accepted v42 assumptions without new evidence. Design a separate refrigerant-temperature/cooling-efficiency backend only after evidence supports it; preserve v42 and all v43 diagnostics.
