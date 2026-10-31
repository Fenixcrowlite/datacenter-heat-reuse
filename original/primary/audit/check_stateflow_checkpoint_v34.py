"""Post-close checkpoint/receipt/hash consistency. No simulations rerun."""
import argparse,hashlib,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('manifest');args=parser.parse_args()
    manifest_path=Path(args.manifest).resolve();manifest=load(manifest_path);checks=[]
    def ck(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    for item in manifest['files']:
        path=ROOT/item['path'];ck(item['path'],path.is_file() and path.stat().st_size==item['bytes'] and digest(path)==item['sha256'])
    s=load(ROOT/'STATUS_stateflow_v34.json');folder=ROOT/s['result_directory'];q=load(ROOT/s['independent_qa'])
    a=load(folder/'acceptance_summary_v34.json');r=load(ROOT/s['execution_receipt']);eq=load(folder/'source_snapshot/spec/equation_checks.json')
    ck('all_authoritative_gates_pass',s['stateflow_acceptance']=='PASS' and a['failed']==0 and r['exit_code']==0 and eq['failed']==0 and not any(v['failed'] for v in q['counts'].values()))
    ck('bound_QA_counts',s['independent_check_breakdown']==q['counts'])
    for statuskey,actualkey in [('scenarios','scenarios'),('intervals','intervals'),('segment_slots','slots'),('positive_segments','positive_segments'),('matlab_checks_passed','passed'),('matlab_checks_failed','failed'),('runtime_fault_rejections','runtime_rejected'),('max_abs_balance_residual_MWh','max_abs_balance_residual_MWh')]:
        ck(statuskey,s[statuskey]==a[actualkey])
    ck('equation_count',s['equation_checks_passed']==eq['passed'])
    ck('new_model_bound',s['new_model'] and s['model_version']=='0.34' and s['model_sha256']==q['model_sha256']==digest(ROOT/s['generated_model']))
    ck('exact_reviewer_bound',q['reviewer_sha256']==digest(ROOT/'audit/verify_stateflow_v34.py'))
    ck('closed_execution_log',(ROOT/r['log_path']).is_file() and 'ACCEPTANCE_OUTPUT=' in (ROOT/r['log_path']).read_text(encoding='utf-8-sig') and 'MAT_AUDIT_OUTPUT=' in (ROOT/r['log_path']).read_text(encoding='utf-8-sig'))
    old=load(ROOT/'STATUS_stateflow_v33.json');ck('v32_counterexample_preserved',old['model_sha256']==digest(ROOT/old['generated_model']))
    ck('validation_limits_explicit',s['independent_physical_validation']=='NOT_TESTED' and not s['primary_article_replication'] and s['full_primary_signoffs']==0)
    board=(ROOT/'MASTER_STAGEBOARD_stateflow_v34.md').read_text();progress=(ROOT/'automation/engineering_progress.md').read_text()
    ck('stageboard_handoff',s['next'] in board and str(a['passed']) in board)
    ck('progress_handoff',s['next'] in progress and 'v34 executed HP hysteresis/dwell Stateflow' in progress)
    now=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    report=dict(version='0.34',timestamp_utc=now,manifest=str(manifest_path.relative_to(ROOT)),manifest_sha256=digest(manifest_path),
        passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks),checks=checks,
        evidence_class='postclose_packaging_only_no_new_numeric_or_physical_validation')
    path=ROOT/'audit'/f'Stateflow_postclose_v34_{now}.json';path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['passed','failed']}));print('POSTCLOSE_OUTPUT='+str(path.relative_to(ROOT)))
    assert not report['failed']
if __name__=='__main__':main()
