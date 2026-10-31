"""Read-only post-close integrity check of v74 and prior artifact preservation."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    checks=[]
    def check(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    seal=json.loads((folder/'release_seal_v74.json').read_text())
    for path,field in [('STATUS_v74.json','status_sha256'),('MASTER_STAGEBOARD_v74.md','stageboard_sha256'),('audit/Held_schedule_results_v74.md','results_sha256')]:check(path,sha(ROOT/path)==seal[field])
    for path,field in [('evidence_hashes_v74.json','evidence_manifest_sha256'),('final_source_hashes_v74.json','source_manifest_sha256'),('ledger_prefix_seals_v74.json','ledger_prefix_manifest_sha256')]:check(path,sha(folder/path)==seal[field])
    for r in json.loads((folder/'evidence_hashes_v74.json').read_text()):check('evidence/'+r['path'],sha(folder/r['path'])==r['sha256'])
    for r in json.loads((folder/'final_source_hashes_v74.json').read_text()):check('source/'+r['path'],sha(ROOT/r['path'])==r['sha256'] and sha(folder/'final_source_snapshot'/r['path'])==r['sha256'])
    for r in json.loads((folder/'preservation.json').read_text()):check('preserved/'+r['path'],sha(ROOT/r['path'])==r['sha256'])
    for r in json.loads((folder/'ledger_prefix_seals_v74.json').read_text()):
        data=(ROOT/r['path']).read_bytes();check('append_only/'+r['path'],len(data)>r['bytes'] and hashlib.sha256(data[:r['bytes']]).hexdigest()==r['sha256'] and b'v74' in data[r['bytes']:])
    check('status_twins',(ROOT/'STATUS_v74.json').read_bytes()==(ROOT/'STATUS_stateflow_v74.json').read_bytes())
    check('stageboard_twins',(ROOT/'MASTER_STAGEBOARD_v74.md').read_bytes()==(ROOT/'MASTER_STAGEBOARD_stateflow_v74.md').read_bytes())
    status=json.loads((ROOT/'STATUS_v74.json').read_text());report=json.loads((folder/'report.json').read_text());qa=json.loads((ROOT/status['independent_qa']).read_text())
    check('authoritative_counts',status['matlab_passed']==report['summary']['passed'] and status['independent_passed']==qa['summary']['passed'] and report['summary']['failed']==qa['summary']['failed']==0)
    check('accepted_scope',status['new_model'] is False and status['model_executed_this_run'] is True and status['saved_model_version']=='0.73r2' and status['primary_article_replication'] is False and status['independent_physical_validation']=='NOT_TESTED')
    check('model_hash',sha(ROOT/status['saved_model'])==status['model_sha256'])
    for r in qa['reviewer_selfchecks']:check('reviewer_mutation/'+r['name'],r['passed'])
    for c in qa['comparisons']:
        check('comparison_scope/'+c['id']+'/'+c['model'],c['full_schedule_accepted'] and (c['equal_delivered_service_within_budget'] or c['interpretation']=='UNEQUAL_SERVICE_NO_COST_OR_EFFICIENCY_RANKING'))
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');summary=dict(passed=sum(r['passed'] for r in checks),failed=sum(not r['passed'] for r in checks))
    result=dict(version='0.74',timestamp_utc=datetime.now(timezone.utc).isoformat(),verifier_sha256=sha(Path(__file__)),checks=checks,summary=summary)
    out=folder/f'release_verification_v74_{stamp}.json';out.write_text(json.dumps(result,indent=2)+'\n')
    log=dict(release=out.relative_to(ROOT).as_posix(),summary=summary,failed=[r for r in checks if not r['passed']]);(folder/f'release_verification_v74_{stamp}.log').write_text(json.dumps(log,indent=2)+'\n');print(json.dumps(log))
    return int(summary['failed']>0)
if __name__=='__main__':sys.exit(main())
