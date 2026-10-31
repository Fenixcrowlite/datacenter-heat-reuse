# Corrected annual HP dispatch results — v48

2026-10-10T18:28:37.571775+00:00. Scoped implementation acceptance PASS. The v47 nonmaximal-output
defect is repaired in additive `simulate_system_v48`; v13/v2 and all SLX baselines
remain preserved. Annual v48 is a MATLAB controller with legacy loss-first TES.
Accepted actual Stateflow remains v42, executed afresh for matched comparisons.
No new model or annual Stateflow acceptance is claimed.

Three complete 8760-hour trajectories were recomputed from the same seeded
weather/load inputs and zero starting TES. This is realized redispatch within
synthetic screening assumptions, not a sum of static capability credits.

| Boiler cap MW | Legacy unmet MWh | v48 unmet MWh | Unmet reduction MWh | Gas reduction MWh |
|---:|---:|---:|---:|---:|
| 0 | 9905.219073 | 9717.529710 | 187.689362 | 0.000000 |
| 2 | 4763.077051 | 4626.726758 | 136.350293 | 51.339070 |
| 20 | 0.000000 | 0.000000 | 0.000000 | 187.689362 |

All three trajectories produce HP heat 49809.816838 MWh.
Relative to the matching legacy run, HP heat increases
187.267843 MWh and HP electricity increases
42.511215 MWh. Finite boiler limits determine
how increased nonboiler delivery splits between reduced unmet demand and gas.
At 20 MW backup both controllers supply all demand; delivered-heat delta is
zero within aggregate CSV/report rounding (about 1e-9 MWh).

v45/v46 actual-port period reports and equal-delivered-service comparisons are
saved per scenario. Under inherited synthetic prices/emissions, the difference
of these comparator metrics is about EUR 6176.065293
and 33.623592 t CO2. At constrained backup the
two runs deliver different service amounts; these metric differences are not a
direct same-service comparison of the two controllers or market/calibration claims.

Validation: MATLAB 75/0 failures; 26,280 annual intervals
plus nine matched fixture intervals; 12 actual annual-domain rejections.
Actual saved-v42 execution: 10 scenarios, 63 intervals, 71 positive segments,
all six modes, 47 mode transitions in the 48-hour sequence. Three matched
no-storage cases verify source-limited output, zero-penalty compatibility and
the intentional operating-cutoff distinction. Independent 60-digit Decimal
root/inventory/ODE QA: 106795/0; four separate reviewer mutations
detected. Annual nonmaximal outputs: zero. Maximum independent first-law
residual: 1.0482e-13 MWh. MAT reopening,
CSV/report equality, saved SLX hash/CRC, 1100 preservation hashes and source
snapshots pass. Algorithmic independence is same-agent, not independent personnel.

Evidence: `results/annual_dispatch_v48_20261010T182553_348909Z`; `results/annual_dispatch_v48_20261010T182553_348909Z/independent_QA_v48_20261010T182722_145809Z.json`; receipts
`audit/Annual_dispatch_execution_v48_20261010T182602227Z.json`; `audit/Annual_dispatch_derivation_v48.md`.
Failed startup and first cutoff-fixture run remain in the earlier v48 result
folder and timestamped logs/receipts. The 4.0 cutoff fixture stayed ON because
operating COP was 4.0619156; changing its intended cutoff to 4.1 produced the
correct OFF case. No numerical traces from that run were overwritten.

Limitations:

- Annual v48 is MATLAB dispatch with retained legacy loss-first Euler TES, not an annual Stateflow execution or physical equivalence with saved v42.
- Saved v42 freshly executes 63 intervals/71 positive segments/all six modes and 47 transitions; no new SLX, controller, model workspace or accepted model hash is changed.
- Independent QA uses same-agent 60-digit Decimal closed-form roots and ODE/inventory algorithms, not independent personnel or measured physical validation.
- Results are synthetic engineering scenarios. Reservoir COP proxies, capture/HX factors, TES loss/efficiency, weather/load and prices/emissions have no equipment-specific primary calibration here.
- Operating-cutoff v40 intentionally differs from legacy upward COP clamp outside the matched domain; zero-penalty compatibility is tested on one matched no-storage fixture, not every legacy configuration.
- HP request-maximality is a greedy interval policy, not global economic optimality. No HP latch/dwell, TES temperature cutoff, hydraulics, network transient or active-port exact TES integration in the annual adapter.
- Initial/terminal inventory provenance/value, auxiliary electric loads, CAPEX and source-attributed waste heat remain unspecified. Comparisons use equal actually delivered service, not full-demand savings credit.
- Standard finite input fixtures are certified; extreme/subnormal annual arithmetic domains and alternate polynomial HP/disabled HX combinations beyond fixtures are not comprehensively certified.
- Initial sandbox MATLAB startup failure and first 74-pass/1-fail run are retained. The first cutoff fixture specified COP minimum 4 below operating COP 4.0619156; corrected to 4.1. No production controller repair was needed after that fixture failure. Inherited saved-Stateflow shadow warnings remain.
- No new primary-text claim, paper replication or source signoff; full primary signoffs remain 0/31. Historical consumers remain preserved.

Next actionable task: Design and test an additive annual saved-v42 input adapter with explicit TES temperature/cutoff parameters and HP hysteresis/dwell policy. Preflight all 8760 source/sink/delivery inputs against the actual model contract before running it; document unsupported regimes rather than inventing equipment calibration. Execute an initial multi-day sequence with independent port, event, inventory and report QA, then extend to actual annual execution if admissible. Compare exact/event TES with v48 loss-first traces as distinct policies; never relabel v48 MATLAB results as annual Stateflow. Primary equipment calibration, auxiliary loads and inventory valuation remain open.
