# DataCenter v07 -> D ingestion -> Simulink v08 -> SCADA v09: independent lineage QA
2026-10-25, Europe/Bratislava. Scope: isolated A24 directory. Original OneDrive source files and running SCADA are READ-ONLY.

## Verified now
- Recovered actual generating source: `matlab/pool_measurement_v08/priprav_D_replay_v08.py` creates synthetic virtual-sensor D inputs from v07; `kontrola_vstupnych_merani_v07.py` normalizes numeric fields to **8 significant digits**; `spusti_merania_replay_v08_sk.m` feeds 23 channels into the v08 Simulink model and exports eight CSVs. No MATLAB execution was performed in this audit.
- Checked all **8 scenarios x 672 rows = 5,376 row-level provenance chains** from v07 CSV through raw D schema, operational controls, normalized D sensors and final v08 CSV.
- Checked exact SHA256 of all eight raw D sensor CSVs against both D_REPLAY_INPUT_MANIFEST.json and each staged validated_dataset_metadata.json; verified D source URIs, stage status, 900 s timebase and strict 8-significant-digit normalization.
- Compared 21 operational controls, 12 raw sensor fields, staged external sensors, and the v08 sensor/control mapping per row; independently checked v07-v08 temperature and heating regression limits and v08 summary energies. Original v85, v07, v08 model SHA256 all match independent QA manifest.
- Read-only GET to the **currently running** SCADA /api/scenarios: all **8/8 live source SHA256** exactly match the verified v08 CSVs. API declares D_SYNTHETIC and hardware_enabled=false.
- **25/25 mutation-based Python tests PASS**, Python compilation PASS, full real-data lineage PASS, live SCADA source-link PASS. Deliberate corruption of source, staged normalization, timestamps, external/safety sensors, flow, model SHA and SCADA hashes is rejected.

## Important discovery
The staged measurement gate intentionally rounds raw values to **8 significant digits**. A naive fixed 1e-5 absolute comparison falsely rejected valid D inputs (example 201306.751262789 -> 201306.75). The auditor now verifies the *actual producer contract*, including a regression test for this quantization.

## Non-claims / open acceptance
- These are **D_SYNTHETIC replay inputs derived from v07**, not measured pool/IT/ambient field data.
- Static source chain and stored SHA do **not** independently prove the original MATLAB/Simulink run was executed by the declared scripts, or establish a signed execution receipt.
- No calibration, physical validation, standards signoff, real-world hardware safety or true sensor independence is claimed.
- Original source/CSV, MATLAB models, SCADA runtime state, shared GUI, STOP/OAuth and other owners' worktrees were not modified.

## Next executable step
Prepare a *read-only* MATLAB run-receipt inventory for v08: inspect logs, command history and versioned export metadata; if no signed/hashed run receipt exists, record that precise gap instead of manufacturing one. Separately validate pool heat-loss and IT thermal parameters against primary references and uncertainty ranges before physical acceptance.
