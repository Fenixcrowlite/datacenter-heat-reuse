"""Publish a local checkpoint only after executed Stateflow and numeric QA pass."""
from datetime import datetime, timezone
import hashlib, json, sys
from energy_commit_v78 import ROOT, MODEL, NEW, LEDGERS, dump, sha


def close(folder):
    report = json.loads((folder / 'report.json').read_text())
    qapath = sorted(folder.glob('independent_QA_v78_*.json'))[-1]
    qa = json.loads(qapath.read_text())
    capacity_path = sorted(folder.glob('strict_capacity_QA_v78_*.json'))[-1]
    capacity_qa = json.loads(capacity_path.read_text())
    assert capacity_qa['summary']['failed'] == 0
    assert all(c['passed'] for c in capacity_qa['checks'] + capacity_qa['reviewer_selfchecks'])
    assert capacity_qa['report_sha256'] == sha(folder / 'report.json')
    assert capacity_qa['reviewer_sha256'] == sha(ROOT / 'audit/strict_capacity_v78.py')
    assert report['summary']['failed'] == qa['summary']['failed'] == 0
    assert all(c['passed'] for c in report['assertions'] + qa['checks'] + qa['reviewer_selfchecks'])
    assert report['mode_coverage'] == list(range(6))
    assert all(f['runtime_rejected'] for f in report['faults'])
    for e in json.loads((folder / 'preservation.json').read_text()):
        assert sha(ROOT / e['path']) == e['sha256']
    for e in json.loads((folder / 'ledger_prefixes.json').read_text()):
        assert hashlib.sha256((ROOT / e['path']).read_bytes()[:e['size']]).hexdigest() == e['sha256']
    assert sha(ROOT / MODEL) == qa['model_sha256']
    prior_status = json.loads((ROOT / 'STATUS_v77.json').read_text())
    assert sha(ROOT / prior_status['saved_model']) == prior_status['model_sha256']
    ts = datetime.now(timezone.utc).isoformat()
    rel = folder.relative_to(ROOT).as_posix()
    intervals = sum(r['summary']['held_intervals'] for r in report['runs'])
    segments = sum(r['summary']['positive_segments'] for r in report['runs'])
    events = sum(r['summary']['interior_events'] for r in report['runs'])
    sources = NEW + ['audit/strict_capacity_v78.py', 'audit/close_energy_commit_v78.py', 'audit/verify_energy_commit_release_v78.py']
    next_task = ('Resume primary equipment-map evidence and boundary audit from '
                 'audit/HP_upstream_boundary_results_v44.md. Seek accessible primary text and '
                 'performance-correlation supplement for DOI 10.1016/j.tsep.2025.103513; '
                 'distinguish verified equations, coefficients and domains from metadata and '
                 'access blockers. Trace refrigerant/water and compressor/auxiliary boundaries '
                 'before a calibrated backend. Preserve accepted v75-v78 artifacts.')
    limits = [
        'Synthetic bounded normal-mode schedules only; no annual, calibrated equipment, primary article replication, measured physical validation or generated-code acceptance. Full primary signoffs remain 0/31.',
        'Same-agent algorithmic independence: Python Fraction operand equations and separate 120/160-digit closed exp/log trajectories call no production MATLAB solver. MAT binary exports depend on MATLAB reopening; no independent personnel or HDF5-reader claim.',
        'Thermal kernel, policy, trace schema 75 and reporting API 0.76 are unchanged. The monitor checks candidate consistency before emission and commit, not authentication against coordinated internally consistent replacement.',
        'HP source/work overlap is a necessary balance condition, not a physical COP proof. Standing losses and nonlinear event/dwell feasibility require the separate closed-form QA lane. Inherited finite span, clock, collision and segment-budget domains remain.',
        'Fault controls instrument unsaved chart copies after kernel evaluation. They are exact isolated output-corruption witnesses, never physical plant trajectories.'
    ]
    status = dict(version='0.78', timestamp_utc=ts, inherits='STATUS_v77.json',
        result='SAVED_STATEFLOW_ENERGY_PRECOMMIT_MONITOR_ACCEPTED_QA_PASS', new_model=True,
        saved_model=MODEL, saved_model_version='0.78', trace_schema=75,
        reporting_api_version='0.76', model_executed_this_run=True,
        model_sha256=qa['model_sha256'], inherited_model_acceptance_preserved=True,
        correction_scope='Energy/port and temporal verification before Stateflow trace emission and retained-memory commit; unchanged thermal dispatch',
        matlab_passed=report['summary']['passed'], matlab_failed=0,
        independent_passed=qa['summary']['passed'], independent_failed=0,
        exact_capacity_passed=capacity_qa['summary']['passed'], exact_capacity_failed=0,
        exact_capacity_qa=capacity_path.relative_to(ROOT).as_posix(),
        reviewer_selfchecks=len(qa['reviewer_selfchecks']),
        actual_runtime_fault_rejections=len(report['faults']),
        exact_bypass_fault_witnesses=len(report['faults']),
        legacy_v77_acceptance_witnesses=len(report['faults']),
        complete_saved_model_runs=len(report['runs']), fresh_saved_v77_comparisons=len(report['runs']),
        completed_held_intervals=intervals, positive_event_segments=segments, interior_events=events,
        required_actual_final_mode_coverage=report['mode_coverage'], actual_interior_event_types=[1, 2, 3],
        matlab_metadata=report['metadata'], result_directory=rel,
        independent_qa=qapath.relative_to(ROOT).as_posix(),
        retained_incomplete_attempt='results/energy_commit_v78_20261012T130117_147995Z',
        preedit_snapshot='results/energy_commit_v78_preedit_20261013T050751033Z',
        derivation='audit/Energy_commit_derivation_v78.md', results='audit/Energy_commit_results_v78.md',
        source_code=sources, primary_article_replication=False,
        independent_physical_validation='NOT_TESTED', full_primary_signoffs=0, total_sources=31,
        limitations=limits, next_actionable_task=next_task)
    body = f'''UTC {ts}. Actual saved v78 Stateflow model executes all six required modes.
MATLAB {status['matlab_passed']} PASS / 0 FAIL; independent numeric/artifact QA
{status['independent_passed']} PASS / 0 FAIL; {status['reviewer_selfchecks']} separate reviewer self-checks.
Supplementary exact rational capacity QA: {status['exact_capacity_passed']} PASS / 0 FAIL,
with three separate boundary self-checks and no tolerance shared between MW and MWh.
{len(report['runs'])} schedules / {intervals} held intervals / {segments} positive segments /
{events} interior events, including stop, cutoff and restart.
Every trace double matches fresh saved-v77 execution on the same inputs.

{len(report['faults'])} isolated energy corruptions are accepted by the unsaved v77
temporal-monitor copy and rejected by the v78 energy monitor at the expected
runtime assertion. Exact monitor-bypass traces prove every injected field was
reached. Instrumented chart copies are never saved. Clean v78 is reopened and
rerun after instrumentation. The embedded v75 thermal kernel is unchanged.

The new monitor binds port limits/allocation, TES bounds, forcing, port energies,
efficiency/auxiliary losses, segment offsets, interval and cumulative totals,
initial inventory and both first-law residuals before emission and commit.
It calls the preserved v77 temporal monitor. Trace schema 75 and reporting API
0.76 remain compatible.

Saved model `{MODEL}` SHA256 `{qa['model_sha256']}`.
Evidence `{rel}` contains timestamped MATLAB batch logs and receipts, Simulink
diagnostics, original/reopened MAT, binary exports, closed-form numeric CSV,
runtime fault logs, source snapshots and preservation hashes.
Compiler warnings that the energy monitor is unused arise in deliberate
monitor-bypass copies; the saved model retains every pre-commit call.

The unfinished earlier v78 attempt had no saved model or acceptance evidence. Its
harness incorrectly selected v78 as its own comparison model; this run repairs
that selector to v77 and retains a pre-edit snapshot. The restricted-startup
failure is retained in the evidence; only successful actual executions count.
The draft energy reviewer uses a power-ulp slack in its TES bound check.
The mandatory supplementary reviewer directly compares every actual TES hull
against exact C*(Tmax-Ta) in MWh, and checks all power limits separately in MW.
Thus acceptance does not depend on that dimensionally misplaced draft slack.

Limitations:
''' + ''.join('- ' + v + '\n' for v in limits) + '\nNext actionable task: ' + next_task + '\n'
    dump(ROOT / 'STATUS_v78.json', status)
    dump(ROOT / 'STATUS_stateflow_v78.json', status)
    for name in ['MASTER_STAGEBOARD_v78.md', 'MASTER_STAGEBOARD_stateflow_v78.md', 'audit/Energy_commit_results_v78.md']:
        with (ROOT / name).open('x', encoding='utf-8') as f:
            f.write('# Executed Stateflow energy pre-commit monitor v78\n\n' + body)
    progress = ('\n\n## ' + ts + ' — v78 executed energy pre-commit monitor\n\n'
        'Read STATUS/stageboards v77, STATEFLOW_ACCEPTANCE, research frontier, progress, '
        'existing v78 attempt, thermal kernel, builder, harness and independent reviewers before edits. '
        'Work stayed in this project; Jarvice, settings, scheduler and runner untouched.\n\n'
        'Files changed: matlab/run_energy_commit_v78.m (repair prior-model selector and output label). '
        'Files added: audit/strict_capacity_v78.py, audit/close_energy_commit_v78.py, generated v78 SLX, '
        'audit/Energy_commit_results_v78.md and STATUS/stageboard v78 twins. Existing v78 monitor, '
        'builder, batch script, draft reviewer, derivation and scaffolder were inspected and retained; '
        'the executed artifact and mandatory supplementary QA complete their acceptance pipeline. '
        'Prior model/code/data preserved; shared ledgers append only.\n\n' + body)
    for name in LEDGERS:
        text = progress if name.endswith('engineering_progress.md') else '\n\n## Energy pre-commit acceptance — ' + ts + ' / v78\n\n' + body
        with (ROOT / name).open('ab') as f:
            f.write(text.encode('utf-8'))
    artifacts = sources + [MODEL, 'audit/Energy_commit_results_v78.md', 'STATUS_v78.json',
        'STATUS_stateflow_v78.json', 'MASTER_STAGEBOARD_v78.md', 'MASTER_STAGEBOARD_stateflow_v78.md']
    for name in artifacts:
        target = folder / 'closure_snapshot' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
    dump(folder / 'checkpoint_hashes.json', [dict(path=name, sha256=sha(ROOT / name)) for name in artifacts])
    dump(folder / 'evidence_seal.json', [dict(path=p.relative_to(folder).as_posix(), sha256=sha(p))
        for p in sorted(folder.rglob('*')) if p.is_file()
        and not {'cache', 'codegen'}.intersection(p.relative_to(folder).parts)])
    print(json.dumps(dict(result=status['result'], matlab=status['matlab_passed'],
        independent=status['independent_passed'], runtime_faults=len(report['faults']), evidence=rel)))


if __name__ == '__main__':
    folder = (ROOT / sys.argv[1]).resolve()
    assert folder.is_relative_to(ROOT / 'results')
    close(folder)
