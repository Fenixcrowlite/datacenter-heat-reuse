from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, shutil, random

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    folder=ROOT/'results'/('charge_regimes_v56_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'))
    folder.mkdir()
    old=json.loads((ROOT/'results/branch_guard_v55_20261011T064903_468947Z/spec.json').read_text())
    s,p=old['boundary'],old['policy'];cases=[]
    def case(id,E,request=50.,ss=None,pp=None,expected='ACCEPT'):
        cases.append(dict(id=id,E=E,request=request,s=ss or dict(s),p=pp or dict(p),expected=expected))
    for branch,E in [('FLOOR',3.),('TANK',7.)]:
        for mode in ['REQUEST','NAMEPLATE','HOT_FLOW','SOURCE','TES_PORT']:
            ss=dict(s,hp_capacity_MW=30.,source_capacity_MW_per_K=20.,hot_capacity_MW_per_K=20.)
            pp=dict(p,charge_limit_MW=40.)
            req=50.
            if mode=='REQUEST':req=1.
            if mode=='NAMEPLATE':ss['hp_capacity_MW']=1.
            if mode=='HOT_FLOW':ss['hot_capacity_MW_per_K']=.02
            if mode=='SOURCE':ss['source_capacity_MW_per_K']=.02
            if mode=='TES_PORT':pp['charge_limit_MW']=1.
            for loss in [0.,.05,.5]:
                p2=dict(pp,loss_rate_per_h=loss)
                case(f'{branch}_{mode}_loss_{loss}',E,req,ss,p2)
    # Distinct active-limit switches on both sides of the outlet kink.
    case('floor_request_to_hot',3.,2.,dict(s,hot_capacity_MW_per_K=.2),dict(p,charge_limit_MW=20.,loss_rate_per_h=0.))
    case('tank_source_to_request',7.,5.1,dict(s),dict(p,charge_limit_MW=20.,loss_rate_per_h=0.))
    case('floor_branch',3.,4.,dict(s),dict(p,charge_limit_MW=20.,loss_rate_per_h=0.))
    case('tank_branch_cooling',7.,.2,dict(s),dict(p,charge_limit_MW=20.,loss_rate_per_h=.5))
    case('stationary',4.,1.,dict(s),dict(p,eta_charge=.5,loss_rate_per_h=.125))
    case('asymptotic_capacity',7.,2.5,dict(s),dict(p,eta_charge=.5,loss_rate_per_h=.125))
    case('negative_near_zero_k',7.,8.,dict(s),dict(p,loss_rate_per_h=.13))
    rng=random.Random(56)
    for j in range(100):
        ss=dict(s,hp_capacity_MW=rng.uniform(.2,12),hot_capacity_MW_per_K=rng.uniform(.02,4),source_capacity_MW_per_K=rng.uniform(.02,2))
        pp=dict(p,charge_limit_MW=rng.uniform(.2,12),loss_rate_per_h=rng.uniform(0,1))
        case(f'random_{j}',rng.uniform(.1,9.9),rng.uniform(.2,12),ss,pp)
    case('original_binary_kink',5.,8.,expected='REJECT')
    case('request_nameplate_tie',7.,8.,dict(s),dict(p,charge_limit_MW=20.),expected='REJECT')
    # Make request/nameplate the actual tied minima, rather than a masked tie.
    cases[-1]['s']['source_capacity_MW_per_K']=20.
    cases[-1]['s']['hot_capacity_MW_per_K']=20.
    case('tes_request_tie',3.,1.,dict(s),dict(p,charge_limit_MW=1.),expected='REJECT')
    case('initial_capacity',10.,1.,expected='REJECT')
    case('zero_request',3.,0.,expected='REJECT')
    case('negative_loss',3.,1.,pp=dict(p,loss_rate_per_h=-.1),expected='REJECT')
    case('zero_efficiency',3.,1.,pp=dict(p,eta_charge=0.),expected='REJECT')
    case('zero_port',3.,1.,pp=dict(p,charge_limit_MW=0.),expected='REJECT')
    case('negative_energy',-1.,1.,expected='REJECT')
    spec=dict(version='0.56',cases=cases)
    (folder/'spec.json').write_text(json.dumps(spec,indent=2)+'\n')
    prior=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    (folder/'preservation.json').write_text(json.dumps([dict(path=x.relative_to(ROOT).as_posix(),sha256=sha(x)) for x in prior if 'v56' not in x.name],indent=2)+'\n')
    sources=list((ROOT/'matlab').rglob('*v56.m'))+list((ROOT/'audit').glob('*v56.*'))
    sources += [ROOT/'matlab/+dchr/+components/coupled_branch_certificate_v55.m',ROOT/'matlab/+dchr/+components/coupled_temperature_boundary_v55.m',ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v52.slx']
    manifest=[]
    for x in sources:
        dest=folder/'source_snapshot'/x.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(x,dest)
        manifest.append(dict(path=x.relative_to(ROOT).as_posix(),sha256=sha(x)))
    (folder/'source_hashes.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(folder.relative_to(ROOT).as_posix())
if __name__=='__main__':main()
