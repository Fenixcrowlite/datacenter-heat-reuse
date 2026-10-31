# Independent v28 checkpoint review

UTC 2026-10-09T15:34:17.753381+00:00. PASS: 30/30 read-only review checks, including 25 in-memory corruption probes. The AST-isolated finalizer preflight stops before its first checkpoint write; no MATLAB or original finalizer main executed.

Fresh executed evidence records 1221 dispatch assertions, 105 experiment assertions, 46 runtime rejections, 19 scenarios/70 intervals and all six modes. Independent QA has 14575 actual evidence checks and 1039 separately classified synthetic self-tests. The 25 checkpoint corruption probes in this review are also synthetic and must not increase either executed count.

All 273 v27-manifest artifacts currently retain their recorded hashes. Saved v24 and v28 remain unchanged. Project model release 0.28 is distinct from saved Simulink ModelVersionFormat `%<AutoIncrement:1.1>`.

The root repaired provenance gaps found in review: current summary/domain/supplemental/generic-verifier hashes, per-experiment sample traces, assertion/source-snapshot hashes, reviewed-source/console hashes, exact acceptance marker and result-directory binding. Every corresponding tampering probe rejected.

Evidence: `audit/checkpoint_independent_review_v28_20261009T153417_753381Z.json`; reviewed finalizer SHA-256 `8f6afc75ceedd4e898ecfd375ddd03f3b8481e69882c0370586cec7946a5fca0`. Gate probes do not constitute physical validation or new MATLAB execution.
