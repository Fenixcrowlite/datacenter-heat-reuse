# Handoff: Stateflow v85 to pool 500 m3, bridge v03 | 2026-10-23

Owner: independent integration lane. Do not overwrite original DataCenter v85/v86, pool v01/v02 or parallel calibration sources.

## Verified

- Re-executed the saved, unmodified MATLAB R2026a Stateflow v85 in three source cases: service_E3.0_a1.0_H2_dt0.25, charge_E4.95_a1.0_H2_dt0.25 and binding_stop.
- Each four-interval 0.25-hour v85 trace is BITWISE IDENTICAL to its retained MAT file from the v86 evidence.
- Original dchr.report_held_schedule_v76 accepted all these newly executed traces.
- Created a new Simulink model Bazen_Prepripojenie_Sluzby_v85_v03_SK.slx (separate from v85 and earlier pool).
- Fed actual v85 delivered direct HP heat service into the pool and remaining DH service allocation. This is a redistribution, NOT newly recovered heat.
- Executed 3 source cases times 3 pool states = 9 simulations. Independent Python QA: 99 checks PASS.
- In the one-hour service case: v85 0.447565789 MWh = pool 0.150000000 MWh + original-service remainder 0.297565789 MWh.
- No pool heat is counted when the original case only charges TES or delivers no direct HP service, or when pool STOP is activated.
- Original saved v85 SHA-256 remains 2a9de22c0c55e8c4a87f7b0e0cfe9cd97db08c991f09d98361b009de310adde7.
- Three 3-page PDF technical annexes SK, EN and RU built and programmatically verified; actual figure and table output rendered.

## Separate valid scopes

- pool_dc_integration_v02: 8760-h simulation, SYNTHETIC inputs, four cases. Not a true Stateflow-v85 yearly run.
- pool_v85_bridge_v03: true freshly executed short-horizon Stateflow v85 replay into a separate Simulink pool. ONE-WAY, no pool feedback to v85.
- Never repeat short saved v85 schedules to claim a measured or certified year.

## Artifacts in OneDrive

- matlab/pool_v85_bridge_v03/Bazen_Prepripojenie_Sluzby_v85_v03_SK.slx
- matlab/pool_v85_bridge_v03/spusti_skutocne_v85_a_bazen_sk.m
- matlab/pool_v85_bridge_v03/vytvor_most_simulink_v85_sk.m
- matlab/pool_v85_bridge_v03/krok_bazen_v85.txt
- matlab/pool_v85_bridge_v03/qa_most_v85_sk.py
- matlab/pool_v85_bridge_v03/grafy_simulacie_v85_sk.py
- matlab/pool_v85_bridge_v03/vytvor_pdf_v85_v03_3jazyky.py
- docs/pool_v85_bridge_v03/Prepojenie_v85_bazen_v03_SK.md
- results/pool_v85_bridge_v03/most_v85_bazen_v03_SK.json
- results/pool_v85_bridge_v03/QA_NEZAVISLA_V85_BRIDGE_SK.json
- results/pool_v85_bridge_v03/sim_*.csv (9)
- results/pool_v85_bridge_v03/Most_v85_bazen_v03_SK.pdf, EN.pdf, RU.pdf
- results/pool_v85_bridge_v03/priebeh_bazen_v85_SK.png and rozdelena_sluzba_v85_SK.png

Obsidian destination: Documents/Bimba/02_PROJECTS/02_Automation/DataCenter_Heat_Reuse/pool_500m3/pool_v85_bridge_v03

## Next technically necessary implementation

1. New closed-loop stateful controller accepting pool demand and original DH/TES schedule, without restarting v85 across its certified horizon.
2. 8760-h measured or appropriate documented site source data; no certified yearly v85 run is currently available.
3. HX hydraulic design, pump work, manufacturer COP(Tsource,Tsink,PLR) curves and independent temperature sensing.
4. Actual current Slovak consolidated law + full technical pool and commissioning standard check.
5. Correct facility energy boundary: PUE and ERF under EU 2024/1364; redistributing existing v85 heat adds zero aggregate recycled MWh.

## Reproducibility

MATLAB from matlab/pool_v85_bridge_v03: run spusti_skutocne_v85_a_bazen_sk.m.
Python from same folder: qa_most_v85_sk.py, grafy_simulacie_v85_sk.py, vytvor_pdf_v85_v03_3jazyky.py.

Completed as actual invocations. No claim of running background agent after this turn.
