# HANDOFF: Measurement data adapter and actual Simulink D-replay v08 | 2026-10-23

## VERIFIED
- New native MATLAB R2026a model: matlab/pool_measurement_v08/DC_Bazen_Externe_Merania_v08_SK.slx.
- New v08 was cloned from v07; original v07/v06/v05/v04/v85 were not overwritten.
- Two physical-interface temperature inputs to Stateflow gate, supplied from validated timestamped CSV, replace old Simulink Ttrue-derived virtual delay block connections.
- Operational inputs remain synthetic v07 replay; class D time series generated and separately validated as 13-column UTC 900-second CSV, then joined to original 21 operational channels.
- 8 scenarios x 672 steps (15min step = 168h each) actually re-executed in Simulink R2026a.
- Max abs pool temperature differences versus golden v07 scenario: <=3.01e-8 C; heat output error <=0.044 W; all safety latch outputs identical to saved v07.
- Independent Python QA: 91,565 assertions PASS over native Simulink CSV, plus exact per-sample external sensor channel equality, energy balances, stateful latch conditions, original v07 regression.
- Critical defect caught and corrected: first v08 inherited function added raw sensor bias a second time to imported CSV values. New v08 gate now uses exact imported T1/T2 values; all 8 scenarios were rerun and independently validated again. Builder script updated to reproduce corrected behavior. Original v07 untouched.
- Input uncertainty analysis (assumptions D): 30m3/h, deltaT 3K -> 104.236kW nominal, standard uncertainty 11.124kW with 5% flow and 0.2K each independent thermometers. Using whole 500m3 pool temperature at 900s with 0.2K each would produce ~655.17kW power uncertainty. Need actual calibrated flow calorimetry instead.
- Three 3-page technical reports SK EN RU with formulas, scenario table, metrology example, actual charts. Render inspected, proper Cyrillic fonts, PDF images and table bounded.
- Full math documentation in docs/pool_measurement_v08/Matematika_integracia_merani_v08_SK.md.
- Original v85 historical hash unchanged 2a9de22c0c55e8c4a87f7b0e0cfe9cd97db08c991f09d98361b009de310adde7.
- Preserve ownership of parallel calibration/standards lane under calibration/standards_20261023.

## DATA PROVENANCE: NON-NEGOTIABLE
- ALL current v08 input scenarios are classified D SYNTHETIC GENERATED FROM v07. They are not measured Class A.
- This is an offline replay, NOT live BMS/OPC-UA, and NOT physical parameter calibration.
- The CSV includes a flow placeholder and IT power demonstration value, neither measured or used in model tuning. Both must be replaced with real instruments.
- Class A data need actual site dataset identity, timestamp, instrument IDs, calibration documentation, units and uncertainties.
- Even high replay agreement is *not* evidence the simulation represents the real DC+pool installation.

## FILES
- matlab/pool_measurement_v08/vytvor_model_merani_v08_sk.m
- matlab/pool_measurement_v08/bezpecnostne_meranie_externe_v08.txt
- matlab/pool_measurement_v08/oprav_vstup_merani_v08_sk.m
- matlab/pool_measurement_v08/priprav_D_replay_v08.py
- matlab/pool_measurement_v08/spusti_merania_replay_v08_sk.m
- matlab/pool_measurement_v08/qa_nezavisla_v08_sk.py
- matlab/pool_measurement_v08/neistoty_merania_v08_sk.py
- matlab/pool_measurement_v08/grafy_v08_sk.py
- matlab/pool_measurement_v08/vytvor_pdf_v08_3jazyky.py
- results/pool_measurement_v08/D_REPLAY_INPUT_MANIFEST.json
- results/pool_measurement_v08/QA_NEZAVISLA_V08_SK.json
- results/pool_measurement_v08/NEISTOTY_MERANIA_V08_SK.json
- results/pool_measurement_v08/vysledky_v08_SK.json
- results/pool_measurement_v08/sim_v08_*.csv (8), source_D (8x original source+metadata), staged_D (8x accepted normalized records+metadata)
- results/pool_measurement_v08/DC_Bazen_Externe_Merania_v08_{SK,EN,RU}.pdf
- results/pool_measurement_v08/externe_snimace_v08_SK.png, regresia_tepla_v08_SK.png

## NEXT, HARD BLOCKERS
1. Get real Class A IT/DC facility heat source and pool sensors with timestamp, independent instrument IDs and calibration certificates. Validate UTC missing/duplicate points and clock error.
2. Estimate propagation of flow + return/supply temperature uncertainty and correlated errors, not just independent assumed 0.2K.
3. Calibrate manufacturer HP COP(Tsource,Tsink,PLR), real HX UA and hydraulic head, quantify errors by genuine measured validation holdout.
4. Replace virtual IT buffer hypothesis with measured cooling response and actual manufacturer N+1 cooling capacity.
5. For the specific pool category audit current consolidated Slovak law / relevant EN pool standards, and ERF cross-site boundary under EU 2024/1364.

## REPRODUCTION
From matlab/pool_measurement_v08:
- MATLAB R2026a: spusti_merania_replay_v08_sk
- Python: qa_nezavisla_v08_sk.py, neistoty_merania_v08_sk.py, grafy_v08_sk.py, vytvor_pdf_v08_3jazyky.py.
- Do not rerun priprav_D_replay_v08.py without an explicit new release destination: it deliberately refuses overwrites.

Completed work in this conversation; no assistant background execution is claimed.
