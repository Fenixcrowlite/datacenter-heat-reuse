"""Publish a local checkpoint only after saved-model execution and QA pass."""
from datetime import datetime, timezone
import hashlib
import json
import sys
from standing_loss_v80 import ROOT, MODEL, NEW, LEDGERS, dump, sha
from earliest_closed_form_v73 import rows


def close(folder):
    report = json.loads((folder/'report.json').read_text())
    paths = {
        'independent': sorted(folder.glob('independent_QA_v80_*.json'))[-1],
        'capacity': sorted(folder.glob('strict_capacity_QA_v78_*.json'))[-1],
    }
    qa = {name: json.loads(path.read_text()) for name, path in paths.items()}
    assert report['summary']['failed'] == 0 and all(c['passed'] for c in report['assertions'])
    for v in qa.values():
        assert v['summary']['failed'] == 0
        assert all(c['passed'] for c in v['checks']+v.get('reviewer_selfchecks', []))
    assert qa['capacity']['report_sha256'] == sha(folder/'report.json')
    assert qa['capacity']['reviewer_sha256'] == sha(ROOT/'audit/strict_capacity_v78.py')
    assert qa['independent']['model_sha256'] == sha(ROOT/MODEL)
    assert report['mode_coverage'] == list(range(6))
    assert len(report['faults']) == 4 and all(f['runtime_rejected'] for f in report['faults'])
    receipts = [json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')]
    assert any(v['exit_code'] == 0 and 'run_standing_loss_v80(' in v['command'] for v in receipts)
    for e in json.loads((folder/'preservation.json').read_text()):
        assert sha(ROOT/e['path']) == e['sha256']
    for e in json.loads((folder/'source_hashes.json').read_text()):
        assert sha(ROOT/e['path']) == e['sha256']
        assert sha(folder/'source_snapshot'/e['path']) == e['sha256']
    for e in json.loads((folder/'ledger_prefixes.json').read_text()):
        assert hashlib.sha256((ROOT/e['path']).read_bytes()[:e['size']]).hexdigest() == e['sha256']
    prior = json.loads((ROOT/'STATUS_v79.json').read_text())
    assert sha(ROOT/prior['saved_model']) == prior['model_sha256']
    ts = datetime.now(timezone.utc).isoformat()
    rel = folder.relative_to(ROOT).as_posix()
    intervals = sum(len(rows(r['trace'])) for r in report['runs'])
    segments = sum(int(t[12]) for r in report['runs'] for t in rows(r['trace']))
    events = sum(int(t[13]) for r in report['runs'] for t in rows(r['trace']))
    sources = NEW+['audit/close_standing_loss_v80.py', 'audit/verify_standing_loss_release_v80.py']
    limits = [
        'Necessary standing-loss overlap bound only; wide or internally consistent wrong hulls can pass. Endpoint monotonicity follows from the assumed held reduced ODE; no complete nonlinear/event/dwell trajectory certification by this gate.',
        'Unchanged engineering TES and HP assumptions, thermal kernel, policy, trace schema 75 and reporting API 0.76. No primary replication, measured validation, equipment calibration, annual or generated-code acceptance; full primary signoffs 0/31.',
        'Same-agent algorithmic independence: exact Fraction operand bounds and separate 120/160-digit closed exp/log QA call no production MATLAB solver. Binary exports depend on MATLAB reopening original MAT; no independent personnel or independent MAT-parser claim.',
        'Bounded synthetic normal-mode schedules. Inherited finite span, clock, event collision and segment-budget refusals remain; the added positive multiplication rejects nonfinite loss bounds.',
        'Four coordinated post-kernel record faults use unsaved in-memory charts and are QA controls, never physical plant simulation results. Accepted SLX is reopened clean after instrumentation.',
    ]
    next_task = ('Resume primary equipment-map evidence and boundary audit from audit/HP_upstream_boundary_results_v44.md. '
                 'Seek primary text and performance-correlation supplement for DOI 10.1016/j.tsep.2025.103513; '
                 'distinguish verified coefficients and domains from metadata and access blockers. '
                 'Trace refrigerant/water and compressor/auxiliary boundaries before a calibrated backend. '
                 'Preserve v75-v80 model acceptance and independent nonlinear QA.')
    status = dict(
        version='0.80', timestamp_utc=ts, inherits='STATUS_v79.json',
        result='SAVED_STATEFLOW_CONSTITUTIVE_STANDING_LOSS_ACCEPTED_QA_PASS',
        new_model=True, saved_model=MODEL, saved_model_version='0.80',
        model_executed_this_run=True, model_sha256=sha(ROOT/MODEL),
        trace_schema=75, reporting_api_version='0.76', inherited_model_acceptance_preserved=True,
        correction_scope='Necessary TES standing-loss coefficient/duration/inventory binding before emission and memory commit',
        matlab_passed=report['summary']['passed'], matlab_failed=0,
        independent_passed=qa['independent']['summary']['passed'], independent_failed=0,
        exact_capacity_passed=qa['capacity']['summary']['passed'], exact_capacity_failed=0,
        complete_saved_model_runs=len(report['runs']), fresh_saved_v79_comparisons=len(report['runs']),
        passive_coefficient_inventory_variants=12, completed_held_intervals=intervals,
        positive_event_segments=segments, interior_events=events,
        required_actual_final_mode_coverage=report['mode_coverage'], actual_interior_event_types=[1, 2, 3],
        actual_runtime_fault_rejections=4, exact_bypass_fault_witnesses=4, legacy_v79_acceptance_witnesses=4,
        reviewer_selfchecks=sum(len(v.get('reviewer_selfchecks', [])) for v in qa.values()),
        matlab_metadata=report['metadata'], result_directory=rel,
        independent_qa=paths['independent'].relative_to(ROOT).as_posix(),
        exact_capacity_qa=paths['capacity'].relative_to(ROOT).as_posix(),
        derivation='audit/Standing_loss_derivation_v80.md', results='audit/Standing_loss_results_v80.md',
        source_code=sources, primary_article_replication=False,
        independent_physical_validation='NOT_TESTED', full_primary_signoffs=0, total_sources=31,
        limitations=limits, next_actionable_task=next_task,
    )
    table = '| Control | lambda (h^-1) | duration (h) | initial (MWh) | injected end (MWh) | injected loss (MWh) |\n|---|---:|---:|---:|---:|---:|\n'
    for f in report['faults']:
        u = rows(f['input'])[0]
        table += f"| {f['id']} | {f['p'][5]} | {u[4]} | {u[9]} | {f['endpoint']} | {f['loss']} |\n"
    body = f'''UTC {ts}. New saved v80 Stateflow actually executes all six required modes.
MATLAB {status['matlab_passed']} PASS / 0 FAIL; independent actual equation/artifact
QA {status['independent_passed']} PASS / 0 FAIL; exact MW/MWh capacity QA
{status['exact_capacity_passed']} PASS / 0 FAIL. Separate reviewer self-checks:
{status['reviewer_selfchecks']} PASS, including a wide loss hull overlap scope witness.

{len(report['runs'])} schedules / {intervals} held intervals / {segments} positive segments /
{events} interior events (stop/cutoff/restart). Twelve passive variants exercise
lambda=0/.01/.5/1 h^-1 and initial inventory=0/3/9 MWh, including lambda*dt=1.
Every valid trace double matches fresh saved-v79 execution on the same inputs.
The saved v75 thermal kernel, policy, trace schema and reporting API are unchanged.

The v79 monitor accepts four energy-balanced but constitutively impossible
passive records. v80 rejects each at the expected standing-loss assertion
before emission/commit. Exact bypass traces prove changed endpoint/loss/copy
fields reached output. Independent closed equations separately reject all four
controls. No corrupt chart is saved; clean v80 is reopened and rerun afterwards.

{table}

For held E'=B-lambda*E, monotonicity bounds integral(lambda E dt) by
lambda*duration*[minimum endpoint inventory, maximum endpoint inventory].
Zero lambda requires exact zero standing loss. The runtime check calls no
thermal flow, exponential, root finder or quadrature routine. Exact Fraction
operand QA and independent 120/160-digit exp/log trajectories verify original-MAT
binary exports, conservation, source/work/loss/service, reporting and temporal links.
The separate capacity reviewer keeps MW and MWh bounds distinct without slack.

Saved model `{MODEL}` SHA256 `{status['model_sha256']}`.
Evidence `{rel}` contains timestamped MATLAB logs and execution receipts,
Simulink diagnostics, original/reopened MAT, binary exports, numeric CSV,
all runtime fault logs, source snapshots and preservation hashes.
Restricted-startup failure is retained; only successful actual batches count.
Compiler unused-monitor warnings arise in deliberate unsaved bypass charts.

Limitations:
'''+''.join('- '+v+'\n' for v in limits)+'\nNext actionable task: '+next_task+'\n'
    dump(ROOT/'STATUS_v80.json', status)
    dump(ROOT/'STATUS_stateflow_v80.json', status)
    for name in ['MASTER_STAGEBOARD_v80.md', 'MASTER_STAGEBOARD_stateflow_v80.md', 'audit/Standing_loss_results_v80.md']:
        with (ROOT/name).open('x', encoding='utf-8') as f:
            f.write('# Executed Stateflow constitutive standing loss v80\n\n'+body)
    progress = ('\n\n## '+ts+' — v80 executed constitutive standing-loss guard\n\n'
                'Read STATUS/stageboards v79, STATEFLOW_ACCEPTANCE, research frontier/progress, '
                'thermal kernel, monitors, builder, adapter, harnesses and independent QA before edits. '
                'All work stayed in this project. Jarvice, unrelated files, user settings, scheduler '
                'and runner untouched; no publication.\n\n'
                'Files added: v80 monitor, builder, generated SLX, MATLAB harness, local batch script, '
                'scaffolder, Fraction/closed-form/release QA, derivation, results and STATUS/stageboard twins. '
                'Files changed: shared progress, acceptance and research ledgers append only. '
                'Prior data/code/models/checkpoints preserved and verified by hashes.\n\n'+body+
                '\nStop after this coherent executed deliverable and clear handoff.\n')
    for name in LEDGERS:
        text = progress if name.endswith('engineering_progress.md') else '\n\n## Standing-loss acceptance — '+ts+' / v80\n\n'+body
        with (ROOT/name).open('ab') as f:
            f.write(text.encode('utf-8'))
    artifacts = sources+[MODEL, 'audit/Standing_loss_results_v80.md', 'STATUS_v80.json', 'STATUS_stateflow_v80.json',
                         'MASTER_STAGEBOARD_v80.md', 'MASTER_STAGEBOARD_stateflow_v80.md']
    for name in artifacts:
        dst = folder/'closure_snapshot'/name
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes((ROOT/name).read_bytes())
    dump(folder/'checkpoint_hashes.json', [dict(path=name, sha256=sha(ROOT/name)) for name in artifacts])
    dump(folder/'evidence_seal.json', [dict(path=p.relative_to(folder).as_posix(), sha256=sha(p))
         for p in sorted(folder.rglob('*')) if p.is_file()
         and not {'cache', 'codegen'}.intersection(p.relative_to(folder).parts)])
    print(json.dumps(dict(result=status['result'], matlab=status['matlab_passed'],
                         independent=status['independent_passed'], evidence=rel)))


if __name__ == '__main__':
    folder = (ROOT/sys.argv[1]).resolve()
    assert folder.is_relative_to(ROOT/'results')
    close(folder)
