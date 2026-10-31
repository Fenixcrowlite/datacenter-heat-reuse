"""Read-only post-close consistency gate; seal its own completed artifacts later."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    s=read(ROOT/'STATUS_stateflow_v40.json');qa=read(ROOT/s['independent_qa']);checks=[]
    def ck(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    manifest=ROOT/Path(sys.argv[1]);m=read(manifest)
    ck('scoped_acceptance',s['stateflow_acceptance']=='PASS_SCOPED_IMPLEMENTATION' and s['model_version']=='0.40' and s['new_model'])
    ck('actual_model_hash',sha(ROOT/s['generated_model'])==s['model_sha256']==qa['model_sha256'])
    for v in (14,24,28,30,32,34,36,38):
        ck(f'baseline_v{v}_present',(ROOT/f'matlab/simulink/DCHR_Dispatch_Stateflow_v{v}.slx').is_file())
    ck('all_QA_pass',all(v['failed']==0 for v in qa['counts'].values()))
    ck('actual_counts',s['independent_evidence_checks_passed']==sum(v['passed'] for k,v in qa['counts'].items() if k!='synthetic'))
    ck('synthetic_counts_separate',s['synthetic_reviewer_checks_passed']==qa['counts']['synthetic']['passed']==3)
    ck('analytic_counts',s['implementation_comparisons']==qa['implementation_comparisons'] and qa['implementation_comparisons']['failed']==0)
    ck('implementation_check_rows',len(qa['implementation_checks'])==sum(qa['implementation_comparisons'].values()) and all(v['passed'] for v in qa['implementation_checks']))
    modes={int(r[2]) for a in read(ROOT/s['result_directory']/'execution_v40.json') for r in a['segments']}
    ck('six_actual_modes',modes==set(range(6)))
    for p in s['matlab_batch_receipts']:
        r=read(ROOT/p);ck(p+'_exit',r['exit_code']==0 and (ROOT/r['log_path']).stat().st_size>0)
    ck('first_law_residual',s['max_independent_balance_residual_MWh']<=1e-7)
    for v in ('primary_article_replication','physical_validation'):
        ck(v+'_not_claimed',qa.get(v,False)==False)
    ck('physical_validation_status',s['independent_physical_validation']=='NOT_TESTED' and s['primary_article_replication']==False)
    ck('primary_signoffs_scope',s['full_primary_signoffs']==0 and s['total_sources']==31)
    for x in m['files']:
        p=ROOT/x['path'];ck(x['path'],p.is_file() and p.stat().st_size==x['bytes'] and sha(p)==x['sha256'])
    report=dict(version='0.40',timestamp_utc=datetime.now(timezone.utc).isoformat(),
        manifest=str(manifest.relative_to(ROOT)),sealed_entries=len(m['files']),
        passed=sum(x['passed'] for x in checks),failed=sum(not x['passed'] for x in checks),checks=checks)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    path=ROOT/'audit'/('Stateflow_HP_postclose_v40_'+stamp+'.json')
    path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('POSTCLOSE='+str(path.relative_to(ROOT)));print('COUNTS='+json.dumps({k:report[k] for k in ('passed','failed','sealed_entries')}))
    assert report['failed']==0,[x['name'] for x in checks if not x['passed']]
if __name__=='__main__':main()
