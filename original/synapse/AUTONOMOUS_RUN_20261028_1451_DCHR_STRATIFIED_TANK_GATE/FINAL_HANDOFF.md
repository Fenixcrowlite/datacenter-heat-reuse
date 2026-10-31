# DCHR stratified tank dynamic energy gate | 2026-10-28T14:56:24+01:00

VERIFIED isolated 8-layer / 8-substep per hour stratified water-tank counterfactual on 8760 SYNTHETIC hours, 3 repeated years.
Source SHA256 8125719923bae97901f37cf0f5354df77b46544df0477f863172255748873f25. Existing Simulink 100 MWh baseline not modified.
Five cases: 10,000 and 305,485.8 m3, 72/80 C, U=0.15 W/m2/K assumed cylinder h=10m, plus lossless 10,000 m3 control.
Year3 delivered MWh / extra electric MWh: 10000m3@72C=341.037/226.472, 10000m3@80C=437.112/331.553, 305485.8m3@72C=3460.154/3413.141, 305485.8m3@80C=3004.792/3413.141, 10000m3@80C=456.073/234.1
QA 21/21 unit PASS; independent 15/15 annual energy ledgers, 15/15 electric splits, 5/5 UA geometry, 5/5 profile energy PASS.
Existing Synapse task scc-2aab24704c2bd0; evidence event #1390; task remains queued, no worker created.
Card: https://desktop-m9l3i4m.taila1c6bd.ts.net/?synapse_task=scc-2aab24704c2bd0
Artifact: C:\Users\Lysda\Desktop\SynapseControlCenter\recovery\AUTONOMOUS_RUN_20261028_1451_DCHR_STRATIFIED_TANK_GATE
SHA256 manifest: 06d4c713b51e32db06543cb8f5c74dd754688cf943aec8b404458ba0fd113ef5
SHA256 evidence: 845fdcec8f02c395156cf575618ca4f6e28edf372ac26fceaa95dd22beb030e3
Live intake 2026-10-28 14:51 CET: primary SynapseMCP Web ping OK, RAM free 2.23 GiB, GPU 1282/8188 MiB 0%, STOP/PAUSE not found in inspected roots, existing Jarvice and Codex worktrees observed and untouched.
No new Codex, GPU jobs, workers, VRS, OAuth, GUI, purchases or production source edits.
LIMITATIONS: synthetic data; assumed U/UA, mixing, return 35 C, COP derating and 10 m geometry; not incremental gas savings; no validated equipment, no MATLAB integration, 0/31 primary source signoffs.
NEXT: Compare against existing 100 MWh Simulink dispatch boundary in isolated MATLAB test; validate UA/COP/return temperature, equipment, tariffs and 31 primary sources.
