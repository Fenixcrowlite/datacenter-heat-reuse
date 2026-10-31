"""Post-close artifact/status check; adds no simulation acceptance."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    manifest=read(ROOT/Path(sys.argv[1]));status=read(ROOT/'STATUS_stateflow_v41.json');qa=read(ROOT/status['independent_qa'])
    checks=[]
    def ck(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    for f in manifest['files']:
        p=ROOT/f['path'];ck(f['path'],p.is_file() and p.stat().st_size==f['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==f['sha256'])
    ck('open_defect_not_repaired_acceptance',status['stateflow_acceptance']=='DEFECT_CONFIRMED_OPEN' and not status['new_model'] and status['model_version']=='0.40')
    ck('ten_unresolved_no_certain_premature',status['uncertainty_dwell_guarantee_failures']==qa['unresolved_transitions']==10 and qa['certainly_premature_transitions']==0)
    ck('independent_actual_QA_counts',status['independent_evidence_checks_passed']==qa['qa_passed'] and status['independent_evidence_checks_failed']==qa['qa_failed']==0)
    ck('separate_synthetic_counts',status['synthetic_reviewer_checks_passed']==qa['synthetic']['passed']==4 and status['synthetic_reviewer_checks_failed']==qa['synthetic']['failed']==0)
    ck('four_actual_zero_exit_batches',len(status['matlab_batch_receipts'])==4 and all(read(ROOT/p)['exit_code']==0 for p in status['matlab_batch_receipts']))
    ck('actual_coverage_assertion',any(c['name']=='six_modes_executed' and c['passed'] for c in qa['checks']['execution']))
    ck('combined_scenarios',status['scenarios']==29 and status['completed_scenarios']==27 and status['intervals']==33 and status['positive_segments']==47)
    ck('no_physical_or_article_claim',status['independent_physical_validation']=='NOT_TESTED' and not status['primary_article_replication'] and status['full_primary_signoffs']==0)
    for k in ('scenarios','completed_scenarios','intervals','positive_segments','harness_passed','harness_failed'):
        ck('harness_'+k,status[k]==qa['summary'][k])
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');passed=sum(c['passed'] for c in checks);failed=len(checks)-passed
    path=ROOT/'audit'/('Stateflow_clock_postclose_v41_'+stamp+'.json')
    path.write_text(json.dumps(dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),passed=passed,failed=failed,manifest=sys.argv[1],checks=checks),indent=2)+'\n')
    print(f'PACKAGING={passed} PASS/{failed} FAIL');print('REPORT='+path.relative_to(ROOT).as_posix())
    if failed:sys.exit(1)
if __name__=='__main__':main()
