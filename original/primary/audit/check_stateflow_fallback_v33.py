"""Post-close packaging checks, separate from numerical/controller validation."""
import argparse
import json
from pathlib import Path
from stateflow_fallback_v33 import ROOT, sha, save, stamp

def main(manifest_path):
    m=json.loads(manifest_path.read_text());checks=[]
    def ck(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    for item in m['files']:
        p=ROOT/item['path'];ck(item['path'],p.exists() and p.stat().st_size==item['bytes'] and sha(p)==item['sha256'])
    status=json.loads((ROOT/'STATUS_stateflow_v33.json').read_text())
    folder=ROOT/status['result_directory'];s=json.loads((folder/'summary_v33.json').read_text())
    qa=json.loads((ROOT/status['independent_qa']).read_text())
    rc=json.loads((ROOT/status['execution_receipt']).read_text(encoding='utf-8-sig'))
    ck('passed_observed_batch',status['matlab_batch_exit_code']==rc['exit_code']==0)
    ck('summary_assertions',status['matlab_checks_passed']==s['passed']==16200 and s['failed']==0)
    ck('independent_QA',qa['failed']==0 and status['independent_check_breakdown']==qa['categories'])
    ck('equation_counts',status['equation_checks_passed']==qa['equation_checks_passed']==643)
    ck('model_preserved',status['model_version']=='0.32' and not status['new_model'] and
       status['model_sha256']==sha(ROOT/status['generated_model'])==qa['model_sha256'])
    ck('open_defect_handoff',status['controller_defect'].startswith('CONFIRMED_OPEN') and 'v34' in status['next'])
    ck('research_limit',status['full_primary_signoffs']==0 and not status['primary_article_replication'])
    ck('closed_console',(ROOT/rc['log_path']).read_text(encoding='utf-8-sig').find('FALLBACK_OUTPUT=')>=0)
    report=dict(timestamp_utc=stamp(),evidence_class='postclose_packaging_only',manifest=str(manifest_path.relative_to(ROOT)),
        passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks),checks=checks)
    out=ROOT/'audit'/f'Stateflow_fallback_postclose_v33_{stamp()}.json';save(out,report)
    print(json.dumps(dict(report=str(out.relative_to(ROOT)),passed=report['passed'],failed=report['failed'])))
    return int(report['failed']>0)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('manifest',type=Path);a=p.parse_args()
    raise SystemExit(main(a.manifest.resolve()))
