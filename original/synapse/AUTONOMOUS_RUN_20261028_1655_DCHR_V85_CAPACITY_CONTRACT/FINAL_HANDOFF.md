# DCHR C34 saved v85 storage contract | 2026-10-28T16:55:50+01:00

VERIFIED: actual saved v85 model hash 2a9de22c0c55e8c4a87f7b0e0cfe9cd97db08c991f09d98361b009de310adde7.
The 27 archived v85 cases all specify C=0.2 MWh/K, Tmin=20C, Tmax=70C, so Emax=10 MWh.
Source electrical_policy_v85.m and earliest_dispatch_kernel_v75.m implement Emax=C*(Tmax-Tmin).
CRITICAL CORRECTION: prior C33 synthetic 100 MWh baseline is NOT equivalent to these v85 10 MWh test cases.
No assertion about all possible v85 configurations or actual real-world tank volume.
Independent QA 166/166 PASS; model ZIP integrity, Decimal cases, source SHA, negative controls.
No MATLAB execution; no changes to OneDrive, Simulink model, shared GUI, OAuth, VRS or other branches.
Existing Synapse task scc-2aab24704c2bd0 evidence event #1394; task remains queued, no worker.
Card: https://desktop-m9l3i4m.taila1c6bd.ts.net/?synapse_task=scc-2aab24704c2bd0
Artifact: C:\Users\Lysda\Desktop\SynapseControlCenter\recovery\AUTONOMOUS_RUN_20261028_1655_DCHR_V85_CAPACITY_CONTRACT
SHA256 manifest: c59c17e3b6d1b0de5bd56adb65a33ec99da82203496febf85d5776ed8a03c22b
SHA256 evidence: a3ceb1d5e6842846261a7c86091f9d329b78b216ba33d5de847591087539385c
Primary source signoffs: 0/31. Dynamic model parity: NOT VERIFIED.
NEXT: Locate the real 100 MWh baseline model/dataset and inspect its SOC and temperature definition; then compare C31 and the actual baseline at identical boundaries. Do not conflate the v85 10 MWh test cases.
