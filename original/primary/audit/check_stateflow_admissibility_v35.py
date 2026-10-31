"""Read-only post-close package checks; not additional simulation evidence."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest_path = max((ROOT/'audit').glob('Stateflow_admissibility_manifest_v35_*.json'))
    manifest = load(manifest_path); status = load(ROOT/'STATUS_stateflow_v35.json'); checks = []

    def ck(name, ok):
        checks.append(dict(name=name, passed=bool(ok)))

    for e in manifest['files']:
        path = ROOT/e['path']
        ck(e['path'], path.is_file() and path.stat().st_size == e['bytes'] and digest(path) == e['sha256'])
    qa = load(ROOT/status['independent_qa']); receipt = load(ROOT/status['execution_receipt'])
    completion = load(ROOT/status['completion_qa'])
    summary = load(ROOT/status['result_directory']/'summary_v35.json')
    ck('model remains preserved v34', status['model_version'] == '0.34' and not status['new_model'] and
       status['model_sha256'] == load(ROOT/'STATUS_stateflow_v34.json')['model_sha256'] == digest(ROOT/status['generated_model']))
    ck('explicit open defect', status['stateflow_acceptance'] == 'OPEN_DEFECT_NO_NEW_MODEL_ACCEPTANCE' and
       status['audit_result'] == 'PASS_DEFECT_REPRODUCED' and status['controller_defect'].startswith('OPEN'))
    ck('actual zero exit', receipt['exit_code'] == status['matlab_batch_exit_code'] == 0)
    ck('executed assertion counts', status['matlab_checks_passed'] == summary['passed'] == 1205 and
       status['matlab_checks_failed'] == summary['failed'] == 0)
    ck('executed scope', (status['scenarios'],status['intervals'],status['positive_segments']) == (20,109,136))
    ck('fault count', status['actual_clock_fault_trials'] == 4 and status['clock_faults_rejected'] == 3 and
       status['clock_faults_incorrectly_accepted'] == 1)
    ck('independent QA bound', status['independent_check_breakdown'] == qa['counts'] and
       not any(v['failed'] for v in qa['counts'].values()))
    ck('completion QA passed', completion['failed'] == 0 and all(c['passed'] for c in completion['checks']))
    ck('research claims limited', not status['primary_article_replication'] and
       status['independent_physical_validation'] == 'NOT_TESTED' and status['full_primary_signoffs'] == 0)
    ck('equations bound', status['equation_checks_passed'] == 27 and status['equation_checks_failed'] == 0)
    ck('actionable v36 handoff', 'Stateflow v36' in status['next'] and 'tolerances' in status['next'])
    ck('prior preserved count', status['previous_immutable_entries_preserved'] == qa['previous_unique_entries'] == 1347)
    board = (ROOT/'MASTER_STAGEBOARD_stateflow_v35.md').read_text(encoding='utf-8')
    ck('stageboard agrees', 'defect OPEN' in board and '1205 MATLAB assertions' in board and 'v36' in board)
    tag = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    path = ROOT/'audit'/f'Stateflow_admissibility_postclose_v35_{tag}.json'
    report = dict(version='0.35', timestamp_utc=tag, manifest=str(manifest_path.relative_to(ROOT)),
         passed=sum(c['passed'] for c in checks), failed=sum(not c['passed'] for c in checks), checks=checks,
         classification='postclose_packaging_only_not_numerical_or_physical_validation')
    path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'], failed=report['failed'], report=str(path.relative_to(ROOT)))))
    assert not report['failed'], 'Post-close packaging failed'


if __name__ == '__main__':
    main()
