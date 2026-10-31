# SCADA/MATLAB source integration and DH pilot | 2026-10-25

## VERIFIED now (DESKTOP-M9L3I4M)
- Existing SCADA native replay: http://127.0.0.1:8091/ remains online, source `D_SYNTHETIC`, v08 CSV.
- MATLAB LIVE v04: http://127.0.0.1:8094/ remains online, last completed genuine MATLAB/Simulink `sim()` job restored; NO new MATLAB run in this checkpoint.
- Main SCADA navigation points to http://127.0.0.1:8094/#source-selector. The same v04 dashboard has a native v04/v08 source selector, independent chart series, per-source sample table and per-source diagnostics.
- New `GET /api/archive` is fixed to loopback 127.0.0.1:8091 and selected SCADA scenario (full 672×900s source samples). Rejects non-D provenance, invalid/scenario-injected source IDs, bad grids, redirects and payload >4 MB. Does NOT proxy `csrf_token`, commands or hardware.
- `GET /api/result` continues to represent the last completed v04 source with `D_DERIVED`, NOT v08 replay/v85.
- v08 flags are labelled **model flags for selected time**, not physical alarms; v04 balance residuals are **model diagnostics**, not native SCADA alarm history. v08 and v04 samples and historian namespaces are deliberately **not merged**.
- Browser Chrome E2E executed with localhost-only isolated headless profile. Actual DOM v04 first `T_pool_C=16.02°C` → v08 initial `16.07°C` → v08 sample 80 `21.75°C`, correct model/time/provenance flags, 0 uncaught JS errors. Screenshot `runtime/QA_SOURCE_SELECTOR_BROWSER_20261025.png`.
- Tests: main SCADA 27/27 PASS, MATLAB bridge 10/10 PASS, archival adapter 4/4 PASS, Node live HTTP+DOM/canvas harness PASS. JavaScript syntax PASS.
- Source model SHA256 unchanged: `0D9A59466A0284CA6BB61D6756222DCCAFC2AC7AA683AE41DE35CE6D72F94EE0`.
- Main SCADA and MATLAB bridge STOP files absent. Native MQTT loopback 18883 running; FUXA 1881 not installed/running. Free RAM last check ~2.6 GiB; no Docker, FUXA or MATLAB process started by this checkpoint.

## Separate dynamic district-heating pilot (D_ASSUMED)
- New `dh_dynamic_pilot.py` reads the already completed v04 job `ca74c32211a44b6d9e83cd61d96cf59f`. It does **not** modify a saved .slx, rerun Simulink or feed heat back into the Stateflow supervisor.
- Explicitly ASSUMED (not field-calibrated): supply and return water each 10,000 kg; heat capacities 4182 J/kg/K; heat-loss coefficients 120 and 80 W/K; ambient 15°C; nominal pump differential 150 kPa at 5 kg/s; pump efficiency 70%, density 997 kg/m³.
- Two coupled implicit water-node equations plus bounded load delivery, zero circulating flow and pump power after DH OFF, quadratic surrogate pressure drop. Numerical residual is independently checked:
  `Cs*(Ts_next-Ts)/dt + Cr*(Tr_next-Tr)/dt = Q_DH_in - Q_load - UA_s*(Ts_next-T_ambient) - UA_r*(Tr_next-T_ambient)`.
- 672 x 900-second steps, full 168h. Pilot sources 7.615207629 MWh of allocated v04 DH heat and estimates 7.089041555 MWh delivered to the illustrative load; circulation electricity 0.006602665 MWh. Max first-law residual 9.61e-10 W. These are contingent on pilot assumptions, **not measured energy or validated system efficiency**.
- Isolated outputs: `runtime/dh_pilot_v01/ca74c32211a44b6d9e83cd61d96cf59f/{trajectory.csv,summary.json}`. Tests `tests_dh_dynamic_pilot.py` 6/6 PASS, including independent two-node first law, zero-flow/no-pump, equilibrium, bounds, correct OFF from hour 96.
- The pilot is NOT full pipe hydraulics, hydraulic balancing, a pump characteristic curve, calibrated pressure loss, transport delay by distributed PDE, or closed-loop dispatch. Do not call it the updated Simulink heating network.

## File ownership / rollback
- Backups before editing: `runtime/backup_sources_20261025/{live_bridge.py,dashboard.html,dashboard.js,index_before_source_selection.html}`.
- Modified: `live_bridge.py`, `dashboard.html`, native `../web/index.html` navigation text/link only.
- Added: `source_compare.js`, `tests_source_compare.cjs`, `test_sources_browser.mjs`, `tests_archive_adapter.py`, `dh_dynamic_pilot.py`, `tests_dh_dynamic_pilot.py`.
- No existing source .slx, v08 CSV, v85 Stateflow, STOP markers, PLC endpoints, physical controllers, global firewall/power/WSL settings changed.
- The updated live bridge was safely restarted after verifying it owned its PID and was not executing a MATLAB job. STOP markers were never deleted.

## Next concrete engineering gate
1. Integrate the two-node dynamic DH subsystem **within a new isolated Simulink revision**, with pump dynamics, demand return, heat losses and limits, and connect the changed Q/load/flow state into supervisor dispatch. Preserve existing v04/v85 source models.
2. Run actual MATLAB Simulink with two cases (baseline and DH OFF at 96h), compare traces and independently validate energy/temperature/flow/pump power, refuse on violation. Do not assert this done yet.
3. Extend source selector with independent *visited* historian namespace for new v04 runs (distinct from v08 native SQLite); preserve native alarms and separate diagnostic alarms, with unambiguous labels.
4. Only consider FUXA with compatible isolated Node runtime, local auth, MQTT reader-only and adequate RAM, verify browser E2E. No PLC writes.
5. v85 full Stateflow integration only after guard compatibility checks (clock, latch, inventory, event memory, rated compressor electrical limit); no silent substitution of v04 controller.
