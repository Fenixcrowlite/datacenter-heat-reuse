"""Post-close packaging/binding QA; no new simulations or physics claims."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json

ROOT=Path(__file__).resolve().parents[1]
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    checks=[]
    def ck(name,ok): checks.append(dict(name=name,passed=bool(ok)))
    status=read(ROOT/'STATUS_stateflow_v39.json')
    folder=ROOT/status['result_directory']; qa=read(ROOT/status['independent_qa'])
    summary=read(folder/'summary_v39.json'); assertions=read(folder/'assertions_v39.json')
    manifest_path=next((ROOT/'audit').glob('Stateflow_HP_manifest_v39_*.json'))
    manifest=read(manifest_path)
    for entry in manifest['files']:
        p=ROOT/entry['path']
        ck(entry['path']+'_immutable',p.is_file() and p.stat().st_size==entry['bytes'] and sha(p)==entry['sha256'])
    ck('defect_status_explicit',status['stateflow_acceptance']=='DEFECT_REPRODUCED_OPEN')
    ck('no_new_model',status['new_model'] is qa['new_model'] is summary['new_model'] is False)
    ck('saved_model_release',status['model_version']==qa['model_release']==summary['model_version']=='0.38')
    ck('saved_model_hash',sha(ROOT/status['generated_model'])==status['model_sha256']==qa['model_sha256'])
    ck('prior_scoped_v38_preserved',status['model_sha256']==read(ROOT/'STATUS_stateflow_v38.json')['model_sha256'])
    ck('harness_count',len(assertions)==summary['harness_passed']==status['harness_checks_passed'] and all(x['passed'] for x in assertions))
    ck('zero_harness_failures',summary['harness_failed']==status['harness_checks_failed']==0)
    ck('actual_QA_count',status['independent_evidence_checks_passed']==sum(v['passed'] for k,v in qa['counts'].items() if k!='synthetic'))
    ck('separate_synthetic_count',status['synthetic_reviewer_checks_passed']==qa['counts']['synthetic']['passed']==3)
    ck('zero_evidence_QA_failures',all(v['failed']==0 for v in qa['counts'].values()))
    ck('controller_FAIL_retained',status['implementation_comparisons']==qa['implementation_comparisons'] and qa['implementation_comparisons']['failed']>0)
    ck('implementation_failure_assertions',sum(not x['passed'] for x in qa['implementation_checks'])==qa['implementation_comparisons']['failed'])
    ck('implementation_pass_assertions',sum(x['passed'] for x in qa['implementation_checks'])==qa['implementation_comparisons']['passed'])
    for key,sk in [('scenarios','scenarios'),('completed_scenarios','completed_scenarios'),('completed_intervals','intervals'),('positive_segments','positive_segments'),('hp_component_probes','hp_probes')]:
        ck(key+'_binding',status[key]==summary[sk])
    executions=read(folder/'execution_v39.json')
    ck('execution_trace_scope',len(executions)==summary['scenarios'] and not any(x['rejected'] for x in executions))
    ck('numeric_trace_intervals',sum(len(x['dispatch']) for x in executions)==summary['intervals'])
    ck('segment_trace_scope',sum(len(x['segments']) for x in executions)==summary['positive_segments'])
    stamp=Path(status['independent_qa']).stem.replace('independent_QA_v39_','')
    reviewer=folder/'qa_source'/stamp/'verify_stateflow_hp_domain_v39.py'
    ck('exact_successful_reviewer_snapshot',reviewer.is_file() and sha(reviewer)==sha(ROOT/'audit/verify_stateflow_hp_domain_v39.py'))
    ck('failed_reviewer_retained',len(list(folder.glob('independent_QA_v39_*.json')))>=2 and any(
       any(c['failed']>0 for c in read(p)['counts'].values()) for p in folder.glob('independent_QA_v39_*.json')))
    ck('two_declared_legacy_exclusions',set(qa['preservation_exclusions'])=={
       'automation/engineering_progress.md','automation/logs/stateflow_finalize_v22_20261009T050008.log'})
    for rp in status['matlab_batch_receipts']:
        receipt=read(ROOT/rp); raw=(ROOT/receipt['log_path']).read_bytes()
        text=raw.decode('utf-16' if raw[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig')
        ck(rp+'_observed_exit',receipt['exit_code']==0)
        ck(rp+'_observed_completion',folder.name in text and ('AUDIT_OUTPUT=' in text or 'MAT_AUDIT_OUTPUT=' in text))
    for name in ('automation/engineering_progress.md','MASTER_STAGEBOARD_stateflow_v39.md','audit/HP_dynamic_range_results_v39.md'):
        ck(name+'_handoff',status['next'] in (ROOT/name).read_text(encoding='utf-8'))
    ck('six_executed_modes',{int(r[2]) for x in executions for r in x['segments']}==set(range(6)))
    for bits in (90,120):
        wide=next(x for x in qa['plant_ledger'] if x['id']==f'wide_request_{bits}')
        tight=next(x for x in qa['plant_ledger'] if x['id']==f'tight_request_{bits}')
        ck(f'{bits}_actual_false_OFF',wide['actual_HP_heat_MW']==0 and wide['expected_HP_heat_MW']>0)
        ck(f'{bits}_matched_service_control',wide['actual_unmet_MW']==wide['demand_MW']==tight['demand_MW']>0 and tight['actual_unmet_MW']==0)
    ck('no_article_or_physical_claim',status['primary_article_replication'] is False and status['independent_physical_validation']=='NOT_TESTED' and status['full_primary_signoffs']==0)
    ts=datetime.now(timezone.utc); tag=ts.strftime('%Y%m%dT%H%M%S_%fZ')
    path=ROOT/'audit'/f'Stateflow_HP_postclose_v39_{tag}.json'
    report=dict(timestamp_utc=ts.isoformat(),evidence_class='postclose_packaging_only',
        manifest=str(manifest_path.relative_to(ROOT)),passed=sum(x['passed'] for x in checks),
        failed=sum(not x['passed'] for x in checks),checks=checks)
    path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('passed','failed','manifest')}))
    print('POSTCLOSE='+str(path.relative_to(ROOT)))
    assert report['failed']==0,[x['name'] for x in checks if not x['passed']]

if __name__=='__main__': main()
