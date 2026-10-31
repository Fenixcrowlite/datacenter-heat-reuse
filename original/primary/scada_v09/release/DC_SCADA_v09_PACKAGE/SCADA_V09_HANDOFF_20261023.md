# DC SCADA v09 | verified local HMI handoff | 2026-10-23

## VERIFIED — Windows DESKTOP-M9L3I4M
- Source project: `scada_v09/`. Main service Python standard library on `127.0.0.1:8091`.
- Live server launched via `scada_v09/start_scada.ps1` and confirmed with `GET /api/health` (own PID/instance_id). No Docker required.
- 8 native Simulink v08 data sets × 672 samples, dt = 900 s, 168 h coverage per case; source is explicitly **D_SYNTHETIC**, not physically measured or certified.
- Visual desktop browser acceptance: Chrome headless screenshot 1600×940 `scada_v09/runtime/QA_HMI_1600x940.png`; tablet 920×1200 `scada_v09/runtime/QA_HMI_TABLET_920x1200.png`. Synoptic, KPI, alarm feed, scenario player rendered.
- Independent tests on actual Windows host after code freeze: **27/27 Python tests PASS**, `node --check web/app.js` PASS, `python -m compileall` PASS.
- Live GET endpoints /api/health, /api/status, /api/scenarios, /api/snapshot, /api/history, /api/alarms all returned 200 with D_SYNTHETIC metadata.
- Live alarm E2E: selected both-REJECT-failed scenario, sought to indexed source CSV alarm sample #219, `IT_model_alarm` active, model IT risk 42.996°C (NOT actual CPU temperature); replay PLAY moved index 219→220, PAUSE succeeded, restored healthy scenario.
- SQLite historian and acknowledgement event-change logic tested, duplicate sample protection and persistence verified in automated tests.
- STOP file + signed Origin/CSRF control, no hardware/PLC outputs, loopback-only binding.
- Existing v04-v08 Simulink and their CSV untouched.
- Protected optional container profile `docker-compose.yml` for FUXA/Mosquitto + opt-in Grafana; MQTT exporter `mqtt_bridge.py` only publishes read-only D_SIMULATED tags. Not deployed because starting Docker Desktop consumed >8 GB of RAM and left <0.4 GB free. Docker was stopped to restore ~7.4 GB free. **Do not claim live MQTT, FUXA or Grafana deployed**.
- User authorized local service startup; not scheduled for automatic reboot, no WSL/PLC/firewall/power modifications.

## Technical evidence / paths
- Source: `C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\scada_v09`
- Live URL (available only while machine and SCADA process run): http://127.0.0.1:8091/
- Stop: `scada_v09/stop_scada.ps1`. It persists STOP and requests graceful shutdown of **owned** process. Never remove STOP automatically.
- Docs: `scada_v09/README_RU.md`, `ARCHITECTURE_SK.md`, `TEST_PLAN.md`, `CODEX_RESULT.md`.
- Independent QA: `python -m unittest discover -s tests -v`.
- Screenshots stored in runtime (ignored by git) and included in release artifact.
- Data: `results/pool_measurement_v08/sim_v08_*_SK.csv`. Strict synthetic D provenance.
- Release archive and Obsidian: see release files once generated.

## Next milestones, not yet VERIFIED
1. FUXA/Mosquitto backend integration only if memory budget and Docker Desktop stability verified; broker password files, ACL and FUXA initial admin setup required. Grafana/InfluxDB historian are not running; native SQLite historian IS running.
2. Opcional export with paho-mqtt only after broker and passwords configured; verify retain/staleness/ACL end-to-end. No hardware writes.
3. Real measured Class A data with instrument IDs/calibration, error and timestamp checks; physically measured heat exchanger supply/return T, flow, site DC and IT energy. Separate measured vs simulated SCADA instance or namespaces.
4. Site security design and trained operator review before any physical PLC coupling; hardware safety interlocks remain independent.
5. WSL/Docker memory resource caps only with deliberate review, do not globally change user WSL settings without analysis.

No assertion of continuous assistant background work; locally launched service is self-running under the user's ownership until explicitly stopped.
