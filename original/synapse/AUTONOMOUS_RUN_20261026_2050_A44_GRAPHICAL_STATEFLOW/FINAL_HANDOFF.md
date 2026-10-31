# A44 verified handoff | DESKTOP-M9L3I4M

A44 graphical Stateflow.Chart: 4 states, 7 transitions, isolated Simulink model.
MATLAB R2026a four scenarios x 672 intervals: 5376/5376 output comparisons PASS.
Python regression: 8/8 PASS. ZIP Stateflow chart and CRC independently checked.
First MATLAB run failed due to From Workspace extrapolation; fixed in owned script.
Synthetic, supervisor-only, not A43 closed-loop integration, no compressor lag or hardware I/O.

Model: C:\Users\Lysda\Desktop\SynapseControlCenter\recovery\AUTONOMOUS_RUN_20261026_2050_A44_GRAPHICAL_STATEFLOW\DCHR_A44_Graphical_Supervisor.slx
Model SHA256: c55dc5a1d4311104e675aebd6045e19883f95f27ea33db42d155edbdffe12307
Evidence SHA256: 198d024e2ecc3301e79732ceb2b65c8d89d55975ec32b5dafe97aa585eb09c21
Manifest SHA256: 89ea0096552e83fdb376c2850289a97a2c41eaf52ca55847e5f40d3cbf9b2977
Synapse existing task: scc-3d9d172beb6e1b, event 1243 (CREATED_EVENT)
Card: https://desktop-m9l3i4m.taila1c6bd.ts.net/?synapse_task=scc-3d9d172beb6e1b
STOP exact flags absent in checked scopes during registration.
No new Codex/GPU worker or card; VRS excluded; shared GUI and production unchanged.
Next step: A45 connect graphical chart to A43 closed-loop thermal system; implement HP compressor startup lag with energy balances; rerun 7x672, independent QA
