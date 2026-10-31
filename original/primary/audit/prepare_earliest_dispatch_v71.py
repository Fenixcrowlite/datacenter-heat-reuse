"""Create immutable v71 test inputs, pre-run preservation and source seals."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, shutil
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    prior=json.loads((ROOT/'results/event_candidates_v70_20261012T024414_059326Z/spec.json').read_text())
    ids=['zero_demand','HP_only','TES_charge','TES_discharge','boiler_limit','insufficient_heat',
        'unit_efficiency_zero_loss','near_cutoff_no_credit','stop_overshoot_repair','interior_stop',
        'HP_only_contact_strict0','HP_only_contact_delayed','inactive_cutoff_strict_repaired',
        'inactive_cutoff_delayed_strict_repaired','OFF_blocked_hypothetical_stop',
        'OFF_discharge_restart_0p0','OFF_discharge_restart_0p01','enabled_pair_cutoff_first',
        'enabled_pair_restart_first','future_charge_sink_above_stop',
        'span_equal_one','span_near_one','span_inside_one','span_delayed',
        'repeated_0p25','repeated_0p5','repeated_1p0']
    cases=[]
    for id in ids:
        c=next(c for c in prior['cases'] if c['id']==id)
        modes=[2,3] if id=='enabled_pair_restart_first' else c['expected_modes']
        cases.append(dict(id=id,p=c['cfg'][35:],input=c['input'],expected_modes=modes,min_events=8 if id.startswith('repeated') else 0))
    # Recompute forcing after cutoff before restart under passive cooling.
    c=next(c for c in prior['cases'] if c['id']=='enabled_pair_cutoff_first')
    p=c['cfg'][35:];p[22]=5.4;p[5]=.12
    cases.append(dict(id='cutoff_then_passive_restart',p=p,input=[[1,0,6,1,6,.5,20,1,1,8.5,0,0]],expected_modes=[2,3,4],min_events=2))
    # Multiple stop/restart events within a single macro call, not just between
    # calls. Faster passive retention, small hysteresis band, certified dwell.
    p=c['cfg'][35:];p[5]=.2;p[8]=12;p[10]=20;p[15]=3;p[22]=.03;p[24]=61;p[4]=60
    cases.append(dict(id='multiple_cycles_one_call',p=p,input=[[1,0,1,1,1,0,20,1,1,7.9,1,1]],expected_modes=[0,2],min_events=3))
    faults=[]
    for id,base,index,value,guard in [('negative_demand','HP_only',5,-1,'v71 input domain'),
        ('invalid_HP_enable','HP_only',7,2,'v71 input domain'),('invalid_initial','HP_only',9,-1,'v71 initial domain')]:
        c=next(c for c in cases if c['id']==base);ii=[list(c['input'][0])];ii[0][index]=value
        faults.append(dict(id=id,base_id=base,p=c['p'],input=ii,expected_guard=guard))
    base=next(c for c in cases if c['id']=='HP_only');ii=[list(base['input'][0]) for _ in range(2)];ii[1][2]=2*ii[1][4];ii[1][5]=-1
    faults.append(dict(id='delayed_negative_demand',base_id='HP_only',p=base['p'],input=ii,expected_guard='v71 input domain'))
    for id,priorid,guard in [('genuine_stop_boundary','active_stop_boundary_strict','v71 unresolved event boundary'),
        ('genuine_cutoff_boundary','active_cutoff_boundary_strict','v71 unresolved event boundary'),
        ('genuine_enabled_collision','enabled_pair_collision_strict','v71 unresolved enabled event ordering'),
        ('unresolved_stop_derivative','unresolved_stop_monotonicity_strict','v71 unresolved stop derivative')]:
        f=next(f for f in prior['faults'] if f['id']==priorid)
        faults.append(dict(id=id,base_id='HP_only',p=f['cfg'][35:],input=f['input'],expected_guard=guard))
    folder=ROOT/'results'/('earliest_dispatch_v71_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'));folder.mkdir()
    (folder/'spec.json').write_text(json.dumps(dict(version='0.71',cases=cases,faults=faults),indent=2)+'\n')
    paths=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    (folder/'preservation.json').write_text(json.dumps([dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in paths if 'v71' not in p.name],indent=2)+'\n')
    paths=[p for p in (ROOT/'audit').glob('*v71*') if p.is_file()]+[p for p in (ROOT/'matlab').rglob('*v71*') if p.is_file()]
    manifest=[]
    for src in paths:
        rel=src.relative_to(ROOT).as_posix();dst=folder/'source_snapshot'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);manifest.append(dict(path=rel,sha256=sha(src)))
    (folder/'source_hashes.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(folder.relative_to(ROOT).as_posix())
if __name__=='__main__':main()
