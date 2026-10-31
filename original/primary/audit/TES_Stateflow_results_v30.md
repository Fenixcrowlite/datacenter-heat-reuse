# Executed v30 results: temperature-aware TES with exact active-flow integration

Implementation acceptance **PASS**, 2026-10-09. Authoritative numeric evidence: `results/stateflow_v30_20261009T212727142Z`; MATLAB R2026a Update 5, Stateflow available, observed completed batch exit 0. New release `matlab/simulink/DCHR_Dispatch_Stateflow_v30.slx` preserves every previous saved model. Reproduce using `MASTER_STAGEBOARD_stateflow_v30.md`.

The model uses physical sensible energy above fixed ambient, explicit heat capacity and delivery cutoff, exact integration of uniformly held charge/discharge powers, and precomputed feasible powers that keep the entire interval within capacity/cutoff constraints. The distinction between physical energy and useful inventory is now explicit. Derivation, evidence classification and controller assumptions: `audit/TES_temperature_exact_flow_derivation_v30.md`.

## Executed acceptance and independent QA

23 scenarios, 69 intervals, all six dispatch modes; **1334/1334 MATLAB assertions PASS**, maximum absolute system residual `1.7763568394002505e-15 MWh`. **18/18 runtime fault rejections**: 12 finite domain cases, 2 delayed finite faults, 4 output-monitor corruptions. Saved MAT error metadata independently confirms rejection in Execution at the expected time, and correct accepted-prefix sample counts. Clean post-fault restart completes. These are limited numerical/domain fault tests, not equipment faults or full v29 coverage on v30.

Independent equation/units checks: **364/364 PASS**, including a separate temperature/loss RK4 integrator and Decimal coefficients. Independent actual numeric checks **3131 PASS**, saved SLX XML/connectivity/source checks **66 PASS**, artifact/runtime/MAT bindings **2040 PASS**. Separate synthetic verifier mutation tests **6/6 PASS**; they are not additional actual simulation checks. Evidence report: `audit/Stateflow_independent_QA_v30_20261009T212925_625430Z.json`. No failed independent checks.

## Actual controlled timestep comparison

These are assumed, deliberately unconstrained two-hour scenarios with loss rate `0.2 h^-1`, efficiencies `etaC=0.9`, `etaD=0.8`, and delivery cutoff at ambient. Charging starts empty with external charge 2 MW (internal 1.8 MW); discharge starts at 10 MWh with external delivery 0.5 MW (internal -0.625 MW). Fixed COP 4 is an engineering scenario assumption. Saved v28 and v30 models both executed at each timestep. Results are physical ambient-referenced energy, not usable energy above a nonzero cutoff.

| Timestep h | Charge v30 MWh | Charge v28 MWh | Discharge v30 MWh | Discharge v28 MWh |
|---:|---:|---:|---:|---:|
| 2 | 2.967120 | 3.600000 | 5.672951 | 5.453200 |
| 1 | 2.967120 | 3.273715 | 5.672951 | 5.566494 |
| 0.5 | 2.967120 | 3.117948 | 5.672951 | 5.620580 |
| 0.25 | 2.967120 | 3.041916 | 5.672951 | 5.646980 |

v30 matches the independently derived fixed-power continuous endpoint at every tested timestep. v28's loss-first splitting overestimates charging energy and underestimates discharge endpoint energy; the observed discrepancies match the derived split-bias formula. This does not establish partition invariance for state-dependent or bound-limited dispatch. Full-precision results and predicted discrepancies: `active_flow_comparison_v30.csv`; actual saved comparison SimulationOutputs and read-only exports bind these numbers to executed artifacts.

## Temperature/cutoff and saturation observations

Assumed `C=0.2 MWh/K`, ambient20°C, cutoff45°C, maximum70°C, rate0.1 h^-1. In `passive_cutoff_crossing`, physical energy5.2 MWh cools to4.705154573787 MWh /43.525772868935°C in one hour; the state remains physically positive but useful inventory becomes zero. On the next interval TES delivery is zero and finite backup supplies1 MW. No artificial clipping to45°C occurs.

In `cutoff_endpoint`, initial7 MWh permits a held TES output1.121333111164 MW for one hour, ending at5 MWh /45°C; boiler2 MW and explicit unmet demand account for the remaining4 MW load. Subsequent intervals have no TES discharge and passive cooling continues below cutoff. In `capacity_endpoint`, initial9.9 MWh charges at1.216759243831 MW to10 MWh /70°C. Subsequent charge1.111111111111 MW exactly offsets1 MW standing loss at capacity, with charge inefficiency included in the first law. These are numerical scenario observations, not measured tank behavior.

## Defects repaired and limitations

The unfinished adapter omitted the required initial-temperature parameter; it now reconstructs it from the current physical state. The monitor's zero-rate limiting branch is consistent with the kernel. First executed acceptance stopped on an invalid zero-capacity test fixture with unsupported delivery temperature; the corrected fixture sets delivery to ambient. Second full attempt passed1332/1334 but exposed empty-vector orientation in two one-interval feedback assertions. The corrected fresh batch passes1334/1334. Every attempt, source/spec snapshot and timestamped log is retained. Nonfatal Stateflow helper shadow warnings remain visible.

The constant-ambient mixed-store reduction and reservoir proxies are uncalibrated. Uniform interval throttling can be conservative relative to an event controller that supplies full power until cutoff; it may give a different delivered heat total as timestep changes. No stratification, hydraulic tank connection, approach temperature, changing ambient, standalone generated-code deployment, hysteresis/cycling, sensor/equipment faults, article replication or measured physical validation. Inherited Cadau relevant equation evidence remains partial article verification; EnergyPlus is engineering documentation. Full primary article signoffs remain0/31.

Next: derive and independently compare full-power cutoff/capacity event dispatch against this uniform v30 policy, quantify service/timestep differences, then decide whether another Stateflow version is justified.
