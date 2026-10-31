# HANDOFF | DC + 500 m3 swimming pool redundancy v07 | 2026-10-23

## VERIFIED, actual executed evidence
- DESKTOP-M9L3I4M MATLAB/Simulink R2026a: 8 synthetic 168-hour scenarios, each 672 x 900-second steps.
- New native model: matlab/pool_redundancy_v07/DC_Bazen_Dvojita_Ochrana_v07_SK.slx.
- Existing five-state Stateflow v04-derived engine, enhanced physical plant wrapper. This is **NOT** closed-loop re-use of the original v85 chart, though v85 source file is preserved.
- v07 dual series pool isolation valves, two independent thermal REJECT channels in model, conditional modeled 70% IT thermal load shedding after both REJECT availability signals turn off and simulated IT buffer T >=38C.
- One stuck valve: **0 MWh leakage**; both stuck: **0.4899586 MWh uncontrolled heat** while heating command is off.
- Main REJECT down with backup up: backup handled **0.0796600 MWh**, leaving zero unhandled heat in the scenario.
- Both REJECT down, shedding off: 0.0796600 MWh unhandled, modeled IT risk T max 47.06055C.
- Both REJECT down, shedding on: 0.04989 MWh unhandled, 0.15212 MWh avoided nominal waste heat, T_IT_model max 40.33C. These are HYPOTHETICAL, NOT REAL SERVER TEMPERATURES.
- Common -0.4 K sensor bias remains undetected in the model.
- Python independently re-read saved CSV and performed **129251 assertions, all PASS**, including energy balances, stateful sensor delays, stop latch, physical leakage, both coolers, heat derating, buffer dynamics.
- Original v85 SHA256 remains: 2a9de22c0c55e8c4a87f7b0e0cfe9cd97db08c991f09d98361b009de310adde7.
- Three PDFs in SK/EN/RU, 3 pages each, charts actually embedded, text and box bounds verified and render inspected.
- Full Slovak math: docs/pool_redundancy_v07/Matematika_redundancia_a_bilancie_v07_SK.md.

## PREPARED, NOT CLAIMED COMPLETE
- Strict 900-second telemetry CSV+JSON provenance validator written as matlab/pool_redundancy_v07/kontrola_vstupnych_merani_v07.py.
- A field-measured data requires instrument IDs and calibration documentation; D synthetic is never promoted to A. Negative tests: fabricated A rejected, 1200s wrong cadence rejected. Normalized rows are not yet physically wired to the current v07 Simulink virtual sensor model.
- Actual facility measured data: ABSENT. v07 source profiles are D synthetic, as in v04-v06.
- No manufacturer COP(Tsource,Tsink,PLR), measured HX UA/flow/head-loss curves, measured IT heat capacities, or actual dual REJECT ratings.
- No SIL/PL certification or full safety FMEA. No conclusive legal standards compliance.
- Parallel calibration/standards lane owned by another working chat. DO NOT overwrite its directories.

## INPUT ASSUMPTIONS TO CHALLENGE
- 500m3 water volume, C=2.084727e9 J/K.
- Main REJECT 180kW, backup 150kW, virtual IT buffer C=8e6 J/K, passive 2000W/K.
- Two serial valves considered fail-isolated unless BOTH mechanically stuck, capped leakage 25kW, UA 4500 W/K.
- Instantaneous modeled waste-heat reduction by 70% after model buffer T>=38C and both cooling availabilities off; actual IT power ramp-down and SLA unknown.
- Sensors are still delayed model truths plus injected biases. Common-power/common-mode failures not verified.

## Handoff for next validated engineering stage
1. Obtain real measured 900-second timestamp series, physically separate pool sensor 1/2, heat flows, source and reject temperatures, IT electrical power; validate A provenance.
2. Build v08 signal adapter actually connected to real sensor channels, separate measurement uncertainty, pressure/flow sensor faults, and fail-safe loss-of-power hard stop.
3. Get manufacturer REJECT and HP curves, hydraulic design and backup redundancy N+1 / N+2 documentation.
4. Model IT load shed response time, fail to shed, UPS/control loss, thermal capacitance ranges, common power outages.
5. Never claim European regulation compliance based solely on our synthetic test.

## Reproducible commands
MATLAB R2026a from matlab/pool_redundancy_v07:
- spusti_scenare_v07_sk.m
Python:
- qa_nezavisla_v07_sk.py
- grafy_v07_sk.py
- vytvor_pdf_v07_3jazyky.py
- test_schema_merani_v07.py

Generated assets in results/pool_redundancy_v07 and synced Obsidian destination Documents/Bimba/02_PROJECTS/02_Automation/DataCenter_Heat_Reuse/pool_500m3/pool_redundancy_v07.
No background work is inferred from this completed turn.
