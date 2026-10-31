"""Additive saved-v71 admissibility inputs and immutable pre-run seals."""
from pathlib import Path
from datetime import datetime, timezone
import copy, hashlib, json, shutil
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    prior=json.loads((ROOT/'results/earliest_dispatch_v71_20261012T030016_337397Z/spec.json').read_text())
    byid={c['id']:c for c in prior['cases']};cases=[]
    for id in ['zero_demand','HP_only','TES_charge','TES_discharge','boiler_limit','insufficient_heat','multiple_cycles_one_call']:
        c=copy.deepcopy(byid[id]);c['family']='baseline';cases.append(c)
    def add(id,base,p,ii,family):
        cases.append(dict(id=id,p=p,input=ii,expected_modes=[],min_events=0,family=family))
    for lam,n in [(0.01,256),(0.2,256),(1.0,80)]:
        p=copy.deepcopy(byid['HP_only']['p']);p[5]=lam
        ii=[[1,0,k+1,0,1,.5,20,1,0,3,1,1] for k in range(n)]
        add('passive_service_lambda_'+str(lam).replace('.','p'),'HP_only',p,ii,'passive_long')
    c=byid['repeated_1p0'];ii=[]
    for cycle in range(4):
        for old in c['input']:
            u=list(old);u[2]=len(ii)+1;ii.append(u)
    add('repeated_service_208h','repeated_1p0',c['p'],ii,'repeated_long')
    # Hold a physically identical disable boundary; exact dwell equality vs margin.
    for dt,n,minon,id in [(0.125,2,.25,'disable_exact_dwell'),(.125,3,.25,'disable_after_dwell'),(.125,1,.25,'disable_before_dwell')]:
        p=list(byid['HP_only']['p']);p[5]=0;p[21]=minon
        ii=[[1,0,(k+1)*dt,0,dt,.5,20,int(k<n),0,3,1,0] for k in range(n+1)]
        add(id,'HP_only',p,ii,'disable')
    # Active source, water, and almost coincident limiting operands.
    for source,id in [(.02,'source_limited'),(.1817,'near_source_water_tie'),(20,'water_limited')]:
        p=list(byid['HP_only']['p']);p[5]=0
        # Inventory below the floor-branch crossing: exact source ratio is constant.
        ii=[[1,0,.1,0,.1,2,source,1,0,3,1,1]]
        add(id,'HP_only',p,ii,'limiter')
    p=list(byid['HP_only']['p']);p[5]=0
    te=p[11]-p[12]-p[13];a=p[14]*(te+273.15)
    tie=p[15]*p[16]/(p[12]*(1+(p[18]+p[19]+p[17]-te)/a))
    for source,id in [(tie,'rounded_source_water_tie'),(tie*(1-2**-40),'source_below_tie'),(tie*(1+2**-40),'source_above_tie')]:
        add(id,'HP_only',p,[[1,0,.1,0,.1,2,source,1,0,3,1,1]],'limiter')
    for exponent in [10,20,32,42]:
        p=list(byid['multiple_cycles_one_call']['p']);band=2**-exponent;p[24]=p[4]+band;p[22]=0
        dt=band*.2;initial=p[0]*(p[4]-p[1])-band*.01
        add('restart_band_2m'+str(exponent),'multiple_cycles_one_call',p,[[1,0,dt,0,dt,0,20,1,1,initial,1,1]],'small_band')
    p=list(byid['multiple_cycles_one_call']['p']);p[24]=60.5;p[22]=0
    add('segment_budget_exhaustion','multiple_cycles_one_call',p,[[1,0,1,0,1,0,20,1,1,7.9,1,1]],'budget')
    folder=ROOT/'results'/('earliest_admissibility_v72_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'));folder.mkdir()
    (folder/'spec.json').write_text(json.dumps(dict(version='0.72',saved_model_version='0.71',cases=cases),indent=2)+'\n')
    paths=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    (folder/'preservation.json').write_text(json.dumps([dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in paths if 'v72' not in p.name],indent=2)+'\n')
    paths=[p for p in (ROOT/'audit').glob('*v72*') if p.is_file()]+[p for p in (ROOT/'matlab').rglob('*v72*') if p.is_file()]
    paths+=[ROOT/'audit/verify_earliest_dispatch_v71.py']
    manifest=[]
    for src in paths:
        rel=src.relative_to(ROOT).as_posix();dst=folder/'source_snapshot'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);manifest.append(dict(path=rel,sha256=sha(src)))
    (folder/'source_hashes.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(folder.relative_to(ROOT).as_posix())
if __name__=='__main__':main()
