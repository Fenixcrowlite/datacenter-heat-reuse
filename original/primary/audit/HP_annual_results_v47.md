# Annual HP capability audit results — v47

2026-10-10T18:16:51.034755+00:00. Annual-reference nonmaximal HP dispatch defect CONFIRMED OPEN.
No new model/controller release. Actual accepted model remains v42.
Evidence: `results/hp_annual_v47_20261010T181354_797146Z`. Independent QA: `results/hp_annual_v47_20261010T181354_797146Z/independent_QA_v47_20261010T181530_627876Z.json`.

Fresh MATLAB 26.1.0.3346908 (R2026a) Update 5: 8760 annual v13 intervals, 72 component
vectors and eight actual saved-v42 scenarios/all six modes. MATLAB
193 PASS / 0 FAIL. Independent actual checks 36312
PASS / 0 FAIL; four separate synthetic reviewer mutations detected.
Stateflow license was observed. `ver('Stateflow')` returned an empty array;
no standalone toolbox-version value is fabricated. Inherited argument-shadow
warnings are present. Initial sandbox startup failure exit1 is retained;
the identical authorized local batch completed outside the sandbox exit0.

The annual trace has zero source-feasibility violations but
3925 nonmaximal-output intervals. Lower operating
COP needs MORE compressor work and LESS source extraction for fixed output;
the nominal-COP potential is conservative in the documented domain. Analytic
source-constraint inversion identifies additional capability at that same
starting inventory/request. Static gap 220.771579093
MWh; largest interval gap 0.081004677718 MW.
These are diagnostics, not annual delivery or economic savings.

Concrete first-interval counterexample (01-Jan-2026 00:00:00): source
6.50562204447 MW; legacy output 8.71802428432 MW;
source unused 0.0494898323496 MW. Independent maximum is
8.78348050244 MW, a 0.065456218126 MW
gap while the historical trace supplies 2 MW
boiler heat and records 3.92544206902 MW unmet heat.

Matched HP comparisons use no charging/discharging and constant input, so TES
policy does not explain the output gap. Both actual saved-v42 outputs match
the independent 60-digit analytic root:

| Source MW | Legacy maximum MW | Saved v42 MW | Independent analytic maximum MW | Gap MW |
|---:|---:|---:|---:|---:|
| 1 | 1.29308937132 | 1.32280122781 | 1.32280122781 | 0.0297118564899 |
| 6 | 7.75853622794 | 7.82420364172 | 7.82420364172 | 0.0656674137791 |

Independent QA reopens original annual/probe/SimulationOutput MATs and compares
all exported numeric CSV bytes and report JSON. Annual source/nominal/operating
COP, request, HP potential/output, service and TES recurrence are independently
recomputed. Eight actual segment traces pass ODE, HP/source/service allocation,
SOC/port bounds, mode authority, interval partition and first-law checks.
Maximum independent saved-segment residual
2e-15 MWh. All
849 preserved artifact hashes pass, as do accepted
SLX hash/archive checks and execution snapshots. Reviewer mutations of output,
source use, penalty and nominal COP are detected separately from actual checks.

No primary paper equation or empirical map is claimed. This run resolves a
code-derived engineering assumption; source signoffs remain 0/31. Accepted v42
was tested, not rebuilt or overwritten. No Jarvice/unrelated files, settings,
scheduled tasks, agent runner, secrets or external publication touched.

Limitations:

- This checkpoint confirms an annual-reference nonmaximal HP dispatch defect; no corrected annual controller or new SLX is accepted.
- Fresh saved v42 execution is eight single-interval scenarios/all six modes, not annual Stateflow or a new transition-coverage campaign.
- Source-feasibility proof is restricted to nominal COP >= minimum >1, nonnegative source/request, valid capacity and penalty in [0,1). Arbitrary legacy configs are not certified.
- Closed-form comparisons restrict to a=C0*(1-r)>=cop_min: legacy upward COP clamp differs from v40 operating cutoff outside this domain.
- 220.77157909264 MWh is static extra HP capability on the preserved legacy starting-inventory/request sequence; it is not realizable annual delivered heat, savings or a revised unmet-demand result.
- Annual v13 retains loss-first lumped TES, reservoir temperature proxies and synthetic weather/load/economic assumptions. Physical equivalence with saved v42 is not claimed.
- Independent QA uses same-agent 60-digit Decimal analytic roots/ODE expressions, not independent personnel or measured physical validation.
- Inherited Stateflow argument-shadow warnings and one sandbox MATLAB startup failure are retained. No user settings or runtime configuration changed.
- No new literature claim or source signoff: code-derived engineering equations only, full primary signoffs remain 0/31. Equipment map calibration, auxiliaries and inventory value remain unspecified.

Next actionable task: Implement additive simulate_system_v48 using verified heat_pump_step_v40 for actual source-constrained HP output, with demand plus admissible TES charge request. Preserve v13/v2, saved Stateflow v42 and v46/v47 evidence. Initially keep the legacy TES loss-first law explicitly labelled to isolate the HP dispatch correction; do not claim equivalence to v42 exact/event TES. Recompute the entire 8760-interval dispatch and inventory trajectory, not a static capability-gap credit. Verify source limits, HP/request maximality, TES recurrence, boiler cap, unmet heat and first-law closure independently. Compare matched constant-input/no-storage cases with actual saved v42 execution; include zero-penalty compatibility and operating-cutoff domain distinctions. Feed corrected actual ports to v45/v46 period reports and equal-delivered-service comparison. Only then plan an actual annual Stateflow adapter/execution. Equipment-specific primary calibration, auxiliary loads and inventory valuation remain open.

Run complete; stop with this handoff.
