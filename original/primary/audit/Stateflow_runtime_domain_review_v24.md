# Independent Stateflow runtime and integration review — v24

Reviewer lane `/root/stateflow_qa`. Reviewed `automation/STATEFLOW_ACCEPTANCE.md`, the authoritative v22 Stateflow status/stageboard, latest v23 research status/stageboard, the research frontier, v22 model/acceptance/QA evidence, and v14 HP/v16 TES/dispatch source before specifying tests. Reviewed the additive v24 builder, clock adapter, state allocation and runtime monitor source independently of their implementation. No production source was edited by this lane. All model constants remain explicit engineering assumptions; this review adds no primary-source verification or equipment calibration.

## Newly identified actual-model defect

The v22 saved model exposes two distinct time controls: `dchr_dt_v22` determines the Simulink solver, input, chart and Unit Delay sample interval, while parameter port `p(1)` determines the HP charging request and TES energy update. Its positive-case runner sets them equal, but the saved model itself does not enforce equality. The negative tests in its 476-check acceptance runner call the v16 reference or host HP adapter directly; they do not establish actual Simulink rejection.

This is a substantive integration defect even though the existing ordinary v22 acceptance remains valid under its synchronized configuration. First-law residuals calculated with the same wrong physical timestep as the update can appear zero. A physically admissible state and bounded flows alone cannot prove the interval represented by a saved model sample.

The read-only actual v22 probe in `results/stateflow_clock_defect_v24_20261009T031115019Z` uses 1 h model sampling, physical parameter `p(1)=0.5 h`, 5 MWh initial storage, 1 MW useful TES discharge, discharge efficiency 0.8, zero standing loss, no recovered source and no boiler. The first saved update is 4.375 MWh, followed by 3.75 MWh. The model reports zero balance residual at both samples. Independent arithmetic gives the correct one-hour removal `1/0.8=1.25 MWh`, versus the implemented half-hour removal `0.625 MWh`; each actual-time balance is therefore `-0.625 MWh`. These are executed model outputs and an independent energy calculation, not experimental equipment performance.

## Independent equations for the acceptance monitor

Require one finite positive interval `dt_model = p(1)`. Inputs and physical parameters obey the reviewed v14/v16 domains: finite nonnegative source/demand/capacities, Kelvin-positive reservoir proxies with positive heating lift, `0<=E<=K`, `0<eta_c,eta_d<=1`, `0<=lambda*dt<=1`, and admissible HP COP/backend parameters. Invalid conditions must fail when the actual saved model is simulated.

Let the HP ports be demand `D`, condenser heat `H`, work `W`, evaporator extraction `U`, and request `R`. Chart outputs are direct HP heat `H_d`, external TES charge/discharge powers `Q_c,Q_d`, useful boiler heat `B`, unmet demand `M`, loss-first energy `E_a`, next energy `E_n`, standing/charge/discharge losses `L_s,L_c,L_d`, and useful supplied heat `Y`. For every accepted output:

- HP first law: `H=U+W`; complete condenser allocation: `H=H_d+Q_c`.
- Demand accounting: `D=H_d+Q_d+B+M`; useful supply: `Y=H_d+Q_d+B`.
- Linear loss-first storage: `E_a=E(1-lambda*dt)` and `L_s=E-E_a`.
- Port losses: `L_c=(1-eta_c)Q_c*dt`, `L_d=(1/eta_d-1)Q_d*dt`.
- TES port closure: `E+(Q_c-Q_d)dt=E_n+L_s+L_c+L_d`.
- Whole boundary closure: `(U+W+B)dt+E=Ydt+E_n+L_s+L_c+L_d`.

Enforce nonnegative bounded flows and energies, mutual TES exclusivity, exact integral mode codes 0–5, and dominant-flow mode order unmet, backup, discharge, charge, recovery, idle. An operating HP requires finite COP greater than one with `H=W*COP`; an off HP has zero availability and undefined (NaN) operating COP. Recompute closure from ports rather than trusting chart output 13. Scale numerical tolerances from finite interval energy; require finite tolerance itself. Power and energy inequalities use power and energy tolerances respectively.

The inspected v24 monitor implements these equations and the clock check. Initial review identified a potential tolerance overflow and the use of an energy tolerance for power signs; the implementation owner corrected both before saving the new model. The monitor has no new TES/HP physical assumption. It remains downstream of the operational chart, with checked output driving both feedback and the accepted dispatch trace.

## Independently specified executable tests

`stateflow_domain_cases_v24.json` specifies 44 negative cases without importing production model code. Coverage includes first- and second-tick bad source/demand/lift, nonfinite ports, initial-state bounds, every storage-efficiency/power/loss domain, finite boiler capacity, HP capacity/Carnot fraction/COP range/part-load/backend domains, polynomial Carnot and overflow prediction, and two positive physical/model timestep mismatches. All cases require an actual `sim(SimulationInput(...))` attempt. Physical-domain errors must preserve their original cause beneath `DCHR:v24:PhysicalDomain`; positive timestep mismatches must include `DCHR:v24:IntegrationStep`.

The evidence checker requires the exact independent case set, expected identifiers, intended invalid-input tick, actual simulation/rejection flags, no accepted invalid trace, nonempty diagnostics, and the specific runtime cause. Intended second-tick placement does not prove completion of a prior valid tick when failure timing/partial traces are unavailable. Such timing is explicitly left unverified rather than inferred.

Valid-case numerical evidence explicitly reuses `verify_stateflow_trace_v22.py`, the already independent fixed-COP oracle and conservation/bounds/memory verifier. Its SHA256 is recorded in every v24 QA report. Reuse is appropriate because v24 preserves the v14 HP/v16 discrete TES allocation equations; the new evidence concerns model integration and runtime failure behavior, not a new physical fit or repeated tests claimed as new physics.

## Saved-model provenance and executable evidence

Independent Python ZIP/XML inspection of the actual additive `.slx` passed 78/78 assertions. It verifies all six operating states, 30 guarded mode changes, six startup choices, common input/chart/delay timing, the dedicated model-interval constant into HP and monitor port 5, each monitor input connection, no unchecked chart output bypass to trace/feedback, index-8 energy feedback, and exact equality of all three embedded dispatch/monitor helpers to reviewed source. The saved model SHA256 is `1f1c826f0f61d04bea58c2ab39d607268ac273bad9564e69bec89e361c461389`. Static inspection proves saved structure/provenance; it does not itself execute Stateflow.

The independent rejection-schema verifier initially passed nine synthetic self-tests, including deliberate corruption of attempt, rejection, invalid-acceptance, expected cause, tick, missing and duplicate cases. A later self-test adds the MATLAB summary-wrapper schema. These fixtures are expressly marked synthetic and are separate from actual simulation results.

Final actual v24 acceptance, runtime-rejection and contract-gate fault evidence will be reviewed and recorded below before final handoff. A compile-only result is insufficient.

## Remaining physical limits and handoff

The host HP call remains normal-mode MATLAB simulation; standalone generated-code deployment remains untested. Loss-first linear TES retention remains dependent on time partition, and newly charged energy experiences standing loss only in the next interval. No hysteresis, minimum dwell, equipment fault model, compressor cycling, hydraulic/network/fuel/auxiliary model, primary-paper replication or measured-system validation is added.

After this concrete integration defect is corrected and executed gates pass, next actionable task is the previously documented primary-text TES standing-loss audit and independently derived continuous/exponential reference with timestep convergence. Preserve the v22/v24 declared discrete baseline for comparison.
