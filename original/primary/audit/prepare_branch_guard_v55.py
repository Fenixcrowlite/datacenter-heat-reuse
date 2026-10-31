from pathlib import Path
from datetime import datetime, timezone
import json, math, shutil, hashlib

ROOT=Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    folder=ROOT/'results'/('branch_guard_v55_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'))
    folder.mkdir()
    old=ROOT/'results/coupled_interface_v54_20261011T064243_962223Z'
    spec=json.loads((old/'spec.json').read_text()); spec['version']='0.55'
    vectors=[]
    for i,v in enumerate(json.loads((old/'report.json').read_text())['vectors']):
        vectors.append(dict(id=f'v54_{i}',s=v['spec'],p=v['policy'],E=v['energy'],request=v['request'],legacy_branch=v['boundary']['tank_branch']))
    s=spec['boundary']; p=spec['policy']
    for shift in [0., 16., -16.]:
        ss=dict(s);pp=dict(p);pp['ambient_C']+=shift
        for key in ['source_in_C','tank_max_C','delivery_C']:ss[key]+=shift
        for steps in [-128,-32,-8,-2,-1,0,1,2,8,32,128]:
            E=5.
            for _ in range(abs(steps)):E=math.nextafter(E,math.inf if steps>0 else -math.inf)
            vectors.append(dict(id=f'kink_{shift}_{steps}',s=ss,p=pp,E=E,request=8.,legacy_branch=None))
    for C in [2.**-900,2.**-500,2.**-40,.2,2.**40,2.**500,2.**900]:
        pp=dict(p);pp['heat_capacity_MWh_per_K']=C
        for rise in [0.,10.,25.,40.,48.]:
            vectors.append(dict(id=f'scale_{C}_{rise}',s=s,p=pp,E=C*rise,request=8.,legacy_branch=None))
    for E in [0.,math.ulp(0.),math.ulp(0.)*2,math.ulp(0.)*128]:
        pp=dict(p);pp['heat_capacity_MWh_per_K']=math.ulp(0.)*1024
        vectors.append(dict(id=f'subnormal_{E}',s=s,p=pp,E=E,request=8.,legacy_branch=None))
    # Source/hot/nameplate/request ties and close neighbors are diagnostics.
    for hot in [.6,2.3,4.]:
        for req in [1.,4.,8.]:
            ss=dict(s);ss['hot_capacity_MW_per_K']=hot
            vectors.append(dict(id=f'limiter_{hot}_{req}',s=ss,p=p,E=9.6,request=req,legacy_branch=None))
    spec['vectors']=vectors;spec['scope']='INSTANTANEOUS_CONSERVATIVE_GATE_WITH_SAVED_V52_SAMPLED_CONTROLS'
    (folder/'spec.json').write_text(json.dumps(spec,indent=2)+'\n')
    prior=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    prior+=[old/'report.json',old/'spec.json',ROOT/'audit/research_frontier_2026_10_08.md']
    (folder/'preservation.json').write_text(json.dumps([dict(path=x.relative_to(ROOT).as_posix(),sha256=sha(x)) for x in prior if 'v55' not in x.name],indent=2)+'\n')
    snapshot=[]
    for x in list((ROOT/'matlab').rglob('*v55.m'))+list((ROOT/'audit').glob('*v55.*')):
        dest=folder/'source_snapshot'/x.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(x,dest)
        snapshot.append(dict(path=x.relative_to(ROOT).as_posix(),sha256=sha(x)))
    (folder/'source_hashes.json').write_text(json.dumps(snapshot,indent=2)+'\n')
    print(folder.relative_to(ROOT).as_posix())
if __name__=='__main__': main()
