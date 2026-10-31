# DCHR SCADA MATLAB & MQTT handoff — 2026-10-24

## VERIFIED at 23:xx Bratislava, Windows DESKTOP-M9L3I4M
- Native SCADA v09: http://127.0.0.1:8091/ (Python localhost; replays 8 native D_SYNTHETIC v08 files).
- MATLAB LIVE v01: http://127.0.0.1:8094/ (localhost Python bridge, executes genuine MATLAB R2026a Simulink/Stateflow v04 batches, results persisted).
- MQTT: 127.0.0.1:18883 (native Node Aedes + read-only exporter). Actual v09 snapshot -> MQTT broker -> viewer E2E PASSED 10 scalar tags including T_pool_C exact equality. No real device connections.
- FUXA (:1881), Grafana and Docker: NOT RUNNING. FUXA npm package not installed. Bounded npm attempt halted (no finished package); don't claim FUXA dashboard.
- All three listeners are loopback-only; STOP absent at last check; Windows ACL restricted credential file.
- At last check no MATLAB process running after two successful batches.
- Native v09 regression 27/27 PASS; MATLAB live Python 10/10 PASS; MQTT Node ACL/broker/publisher tests 13/13 PASS; headless Chrome rendered MATLAB LIVE with temperature 20.73 C and two canvas graphs.
- v04 source SHA256 preserved 0D9A59466A0284CA6BB61D6756222DCCAFC2AC7AA683AE41DE35CE6D72F94EE0.
- Note source boundaries: MQTT currently publishes native SCADA v08 replay only; new v04 jobs appear in independent localhost 8094 MATLAB LIVE UI, not yet merged into MQTT/Historian. v85 stays separate. All classes D_SYNTHETIC or D_DERIVED.

## Source and controls
- scada_v09/matlab_live_v01: live_bridge.py, live_v04_runner.m, dashboard.html/dashboard.js, tests_live.py, start_live.ps1, stop_live.ps1, README_RU.md, QA_RESULT_20261024.md.
- scada_v09/fuxa_bridge: broker.cjs, publisher.cjs, run_stack.cjs, runtime-config.cjs, tests/, verify_live.cjs, start_mqtt_native.ps1, stop_mqtt_native.ps1.
- Persistent results: scada_v09/matlab_live_v01/runtime/jobs/<uuid> (copy of v04 SLX, signed config SHA and CSV/JSON, local log).
- Main STOP in scada_v09/STOP respected. Bridge/fuxa subfolders have independent STOP files, never auto-cleared; no hardware actions. Stop processes only if PID and command path ownership match.

## Latest MATLAB runs
- Baseline id 79b874c619674e1e966c72bf92eb67b3: 672 rows, Qpool 10.3930843 MWh, QDH 16.1011323 MWh, Qreject 6.2456867 MWh, HP compressor electric 4.7635249 MWh.
- What-if id ca74c32211a44b6d9e83cd61d96cf59f: pool OFF from 24h, DH OFF from 96h, HP→pool OFF entire interval, 672 rows and zero OFF-gate violations; Qpool 0.9600 MWh, QDH 7.6152076 MWh, Qreject 19.7843925 MWh, P_HP electric 1.3522478 MWh. Max T pool 20.7302 C.
- All balances < 1e-8 W numerical residual in validated runs. This is source equation coherence, NOT measurement accuracy.

## Deferred milestones
1. Compatible FUXA runtime (upstream recommends Node 18; local Node 24) with bound 127.0.0.1:1881, built-in authentication before operator usage, and FUXA read-only MQTT device for 10 tags. Do not deploy wildcard public listeners.
2. New v04 job namespace in MQTT (if added, explicitly labeled model v04 with derived D and time/age), with first-class chooser between archived v08 and new v04 in single native HMI and historian.
3. Physically meaningful DH hydraulic/inertia block in Simulink; compare with v85 stateflow under separate certified contract, no false equivalence or certification.
4. Preserve STOP, source hashes, no real PLC or measured-data claims.
