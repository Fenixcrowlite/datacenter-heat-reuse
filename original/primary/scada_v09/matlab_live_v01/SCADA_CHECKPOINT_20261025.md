# SCADA ↔ MATLAB: checkpoint 2026-10-25

## VERIFIED
- Native SCADA v09 active on 127.0.0.1:8091. D_SYNTHETIC archival v08 replay, NOT a fresh Simulink run.
- MATLAB LIVE bridge active on 127.0.0.1:8094 with restored completed real v04 Simulink job ca74c32211a44b6d9e83cd61d96cf59f, 672 samples.
- Native MQTT broker active on 127.0.0.1:18883; Node broker role, freshness and STOP tests 13/13 PASS.
- Bridge Python regression 10/10 PASS; front-end JS files syntax PASS.
- New read-only audit script: matlab_live_v01/audit_sources.py. Output: runtime/SOURCE_AUDIT_LATEST.json, PASS.
- Verified v08 T_pool at current replay index 0 = 16.068635804129 °C; separately verified v04 first T_pool = 16.0211475718569 °C, last 20.7301977290449 °C.
- All new per-row residual_* fields below 1e-5 W, all 672 rows finite, exactly 900-second time grid, source class synthetic, hardware disabled.
- STOP flags absent during checks, no user models edited or rebooted.

## NOT DONE / limitations
- The original SCADA historian, alarms, SVG and MQTT publisher remain driven by v08 archival replay. v04 current run has separate HMI and not unified provenance-aware historian.
- v04 live bridge does not run v85 six-mode Stateflow; no claim of full v85 electrical/thermal dispatch.
- Temperatures of district heating supply are derived algebraically, without hydraulic inertia and calibrated pipe losses.
- FUXA not installed; port 1881 closed. Do NOT start large Docker/FUXA blindly: free RAM during this audit only ~2.4–3.3 GiB.
- Data quality D_SYNTHETIC / D_DERIVED, no sensors and no industrial controls.
- No new MATLAB simulation executed during this checkpoint: audited already completed job and available endpoints.

## Next engineering change
1. Design a read-only provenance-selected unified view: distinct v08/v04 sources, separate chart/historian namespace, alarms calculated per source, reject mixing.
2. Extend the v04 Simulink model to central-heating hydraulic/temperature dynamics with independent first-law and switching tests. Do not silently proxy such dynamics using the algebraic T_supply.
3. Gate eventual v85 integration on its saved model clock, latch, inventory and admissibility constraints; preserve immutable v85 source and regression hashes.
4. Only after a RAM budget check: isolated compatible FUXA runtime with loopback-only transport, authentication, MQTT reader role, browser E2E.
