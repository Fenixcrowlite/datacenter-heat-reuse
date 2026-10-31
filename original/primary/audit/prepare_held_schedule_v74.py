"""Additive synthetic held schedules, original baselines and preservation seals."""
from pathlib import Path
from datetime import datetime, timezone
import copy, hashlib, json, shutil
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    prior=json.loads((ROOT/'results/earliest_repair_v73r2_20261012T073823_950801Z/spec.json').read_text())
    cases=[]
    def add(id,p,holds,initial,compare66=True,compare57=False,family='schedule',guard=''):
        end=0.;schedule=[]
        for dt,demand,source,enable,charge in holds:
            end+=dt;schedule.append([dt,end,demand,source,enable,charge])
        cases.append(dict(id=id,p=p,schedule=schedule,initial=initial,compare66=compare66,compare57=compare57,family=family,expected_guard=guard))
    for c in prior['cases'][:6]:
        u=c['input'][0];add(c['id'],c['p'],[[u[4],u[5],u[6],u[7],u[8]]],u[9:12],family='six_mode')
    p=copy.deepcopy(prior['cases'][0]['p'])
    # Four operating windows are synthetic seasonal motifs, not weather data.
    stages=[(10,0,20,1,1),(2,6,0,0,0),(1,0,0,0,0),(13,1,20,1,1),(10,.25,.2,1,1),(12,3,0,0,0)]
    for dt in [.25,.5,1.]:
        holds=[[dt,d,s,e,c] for span,d,s,e,c in stages for _ in range(int(span/dt))]
        add('seasonal_'+str(dt).replace('.','p'),p,holds,[7.9,1,1],compare57=dt==.5,family='seasonal_motifs')
    pp=copy.deepcopy(p);pp[8]=0;pp[9]=0
    add('equal_service_HP',pp,[[.5,d,20,1,0] for d in ([.25,.5,.75,1]*4)],[3,1,1],compare57=True,family='equal_service')
    add('variable_holds',pp,[[dt,d,20,1,0] for dt,d in [(0.25,.5),(.5,1),(1,.25),(.25,.75)]*4],[3,1,1],family='variable_holds')
    # Input change must carry state. Disable is valid after adequate ON age.
    add('enable_changes',pp,[[.5,1,20,e,0] for e in [1,1,0,0,1,1]],[3,1,1],family='enable_changes')
    for id,guard in [('genuine_enabled_collision','v73 unresolved enabled event ordering'),('segment_budget_exhaustion','v73 event segment budget'),('genuine_stop_boundary','v73 unresolved event boundary'),('disable_before_dwell','v73 ON dwell not certified')]:
        c=next(c for c in prior['cases'] if c['id']==id)
        add(id,c['p'],[[u[4],u[5],u[6],u[7],u[8]] for u in c['input']],c['input'][0][9:12],False,False,'expected_refusal',guard)
    add('span_refusal',p,[[101,1,20,1,0]],[3,1,1],False,False,'expected_refusal','v73 thermal/span domain')
    # Bounded advancing binary clock refusal enters the saved model, after a
    # valid .5h prefix. The malformed external label bypasses only the adapter.
    add('clock_refusal',pp,[[.5,1,20,1,0],[.5,1,20,1,0]],[3,1,1],False,False,'raw_clock_refusal','v73 physical clock')
    folder=ROOT/'results'/('held_schedule_v74_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'));folder.mkdir()
    cfg=json.loads(next((ROOT/'results').glob('stop_guard_v66_*/spec.json')).read_text())['cases'][0]['cfg']
    (folder/'spec.json').write_text(json.dumps(dict(version='0.74',cases=cases,v66_prefix_cfg=cfg[:35]),indent=2)+'\n')
    preserved=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    (folder/'preservation.json').write_text(json.dumps([dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in preserved if 'v74' not in p.name],indent=2)+'\n')
    sources=[p for base in ['audit','matlab'] for p in (ROOT/base).rglob('*v74*') if p.is_file() and '__pycache__' not in p.parts]
    sources += [ROOT/'audit'/name for name in ['earliest_closed_form_v73.py','verify_interval_dispatch_v66.py','verify_stateflow_finite_v57.py','verify_restart_chain_v64.py','verify_capacity_chain_v63.py','verify_interval_dispatch_v65.py','earliest_service_reference_v66.py']]
    manifest=[]
    for src in sources:
        rel=src.relative_to(ROOT).as_posix();dst=folder/'source_snapshot'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);manifest.append(dict(path=rel,sha256=sha(src)))
    (folder/'source_hashes.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(folder.relative_to(ROOT).as_posix())
if __name__=='__main__':main()
