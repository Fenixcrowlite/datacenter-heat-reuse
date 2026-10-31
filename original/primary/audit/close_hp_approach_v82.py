"""Close a passing boundary experiment and append a precise local handoff."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal as D, localcontext
import csv, hashlib, json, sys, zipfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):
    with p.open('x',encoding='utf-8') as out:json.dump(v,out,indent=2);out.write('\n')
def matrix(v):return [v] if isinstance(v[0],(int,float)) else v
def write(p,s):
    with p.open('x',encoding='utf-8') as out:out.write(s)

def main(folder):
    report=json.loads((folder/'report.json').read_text())
    qa_path=sorted(folder.glob('independent_QA*.json'))[-1];qa=json.loads(qa_path.read_text())
    assert report['summary']['failed']==qa['summary']['failed']==0
    assert all(c['passed'] for c in qa['checks']+qa['reviewer_selfchecks']+qa['comparisons'])
    assert report['mode_coverage']==list(range(6)) and len(report['runs'])==42
    model=ROOT/'matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v80.slx'
    assert sha(model)==json.loads((ROOT/'STATUS_v81.json').read_text())['model_sha256']
    names=['IDLE','HEAT_RECOVERY','STORAGE_CHARGE','STORAGE_DISCHARGE','BACKUP','UNMET_DEMAND']
    with zipfile.ZipFile(model) as archive:
        chart_files=[n for n in archive.namelist() if n.startswith('simulink/stateflow/chart_') and n.endswith('.xml')]
        assert len(chart_files)==1
        chart=ET.fromstring(archive.read(chart_files[0]))
        labels=[(p.text or '').split('\n')[0] for p in chart.iter('P') if p.attrib.get('Name')=='labelString']
        assert all(labels.count(n)==1 for n in names)
    observations=json.loads((folder/'primary_observations.json').read_text())
    assert not observations['upstream_supplement_acquired'] and not observations['equipment_calibrated']
    assert observations['local_primary']['sha256']=='713d1ea564efacbb8813eafc474482292b167140e1b2f47d1e234d3db7302a6e'
    logs=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')]
    good=next(v for v in logs if v['exit_code']==0);log=Path(good['log_path']).read_text()
    assert 'HP_APPROACH_V82 PASS=128 FAIL=0 COMPLETE_RUNS=42' in log
    assert not any(s in log for s in ['Error in ','Fatal Startup Error','Warning:'])
    now=datetime.now(timezone.utc).isoformat();rel=folder.relative_to(ROOT).as_posix()
    intervals=sum(len(matrix(r['trace'])) for r in report['runs'])
    segments=sum(int(row[12]) for r in report['runs'] for row in matrix(r['trace']))
    events=sum(int(row[13]) for r in report['runs'] for row in matrix(r['trace']))
    totals=qa['reconstructed_totals'];selected=[]
    with localcontext() as ctx:
        ctx.prec=160
        for family in ['fixed_output','source_limited']:
            for e,h in [(1,1),(10,10)]:
                key=f'{family}_T30_e{e}_h{h}';t=totals[key]
                selected.append(dict(id=key,delivered_MWh=t['delivered_service'],
                    source_MWh=t['recovered_source'],compressor_MWh=t['compressor_work'],
                    unmet_MWh=t['unmet_demand'],heating_COP=str(D(t['hp_heat'])/D(t['compressor_work']))))
        base=totals['fixed_output_T30_e1_h1'];end=totals['fixed_output_T30_e10_h10']
        work_increase=(D(end['compressor_work'])/D(base['compressor_work'])-1)*100
        base2=totals['source_limited_T30_e1_h1'];end2=totals['source_limited_T30_e10_h10']
        service_increase=(D(end2['delivered_service'])/D(base2['delivered_service'])-1)*100
    next_task=('Acquire the reference62 primary supplement or inspect the author-group-linked '
        '2022 predecessor DOI 10.1016/j.applthermaleng.2022.118194 as separately labelled '
        'primary evidence. Do not substitute predecessor coefficients for the 2025 fit. '
        'Trace compressor electrical rating, refrigerant axes, admissible map domain and '
        'auxiliary thermal destinations before adding a separate explicit electrical-power '
        'capacity backend. Preserve accepted v80 and v81-v82 evidence; no repeated monitor tests '
        'without a new hypothesis.')
    limitations=[
        'Synthetic reduced constant-cooling-factor HP and ambient-reference TES; no equipment calibration, article replication, measured physical validation, annual or generated-code acceptance. Full primary signoffs remain 0/31.',
        'Checkpoint 0.82 is an executed sensitivity experiment; saved model remains 0.80, thermal kernel/trace schema 75 and reporting API 0.76. No new SLX or production equation change.',
        'Approach values, eta=0.5, source coefficient, temperature/glide and auxiliary settings are engineering assumptions. The 2025 commercial-device correlation supplement is not acquired.',
        'No independent compressor-electricity capacity is enforced. Increased source-limited condenser service at larger approaches comes from added compressor work, not extra waste heat. This is a model-boundary limitation, not a numerical dispatch defect.',
        'Independent QA is same-agent algorithmic independence: exact Fraction algebra and 120/160-digit exp/log trajectories call no production MATLAB solver. MATLAB reopens MAT for binary export; no independent personnel or independent MAT-parser claim.',
        'The 36 comparison schedules remain below the hot-water floor and contain no interior events. Six standard fixtures cover final modes. No general nonlinear/variable-source-map sensitivity is proved.',
        'Restricted startup, first batch JSON cell/struct failure, and first QA single-row-shape failures are retained. The reviewer shape repair is separately hash-sealed; production outputs, equations and tolerances were unchanged.'
    ]
    lines=[f'# Saved-Stateflow refrigerant approach experiment v82\n\nUTC {now}.',
        f'Preserved saved v80 actually executes 42 schedules / {intervals} held intervals / {segments} positive segments / {events} interior events. '
        f'MATLAB 128 PASS / 0 FAIL; independent equation/artifact QA {qa["summary"]["passed"]} PASS / 0 FAIL; '
        '48 monotonic comparisons and four separate reviewer self-checks PASS. All six required final modes are observed. '
        'The clean saved model is reopened and replayed bitwise.',
        f'At source-water 30 C, changing both approaches from 1 K to 10 K increases fixed-output '
        f'compressor electricity by {work_increase:.6f}% while delivered service stays 0.25 MWh. '
        f'At fixed evaporator budget 0.1 MW, source-limited service increases {service_increase:.6f}% '
        'through added compressor work. COP decreases in both cases. Extra condenser output is not extra recovered waste heat.',
        '| Boundary and approaches | Delivered (MWh) | Recovered source (MWh) | Compressor (MWh) | Heating COP |\n'
        '|---|---:|---:|---:|---:|']
    for v in selected:
        lines.append(f'| {v["id"]} | {D(v["delivered_MWh"]):.10g} | {D(v["source_MWh"]):.10g} | {D(v["compressor_MWh"]):.10g} | {D(v["heating_COP"]):.10g} |')
    lines += ['\nSource20 printed pages 8 and 27 were visually verified against preserved publisher bytes. '
        'Its compressor balance and refrigerant-temperature convention support the limited derivation. '
        'The [university record](https://flore.unifi.it/handle/2158/1432822) lists no attached files; '
        'the new [research-group route](https://www.dief.unifi.it/vp-278-research.html) links the DOI, not a supplement. '
        'Direct publisher open returned 403 and the PDF-route tool cache missed. Metadata and abstract do not supply calibration coefficients. '
        'These observations do not establish global unavailability.',
        f'\nModel `{model.relative_to(ROOT).as_posix()}`, SHA256 `{sha(model)}`. '
        f'Evidence `{rel}` includes timestamped MATLAB/Simulink logs, successful receipt, 42 original MAT files, '
        'reopened combined MAT, binary exports, independent numeric CSV, specification, primary observations, source snapshots, '
        'reviewer revision and preservation hashes. Failed attempts remain in the directory identified by prior_attempts.json.',
        '\nLimitations:\n'+'\n'.join('- '+s for s in limitations),
        '\nNext actionable task: '+next_task+'\n']
    text='\n\n'.join(lines).replace('|\n\n|','|\n|')
    write(ROOT/'audit/HP_approach_results_v82.md',text)
    write(ROOT/'MASTER_STAGEBOARD_v82.md',text);write(ROOT/'MASTER_STAGEBOARD_stateflow_v82.md',text)
    status=dict(version='0.82',timestamp_utc=now,inherits='STATUS_v81.json',
        result='SAVED_V80_REFRIGERANT_APPROACH_SENSITIVITY_ACCEPTED_CALIBRATION_OPEN',
        new_model=False,saved_model=model.relative_to(ROOT).as_posix(),saved_model_version='0.80',model_sha256=sha(model),
        model_executed_this_run=True,trace_schema=75,reporting_api_version='0.76',
        matlab_passed=128,matlab_failed=0,independent_passed=qa['summary']['passed'],independent_failed=0,
        complete_saved_model_runs=42,held_intervals=intervals,positive_segments=segments,interior_events=events,
        required_actual_final_mode_coverage=report['mode_coverage'],monotonic_comparisons_passed=48,monotonic_comparisons_failed=0,
        reviewer_selfchecks=4,matlab_metadata=report['metadata'],result_directory=rel,
        independent_qa=qa_path.relative_to(ROOT).as_posix(),derivation='audit/HP_approach_derivation_v82.md',
        results='audit/HP_approach_results_v82.md',primary_article_replication=False,
        upstream_performance_supplement_acquired=False,independent_physical_validation='NOT_TESTED',full_primary_signoffs=0,total_sources=31,
        limitations=limitations,next_actionable_task=next_task,representative_results=selected)
    dump(ROOT/'STATUS_v82.json',status);dump(ROOT/'STATUS_stateflow_v82.json',status)
    sources=['audit/HP_approach_derivation_v82.md','audit/hp_approach_sensitivity_v82.py',
        'audit/close_hp_approach_v82.py','audit/run_hp_approach_sensitivity_v82.ps1','matlab/run_hp_approach_sensitivity_v82.m']
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as out:
        out.write(f'\n\n## {now} - v82 executed refrigerant boundary sensitivity\n\n'
            'Read latest STATUS/stageboards, acceptance, research frontier/progress, saved model builder/kernel, adapters/reporters '
            'and independent QA before edits. Used PDF skill for visual primary-page verification. '
            'All operations stayed in this project; no Jarvice, settings, scheduler, runner or external publication changes.\n\n'
            'Files added: '+', '.join(sources)+', results report and STATUS/stageboard twins. '
            'Shared ledgers appended; all prior MATLAB, SLX, primary PDF and checkpoints hash-preserved.\n\n'+text+
            '\nStop after this coherent executed deliverable and clear handoff.\n')
    for p in ['automation/STATEFLOW_ACCEPTANCE.md','audit/research_frontier_2026_10_08.md']:
        with (ROOT/p).open('a',encoding='utf-8') as out:out.write(f'\n\n## Saved-v80 approach boundary checkpoint - {now} / v82\n\n'+text+'\n')
    # Closure has no authority to modify sealed execution/QA evidence or ledger prefixes.
    for e in json.loads((folder/'preservation.json').read_text()):assert sha(ROOT/e['path'])==e['sha256']
    for e in json.loads((folder/'ledger_prefixes.json').read_text()):
        assert hashlib.sha256((ROOT/e['path']).read_bytes()[:e['size']]).hexdigest()==e['sha256']
    files=[p for p in folder.rglob('*') if p.is_file() and 'cache' not in p.parts and 'codegen' not in p.parts]
    files += [ROOT/p for p in sources]+[ROOT/'audit/HP_approach_results_v82.md',ROOT/'STATUS_v82.json',ROOT/'STATUS_stateflow_v82.json',ROOT/'MASTER_STAGEBOARD_v82.md',ROOT/'MASTER_STAGEBOARD_stateflow_v82.md']
    dump(folder/'release_manifest_v82.json',[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in files])
    dump(folder/'release_QA_v82.json',dict(timestamp_utc=now,passed=True,
        checks=['latest_equation_QA_pass','all_selfchecks_pass','all_comparisons_pass','MATLAB_42_actual_runs',
            'successful_log_clean','saved_model_same_hash','archive_six_states','primary_hash_and_access_scope',
            'prior_files_preserved','ledger_prefixes_preserved'],model_sha256=sha(model)))
    print(json.dumps({k:status[k] for k in ['version','result','matlab_passed','independent_passed','held_intervals','positive_segments']}))

if __name__=='__main__':main((ROOT/sys.argv[1]).resolve())
