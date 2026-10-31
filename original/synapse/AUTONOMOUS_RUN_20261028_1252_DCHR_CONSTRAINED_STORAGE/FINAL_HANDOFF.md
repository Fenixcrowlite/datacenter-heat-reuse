# DCHR constrained storage | 2026-10-28

VERIFIED isolated 8760-hour synthetic sensitivity, 8 electric/capacity scenarios + 5 temperature/loss scenarios. Source SHA256 8125719923bae97901f37cf0f5354df77b46544df0477f863172255748873f25; original CSV/Simulink/SCADA unchanged.
Reference 2500 MWh storage / 1.5 MW extra HP cap / 72 C / 0.025% hourly loss: theoretical year-3 gas heat coverage 1910.037 MWh; extra HP electricity 2399.183 MWh. NOT net gas savings; existing baseline already has 100 MWh storage.
QA: 20/20 unit PASS, 39 annual balances PASS, 26280 independent Decimal hour steps PASS; 0/31 primary-source signoffs.
Existing Synapse task scc-2aab24704c2bd0, evidence event #1388, status remains queued, no worker.
Card: https://desktop-m9l3i4m.taila1c6bd.ts.net/?synapse_task=scc-2aab24704c2bd0
Artifact: C:\Users\Lysda\Desktop\SynapseControlCenter\recovery\AUTONOMOUS_RUN_20261028_1252_DCHR_CONSTRAINED_STORAGE
SHA256 manifest: f7ceeea44367a539456f8429fcecf5854256db021c9f2c3b7b582016c6f2f15f
SHA256 evidence: 2373a6877a09c33fafcd3bbd0c7e93c08f97e6f401266f6d6f3f00500864841c
Live intake 2026-10-28 12:50-12:51 CET: SynapseMCP Web ping OK; RAM free 2.87 GiB; VRAM 1269/8188 MiB, GPU 2%; checked root STOP/PAUSE absent; Jarvice worktrees and existing processes observed, untouched.
No Codex sessions, new GPU workers, GUI/OAuth/secret edits, purchases, VRS or source-model modifications.
LIMITATIONS: uncalibrated COP inverse-lift model, assumed site/HP power caps, fixed storage temperature, no stratification, dispatch integration, tariffs or CAPEX. This is a counterfactual, not measured savings.
NEXT: Integrate storage dispatch with the original 100 MWh Simulink baseline, validate actual HP COP and electrical nameplate limits, temperature dynamics and hourly tariffs, then independently verify net economics.
