"""Create immutable input/evidence folder for additive v70 candidate repair."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib, json, shutil
ROOT=Path(__file__).resolve().parents[1]

def main():
    v68=json.loads((ROOT/'results/span_repair_v68_release_20261011T215822_761796Z/spec.json').read_text())
    v69=json.loads((ROOT/'results/event_applicability_v69_20261012T022722_485396Z/spec.json').read_text())
    cases=[dict(c,audit_kind='regression') for c in v68['cases']]
    ids={c['id'] for c in cases}
    cases.extend(c for c in v69['cases'] if c['id'] not in ids)
    for f in v69['faults'][:-1]:
        base=next(c for c in cases if c['id']==f['base_id'])
        cases.append(dict(base,id=f['id']+'_repaired',input=f['input']))
    cases=[{k:c[k] for k in ['id','cfg','input','expected_modes','audit_kind']} for c in cases]
    faults=[dict(v69['faults'][-1],expected_guard='v70 unresolved enabled event ordering')]
    # Domain and enabled-boundary runtime controls, including valid prefix.
    base=next(c for c in cases if c['id']=='HP_only')
    for id,index,value,guard in [
        ('negative_demand',5,-1.,'v66 service input domain'),
        ('invalid_HP_enable',7,2.,'v66 service input domain'),
        ('invalid_strict_flag',3,2.,'v70 strict event flag'),
        ('delayed_negative_demand',5,-1.,'v66 service input domain')]:
        ii=[list(base['input'][0])];ii[0][index]=value
        if id.startswith('delayed'):
            valid=list(base['input'][0]);invalid=list(ii[0]);invalid[2]=2*valid[4]
            ii=[valid,invalid]
        faults.append(dict(id=id,base_id=base['id'],cfg=base['cfg'],input=ii,expected_guard=guard))
    # Disable direct HP: cutoff now genuinely active, so near boundary rejects.
    base=next(c for c in cases if c['id']=='HP_only_contact_strict0')
    ii=[list(base['input'][0])];ii[0][3]=1;ii[0][7]=0;ii[0][10]=0
    cfg=list(base['cfg']);cfg[40]=.01
    with localcontext() as ctx:
        ctx.prec=100
        D=lambda x:Decimal(Fraction(x).numerator)/Decimal(Fraction(x).denominator)
        cut=Fraction(cfg[35])*(Fraction(cfg[38])-Fraction(cfg[36]));lam=D(cfg[40])
        eq=D(-Fraction(ii[0][5])/Fraction(cfg[42]))/lam
        horizon=float(-((D(cut)-eq)/(D(ii[0][9])-eq)).ln()/lam)
    ii[0][2]=ii[0][4]=horizon
    faults.append(dict(id='active_cutoff_boundary_strict',base_id=base['id'],cfg=cfg,input=ii,expected_guard='v70 unresolved enabled event ordering'))
    base=next(c for c in cases if c['id']=='OFF_discharge_restart_0p0')
    cfg=list(base['cfg']);cfg[40]=.01
    # Positive loss leaves a strictly interior sampled SOC margin. Zero-loss
    # saturated full-horizon discharge may be refused by the inherited gate.
    with localcontext() as ctx:
        ctx.prec=100
        D=lambda x:Decimal(Fraction(x).numerator)/Decimal(Fraction(x).denominator)
        cut=Fraction(cfg[35])*(Fraction(cfg[38])-Fraction(cfg[36]))
        lam=D(cfg[40]);eq=D(-Fraction(.5)/Fraction(cfg[42]))/lam
        cutoff_time=float(-((D(cut)-eq)/(D(8.5)-eq)).ln()/lam)
    cfg[57]=cutoff_time
    ii=[[1,0,6,0,6,.5,20,1,1,8.5,0,0]]
    cases.append(dict(id='enabled_pair_collision',cfg=cfg,input=ii,expected_modes=[4],audit_kind='pair_collision'))
    ii=[list(ii[0])];ii[0][3]=1
    faults.append(dict(id='enabled_pair_collision_strict',base_id='enabled_pair_collision',cfg=cfg,input=ii,expected_guard='v70 unresolved enabled event ordering'))
    for id,dwell in [('enabled_pair_cutoff_first',cutoff_time+.5),('enabled_pair_restart_first',2.)]:
        cfg=list(base['cfg']);cfg[40]=.01;cfg[57]=dwell
        cases.append(dict(id=id,cfg=cfg,input=[[1,0,6,1,6,.5,20,1,1,8.5,0,0]],expected_modes=[4],audit_kind=id))
    cfg=list(base['cfg']);cfg[40]=.2
    cases.append(dict(id='future_charge_sink_above_stop',cfg=cfg,input=[[1,0,1,1,1,0,20,1,1,9.7,0,1]],expected_modes=[0],audit_kind='future_charge_sink'))
    cfg=list(base['cfg']);cfg[40]=.125;cfg[41]=1.;cfg[43]=1.2
    ii=[[1,0,1,0,1,0,20,1,1,8,1,1]]
    cases.append(dict(id='unresolved_stop_monotonicity',cfg=cfg,input=ii,expected_modes=[2],audit_kind='unresolved_monotonicity'))
    ii=[list(ii[0])];ii[0][3]=1
    faults.append(dict(id='unresolved_stop_monotonicity_strict',base_id='unresolved_stop_monotonicity',cfg=cfg,input=ii,expected_guard='v70 unresolved enabled event ordering'))
    faults=[{k:f[k] for k in ['id','base_id','cfg','input','expected_guard']} for f in faults]
    folder=ROOT/'results'/('event_candidates_v70_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'))
    folder.mkdir()
    (folder/'spec.json').write_text(json.dumps(dict(version='0.70',cases=cases,faults=faults),indent=2)+'\n')
    prior=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    prior=[p for p in prior if 'v70' not in p.name or p.name=='DCHR_Event_Candidates_Stateflow_v70.slx']
    (folder/'preservation.json').write_text(json.dumps([dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in prior],indent=2)+'\n')
    sources=['audit/prepare_event_candidates_v70.py','audit/verify_event_candidates_v70.py','audit/run_event_candidates_v70.ps1','audit/Event_candidates_derivation_v70.md','matlab/run_event_candidates_v70.m','matlab/simulink/build_event_candidates_v70.m','matlab/simulink/interval_dispatch_kernel_v70.m','matlab/simulink/event_candidates_v70.m',
        'audit/verify_interval_dispatch_v66.py','audit/verify_span_repair_v68r2.py','audit/span_tail_review_v68r2.py','audit/verify_capacity_chain_v63.py','audit/verify_restart_chain_v64.py','audit/verify_interval_dispatch_v65.py','audit/earliest_service_reference_v66.py']
    model='matlab/simulink/DCHR_Event_Candidates_Stateflow_v70r2.slx'
    if (ROOT/model).exists():sources.append(model)
    manifest=[]
    for rel in sources:
        src=ROOT/rel;dst=folder/'source_snapshot'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
        manifest.append(dict(path=rel,sha256=hashlib.sha256(src.read_bytes()).hexdigest()))
    (folder/'source_hashes.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(folder.relative_to(ROOT).as_posix())
if __name__=='__main__':main()
