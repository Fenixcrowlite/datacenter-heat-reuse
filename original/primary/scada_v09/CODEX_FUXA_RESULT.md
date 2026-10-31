# SCADA v09 MQTT / FUXA status — 2026-10-24

**MQTT VERIFIED (runtime) / FUXA BLOCKED (not installed).**

- Native Aedes via asynchronous Aedes.createBroker (documented API). Broker and publisher on 127.0.0.1:18883; no Docker. Source GET is exactly http://127.0.0.1:8091/api/snapshot.
- Source D_SYNTHETIC quality D, 10 finite validated scalar tags + retained provenance metadata and online/stale/offline states. Role-separated secrets and reader-only subscribe / exporter-only publish ACL. Source stale/redirect/oversize/STOP clear retained values; passwords are not logged.
- Node automated tests: 13/13 PASS, including real broker, stale/restore, role ACL, source validation, STOP. verify_live.cjs: MQTT_LIVE_E2E_PASS, 10 tags, T_pool_C 16.068635804129 = original SCADA source at sample index 0, error 0 C.
- Server was started locally using fuxa_bridge/start_mqtt_native.ps1 and remains under the user's ownership. Persistent STOP with stop_mqtt_native.ps1 and PID guard.
- FUXA runtime not available at http://127.0.0.1:1881; @frangoteam/fuxa-min 1.3.1 not installed. Attempted isolated npm install under fuxa_bridge/fuxa, but did not complete, so owned npm installer was stopped. Node 24 is currently installed; upstream FUXA guide recommends Node 18. Need a compatible, bounded installation and GUI project setup before claiming FUXA E2E.
- Grafana and Docker were not started. No PLC devices were configured. MQTT exporter publishes archived v08 replay, not newer MATLAB live v04 runs.
