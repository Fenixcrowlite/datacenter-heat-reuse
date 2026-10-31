# HANDOFF | DC -> Pool 500 m3, v04 closed-loop Stateflow, 2026-10-23

Ownership: v04 independent lane; old v85/v86, pool 7-day v01, yearly synthetic v02 and one-way v85 bridge v03 are intentionally unchanged.

## Actual executed and verified

- New native MATLAB R2026a / Simulink SLX model: matlab/pool_feedback_v04/DC_Bazen_Uzavreta_Regulacia_v04_SK.slx.
- Real 5-state Stateflow.Chart; modes 0 NO_SOURCE, 1 DIRECT_HX, 2 HEAT_PUMP, 3 TES_ONLY, 4 IT_STOP.
- Real 15-minute feedback loops: Tpool -> demand -> Stateflow -> dispatch -> Tpool and TES energy -> dispatch.
- 8 synthetic scenarios each 672 time steps (7 days = 168 h), full saved time-series CSV, output JSON and actual MATLAB-generated plot.
- Initial compiled Stateflow-shadow warnings were fixed and all 8 simulations re-executed successfully without warnings.
- Independent CSV-based Python QA: 65,493 checks PASS.
- Original v85 SHA-256 preserved: 2a9de22c0c55e8c4a87f7b0e0cfe9cd97db08c991f09d98361b009de310adde7.
- Pool T ceiling 27.75 C, observed maximum T 27.58 C; HP thermal cap 200 kW, compressor cap 55 kW, pool cap 150 kW, TES capacity 0.90 MWh.
- Baseline synthetic 168 h: Q_DC 28.560 MWh = direct HX 3.051 + HP source 19.263 + rejection 6.246 MWh.
- Baseline pool 10.393 MWh, DH 16.101 MWh (unmet 1.539), compressor 4.764 MWh, auxiliary modeled 0.297 MWh.
- Warmer source +12 C: compressor drops to 2.744 MWh and direct HX goes to 9.638 MWh (scenario only).
- No cover: pool rises to 11.410 MWh. No TES: unmet DH increases to 2.035 MWh.
- 3 technical PDF reports SK / EN / RU (3 pages each), programmatically validated including tables/formulas and figure; preview physically inspected.
- Detailed Slovak math and model info in docs/pool_feedback_v04/Popis_a_rovnice_Stateflow_v04_SK.md, copied to Obsidian.

## Scope and strict scientific boundaries

v04 is a NEW CONTROLLER and not the saved-v85 engine. The old v85 logic was never modified or replaced; do not claim bidirectional v85 integration or bitwise equivalence of dispatch.
No measured real DC/pool data and no validated year; the eight schedules are SYNTHETIC, not real capacity forecasts. Units: W, seconds, J; COP has assumed Carnot quality factor 0.43, clip 2.5-6, temperature 52 C condenser. Heat exchange 8500 W/K with approach 5 K is assumed; TES losses 0.2%/day; no real hydraulic design or natatorium HVAC. No certified safety/legal compliance.

Current reference model can be safely re-run via matlab/pool_feedback_v04/spusti_scenare_v04_sk.m (existing SLX left untouched).
Independent QA: matlab/pool_feedback_v04/qa_nezavisla_v04_sk.py
Three-language PDF: matlab/pool_feedback_v04/vytvor_pdf_v04_3jazyky.py.

## Necessary next work, do not silently fabricate

1. Bidirectional integrated v85-derived controller with certified temporal state and event memory, not a v85 state reset; integrate pool demand while preserving v85 invariants.
2. Original site or official observed time-series, documented denominator boundaries for annual PUE/ERF.
3. Manufacturer COP(Tsource,Tsink,PLR), heat exchanger UA / mass flow, pump electricity, thermal storage stratification and hydraulic isolation.
4. Independent sensor fault injection with temperature and flow delays, cooling failsafes, pool water turnover, real HVAC/dehumidification.
5. Normative review of applicable Slovak swimming-pool rules current consolidated edition; STN EN 15288-1+A1:2024 licensed standard as applicable. EU 2024/1364 ERF credit only external DC heat crossing site boundary.

No async background process is implied by this handoff. Results were generated and tested on the local machine during the current conversation.
