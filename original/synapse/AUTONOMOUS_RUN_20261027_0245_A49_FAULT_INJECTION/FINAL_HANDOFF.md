# A49 synthetic fault-injection checkpoint | 2026-10-27
Existing Synapse task: scc-3d9d172beb6e1b, status review/planned, no live worker asserted.
QA: 9/9 unittest PASS; 7 baseline cases x 672 steps; 24 deterministic randomized demand/latency/HP trials x 160 steps; 5 deliberate corruption probes detected; 9 zero-capacity trip-delay cases checked.
Independent trace ledger: IT, HP, user, TES, temperature, sensor lag, REJECT ramp and compressor lag.
Full zero-capacity fault: trip indices 96,98,100 for synthetic delays 0,2,4 samples, independent of sensor lag 0,1,4 samples.
Important: A49 Python-only. No new MATLAB/Simulink run or real equipment testing; physical validation and 31 primary-source signoffs remain BLOCKED.
Source SHA256: 95b579b23571a41ff5efb86d2b3b28abebc97837a4b4b0c32f96b9756692ef6f
Result SHA256: f05d42aeb61722ae7c5d432b667eda69d64578a870e3ae48183806674955ccea
Evidence SHA256: a70bc02b05516ceebfb2e2584202e72d58fab9469822db29d87596218b2cf406
Manifest SHA256: 7e3c141e5e0060116a52c3b02b1343060467248f421fb60c22947e06ef01a62c
Unmodified A48 model SHA256: 063f9afb5816cd4f6bed415256293eee67b328718b141c29d84853ddafab25cb
No Codex, new worker, GPU job, GUI/OAuth/STOP change, VRS, or external side effects.
Next: A50: run selected sensor-lag and trip-delay fault injections against graphical A48 Stateflow in MATLAB, compare with independent A49 trace ledger; retain 31-source physical signoff gate.
