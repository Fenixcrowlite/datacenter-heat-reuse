"""Read-only post-close checks; separate from simulation/equation evidence."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    s=read(ROOT/'STATUS_stateflow_v37.json');q=read(ROOT/s['independent_qa']);folder=ROOT/s['result_directory']
    manifest=ROOT/Path(sys.argv[1]);m=read(manifest);checks=[]
    def ck(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    for f in m['files']:
        p=ROOT/f['path'];ck(f['path'],p.is_file() and sha(p)==f['sha256'] and p.stat().st_size==f['bytes'])
    ck('unchanged_saved_model',sha(ROOT/s['generated_model'])==s['model_sha256']==q['model_sha256'])
    ck('actual_v36_not_new_model',s['model_version']=='0.36' and not s['new_model'])
    ck('open_defects_no_corrected_acceptance',s['stateflow_acceptance']=='PASS_DEFECT_REPRODUCTION_ONLY' and 'OPEN' in s['controller_defect'])
    ck('QA_counts',s['independent_checks_passed']==sum(v['passed'] for v in q['counts'].values()) and s['independent_checks_failed']==sum(v['failed'] for v in q['counts'].values())==0)
    ck('equation_count',s['equation_checks_passed']==q['counts']['equation']['passed'])
    ck('preservation_count',s['previous_immutable_entries_preserved']==q['previous_immutable_entries'])
    a=read(folder/'execution_v37.json');ck('scenario_count',s['scenarios']==len(a)==24)
    ck('runtime_outcomes',s['completed_scenarios']==sum(not r['rejected'] for r in a)==19 and s['runtime_rejections']==sum(r['rejected'] for r in a)==5)
    ck('completed_interval_count',s['completed_intervals']==sum(len(r['clock_end']) if r['clock_end'] and isinstance(r['clock_end'][0],list) else int(bool(r['clock_end'])) for r in a))
    for receipt in s['matlab_batch_receipts']:
        r=read(ROOT/receipt);ck(receipt+'_exit0',r['exit_code']==0)
        log=(ROOT/r['log_path']).read_text(encoding='utf-8-sig',errors='replace')
        ck(receipt+'_closed_log',f'RECEIPT={receipt.replace(chr(92),"/")}' in log)
    ck('unchanged_primary_claims',s['full_primary_signoffs']==0 and s['total_sources']==31 and not s['primary_article_replication'] and s['independent_physical_validation']=='NOT_TESTED')
    ck('concrete_v38_handoff','v38' in s['next'] and 'compensated' in s['next'] and 'normalized' in s['next'])
    report=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),evidence_class='postclose_packaging_only',
        passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks),checks=checks)
    out=ROOT/'audit'/('Stateflow_postclose_v37_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')+'.json')
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:report[k] for k in ['passed','failed']}));print('POSTCLOSE='+str(out.relative_to(ROOT)))
    for c in checks:
        if not c['passed']:print('FAIL='+c['name'])
    assert report['failed']==0
if __name__=='__main__':main()
