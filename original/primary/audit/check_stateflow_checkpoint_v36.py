"""Read-only post-close integrity and checkpoint consistency; no new simulation."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def load(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    status=load(ROOT/'STATUS_stateflow_v36.json')
    manifest_path=ROOT/'audit/Stateflow_manifest_v36_20261010T074627_486567Z.json'
    manifest=load(manifest_path);checks=[]
    def ck(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    for item in manifest['files']:
        p=ROOT/item['path']
        ck(item['path'],p.is_file() and p.stat().st_size==item['bytes'] and digest(p)==item['sha256'])
    result=ROOT/status['result_directory'];summary=load(result/'summary_v36.json')
    qa=load(ROOT/status['independent_qa']);completion=load(ROOT/status['completion_qa'])
    ck('accepted actual v36',status['stateflow_acceptance']=='PASS_IMPLEMENTATION_ONLY' and status['new_model'] and status['model_version']=='0.36')
    ck('MATLAB and completion pass',summary['failed']==completion['failed']==0 and summary['passed']==status['matlab_checks_passed'])
    ck('independent QA pass',all(g['failed']==0 and g['passed']>0 for g in qa['counts'].values()) and status['independent_check_breakdown']==qa['counts'])
    ck('scope binding',status['scenarios']==summary['scenarios']==51 and status['intervals']==summary['intervals']==351 and status['positive_segments']==summary['positive_segments']==535)
    ck('actual fault scope',status['actual_runtime_fault_trials']==status['actual_runtime_faults_rejected']==55 and summary['faults_rejected']+summary['runtime_faults_rejected']+summary['extended_faults_rejected']==55)
    ck('physical claim boundaries',status['independent_physical_validation']=='NOT_TESTED' and not status['primary_article_replication'] and status['full_primary_signoffs']==0)
    ck('saved model binding',status['model_sha256']==qa['model_sha256']==digest(ROOT/status['generated_model']))
    for name,marker in [('build_receipt','BUILT_AND_COMPILED='),('execution_receipt','AUDIT_OUTPUT='),('mat_export_receipt','MAT_AUDIT_OUTPUT=')]:
        receipt=load(ROOT/status[name]);log=(ROOT/receipt['log_path']).read_text(encoding='utf-8-sig',errors='replace')
        ck(name+' observed exit and closed marker',receipt['exit_code']==0 and marker in log)
    prior=load(ROOT/'STATUS_stateflow_v34.json')
    ck('v34 defect baseline preserved',digest(ROOT/prior['generated_model'])==prior['model_sha256'])
    defect=load(ROOT/'STATUS_stateflow_v35.json')
    ck('v35 preserved defect record',defect['clock_faults_incorrectly_accepted']==1 and defect['new_model'] is False)
    ck('coherent handoff',status['next'].startswith('Audit near-boundary numerical admissibility') and 'Next:' in (ROOT/'MASTER_STAGEBOARD_stateflow_v36.md').read_text(encoding='utf-8'))
    now=datetime.now(timezone.utc);tag=now.strftime('%Y%m%dT%H%M%S_%fZ')
    report=dict(timestamp_utc=now.isoformat(),passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks),
        checks=checks,manifest=str(manifest_path.relative_to(ROOT)),immutable_entries=len(manifest['files']),
        evidence_class='postclose_hash_size_scope_QA_not_additional_simulation')
    path=ROOT/'audit'/f'Stateflow_postclose_v36_{tag}.json'
    path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['passed','failed','immutable_entries']}));print('POSTCLOSE='+str(path.relative_to(ROOT)))
    assert not report['failed'],path
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:
        f.write(f'\nFinal v36 post-close packaging: {report["passed"]}/{report["passed"]} PASS, zero failures. '
            f'All {report["immutable_entries"]} immutable v36 entries retain hashes/sizes; status, observed zero-exit receipts, actual scope, QA and preserved v34/v35 records agree. '
            f'Evidence: {path.relative_to(ROOT)}. Checker/report/log are post-manifest packaging evidence, not additional simulation or physical validation. Run complete; next task remains the supported numerical-domain audit.\n')

if __name__=='__main__':main()
