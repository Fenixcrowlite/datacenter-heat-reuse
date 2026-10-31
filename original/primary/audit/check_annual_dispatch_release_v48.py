"""Final sealed-file/status consistency check; no simulation recomputation."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
s=json.loads((ROOT/'STATUS_v48.json').read_text());folder=ROOT/s['result_directory'];q=json.loads((ROOT/s['independent_qa']).read_text())
r=json.loads((folder/'annual_dispatch_v48.json').read_text());mp=sorted((ROOT/'audit').glob('Annual_dispatch_manifest_v48_*.json'))[-1];m=json.loads(mp.read_text())
checks=[]
def check(name,ok):checks.append(dict(name=name,passed=bool(ok)))
for a in m['files']:
    p=ROOT/a['path'];check(a['path'],p.is_file() and p.stat().st_size==a['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==a['sha256'])
check('zero_failures',s['harness_failed']==r['summary']['harness_failed']==q['actual_failed']==q['reviewer_selfchecks_failed']==0)
check('reported_counts',s['harness_passed']==r['summary']['harness_passed']==75 and s['independent_actual_passed']==q['actual_passed']==106795)
check('actual_scope',s['annual_intervals']==26280 and s['saved_model_intervals']==63 and s['positive_segments']==71 and s['actual_period_mode_transitions']==47 and not s['annual_stateflow_executed'] and not s['new_model'])
check('repair_scope',q['annual_nonmaximal_intervals']==0 and s['model_version']=='0.42' and s['primary_article_replication'] is False and s['independent_physical_validation']=='NOT_TESTED')
check('handoff_saved',s['next_actionable_task'] in (ROOT/'MASTER_STAGEBOARD_v48.md').read_text())
check('progress_saved','v48 source-constrained annual MATLAB repair' in (ROOT/'automation/engineering_progress.md').read_text())
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
out=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),manifest=mp.relative_to(ROOT).as_posix(),sealed_files=len(m['files']),passed=sum(x['passed'] for x in checks),failed=sum(not x['passed'] for x in checks),checks=checks)
path=ROOT/'audit'/('Annual_dispatch_postclose_v48_'+stamp+'.json');path.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='checks'},indent=2))
if out['failed']:raise SystemExit(1)
with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:
    f.write(f"\nFinal v48 packaging: {out['passed']} PASS / 0 FAIL; {out['sealed_files']} sealed release-file hashes/sizes intact. Evidence: {path.relative_to(ROOT).as_posix()}. Original numeric/model evidence unchanged after independent QA. Run complete; stop with STATUS_v48/MASTER_STAGEBOARD_v48 handoff.\n")
