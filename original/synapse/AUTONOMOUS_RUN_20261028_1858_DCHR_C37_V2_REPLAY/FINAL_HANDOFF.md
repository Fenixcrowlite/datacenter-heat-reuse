# DCHR C37 — Warm45_Storage100 v2 hourly Python replay
Verified local: 2026-10-28T18:57:52+01:00

Recovered source equations and reconstructed an isolated 8760-hour v2 Warm45_Storage100 CSV.
Validation: 192720 hourly comparisons to Liquid35 v2 MATLAB CSV, max abs error 8.53e-14.
Independent QA: 8760/8760 Decimal storage balances, 6 annual sums PASS.
Warm45 v2 gas: 10542.548227789 MWh; HP electricity: 7969.875645450 MWh.
Warm45 v2 minus v1 gas: 129.132288720 MWh; architecture differs, not measured savings.
Original OneDrive CSV/MATLAB/SLX unchanged. No MATLAB run; no Stateflow/physical parity.
No new Codex/GPU worker, no VRS, OAuth or shared GUI modifications.
Existing task scc-2aab24704c2bd0 evidence event #1397; task remains queued, no worker.
Card: https://desktop-m9l3i4m.taila1c6bd.ts.net/?synapse_task=scc-2aab24704c2bd0
Artifact: C:\Users\Lysda\Desktop\SynapseControlCenter\recovery\AUTONOMOUS_RUN_20261028_1858_DCHR_C37_V2_REPLAY
CSV SHA256: bbe8f22ff33fce9b77450967ecd8f8e59a7950ce78c6f16fcec3f2b098b4dbb9
SHA256 manifest: 960dcdf68b4c79835fac115a81f8c3a1d3d5e5063f0c2957eb0793e66e265007
SHA256 evidence: 90de0204e39bc59690b097d6936e940b702951bfb66e05096316c274b61cbeb0
Primary source signoffs 0/31. Next: Run a native MATLAB v2 Warm45_Storage100 export to a new isolated CSV, compare 8760 rows against C37 replay, then establish same-boundary Stateflow v85 10 MWh and stratified-tank parity. Do not overwrite original results.
