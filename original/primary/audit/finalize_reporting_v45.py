"""Seal the scoped energy-report release and append scheduler handoff ledgers."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import hashlib, json, sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(path,value):
    assert not path.exists(),path
    path.write_text(value if isinstance(value,str) else json.dumps(value,indent=2)+'\n',encoding='utf-8')
def main():
    folder=(ROOT/Path(sys.argv[1])).resolve();assert folder.is_relative_to(ROOT/'results')
    report=json.loads((folder/'reporting_v45.json').read_text())
    qa_path=sorted(folder.glob('independent_QA_v45_*.json'))[-1];qa=json.loads(qa_path.read_text())
    assert report['summary']['harness_failed']==qa['actual_failed']==qa['reviewer_selfchecks_failed']==0
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');now=datetime.now(timezone.utc).isoformat()
    rel=lambda p:str(p.relative_to(ROOT)).replace('\\','/')
    model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx'
    assert sha(model)==json.loads((ROOT/'STATUS_stateflow_v42.json').read_text())['model_sha256']
    baseline=json.loads((folder/'preservation.json').read_text())
    assert all((ROOT/x['path']).stat().st_size==x['bytes'] and sha(ROOT/x['path'])==x['sha256'] for x in baseline)
    next_task=("Create an additive annual reporting adapter/pipeline (preserve run_experiment_v2, run_sensitivity_v2, "
       "run_uncertainty_v3, historical CSVs and accepted v42). Map legacy actual HP_Heat_Used_MW to v45 HP_Heat_MW, "
       "derive HP_Direct_MW=HP_Heat_Used_MW-Storage_Charge_MW, and require explicit Unmet_Heat_MW from "
       "simulate_system_v13 or a newer finite-backup dispatch. Produce a fresh finite-backup period experiment "
       "with explicit durations, integrated COP, nonboiler delivery and service shortfall. Audit gas-baseline "
       "economics/CO2 at equal supplied service before claiming savings; unmet demand must not become avoided fuel. "
       "Do not relabel nonboiler heat as source-attributed ERF or fill absent pump/fan loads with assumptions. "
       "Upstream62 equipment calibration remains blocked until primary supplement/map/domain data are acquired.")
    limitations=[
      'Scoped reporting API acceptance; legacy compute_metrics/compute_metrics_v2 and annual consumers remain unchanged and require migration.',
      'Synthetic engineering fixtures; six independent one-interval saved-model cases and four reporting fixtures, not an annual profile or measured data.',
      'Same-agent independent Fraction algorithms and mutation selfchecks, not independent personnel.',
      'No new SLX or controller correction; normal-mode saved v42 and its prior acceptance remain preserved. This run exercises state entries; transition/dwell acceptance is inherited from v42.',
      'HP electricity includes active HP work only; pump/fan/standby/network loads and their thermal destinations remain unspecified.',
      'Nonboiler delivery contains compressor heat and possible initial TES inventory; no source-attributed waste-heat/ERF claim, equal-service economic/CO2 correction or annualization.',
      'Initial sandbox startup failure, first harness 53-pass/3-fail policy-diagnostic mismatch, and first independent QA singleton-JSON-shape failure retained. Corrected harness reran in a fresh directory; production function unchanged after first simulation.',
      'Inherited Stateflow formal-argument shadow warnings retained. Extreme/subnormal reporting ratios/integration not certified by ordinary-scale fixtures.',
      'Primary signoffs remain 0/31; upstream equipment calibration, article replication and physical validation remain open.'
    ]
    breakdown=Counter(c['kind'] for c in qa['checks'] if c['passed'])
    status=dict(version='0.45',timestamp_utc=now,inherits='STATUS_v44.json',stateflow_inherits='STATUS_stateflow_v42.json',
        checkpoint='Finite-backup delivery and integrated heating-COP reporting repair',
        result='PASS_SCOPED_ENERGY_REPORT_API_LEGACY_CONSUMER_MIGRATION_OPEN',model_version='0.42',
        new_model=False,model_executed_this_run=True,saved_model=rel(model),model_sha256=sha(model),
        production_reporting_api='matlab/+dchr/compute_energy_metrics_v45.m',result_directory=rel(folder),
        independent_qa=rel(qa_path),matlab_version=report['metadata']['matlab_version'],
        stateflow_version=report['metadata']['stateflow_version'],stateflow_license_observed=True,
        fresh_saved_model_scenarios=6,six_modes_executed=True,reporting_fixtures=4,
        harness_passed=report['summary']['harness_passed'],harness_failed=0,matlab_batch_exit_code=0,
        successful_receipts=qa['successful_receipts'],runtime_reporting_rejections=12,
        independent_actual_passed=qa['actual_passed'],independent_actual_failed=0,
        independent_breakdown=dict(breakdown),reviewer_selfchecks_passed=4,reviewer_selfchecks_failed=0,
        max_independent_balance_residual_MWh=qa['max_independent_balance_residual_MWh'],
        preserved_artifacts=len(baseline),legacy_unmet_credit_fixture_MWh=3,
        two_interval_integrated_heating_COP=2.4,two_interval_heat_weighted_diagnostic_COP=8/3,
        new_api_defect_repaired=True,legacy_consumers_repaired=False,full_primary_signoffs=0,total_sources=31,
        primary_article_replication=False,independent_physical_validation='NOT_TESTED',limitations=limitations,next=next_task)
    write(ROOT/'STATUS_v45.json',status)
    results=f'''# Energy-reporting boundary results — v45

{now}. PASS_SCOPED_ENERGY_REPORT_API; legacy consumer migration OPEN.
Evidence folder: `{rel(folder)}`. QA: `{rel(qa_path)}`.
Accepted saved model remains 0.42; original prototype and all prior models preserved.

Fresh MATLAB {report['metadata']['matlab_version']} / observed Stateflow license:
six saved-v42 cases execute IDLE, HEAT_RECOVERY, STORAGE_CHARGE,
STORAGE_DISCHARGE, BACKUP and UNMET_DEMAND. MATLAB 62 PASS / 0 FAIL, with
12 actual new reporting-domain rejections. v30 numerical reference agrees on
physical ports/states and COP; OFF supervisor request semantics are separately
documented rather than asserted equivalent. Numeric CSV, original SimulationOutput
MATs and independent saved-MAT reopen are retained.

| Fixture | Demand MWh | Boiler MWh | Unmet MWh | Actual nonboiler delivery MWh | Legacy reuse MWh |
|---|---:|---:|---:|---:|---:|
| Insufficient heat | 5 | 2 | 3 | 0 | 3 |
| TES charge | 1 | 0 | 0 | 1 | 1 |
| TES discharge from initial inventory | 2 | 0 | 0 | 2 | 2 |

Both historical report functions count the finite-backup shortfall as reused
heat. `compute_energy_metrics_v45` instead integrates explicit direct and TES
discharge ports, reports unmet heat separately and verifies closure.
Two actual MATLAB reporting intervals (4 MW heat/1 MW electric and 8/4 for one
hour each) give integrated heating COP 2.4 versus heat-weighted diagnostic
2.6666666666666665. Unequal durations 0.25 h / 2 h give 68/33. The legacy
mean_cop equals the diagnostic. With no HP work, heating COP is undefined;
initial TES delivery does not create HP COP. No system COP/auxiliary load is invented.

Independent Fraction equations, segment first laws/ports, duration partition,
numeric trace integration, v30 reference, original MAT reopen, SLX chart archive,
receipts, source snapshots and preservation: 688 PASS / 0 FAIL. Maximum
independent first-law residual is 0 MWh for these lossless synthetic fixtures.
Separate reviewer corruptions: 4 detected / 0 missed. {len(baseline)} baseline
artifacts preserve recorded bytes/hashes. These are independent algorithms
run by the same agent; no independent personnel or physical validation is claimed.

Retained failed attempts: sandbox MATLAB startup exit1; first execution
53 PASS / 3 FAIL because the harness compared v30 requested demand against
v42 OFF supervisor request; fresh execution repaired the harness comparison
while preserving every physical-port check and adding COP checks. First
independent review 686 PASS / 1 FAIL was a saved-spec singleton-matrix JSON
serialization shape check; normalization is restricted to known 1x5 inputs,
then all numeric values/other fields are compared exactly. No production
metric function or saved model changed in response to these harness errors.

Limitations: short synthetic fixtures, active HP-only electrical boundary,
unknown initial-inventory heat provenance, inherited Stateflow shadow warnings,
ordinary numerical scale; no primary equation signoff/calibration, economics
repair, source-attributed ERF, article replication or measured validation.
Existing annual consumers still call the old report functions. Their ERE,
screening LCOH and claimed economics need explicit migration/boundary review.

Next actionable task: {next_task}
Stop this coherent run; handoff recorded in STATUS_v45 and the progress ledger.
'''
    write(ROOT/'audit/Reporting_boundary_results_v45.md',results)
    stage=f'''# v45 energy-reporting handoff

{now}. Scoped additive reporting API PASS; legacy consumer migration OPEN.
Saved model 0.42 executed afresh in six required modes; no new SLX.
MATLAB 62/0; 12 reporting faults rejected; independent actual QA 688/0;
separate reviewer mutations 4/0. Nonboiler delivery excludes unmet heat;
integrated HP heating COP is distinct from the heat-weighted diagnostic.
{len(baseline)} baseline artifacts preserved. Physical validation/calibration
and full primary signoffs (0/31) remain open.

Evidence: STATUS_v45.json; audit/Reporting_boundary_derivation_v45.md;
audit/Reporting_boundary_results_v45.md; {rel(folder)}; {rel(qa_path)}.

Next actionable task: {next_task}
Run complete; stop with this handoff.
'''
    write(ROOT/'MASTER_STAGEBOARD_v45.md',stage)
    progress=f'''

## {now} — v45 finite-backup delivery and heating-COP report repair

Read latest STATUS/stageboards, acceptance, research frontier, progress and
production/reporting code before edits. Confirmed actual versioned Stateflow
v42 already has executed implementation acceptance; preserved it and ran fresh
six-mode reporting fixtures. Followed v44 annual-reporting boundary handoff.

Deliverable: additive `matlab/+dchr/compute_energy_metrics_v45.m`, explicit
period-duration/actual HP/delivered/unmet energy API, integrated heating COP and
separately named arithmetic diagnostic. Mathematical closure proves old demand
minus boiler credits unmet heat; actual fixture reproduces 3 MWh false reuse.
Actual two-interval MATLAB fixture gives integrated COP2.4 vs diagnostic8/3.
No inferred auxiliary loads, source-attributed ERF or annualization.

Pass/fail: fresh saved-v42 six modes and v30 physical reference, MATLAB62/0;
12 actual reporting-domain rejections. Independent Fraction/trace/first-law,
MAT reopen/SLX/source/receipt/preservation QA688/0; separate reviewer mutations
4/0. {len(baseline)} baseline hashes/sizes preserved; residual0 in lossless fixtures.
Retained sandbox startup failure, first MATLAB53/3 request-diagnostic harness
mismatch and first QA686/1 singleton-JSON-shape mismatch. Fixed only new harness/
reviewer comparison and reran MATLAB in a new directory; API/model unchanged.
Timestamped console logs, receipts, failed evidence and reviewer snapshots saved.

Files created: compute_energy_metrics_v45.m; run_reporting_v45.m and
export_reporting_v45.m; audit preparation/launcher/verifier/finalizer;
Reporting_boundary_derivation/results_v45.md; STATUS_v45.json and
MASTER_STAGEBOARD_v45.md; versioned result folders/specs/snapshots/numeric CSV/
SimulationOutput MAT/report JSON/QA and timestamped logs/receipts/manifests.
Only progress and acceptance ledgers appended; accepted v42/HPv40 preserved.

Remaining: existing annual consumers still use historical report functions;
economics/CO2 equal-service baseline and source attribution unresolved;
auxiliary electricity/thermal destinations unspecified; synthetic short periods,
same-agent independent algorithms, inherited shadow warnings, no primary-paper
replication or physical validation. Full signoffs0/31. No Jarvice/unrelated files,
settings, scheduled tasks, agent runner, secrets or external publication touched.

Next actionable task: {next_task}
Evidence: {rel(folder)}; {rel(qa_path)};
audit/Reporting_boundary_results_v45.md. Stop after this coherent run/handoff.
'''
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:f.write(progress)
    with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:
        f.write(f'\n\n## Energy-reporting checkpoint — {now} / v45\n\n'
                'Saved v42 executed afresh in all six modes; no controller/new-SLX change.\n'
                'Additive energy-report API passes MATLAB62/0 and independent688/0, with\n'
                '12 reporting rejections and four separate reviewer mutations detected.\n'
                'Legacy unmet reuse credit reproduced; new API excludes unmet and separates\n'
                'integrated heating COP from arithmetic diagnostic. Historical annual consumers\n'
                'remain open migration work. STATUS_v45.json and reporting derivation/results\n'
                'are authoritative. Physical validation/primary calibration remain open.\n')
    paths=set(folder.glob('*'));paths={p for p in paths if p.is_file()}
    paths.update(p for p in (folder/'source_snapshot').glob('*') if p.is_file())
    paths.update(p for p in (folder/'qa_source').rglob('*.py'))
    for pat in ['audit/*reporting*v45*','audit/Reporting*v45*','automation/logs/*reporting*v45*']:
        paths.update(p for p in ROOT.glob(pat) if p.is_file())
    paths.update(ROOT/p for p in ['STATUS_v45.json','MASTER_STAGEBOARD_v45.md','matlab/+dchr/compute_energy_metrics_v45.m',
        'matlab/simulink/run_reporting_v45.m','matlab/simulink/export_reporting_v45.m'])
    manifest=dict(version='0.45',timestamp_utc=now,files=[dict(path=rel(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(paths)])
    manifest_path=ROOT/'audit'/('Reporting_manifest_v45_'+stamp+'.json');write(manifest_path,manifest)
    print(json.dumps(dict(status='STATUS_v45.json',result_directory=rel(folder),manifest=rel(manifest_path),sealed_artifacts=len(paths),baseline_artifacts=len(baseline)),indent=2))
if __name__=='__main__':main()
