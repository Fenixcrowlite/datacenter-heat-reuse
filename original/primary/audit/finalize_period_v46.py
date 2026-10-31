"""Finalize only after executed MATLAB and independent QA acceptance."""
from pathlib import Path
from datetime import datetime, timezone
import collections, csv, hashlib, json, sys
ROOT=Path(__file__).resolve().parents[1]
folder=(ROOT/Path(sys.argv[1])).resolve();assert folder.is_relative_to(ROOT/'results')
report=json.loads((folder/'period_v46.json').read_text());summary=report['summary']
qa_path=sorted(folder.glob('independent_QA_v46_*.json'))[-1];qa=json.loads(qa_path.read_text())
assert summary['harness_failed']==qa['actual_failed']==qa['reviewer_selfchecks_failed']==0
assert qa['successful_receipts'] and report['metadata']['stateflow_license_test']
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');now=datetime.now(timezone.utc).isoformat()
def rel(p):return p.relative_to(ROOT).as_posix()
def write_new(p,value):
    assert not p.exists(),p;p.write_text(value,encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
next_task=('Audit annual v13 HP feasibility and source-limited maximality before extending annual claims to v42: '
    'simulate_system_v13 delegates to v2, whose potential HP heat uses nominal COP before '
    'part_load_cop reduces COP; independently test actual HP_Source_Used_MW against '
    'HX_Heat_to_HP_MW and solve the actual-COP source constraint in fresh saved annual evidence. Derive feasibility/maximality bounds and reproduce '
    'a counterexample or prove the tested domain. Preserve annual/v42/v46 evidence, then '
    'choose an additive verified-component annual dispatch adapter. Do not claim the v13 '
    'annual results are an accepted annual Stateflow execution. Equipment-specific primary '
    'calibration remains blocked; initial/terminal TES inventory and auxiliary loads remain unpriced.')
limitations=[
    'Scoped additive reporting pipeline; historical experiment/sensitivity/uncertainty consumers remain preserved and are not silently migrated.',
    'Actual saved Stateflow v42 executed in six individual fixtures plus a synthetic 48-hour transition sequence; annual runs use the older finite-backup v13 MATLAB reference, not annual Stateflow.',
    'Same-agent independent rational and 50-digit Decimal algorithms; not independent personnel or measured physical validation.',
    'Ideal gas-only comparator is sized for the same actually delivered profile; it is not a constrained-capacity gas-only simulation or a full-demand service guarantee.',
    'Active HP/boiler operational accounting only; CAPEX, pump/fan/standby/network loads, source attribution and initial/terminal inventory value are unspecified.',
    'Inherited prices, emission factors, boiler efficiency, weather and dispatch fixtures are synthetic engineering assumptions; no market quotation, equipment calibration or primary-paper replication.',
    'Annual v13 inherits nominal-COP potential then part-load adjustment and loss-first TES. Its HP source feasibility remains an audit item; physical equivalence with accepted v42 is not claimed.',
    'MATLAB sandbox startup failure and first 74-pass/1-fail fixture run retained; first period lacked HEAT_RECOVERY because surplus caused charging. Only new fixture source input changed before fresh rerun. Reviewer Fraction/text and NaN-equality errors repaired without interpreter settings. Independent QA then caught an actual multirow MAT export reshape defect; corrected reader reran only MAT reopening into a fresh subdirectory. Failed QA and incorrect original exports remain preserved; original SimulationOutputs/report numeric traces were unchanged.',
    'Inherited Stateflow argument-shadow warnings remain. Extreme/subnormal report integration domains are not certified. Full primary signoffs remain 0/31.'
]
status=dict(version='0.46',timestamp_utc=now,inherits='STATUS_v45.json',stateflow_inherits='STATUS_stateflow_v42.json',
    checkpoint='Additive finite-backup period/annual reporting and equal delivered-service comparison',
    result='PASS_SCOPED_PERIOD_PIPELINE_ANNUAL_PHYSICAL_VALIDATION_OPEN',model_version='0.42',new_model=False,
    model_executed_this_run=True,saved_model='matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx',
    model_sha256=sha(ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx'),result_directory=rel(folder),
    independent_qa=rel(qa_path),matlab_version=report['metadata']['matlab_version'],
    stateflow_version=report['metadata']['stateflow_version'],stateflow_license_observed=bool(report['metadata']['stateflow_license_test']),
    saved_model_scenarios=summary['saved_model_scenarios'],saved_model_intervals=summary['saved_model_intervals'],
    actual_period_h=report['stateflow'][-1]['report']['energy']['reported_period_h'],
    annual_reference_scenarios=summary['annual_reference_scenarios'],annual_reference_intervals=summary['annual_reference_intervals'],
    six_modes_executed=True,actual_period_mode_transitions=qa['period_mode_transitions'],
    harness_passed=summary['harness_passed'],harness_failed=0,matlab_batch_exit_code=0,
    reporting_runtime_rejections=summary['report_domain_rejections'],
    independent_actual_passed=qa['actual_passed'],independent_actual_failed=0,
    independent_breakdown=dict(collections.Counter(x['kind'] for x in qa['checks'])),
    reviewer_selfchecks_passed=qa['reviewer_selfchecks_passed'],reviewer_selfchecks_failed=0,
    max_independent_balance_residual_MWh=qa['max_independent_balance_residual_MWh'],
    successful_receipts=qa['successful_receipts'],mat_reopen_directory=qa['mat_reopen_directory'],preserved_artifacts=len(json.loads((folder/'preservation.json').read_text())),
    legacy_consumers_changed=False,full_primary_signoffs=0,total_sources=31,primary_article_replication=False,
    independent_physical_validation='NOT_TESTED',limitations=limitations,next=next_task)
write_new(ROOT/'STATUS_v46.json',json.dumps(status,indent=2)+'\n')
rows=[]
for item in [report['stateflow'][-1]]+report['annual']:
    m=item['report'];e=m['energy'];rows.append(dict(scenario=item['id'],period_h=e['reported_period_h'],
        demand_MWh=e['heat_demand_MWh'],delivered_MWh=e['total_delivered_MWh'],nonboiler_MWh=e['nonboiler_delivered_MWh'],
        boiler_MWh=e['gas_heat_MWh'],unmet_MWh=e['unmet_heat_MWh'],heating_COP=e['hp_heating_COP_integrated'],
        equal_service_opex_difference_EUR=m['equal_delivered_service_opex_difference_EUR'],
        equal_service_CO2_difference_t=m['equal_delivered_service_CO2_difference_t'],
        legacy_unmet_opex_credit_EUR=m['unmet_baseline_opex_credit_EUR'],legacy_unmet_CO2_credit_t=m['unmet_baseline_CO2_credit_t']))
csv_path=folder/'experiment_summary_v46.csv';assert not csv_path.exists()
with csv_path.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
table='| Scenario | Hours | Demand MWh | Nonboiler MWh | Boiler MWh | Unmet MWh | Integrated HP COP | False full-demand cost credit EUR |\n|---|---:|---:|---:|---:|---:|---:|---:|\n'
for r in rows:table+='| '+r['scenario']+' | '+' | '.join(f"{r[k]:.9g}" for k in ['period_h','demand_MWh','nonboiler_MWh','boiler_MWh','unmet_MWh','heating_COP','legacy_unmet_opex_credit_EUR'])+' |\n'
text=f'''# Finite-backup period reporting results — v46

{now}. Scoped reporting pipeline PASS. Accepted actual model remains v42;
no SLX/controller change. Evidence: `{rel(folder)}`; QA: `{rel(qa_path)}`.

MATLAB {status['matlab_version']}, observed Stateflow license. Fresh saved-v42:
seven scenarios / 54 macro intervals, including six required single-case modes
and a 48-hour sequence with {qa['period_mode_transitions']} observed thermal-mode
transitions. The saved segment trace independently closes TES ODE, service,
capacity/cutoff and first laws. Separate annual v13 reference: three scenarios,
26,280 intervals. The annual reference is not an annual Stateflow simulation.

MATLAB {summary['harness_passed']} PASS / 0 FAIL; 12 actual reporting-domain
rejections. Independent actual QA {qa['actual_passed']} PASS / 0 FAIL; four
separate reviewer mutations detected. Max independent segment first-law
residual {qa['max_independent_balance_residual_MWh']:.12g} MWh.

{table}
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
SLX archive, source snapshots, receipts and {status['preserved_artifacts']}
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
corrected MAT reader reopened original evidence into `{qa['mat_reopen_directory']}`
with a fresh batch receipt. Original incorrect exports and failed QA are retained;
the simulation/report traces did not change and the plant was not rerun for this
export correction. Inherited warnings remain.

Limitations:

'''+''.join('- '+x+'\n' for x in limitations)+f'\nNext actionable task: {next_task}\nRun complete; stop with this handoff.\n'
write_new(ROOT/'audit/Period_reporting_results_v46.md',text)
stage=f'''# v46 period reporting handoff

{now}. Additive finite-backup period pipeline PASS; annual physical validation OPEN.
Saved Stateflow v42 freshly executes 54 intervals/all six modes and a 48-hour
transition sequence; no new SLX. Three annual v13 reference cases execute
26,280 intervals with explicit unmet heat. Actual versus potential schema
mapping, integrated heating COP and equal delivered-service cost/CO2 validated.

MATLAB {summary['harness_passed']}/0;12 reporting rejections; independent actual
{qa['actual_passed']}/0; four reviewer mutations detected. Preserved baselines.
Independent QA is same-agent algorithms; physical validation/calibration and
full primary signoffs 0/31 remain open. Historical consumers are preserved.

Evidence: STATUS_v46.json; audit/Period_reporting_derivation_v46.md;
audit/Period_reporting_results_v46.md; {rel(folder)}; {rel(qa_path)}.

Next actionable task: {next_task}
Run complete; stop with this handoff.
'''
write_new(ROOT/'MASTER_STAGEBOARD_v46.md',stage)
progress=f'''

## {now} — v46 additive period/annual reporting migration and equal-service accounting

Read STATUS_v45, stageboard, STATEFLOW_ACCEPTANCE, research frontier, progress,
v42 builder/controller, v45 reporting and annual v13/v2 code before edits.
Immediate actual versioned Stateflow acceptance already recorded; preserved
v42 and ran it afresh. Followed the actionable v45 reporting pipeline handoff.

Delivered explicit schema adapter and operational comparison: actual HP heat,
mandatory unmet demand, supplied-service gas comparator and separate shortfall
credit diagnostic. Fresh actual v42 six modes + 48-hour transition sequence;
three 8760-hour synthetic finite-backup v13 reference cases. No annual Stateflow
or physical-equivalence claim. Mathematical derivation and independent evidence
QA retained. Annual quantities are actual 8760 interval integrals; short periods
are not annualized. Economic constants remain demonstration assumptions.

Pass/fail: MATLAB {summary['harness_passed']}/0;12 reporting rejections;
independent actual {qa['actual_passed']}/0;four reviewer mutations detected.
Independent rational reporting/Decimal TES, 26,280 reference recurrence steps,
MAT reopening, saved-model modes/transitions, CSV integration, receipts,
snapshots/archive and {status['preserved_artifacts']} preserved baseline hashes.
First sandbox startup failure and first 74/1 period-fixture failure retained;
fixed only new source fixture, then fresh complete execution. Independent QA
caught and repaired multirow MAT export reshaping with a focused saved-MAT-only
rerun in a new directory; incorrect exports/failed QA preserved. Fraction-text
and NaN-comparison reviewer defects also retained/repaired. Inherited warnings.

Files created: matlab/+dchr/adapt_dispatch_energy_v46.m,
compute_service_comparison_v46.m; matlab/run_period_experiment_v46.m,
export_period_evidence_v46.m; audit/prepare_period_v46.py, run_period_v46.ps1,
verify_period_v46.py, finalize_period_v46.py, check_period_release_v46.py;
derivation/results, STATUS_v46.json, MASTER_STAGEBOARD_v46.md; versioned results
spec/preservation/snapshots/SimulationOutput and annual MATs/ports/segment CSVs/
summary/reexport/QA, timestamped logs/receipts/manifest. Only shared progress and
acceptance ledgers appended. No Jarvice/unrelated files, settings, scheduled
tasks, agent runner, secrets or external publication touched.

Limitations: {('; '.join(limitations))}

Next actionable task: {next_task}
Evidence: {rel(folder)}; {rel(qa_path)}. Stop this coherent run with handoff.
'''
with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:f.write(progress)
with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:
    f.write(f'''\n\n## Additive period-reporting checkpoint — {now} / v46

Saved v42 executed afresh in 54 intervals/six modes with 48-hour transitions;
no controller or SLX change. Separate annual v13 MATLAB reference executes
26,280 intervals. MATLAB {summary['harness_passed']}/0 and independent actual
{qa['actual_passed']}/0; 12 reporting rejections and four reviewer mutations.
Actual-energy adapter and equal delivered-service cost/CO2 comparator PASS.
Annual reference physical equivalence/calibration and historical consumer
migration remain open; no annual Stateflow acceptance claimed. STATUS_v46.json
and audit/Period_reporting_results_v46.md are authoritative.
''')
paths=set()
for p in folder.rglob('*'):
    if p.is_file() and 'local_build' not in p.parts:paths.add(p)
for pattern in ['matlab/*v46.m','matlab/+dchr/*v46.m','audit/*v46*','STATUS_v46.json','MASTER_STAGEBOARD_v46.md','automation/logs/period_v46_*.log','automation/logs/period_independent_v46_*.log']:
    paths.update(p for p in ROOT.glob(pattern) if p.is_file())
manifest=dict(version='0.46',timestamp_utc=now,files=[dict(path=rel(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(paths)])
manifest_path=ROOT/'audit'/('Period_manifest_v46_'+stamp+'.json');write_new(manifest_path,json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(status='FINALIZED',result_directory=rel(folder),qa=rel(qa_path),manifest=rel(manifest_path),sealed_files=len(paths)),indent=2))
