"""Post-close packaging checks only; never count them as numerical QA."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    manifest_path=Path(sys.argv[1]);manifest=json.loads(manifest_path.read_text());checks=[]
    def ck(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    for entry in manifest['files']:
        path=ROOT/entry['path']
        ck('immutable:'+entry['path'],path.is_file() and path.stat().st_size==entry['bytes'] and digest(path)==entry['sha256'])
    status=json.loads((ROOT/'STATUS_stateflow_v31.json').read_text());prior=json.loads((ROOT/'STATUS_stateflow_v30.json').read_text())
    result=ROOT/status['result_directory'];summary=json.loads((result/'summary_v31.json').read_text())
    qa=json.loads((ROOT/status['independent_qa']).read_text());receipt=json.loads((ROOT/status['execution_receipt']).read_text(encoding='utf-8-sig'))
    ck('model_remains_v30',status['model_version']==summary['model_release']==qa['model_release']=='0.30' and status['model_sha256']==prior['model_sha256']==digest(ROOT/status['generated_model']))
    ck('no_unexecuted_event_SLX_claim',status['new_stateflow_model'] is False and status['event_component_embedded_in_stateflow'] is False)
    ck('all_observed_gates_pass',status['experiment_acceptance']=='PASS' and status['matlab_checks_failed']==summary['failed']==qa['failed']==receipt['exit_code']==0)
    ck('MATLAB_counts',status['matlab_checks_passed']==summary['passed']==summary['checks']==3544)
    ck('independent_counts',status['independent_check_breakdown']==qa['breakdown'] and status['equation_checks_passed']==566)
    ck('coverage',status['saved_model_scenarios']==50 and status['saved_model_intervals']==310 and summary['saved_v30_modes']==list(range(6)) and status['component_domain_rejections']==12)
    ck('nonvalidation_flags',status['primary_article_replication'] is False and status['independent_physical_validation']=='NOT_TESTED' and status['full_primary_signoffs']==0)
    ck('preservation_count',status['previous_immutable_entries_preserved']==manifest['previous_immutable_entries_preserved']==qa['previous_immutable_entries_checked']==413)
    log=ROOT/status['execution_log'];ck('execution_log_binding',digest(log)==qa['execution_log_sha256'] and 'EXIT_CODE=0' in log.read_text(encoding='utf-8-sig'))
    ck('receipt_binding',digest(ROOT/status['execution_receipt'])==qa['receipt_sha256'])
    ck('next_handoff_logged',status['next'] in (ROOT/'automation/engineering_progress.md').read_text(encoding='utf-8') and status['next'] in (ROOT/'MASTER_STAGEBOARD_stateflow_v31.md').read_text())
    report=(ROOT/'audit/TES_event_results_v31.md').read_text()
    ck('finite_backup_counterexample_reported','more unmet demand' in report and 'No policy dominance' in report)
    closure_logs=list((ROOT/'automation/logs').glob('stateflow_checkpoint_close_v31_*.log'))
    ck('observed_successful_closure',any('EXIT_CODE=0' in p.read_text(encoding='utf-8-sig') and manifest_path.name in p.read_text(encoding='utf-8-sig') for p in closure_logs))
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    payload=dict(timestamp_utc=stamp,evidence_class='postclose_packaging_only',manifest_sha256=digest(manifest_path),
                 passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks),checks=checks,
                 note='Post-close report/script/log created after immutable manifest; no numerical rerun or count inflation.')
    output=ROOT/'audit'/f'TES_event_postclose_v31_{stamp}.json'
    with output.open('x',encoding='utf-8') as f:f.write(json.dumps(payload,indent=2)+'\n')
    print(json.dumps(dict(report=output.relative_to(ROOT).as_posix(),passed=payload['passed'],failed=payload['failed'])))
    for c in checks:
        if not c['passed']:print('FAIL',c['name'])
    return int(payload['failed']>0)

if __name__=='__main__':raise SystemExit(main())
