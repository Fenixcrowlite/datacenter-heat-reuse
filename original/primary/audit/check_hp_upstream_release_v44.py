"""Read-only release consistency check with timestamped packaging evidence."""
from pathlib import Path
from datetime import datetime,timezone
import csv,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    manifest_path=sorted((ROOT/'audit').glob('HP_upstream_manifest_v44_*.json'))[-1]
    manifest=json.loads(manifest_path.read_text());checks=[]
    def check(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    for item in manifest['files']:
        p=ROOT/item['path'];check(item['path'],p.is_file() and p.stat().st_size==item['bytes'] and sha(p)==item['sha256'])
    status=json.loads((ROOT/'STATUS_v44.json').read_text())
    qa=json.loads((ROOT/status['independent_qa']).read_text())
    check('status_matches_QA',status['independent_actual_passed']==qa['actual_passed'] and status['independent_actual_failed']==qa['actual_failed']==0)
    check('model_hash_unchanged',status['model_sha256']==sha(ROOT/status['saved_model']) and not status['new_model'] and not status['model_executed_this_run'])
    check('no_calibration_claim',not status['upstream_primary_text_verified'] and not status['equipment_coefficients_acquired'] and not status['primary_article_replication'])
    def readledger(name):
        with (ROOT/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
    old=readledger('audit/literature_traceability_v43.csv');new=readledger('audit/literature_traceability_v44.csv')
    check('ledger_preserves31_sources',len(old)==len(new)==31)
    check('ledger_only20_blocker_extended',all(a==b if a['id']!='20' else all(a[k]==b[k] for k in a if k!='blockers') and b['blockers'].startswith(a['blockers']) for a,b in zip(old,new)))
    check('ledger_no_full_signoff',all(r['fully_signed_off']=='NO' for r in new))
    passed=sum(c['passed'] for c in checks);failed=len(checks)-passed
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    report=ROOT/'audit'/f'HP_upstream_postclose_v44_{stamp}.json'
    report.write_text(json.dumps(dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),manifest=manifest_path.relative_to(ROOT).as_posix(),passed=passed,failed=failed,checks=checks),indent=2)+'\n')
    print(f'POSTCLOSE {passed} PASS / {failed} FAIL; REPORT={report.relative_to(ROOT)}')
    if failed==0:
        with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:
            f.write(f'\nFinal v44 packaging: {passed} PASS / 0 FAIL; {len(manifest["files"])} release artifacts retain hashes/sizes. Evidence: {report.relative_to(ROOT).as_posix()}. No numeric/model artifact changed after QA. Run complete.\n')
    sys.exit(int(failed>0))
if __name__=='__main__':main()
