# DCHR C33 100MWh temperature gate | 2026-10-28T16:00:15+01:00

VERIFIED independent thermodynamic reinterpretation of 100MWh rating using unchanged C31 synthetic 8-layer model.
Max synthetic DH supply 61.95185C; HX approach 3K; reference gate 64.95185C.
For 72C: 100MWh nominal 35C return requires 2327.69m3; gate requires 12219.43m3.
For 80C: nominal 1913.88m3; gate 5723.25m3.
Year3 delivered heat (MWh) for four cases: 79.63, 416.99, 83.97, 251.18. Not incremental savings.
Independent QA 28/28 PASS, Decimal/UA/energy residual/SHA. 8760 SYNTHETIC hours, three repeated years.
Existing task scc-2aab24704c2bd0 event #1393; no new task/worker.
Card: https://desktop-m9l3i4m.taila1c6bd.ts.net/?synapse_task=scc-2aab24704c2bd0
Artifact: C:\Users\Lysda\Desktop\SynapseControlCenter\recovery\AUTONOMOUS_RUN_20261028_1601_DCHR_100MWH_TEMP_GATE
SHA256 manifest: 1f3fec112c28d9ad9bb2550c391a235f5b1746978181394fe71efcd03cde84cc
SHA256 evidence: e51448be8c8abbc81b4e23c103c966c30d713cbb93922ec0edda179e49aa56fc
No Codex, GPU jobs, workers, VRS, OAuth, GUI, shared Simulink source or production edits.
LIMITATIONS: existing Simulink 100MWh rating not yet matched dynamically, no metered validation, 0/31 source signoffs.
NEXT: Inspect the actual 100 MWh Simulink state/dispatch/temperature definition, then compare identical boundary conditions; validate OEM COP/UA and primary sources.
