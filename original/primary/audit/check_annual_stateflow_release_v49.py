"""Final local packaging verification; no simulation or numeric rewrites."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];s=json.loads((ROOT/'STATUS_v49.json').read_text());folder=ROOT/s['result_directory']
r=json.loads((folder/'annual_stateflow_v49.json').read_text());q=json.loads((ROOT/s['independent_qa']).read_text())
mp=sorted((ROOT/'audit').glob('Annual_stateflow_manifest_v49_*.json'))[-1];m=json.loads(mp.read_text());checks=[]
def check(name,ok):checks.append(dict(name=name,passed=bool(ok)))
for a in m['files']:
    p=ROOT/a['path'];check(a['path'],p.is_file() and p.stat().st_size==a['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==a['sha256'])
check('zero_failures',s['harness_failed']==r['summary']['harness_failed']==q['actual_failed']==q['reviewer_selfchecks_failed']==0)
check('counts',s['harness_passed']==r['summary']['harness_passed']==61 and s['independent_actual_passed']==q['actual_passed']==258635)
check('actual_annual_scope',s['annual_stateflow_executed'] and s['annual_intervals']==8760 and s['saved_model_intervals']==8838 and s['positive_segments']==18573 and s['annual_positive_segments']==18495 and s['annual_modes']==[2,3,4,5] and s['six_modes_executed'] and not s['new_model'])
check('boundary_scope',s['native_scheduled_rejected_rows']==s['annual_admitted_rows']==8760 and s['model_version']=='0.42' and s['independent_physical_validation']=='NOT_TESTED' and not s['primary_article_replication'])
check('handoff',s['next_actionable_task'] in (ROOT/'MASTER_STAGEBOARD_v49.md').read_text())
check('progress','v49 actual annual saved-Stateflow adapter and execution' in (ROOT/'automation/engineering_progress.md').read_text())
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');out=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),manifest=mp.relative_to(ROOT).as_posix(),sealed_files=len(m['files']),passed=sum(x['passed'] for x in checks),failed=sum(not x['passed'] for x in checks),checks=checks)
path=ROOT/'audit'/('Annual_stateflow_postclose_v49_'+stamp+'.json');path.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='checks'},indent=2))
if out['failed']:raise SystemExit(1)
with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:f.write(f'\nFinal v49 packaging: {out["passed"]}PASS/0FAIL; {out["sealed_files"]} sealed release-file hashes/sizes intact. Evidence: {path.relative_to(ROOT).as_posix()}. Original simulation/numeric/model evidence unchanged after independent QA. Run complete; stop with STATUS_v49/MASTER_STAGEBOARD_v49 handoff.\n')
