"""Close a documented defect checkpoint, never corrected-model acceptance."""
import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    assert not path.exists(), path
    path.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


def rel(path):
    return str(Path(path).resolve().relative_to(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('folder'); parser.add_argument('qa')
    parser.add_argument('receipt'); parser.add_argument('export_receipt')
    args = parser.parse_args()
    folder = Path(args.folder).resolve(); qa_path = Path(args.qa).resolve()
    receipt_path = Path(args.receipt).resolve(); export_path = Path(args.export_receipt).resolve()
    qa = load(qa_path); summary = load(folder/'summary_v35.json')
    receipt = load(receipt_path); export = load(export_path)
    snap = folder/'source_snapshot'; equations = load(snap/'spec/equation_checks.json')
    model = ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v34.slx'
    checks = []

    def ck(name, ok):
        checks.append(dict(name=name, passed=bool(ok)))

    ck('MATLAB audit completed', receipt['exit_code'] == 0 and summary['failed'] == 0)
    ck('MATLAB export completed', export['exit_code'] == 0 and
       'export_stateflow_admissibility_v35' in export['command'] and rel(folder).replace('\\','/') in export['command'])
    ck('QA passed', not any(c['failed'] for c in qa['counts'].values()))
    ck('equations passed', equations['failed'] == 0 and equations['passed'] == 27)
    ck('saved model preserved', digest(model) == qa['model_sha256'] == load(ROOT/'STATUS_stateflow_v34.json')['model_sha256'])
    ck('reviewer source bound', digest(ROOT/'audit/verify_stateflow_admissibility_v35.py') == qa['reviewer_sha256'])
    for path in snap.glob('*.py'):
        ck(path.name+' Python binding', digest(path) == digest(ROOT/'audit'/path.name))
    for name in ['run_stateflow_admissibility_v35.m','export_stateflow_admissibility_v35.m']:
        ck(name+' MATLAB binding', digest(snap/name) == digest(ROOT/'matlab/simulink'/name))
    log = (ROOT/receipt['log_path']).read_text(encoding='utf-8-sig', errors='replace')
    ck('receipt/output binding', 'AUDIT_OUTPUT='+str(folder) in log)
    ck('clean restore warning absent', 'Invalid or deleted object' not in log)
    spec = load(snap/'spec/cases.json'); mats = {x['file']: x for x in load(folder/'mat_audit_v35.json')}
    with (folder/'trace_v35.csv').open(newline='', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    for case in spec['cases']:
        m = mats[case['id']+'_simulation.mat']; n = len(case['inputs'])
        times = m['sample_time_h'] if isinstance(m['sample_time_h'], list) else [m['sample_time_h']]
        energy = m['energy_start'] if isinstance(m['energy_start'], list) else [m['energy_start']]
        actual = [r for r in rows if r['scenario_id'] == case['id']]
        ck(case['id']+' MAT timestamps', len(times) == n and all(abs(t-i*case['p'][0]) < 1e-12 for i,t in enumerate(times)))
        ck(case['id']+' MAT energy memory', len(energy) == n and all(abs(a-float(b['Storage_E_Start_MWh'])) <= 64*math.ulp(max(1,case['p'][1],abs(a))) for a,b in zip(energy,actual)))
    ck('runtime defect confirmed', summary['actual_fault_trials'] == 4 and
       summary['faults_incorrectly_accepted'] == 1 and summary['faults_rejected'] == 3)
    residual = max(abs(float(r['System_Balance_Residual_MWh'])) for r in rows)
    ck('residual summary bound', abs(residual-summary['max_abs_balance_residual_MWh']) <= 1e-14*max(1e-15,residual))

    equipment = ROOT/'audit/equipment_evidence_v35_20261010T031109285Z'
    acquisition = load(equipment/'acquisition_local_retry.json')
    # The successful acquisition may be named either record; inspect the status.
    if any(s['status'] != 'DOWNLOADED' for s in acquisition['sources']):
        acquisition = load(equipment/'acquisition.json')
    for source in acquisition['sources']:
        path = equipment/source['file']
        ck(source['file']+' acquisition hash', source['status'] == 'DOWNLOADED' and digest(path) == source['sha256'] and path.stat().st_size == source['bytes'])
    import pymupdf
    with pymupdf.open(equipment/'Copeland_AE4_1431_R2.pdf') as pdf:
        title = pdf[0].get_text(); page20 = pdf[19].get_text()
    ck('bulletin equipment scope', 'ZB*KAU' in title and 'R-290' in title)
    ck('bulletin specific run guidance', '10 starts per hour' in page20 and '2-3 minutes' in page20 and 'no minimum off' in page20)
    text = (equipment/'EnergyPlus_extracted.txt').read_text(encoding='utf-8')
    ck('engineering cycling text', 'minimum' in text and 'CyclingRatio = \\frac{PLR_{operating}}{PLR_{min}}' in text and '(16.461)' in text)
    now = datetime.now(timezone.utc); tag = now.strftime('%Y%m%dT%H%M%S_%fZ')
    evidence = ROOT/'audit'/f'Stateflow_completion_QA_v35_{tag}.json'
    save(evidence, dict(timestamp_utc=now.isoformat(), passed=sum(c['passed'] for c in checks),
         failed=sum(not c['passed'] for c in checks), checks=checks,
         classification='receipt_source_equipment_and_MAT_binding_checks_not_additional_model_tests'))
    assert all(c['passed'] for c in checks), evidence

    next_task = ('Implement additive Stateflow v36 with separate energy, power, temperature, dimensionless and physical-hour tolerances; '
        'embed corrected guard/monitor, preserve v34 and v35 counterexamples, execute the six modes and changing-input fixtures, '
        'and require clock corruption and early-dwell guards to reject at every tested energy scale. '
        'Audit representable time resolution and retain equipment assumptions without calibrated cycling-loss claims.')
    limitations = [
        'OPEN clock/guard tolerance defect at adversarial numerical capacity scale; this checkpoint accepts defect reproduction only, no corrected model.',
        'Guard early-age result is a direct component probe, not an observed early transition in a clean Stateflow run; allocator corruption is actual saved-model runtime evidence.',
        'Extreme capacities are numerical stress tests, not plausible installations; clean prior v34 fixture acceptance remains scoped to its evidence.',
        'Held source/demand timelines are preserved across .5/.25/.125 h partitions for three finite fixtures only.',
        'Binding OFF dwell can leave unmet demand from instantaneous TES/backup limits, even with ample energy; source outage can extend OFF indefinitely.',
        'Copeland guidance is equipment-specific primary documentation; EnergyPlus is primary engineering documentation; no new primary article signoff or parameter calibration.',
        'Normal-mode host planner, analytic segment offsets at macro solver timestamps; no standalone code generation or solver-clock events.',
        'No measured or calibrated physical validation, stratification/hydraulics, startup/cycling-loss equipment model or article replication.',
        'Independent algorithm/artifact QA is not separate human/agent review. Nonfatal Stateflow formal-argument shadow warnings remain visible.'
    ]
    status = dict(version='0.35', inherits='STATUS_stateflow_v34.json', research_inherits='STATUS_v25.json',
        timestamp_utc=now.isoformat(), checkpoint='Executed saved-v34 restart/dwell admissibility and dimensional defect audit',
        audit_result='PASS_DEFECT_REPRODUCED', stateflow_acceptance='OPEN_DEFECT_NO_NEW_MODEL_ACCEPTANCE',
        model_version='0.34', new_model=False, generated_model=rel(model), model_sha256=digest(model),
        controller_defect='OPEN energy-scaled tolerance admits clock corruption and early-age guard at stress scale',
        result_directory=rel(folder), independent_qa=rel(qa_path), completion_qa=rel(evidence),
        execution_receipt=rel(receipt_path), execution_log=receipt['log_path'], matlab_batch_exit_code=receipt['exit_code'],
        mat_export_receipt=rel(export_path), scenarios=summary['scenarios'], intervals=summary['intervals'],
        positive_segments=summary['positive_segments'], segment_slots=len(rows)*64,
        matlab_checks_passed=summary['passed'], matlab_checks_failed=summary['failed'],
        actual_clock_fault_trials=4, clock_faults_rejected=3, clock_faults_incorrectly_accepted=1,
        independent_check_breakdown=qa['counts'], equation_checks_passed=equations['passed'], equation_checks_failed=0,
        previous_immutable_entries_preserved=qa['previous_unique_entries'], max_abs_balance_residual_MWh=residual,
        full_primary_signoffs=0, total_sources=31, primary_article_replication=False,
        independent_physical_validation='NOT_TESTED', limitations=limitations, next=next_task)
    save(ROOT/'STATUS_stateflow_v35.json', status)
    report = [f'# v35 executed saved-v34 admissibility and dimensional defect audit\n\nUTC: {now.isoformat()}. **OPEN DEFECT; no new SLX or corrected-controller acceptance.**\n',
        f'Fresh MATLAB batch exit 0: {summary["passed"]}/{summary["passed"]} assertions PASS, {summary["scenarios"]} scenarios, '
        f'{summary["intervals"]} intervals, {summary["positive_segments"]} positive segments, all six modes. '
        f'Independent RK4 bound checks: {equations["passed"]}/{equations["passed"]}. Maximum clean first-law residual {residual:.9g} MWh '
        '(large-energy cancellation stress; smaller-case details remain in traces).\n',
        'The actual saved-v34 allocator mutation adds .01 h (36 s) to each reported end age. The monitor rejects it at 10, 1e4 and 1e6 MWh '
        'but incorrectly accepts it at 1e9 MWh. Independently re-exported MATs contain the corrupted trace; hour-based QA rejects all 128 corrupted slots. '
        'The direct guard probe also admits age .24 h against required .25 h at 1e9 MWh. '
        'Clean source/demand traces are not claimed to exhibit an early restart. The model was restored and re-executed; the original SLX hash is unchanged.\n',
        '| Timeline | Step (h) | End TES (MWh) | Electricity (MWh) | Unmet (MWh) | End latch / age (h) |\n|---|---:|---:|---:|---:|---:|']
    for family in ['demand_step','source_step','safe_held']:
        for dt in [.5,.25,.125]:
            v = qa['experiment_ledger'][f'{family}_h_{dt:g}']
            report.append(f'| {family} | {dt:g} | {v["E"]:.9f} | {v["electric"]:.9f} | {v["unmet"]:.9f} | {v["clock"][0]:g} / {v["clock"][1]:.9f} |')
    report += ['\nThese timelines keep input change times fixed at .5 h boundaries; the finite partition comparisons pass. '
        'The separate initial-OFF overload case yields .875 MWh unmet, matching the independent power-limit calculation. '
        'A sample at StopTime executes its full following physical interval. The base six cases inherit the independently verified v34 fixture specification; '
        'no new annual simulator comparison is claimed here.\n',
        'QA breakdown: `'+json.dumps(qa['counts'])+'`. '+str(qa['previous_unique_entries'])+' prior unique immutable entries preserved. '
        f'Supplementary source/receipt/MAT/equipment bindings: {len(checks)} PASS. These are distinct from model assertions.\n',
        'Primary equipment evidence and independent equations: `audit/TES_admissibility_derivation_v35.md`. '
        'Copeland page 20 was visually inspected, and PDF page 1 establishes equipment scope. Both acquired source hashes were rechecked. '
        'No equipment values were adopted into the model. Full primary article signoffs remain 0/31.\n',
        'Earlier unclosed work is preserved: MATLAB sandbox startup failures, cell/struct harness error, '
        'old reviewer failures (large-scale energy cancellation and an incorrectly placed overload expectation), '
        'and an old cleanup warning. The revised specification explicitly starts the overload control OFF. '
        'This run first rejected an incompatible old-result/new-reviewer pairing with KeyError; that log is retained. '
        'Fresh latest-spec simulation, separate MAT export and reviewer now pass; the final cleanup warning is absent. '
        'All actual Stateflow shadow warnings remain in the batch log.\n',
        f'Evidence: `{rel(folder)}`, `{rel(qa_path)}`, `{rel(evidence)}`, `{rel(receipt_path)}`, `{rel(export_path)}`.\n',
        'Remaining limitations:\n']+['- '+x for x in limitations]+['\nNext: '+next_task]
    report_path = ROOT/'audit/TES_admissibility_results_v35.md'
    assert not report_path.exists(); report_path.write_text('\n'.join(report)+'\n', encoding='utf-8')
    board = ROOT/'MASTER_STAGEBOARD_stateflow_v35.md'
    assert not board.exists(); board.write_text('# v35: saved-v34 dimensional tolerance defect\n\n'+
        f'{now.isoformat()}. Audit PASS; controller defect OPEN. Saved model remains v34, preserved.\n\n'+
        f'{summary["scenarios"]} scenarios / {summary["intervals"]} intervals / {summary["positive_segments"]} positive segments / six modes; '
        f'{summary["passed"]} MATLAB assertions; 27 RK4 bound checks; independent QA zero failures. '
        'Clock mutation rejected at three scales and wrongly accepted at largest; early-age guard defect independently confirmed.\n\n'+
        'Evidence: audit/TES_admissibility_results_v35.md, audit/TES_admissibility_derivation_v35.md, STATUS_stateflow_v35.json.\n\nNext: '+next_task+'\n', encoding='utf-8')
    with (ROOT/'automation/engineering_progress.md').open('a', encoding='utf-8') as f:
        f.write(f'\n\n## {now.isoformat()} — v35 fresh saved-Stateflow admissibility defect audit\n\n'
            'Read latest status/stageboards, acceptance, frontier, progress and production/oracle sources. Resumed unfinished v35; '
            'added complete source snapshot binding, reran saved-v34 Stateflow against latest specification and separately re-exported MATs. '
            'Derived changing-input ON/reserve bounds and distinguished minimum PLR, COP cutoff and equipment-specific dwell guidance.\n\n'
            f'Pass/fail: MATLAB exit0, {summary["passed"]}/{summary["passed"]} assertions; {summary["scenarios"]} scenarios/{summary["intervals"]} intervals/'
            f'{summary["positive_segments"]} positive segments/six modes; equations27/27; independent QA {json.dumps(qa["counts"])}; '
            f'completion bindings {len(checks)}/{len(checks)} PASS; previous immutable entries {qa["previous_unique_entries"]} preserved. '
            'Production defect OPEN: .01h allocator-clock corruption wrongly accepted at 1e9MWh; three smaller scales reject. '
            'Direct guard admits .24h against .25h at large scale; no early clean Stateflow transition claimed. '
            'Initial-OFF overload produces predicted .875MWh unmet. Saved SLX and all earlier baselines unchanged.\n\n'
            'Files changed: matlab/simulink/run_stateflow_admissibility_v35.m (snapshot completeness only). '
            'Files created: audit/finalize_stateflow_admissibility_v35.py, derivation/results/completion QA, '
            'STATUS_stateflow_v35.json, MASTER_STAGEBOARD_stateflow_v35.md, fresh result/MAT/source traces, receipts and timestamped logs/manifest. '
            'Appended progress and acceptance ledgers. Pre-existing unclosed v35 generator/reviewer/equipment artifacts preserved. '
            'Default MATLAB sandbox startup failed before execution; approved local batch succeeded. Old incompatible-result QA preflight failed; '
            'fresh latest-spec QA passed. Earlier failures remain visible.\n\nRemaining limitations: '+' '.join(limitations)+
            '\n\nNext actionable task: '+next_task+'\n\nRun stops at coherent documented defect and handoff. '
            'No Jarvice/unrelated files, settings, scheduler, runner, secrets or external publication changed.\n')
    with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a', encoding='utf-8') as f:
        f.write(f'\n\n## Saved-v34 dimensional defect checkpoint — {now.isoformat()} / v35\n\n'
            f'Fresh saved-v34 execution: {summary["scenarios"]} scenarios/{summary["intervals"]} intervals, {summary["passed"]} MATLAB assertions, '
            '27 independent bound checks and independent numeric/MAT/archive/preservation QA PASS. '
            'Clock/guard tolerance defect OPEN at numerical stress scale; no new SLX or corrected-model acceptance. '
            'Prior v34 acceptance remains limited to its tested fixtures. Authoritative STATUS/stageboard v35 and '
            'audit/TES_admissibility_results_v35.md provide counterexamples and additive-v36 handoff.\n')

    paths = {ROOT/'STATUS_stateflow_v35.json', board, report_path, model, Path(__file__).resolve()}
    for base in [ROOT/'audit',ROOT/'automation/logs',ROOT/'matlab/simulink']:
        for path in base.glob('*v35*'):
            if path.is_dir():
                paths.update(p for p in path.rglob('*') if p.is_file() and '__pycache__' not in str(p))
            elif path.is_file() and 'finalize_console' not in path.name:
                paths.add(path)
    for path in (ROOT/'results').glob('stateflow_admissibility_v35_*'):
        paths.update(p for p in path.rglob('*') if p.is_file())
    manifest = ROOT/'audit'/f'Stateflow_admissibility_manifest_v35_{tag}.json'
    entries = [dict(path=rel(p), bytes=p.stat().st_size, sha256=digest(p)) for p in sorted(paths)]
    save(manifest, dict(version='0.35', timestamp_utc=now.isoformat(), model_version='0.34',
         previous_entries_preserved=qa['previous_unique_entries'], files=entries,
         mutable_exclusions=['automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md','active finalizer log','generated caches']))
    assert all(digest(ROOT/e['path']) == e['sha256'] for e in entries)
    print(json.dumps(dict(checkpoint='STATUS_stateflow_v35.json', result='PASS_DEFECT_REPRODUCED',
                         manifest=rel(manifest), immutable_files=len(entries))))


if __name__ == '__main__':
    main()
