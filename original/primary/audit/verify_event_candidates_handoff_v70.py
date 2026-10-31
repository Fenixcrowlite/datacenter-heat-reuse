"""Verify additive handoff and exact unchanged sampled cores against prior MAT exports."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, sys
ROOT=Path(__file__).resolve().parents[1]
folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=lambda x:[x] if isinstance(x[0],(int,float)) else x
report=json.loads((folder/'report.json').read_text());checks=[]
def check(name,ok):checks.append(dict(name=name,passed=bool(ok)))
for name in ['preservation.json','source_hashes.json','checkpoint_artifact_hashes_v70.json']:
    for x in json.loads((folder/name).read_text()):check(name+'_'+x['path'],sha(ROOT/x['path'])==x['sha256'])
golden_ticks=0;golden_runs=0
current={c['id']:c for c in report['runs']}
for rel in ['results/span_repair_v68_release_20261011T215822_761796Z/report.json','results/event_applicability_v69_20261012T022722_485396Z/report.json']:
    old=json.loads((ROOT/rel).read_text())
    for c in old['runs']:
        if c['id'] not in current:continue
        new=current[c['id']]
        if c['cfg']!=new['cfg'] or rows(c['input'])!=rows(new['input']):continue
        tr=rows(c['trace']);nt=rows(new['trace'])
        check(rel+'_'+c['id']+'_exact_sampled_core',[x[:205] for x in tr]==[x[:205] for x in nt])
        golden_ticks+=len(tr);golden_runs+=1
check('golden_coverage',golden_ticks>=400 and golden_runs>=20)
status=json.loads((ROOT/'STATUS_v70.json').read_text())
check('status_twins',status==json.loads((ROOT/'STATUS_stateflow_v70.json').read_text()))
check('honest_interface_scope',status['model_revision']=='v70r2' and status['embedded_dispatch_schema']==66 and not status['coupled_stateflow_acceptance'] and status['general_repeated_earliest_event_stateflow']=='OPEN')
check('no_primary_or_physical_claim',status['full_primary_signoffs']==0 and not status['primary_article_replication'] and status['independent_physical_validation']=='NOT_TESTED')
for rel in ['automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md','audit/research_frontier_2026_10_08.md']:
    data=(ROOT/rel).read_bytes();check(rel+'_handoff_present',b'v70' in data and b'earliest' in data)
model=ROOT/status['saved_model'];check('accepted_model_hash',sha(model)==status['model_sha256'])
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
out=folder/f'handoff_QA_v70_{stamp}.json'
result=dict(version='0.70',timestamp_utc=datetime.now(timezone.utc).isoformat(),checks=checks,golden_runs=golden_runs,golden_ticks=golden_ticks,
    summary=dict(passed=sum(x['passed'] for x in checks),failed=sum(not x['passed'] for x in checks)))
out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(handoff_qa=out.relative_to(ROOT).as_posix(),summary=result['summary'],golden_runs=golden_runs,golden_ticks=golden_ticks,failed=[x for x in checks if not x['passed']])))
sys.exit(int(result['summary']['failed']>0))
