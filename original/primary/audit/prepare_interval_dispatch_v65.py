from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def policy(c):
    return [c[4],c[5],c[18],c[6]+3,c[34],c[3],c[2],.8,c[17],4,c[15],
            c[10],c[11],c[12],c[13],c[14],c[8],c[9],c[6],c[7],c[19],.25,c[33],2,c[18]-2]
def pure(id,c,mode,E,demand,source,enable,charge,age=1):
    u=[1,0,.1,0,.1,demand,source,enable,charge,E,enable,age]
    return dict(id=id,cfg=c+policy(c),input=[u],expected_modes=[mode])
def main():
    folder=ROOT/'results'/('interval_dispatch_v65_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'));folder.mkdir()
    prior=ROOT/'results/restart_chain_v64_20261011T165507_763815Z/report.json'
    previous=json.loads(prior.read_text());c=previous['runs'][0]['cfg'];cases=[]
    cases.extend([pure('zero_demand',c,0,3,0,0,0,0),pure('HP_only',c,1,3,.5,20,1,0),
        pure('TES_charge',c,2,3,0,20,1,1),pure('TES_discharge',c,3,9,.5,0,0,0),
        pure('boiler_limit',c,4,3,2,0,0,0),pure('insufficient_heat',c,5,3,3,0,0,0)])
    unit=pure('unit_efficiency_zero_loss',c,3,9,.5,0,0,0)
    unit['cfg'][40]=0;unit['cfg'][42]=1
    cases.append(unit)
    cases.append(pure('near_cutoff_no_credit',c,4,.2*28+.001,.5,0,0,0))
    for item in [previous['runs'][0],previous['runs'][-1]]:
        c=item['cfg'];p=policy(c);inputs=[]
        for s in item['steps']:
            inputs.append([0,s[1],s[2],s[3],0,0,0,0,0,0,0,0])
        horizon=item['steps'][-1][2]
        for dt,demand,source,enable,charge in [(.1,.5,20,1,0),(.1,1,0,0,0),(.1,6,0,0,0),
                    (.1,8,0,0,0),(1,0,0,0,0),(.25,.25,20,1,0),(.1,0,20,1,1),(.1,.75,0,0,0)]:
            horizon+=dt;inputs.append([1,0,horizon,0,dt,demand,source,enable,charge,0,0,0])
        cases.append(dict(id='retained_'+item['id'].replace('.','p'),cfg=c+p,input=inputs,expected_modes=list(range(6)),
                          prefix_origin=prior.relative_to(ROOT).as_posix(),prefix_id=item['id']))
    c=previous['runs'][0]['cfg'];p=policy(c);inputs=[];t=0
    # Demonstrate sampled high-temperature safety OFF and interval-certified restart.
    for dt,demand,source,enable,charge in [(.1,0,20,1,1),(25,0,0,0,0),(.1,0,20,1,1),(.3,.5,20,1,0),(.1,.5,20,0,0)]:
        t+=dt;inputs.append([1,0,t,0,dt,demand,source,enable,charge,9.8,1,1])
    cases.append(dict(id='sampled_capacity_restart',cfg=c+p,input=inputs,expected_modes=[0,1,2,3]))
    inputs=[];t=0
    for dt,demand,source,enable in [(.1,.5,20,1),(.1,.6,20,1),(.1,.7,20,1),(.1,2.5,0,0),(.1,.5,20,1),(.3,.5,20,1),(.1,.5,20,1)]:
        t+=dt;inputs.append([1,0,t,0,dt,demand,source,enable,0,3,1,1])
    cases.append(dict(id='delayed_fault_control',cfg=c+p,input=inputs,expected_modes=[1,4,5]))
    (folder/'spec.json').write_text(json.dumps(dict(version='0.65',cases=cases),indent=2)+'\n')
    files=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    (folder/'preservation.json').write_text(json.dumps([dict(path=f.relative_to(ROOT).as_posix(),sha256=sha(f)) for f in files if 'v65' not in f.name],indent=2)+'\n')
    sources=files+list((ROOT/'audit').glob('*v65.*'))+[ROOT/'audit/verify_restart_chain_v64.py',ROOT/'audit/verify_capacity_chain_v63.py']
    manifest=[]
    for f in sources:
        dest=folder/'source_snapshot'/f.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest)
        manifest.append(dict(path=f.relative_to(ROOT).as_posix(),sha256=sha(f)))
    (folder/'source_hashes.json').write_text(json.dumps(manifest,indent=2)+'\n');print(folder.relative_to(ROOT).as_posix())
if __name__=='__main__':main()
