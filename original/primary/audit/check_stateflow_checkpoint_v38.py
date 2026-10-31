"""Post-close packaging check; no extra simulation/physical evidence."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    manifest_path=ROOT/Path(sys.argv[1]);manifest=read(manifest_path);status=read(ROOT/'STATUS_stateflow_v38.json');checks=[]
    def ck(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    for item in manifest['files']:
        p=ROOT/Path(item['path']);ck(item['path'],p.is_file() and p.stat().st_size==item['bytes'] and sha(p)==item['sha256'])
    qa=read(ROOT/Path(status['independent_qa']));folder=ROOT/Path(status['result_directory']);summary=read(folder/'summary_v38.json')
    ck('scoped_saved_v38_acceptance',status['stateflow_acceptance']=='PASS_SCOPED_IMPLEMENTATION' and status['model_version']=='0.38' and status['new_model'])
    ck('model_SHA_binding',sha(ROOT/Path(status['generated_model']))==status['model_sha256']==qa['model_sha256'])
    ck('actual_independent_counts',status['independent_checks_passed']==sum(v['passed'] for k,v in qa['counts'].items() if k!='synthetic'))
    ck('synthetic_separate',status['synthetic_reviewer_checks_passed']==qa['counts']['synthetic']['passed']==3)
    ck('zero_failures',status['harness_checks_failed']==status['independent_checks_failed']==0 and all(v['failed']==0 for v in qa['counts'].values()))
    ck('MATLAB_scope_binding',status['scenarios']==summary['scenarios']==80 and status['completed_intervals']==summary['intervals']==3725 and status['positive_segments']==summary['positive_segments']==3910)
    ck('MATLAB_assertion_binding',status['harness_checks_passed']==summary['harness_passed']==2110)
    commands=('build_dispatch_stateflow_v38','run_stateflow_acceptance_v38','export_stateflow_resolution_v38','export_stateflow_numeric_metadata_v38')
    for command,p in zip(commands,status['matlab_batch_receipts']):
        receipt=read(ROOT/Path(p));log=(ROOT/Path(receipt['log_path'])).read_text(encoding='utf-8-sig')
        marker='BUILT_AND_COMPILED=' if command==commands[0] else 'AUDIT_OUTPUT=' if command==commands[1] else 'MAT_AUDIT_OUTPUT=' if command==commands[2] else 'NUMERIC_METADATA='
        ck(command+'_actual_zero_exit',receipt['exit_code']==0 and command in receipt['command'] and marker in log)
    ck('physical_claims_scoped',status['independent_physical_validation']=='NOT_TESTED' and not status['primary_article_replication'] and status['full_primary_signoffs']==0)
    ck('handoff_present',len(status['next'])>100 and 'clock' in status['next'] and 'primary' in status['next'])
    ts=datetime.now(timezone.utc);stamp=ts.strftime('%Y%m%dT%H%M%S_%fZ')
    path=ROOT/'audit'/('Stateflow_postclose_v38_'+stamp+'.json');assert not path.exists()
    report=dict(timestamp_utc=ts.isoformat(),evidence_class='postclose_packaging_only',manifest=str(manifest_path.relative_to(ROOT)),
        passed=sum(x['passed'] for x in checks),failed=sum(not x['passed'] for x in checks),checks=checks)
    path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('POSTCLOSE='+str(path.relative_to(ROOT)));print(json.dumps({k:report[k] for k in ('passed','failed')}))
    assert report['failed']==0
if __name__=='__main__':main()
