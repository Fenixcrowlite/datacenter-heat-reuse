"""Read-only post-close integrity check; no additional simulation claims."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))

def main():
    status=load(ROOT/'STATUS_stateflow_v32.json')
    manifests=list((ROOT/'audit').glob('Stateflow_manifest_v32_*.json'));assert len(manifests)==1
    manifest=load(manifests[0]);checks=[]
    def ck(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    for label,m in [('new',manifest)]+[(p,load(ROOT/p)) for p in manifest['prior_manifests']]:
        for e in m['files']:
            p=ROOT/e['path'];ck(label+':'+e['path'],p.is_file() and p.stat().st_size==e['bytes'] and sha(p)==e['sha256'])
    folder=ROOT/status['result_directory'];summary=load(folder/'acceptance_summary_v32.json')
    qa=load(ROOT/status['independent_qa']);receipt=load(ROOT/status['execution_receipt'])
    eq=load(folder/'source_snapshot/spec/equation_qa.json')
    ck('status_pass_and_actual_execution',status['stateflow_acceptance']=='PASS' and summary['actual_saved_model_executed'] is True)
    ck('summary_counts',status['matlab_checks_passed']==summary['passed'] and summary['failed']==status['matlab_checks_failed']==0)
    ck('faults',summary['runtime_rejected']==summary['runtime_faults']==status['runtime_fault_rejections']==23)
    ck('six_modes',summary['modes_observed']==list(range(6)))
    ck('equations',status['equation_checks_passed']==eq['passed'] and status['equation_checks_failed']==eq['failed']==0)
    ck('QA_categories',status['independent_check_breakdown']==qa['categories'] and status['independent_checks_failed']==qa['failed']==0)
    ck('QA_model_SHA',status['model_sha256']==qa['model_sha256']==sha(ROOT/status['generated_model']))
    ck('QA_source_SHA',qa['verifier_sha256']==sha(ROOT/qa['verifier_path']))
    ck('selected_result_binding',Path(qa['result_directory']).as_posix()==status['result_directory'] and Path(qa['receipt']).resolve()==(ROOT/status['execution_receipt']).resolve())
    ck('residual_binding',status['max_abs_balance_residual_MWh']==summary['max_abs_balance_residual_MWh']<1e-12)
    ck('preservation_counts',status['previous_immutable_entries_preserved']==manifest['previous_entries_preserved']==qa['previous_entries_preserved']==597)
    log=(ROOT/receipt['log_path']).read_text(encoding='utf-8-sig')
    ck('observed_exit_and_closed_success',receipt['exit_code']==status['matlab_batch_exit_code']==0 and 'BATCH_ACCEPT_PASS' in log and
        'ACCEPTANCE_OUTPUT='+str(folder) in log and 'MAT_AUDIT_OUTPUT='+str(folder/'mat_audit_v32.json') in log)
    ck('physical_claims_not_inflated',status['independent_physical_validation']=='NOT_TESTED' and status['primary_article_replication'] is False and
        status['standalone_codegen'] is False and status['solver_clock_event_activations'] is False and status['full_primary_signoffs']==0)
    closures=list((ROOT/'automation/logs').glob('stateflow_checkpoint_close_v32_*.log'))
    ck('closed_finalizer_log',len(closures)==1 and '"immutable_files_verified": 344' in closures[0].read_text(encoding='utf-8-sig'))
    board=(ROOT/'MASTER_STAGEBOARD_stateflow_v32.md').read_text(encoding='utf-8')
    ck('stageboard_handoff',status['next'] in board and str(summary['passed']) in board)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    report=dict(timestamp_utc=stamp,evidence_class='post_close_packaging_only',manifest=str(manifests[0].relative_to(ROOT)),
        passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks),checks=checks)
    path=ROOT/'audit'/f'Stateflow_postclose_v32_{stamp}.json'
    with path.open('x',encoding='utf-8') as f:f.write(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='checks'}));print('REPORT='+str(path.relative_to(ROOT)))
    for c in checks:
        if not c['passed']:print('FAIL='+c['name'])
    return int(report['failed']>0)
if __name__=='__main__':raise SystemExit(main())
