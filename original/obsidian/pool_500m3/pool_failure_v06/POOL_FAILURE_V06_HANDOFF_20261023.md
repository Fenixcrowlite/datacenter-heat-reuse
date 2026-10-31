# Handoff | v06 physical faults, sensor delays and IT REJECT loss | 2026-10-23

## VERIFIED in actual MATLAB R2026a / Simulink run
- New independent native SLX: matlab/pool_failure_v06/DC_Bazen_Fyzikalne_Poruchy_v06_SK.slx.
- Built by cloning v05 without changing v05, v04 or original v85.
- Reuses the native five-state Stateflow dispatcher inherited from v04.
- Two simulated temperature sensors with different delays: T1=T_true(k-1)+bias1, T2=T_true(k-2)+bias2. Gate does not directly know Ttrue. Equal common-mode bias is NOT detected.
- A separate physical actuator model passes uncontrolled heat if stuck-open, even when latch=1 and pool command=0.
- Uncontrolled valve heat is deducted from original DC REJECT, preserving first-law source accounting.
- Independent REJECT can physically fail; loss of cooling creates Q_unhandled and model-only IT buffer risk temperature. This is NOT observed server temperature.
- 7 synthetic 7-day cases executed with 900-second step (672 samples each).
- Stuck valve: 0.4899585833 MWh leaked at zero software command, 87 samples of unsafe leakage.
- REJECT failure: 0.07966002562 MWh unable to reject; model IT risk T max 47.06055 C (6 alarm samples).
- Combined: 0.1525880024 MWh leakage, 0.0571524362 MWh unhandled; max IT indicator 42.72049 C.
- Healthy model: no leak, no unhandled reject, water matches v04 baseline.
- Independent Python CSV QA: 84,801 assertions PASS, including 900 s water heat balances, source and HP energy, delayed sensor histories, latch, IT buffer differential equation, and risky valve leakage while control is off.
- Original v85 preserved SHA256: 2a9de22c0c55e8c4a87f7b0e0cfe9cd97db08c991f09d98361b009de310adde7.
- Detailed Slovak math at docs/pool_failure_v06/Matematika_a_fyzikalne_poruchy_v06_SK.md.
- Three 3-page PDFs SK/EN/RU produced and rendered/inspected, with genuine graph images embedded.
- Source time series, JSON and QA in results/pool_failure_v06.

## Important scientific boundaries
- All operating input values, source, sensors, cooling performance and fault physics are synthetically assumed, Class D.
- IT T-buffer uses nominal 8e6 J/K and passive 2000 W/K; NOT CPU temperature or acceptance criterion.
- Core v04 still uses modeled actual T for part of thermodynamic control, and Stateflow is the new v04-style controller, NOT original v85 bidirectional integration.
- Valve leak model draws heat only from heat previously allocated to DC reject; physical topology and UA not independently validated.
- This demonstrates SOFTWARE SAFETY ≠ PHYSICAL SAFETY, not certified plant safety.
- Parallel standards/calibration lane belongs to another project/chat and has not been overwritten.

## Next engineering steps
1. Connect actual physical sensors with timestamps, uncertainties and measurable mass flows, no true-T shortcut for the controller.
2. Implement double isolation actuators and analyze valves frozen partly open, component failure correlations, and watchdog/control power loss.
3. Simulate redundant IT cooling paths and executable emergency IT load shedding under limited thermal constraints.
4. Calibrate Q_DC, T_DC, heat exchangers, real COP maps and annual source/weather inputs from traceable sources.
5. Check applicable consolidated Slovak rules for the chosen actual pool category. EU 2024/1364 defines reused energy only across the data-centre boundary; never double-count transferred energy.

## Re-run
MATLAB R2026a: cd to matlab/pool_failure_v06 then spusti_poruchove_scenare_v06_sk.
Python QA: qa_v06_sk.py. Figures: grafy_v06_sk.py. PDFs: vytvor_pdf_v06_sk_en_ru.py.
No background task is assumed after this turn.
