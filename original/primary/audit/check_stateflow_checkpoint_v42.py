"""Read-only packaging QA, distinct from numerical/plant checks."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,zipfile
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    manifest=ROOT/sys.argv[1];release=read(manifest);checks=[]
    def ck(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    for entry in release['files']:
        p=ROOT/entry['path'];ck(entry['path'],p.is_file() and p.stat().st_size==entry['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256'])
    s=read(ROOT/'STATUS_stateflow_v42.json');qa=read(ROOT/s['independent_qa'])
    ck('scoped_acceptance',s['stateflow_acceptance']=='PASS_SCOPED_IMPLEMENTATION' and s['model_version']=='0.42' and s['new_model'])
    ck('QA_zero_failures',qa['qa_failed']==s['independent_evidence_checks_failed']==s['uncertainty_dwell_guarantee_failures']==0)
    ck('QA_count_binding',qa['qa_passed']==s['independent_evidence_checks_passed'])
    ck('MATLAB_checks',s['harness_failed']==0 and s['harness_passed']==61)
    ck('three_successful_batches',len(s['matlab_batch_receipts'])==3 and all(read(ROOT/p)['exit_code']==0 for p in s['matlab_batch_receipts']))
    modes=set()
    for item in read(ROOT/s['result_directory']/'execution_v42.json'):
        rows=item['segments'];rows=rows if not rows or isinstance(rows[0],list) else [rows]
        modes.update(int(r[2]) for r in rows)
    ck('six_actual_modes',modes==set(range(6)))
    ck('fault_counts',sum(s['actual_fault_breakdown'].values())==s['actual_runtime_fault_rejections']==36)
    ck('research_limits',s['full_primary_signoffs']==0 and not s['primary_article_replication'] and s['independent_physical_validation']=='NOT_TESTED')
    ck('handoff_primary_traceability','primary equipment traceability' in s['next'].lower())
    for p in ('MASTER_STAGEBOARD_stateflow_v42.md','audit/Clock_uncertainty_results_v42.md','automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md'):
        content=(ROOT/p).read_text(encoding='utf-8');ck(p+'_ledger_updated','v42' in content and ('uncertainty' in content.lower() or 'Uncertainty' in content))
    model=ROOT/s['generated_model']
    ck('model_hash',hashlib.sha256(model.read_bytes()).hexdigest()==s['model_sha256'])
    with zipfile.ZipFile(model) as z:ck('saved_SLX_archive',z.testzip() is None)
    report=dict(version='0.42',timestamp_utc=datetime.now(timezone.utc).isoformat(),evidence_class='postclose_artifact_and_handoff_checks_not_simulations',
        sealed_artifacts=len(release['files']),passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks),checks=checks)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');path=ROOT/'audit'/('Stateflow_clock_postclose_v42_'+stamp+'.json')
    path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('sealed_artifacts','passed','failed')}));print('POSTCLOSE='+path.relative_to(ROOT).as_posix())
    if report['failed']:sys.exit(1)
if __name__=='__main__':main()
