"""Verify sealed release hashes, executed scope and handoff without rerunning models."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json

ROOT=Path(__file__).resolve().parents[1]

def main():
    s=json.loads((ROOT/'STATUS_v50.json').read_text());folder=ROOT/s['result_directory']
    r=json.loads((folder/'annual_sensitivity_v50.json').read_text())
    q=json.loads((ROOT/s['independent_qa']).read_text())
    mp=sorted((ROOT/'audit').glob('Annual_sensitivity_manifest_v50_*.json'))[-1]
    manifest=json.loads(mp.read_text());checks=[]
    def check(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    for a in manifest['files']:
        p=ROOT/a['path'];check(a['path'],p.is_file() and p.stat().st_size==a['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==a['sha256'])
    check('zero_failures',s['harness_failed']==r['summary']['harness_failed']==q['actual_failed']==q['reviewer_selfchecks_failed']==0)
    check('counts',s['harness_passed']==r['summary']['harness_passed'] and s['independent_actual_passed']==q['actual_passed'] and s['positive_segments']==q['positive_segments']==r['summary']['positive_segments'])
    check('executed_scope',s['completed_annual_scenarios']==9 and s['saved_model_intervals']==9*8760==q['saved_intervals'] and s['model_executed_this_run'] and not s['new_model'] and s['model_version']=='0.42')
    check('validation_scope',s['independent_physical_validation']=='NOT_TESTED' and not s['primary_article_replication'] and s['full_primary_signoffs']==0)
    check('handoff',s['next_actionable_task'] in (ROOT/'MASTER_STAGEBOARD_v50.md').read_text())
    check('progress','v50 matched annual Stateflow sensitivity matrix' in (ROOT/'automation/engineering_progress.md').read_text())
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    out=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),manifest=mp.relative_to(ROOT).as_posix(),sealed_files=len(manifest['files']),passed=sum(v['passed'] for v in checks),failed=sum(not v['passed'] for v in checks),checks=checks)
    path=ROOT/'audit'/('Annual_sensitivity_postclose_v50_'+stamp+'.json')
    path.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='checks'},indent=2))
    if out['failed']:raise SystemExit(1)
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:
        f.write(f'\nFinal v50 packaging: {out["passed"]} PASS / 0 FAIL; {out["sealed_files"]} sealed release-file hashes/sizes intact. Evidence: {path.relative_to(ROOT).as_posix()}. Original simulations/model/numeric evidence unchanged after independent QA. Run complete; stop with STATUS_v50/MASTER_STAGEBOARD_v50 handoff.\n')

if __name__=='__main__':main()
