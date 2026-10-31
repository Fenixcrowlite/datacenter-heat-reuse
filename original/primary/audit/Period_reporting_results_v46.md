# Finite-backup period reporting results — v46

2026-10-10T18:06:57.219122+00:00. Scoped reporting pipeline PASS. Accepted actual model remains v42;
no SLX/controller change. Evidence: `results/period_v46_20261010T180131_369483Z`; QA: `results/period_v46_20261010T180131_369483Z/independent_QA_v46_20261010T180613_325010Z.json`.

MATLAB 26.1.0.3346908 (R2026a) Update 5, observed Stateflow license. Fresh saved-v42:
seven scenarios / 54 macro intervals, including six required single-case modes
and a 48-hour sequence with 47 observed thermal-mode
transitions. The saved segment trace independently closes TES ODE, service,
capacity/cutoff and first laws. Separate annual v13 reference: three scenarios,
26,280 intervals. The annual reference is not an annual Stateflow simulation.

MATLAB 75 PASS / 0 FAIL; 12 actual reporting-domain
rejections. Independent actual QA 2222 PASS / 0 FAIL; four
separate reviewer mutations detected. Max independent segment first-law
residual 9e-15 MWh.

| Scenario | Hours | Demand MWh | Nonboiler MWh | Boiler MWh | Unmet MWh | Integrated HP COP | False full-demand cost credit EUR |
|---|---:|---:|---:|---:|---:|---:|---:|
| saved_v42_48h | 48 | 112 | 58.2730276 | 29.7269724 | 24 | 4 | 1333.33333 |
| annual_v13_cap_0 | 8760 | 59429.9768 | 49524.7577 | 0 | 9905.21907 | 4.61340345 | 550289.948 |
| annual_v13_cap_2 | 8760 | 59429.9768 | 49524.7577 | 5142.14202 | 4763.07705 | 4.61340345 | 264615.392 |
| annual_v13_cap_20 | 8760 | 59429.9768 | 49524.7577 | 9905.21907 | 0 | 4.61340345 | 0 |

The additive adapter selects HP_Heat_Used_MW as actual heat, computes direct
heat after charging, and requires explicit unmet heat. The factor-ten potential
trap with durations 0.25/2 hours integrates 17 MWh actual HP output and COP68/33.
The inherited v45 integration distinguishes heating COP from its arithmetic
diagnostic. Missing shortfall, unknown schema, impossible charge allocation,
invalid economic domains, missing actual heat, nonclosure and overflow reject.

Using full demand for a gas baseline credits shortfall as fuel avoidance;
the new baseline uses exactly delivered service. Nonboiler heat, HP work,
service shortfall and comparison differences are explicit. See the summary CSV
for operational cost/emission differences, including signs. Boiler-cap changes
do not change the older v13 HP/TES nonboiler dispatch. They change delivered
service and unmet heat; that is not an equal-full-demand design comparison.

Original SimulationOutputs and annual out/config/input/report MATs are saved
and reopened; CSVs, port integration, independent annual dispatch recurrence,
SLX archive, source snapshots, receipts and 554
baseline artifacts pass QA. Tests used independent algorithms in the same
agent; no independent personnel or physical validation is claimed.

Failed evidence retained: sandbox startup exit1; first run 74 PASS/1 FAIL because
the intended period HP-only interval had surplus and charged. The new fixture's
source was reduced from 6 to 3 MW so constant COP 4 permits direct 4 MW without
charging, and the full pipeline reran in a fresh directory. Production adapter,
comparison and accepted model were unchanged. First reviewer failed converting
a large exact Fraction to text; preserving Fraction objects repairs that path
without changing interpreter settings. Off-state NaN equality needed exact CSV
comparison. That check then caught a real multirow export-helper reshape defect:
corrected MAT reader reopened original evidence into `results/period_v46_20261010T180131_369483Z/mat_reopen_v46_20261010T180555038Z`
with a fresh batch receipt. Original incorrect exports and failed QA are retained;
the simulation/report traces did not change and the plant was not rerun for this
export correction. Inherited warnings remain.

Limitations:

- Scoped additive reporting pipeline; historical experiment/sensitivity/uncertainty consumers remain preserved and are not silently migrated.
- Actual saved Stateflow v42 executed in six individual fixtures plus a synthetic 48-hour transition sequence; annual runs use the older finite-backup v13 MATLAB reference, not annual Stateflow.
- Same-agent independent rational and 50-digit Decimal algorithms; not independent personnel or measured physical validation.
- Ideal gas-only comparator is sized for the same actually delivered profile; it is not a constrained-capacity gas-only simulation or a full-demand service guarantee.
- Active HP/boiler operational accounting only; CAPEX, pump/fan/standby/network loads, source attribution and initial/terminal inventory value are unspecified.
- Inherited prices, emission factors, boiler efficiency, weather and dispatch fixtures are synthetic engineering assumptions; no market quotation, equipment calibration or primary-paper replication.
- Annual v13 inherits nominal-COP potential then part-load adjustment and loss-first TES. Its HP source feasibility remains an audit item; physical equivalence with accepted v42 is not claimed.
- MATLAB sandbox startup failure and first 74-pass/1-fail fixture run retained; first period lacked HEAT_RECOVERY because surplus caused charging. Only new fixture source input changed before fresh rerun. Reviewer Fraction/text and NaN-equality errors repaired without interpreter settings. Independent QA then caught an actual multirow MAT export reshape defect; corrected reader reran only MAT reopening into a fresh subdirectory. Failed QA and incorrect original exports remain preserved; original SimulationOutputs/report numeric traces were unchanged.
- Inherited Stateflow argument-shadow warnings remain. Extreme/subnormal report integration domains are not certified. Full primary signoffs remain 0/31.

Next actionable task: Audit annual v13 HP feasibility and source-limited maximality before extending annual claims to v42: simulate_system_v13 delegates to v2, whose potential HP heat uses nominal COP before part_load_cop reduces COP; independently test actual HP_Source_Used_MW against HX_Heat_to_HP_MW and solve the actual-COP source constraint in fresh saved annual evidence. Derive feasibility/maximality bounds and reproduce a counterexample or prove the tested domain. Preserve annual/v42/v46 evidence, then choose an additive verified-component annual dispatch adapter. Do not claim the v13 annual results are an accepted annual Stateflow execution. Equipment-specific primary calibration remains blocked; initial/terminal TES inventory and auxiliary loads remain unpriced.
Run complete; stop with this handoff.
