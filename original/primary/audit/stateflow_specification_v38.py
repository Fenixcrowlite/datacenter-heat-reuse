"""Independent fixtures/oracles, without importing production MATLAB code."""
from pathlib import Path
from datetime import datetime,timezone
import copy,csv,json,math
from stateflow_reference_v34 import dispatch,PORTS,HP
ROOT=Path(__file__).resolve().parents[1]
def main():
    prior=json.loads((ROOT/'audit/stateflow_spec_v36_20261010T074004_533303Z/cases.json').read_text())
    stress=json.loads((ROOT/'audit/stateflow_spec_v37_20261010T075547_199176Z/cases.json').read_text())
    cases=copy.deepcopy(prior['cases'])
    for c in cases:c.update(kind='reference',expected_reject=False)
    vectors=[]
    for c in cases:
        e=c['initial_energy_MWh'];m=c['initial_clock']
        for i,x in enumerate(c['inputs']):
            y,ss,m=dispatch(e,x,c['p'],c['h'],m,c['c'])
            vectors.append(dict(scenario_id=c['id'],step=i,**dict(zip(PORTS+HP,y))))
            e=y[7]
    for c in copy.deepcopy(stress['cases'][6:]):
        c['expected_reject']=c['kind']=='band' and c['gap_ulps']<=128
        cases.append(c)
    bandbase=copy.deepcopy(stress['cases'][-3])
    for gap in (1,64,128,129,256):
        c=copy.deepcopy(bandbase)
        c.update(id=f'cutoff_restart_gap_{gap}',kind='cutoff_band',gap_ulps=gap,expected_reject=gap<=128)
        c['c'][0]=c['p'][7]+gap*math.ulp(c['p'][1]);cases.append(c)
    for cap in (8.,1e-300,1e-309):
        for request in (.1,.5,1.,2.):
            for source in (.03,.5,1.):
                for penalty in (0.,.3,.8):
                    for minimum in (1.2,3.5):
                        pass
    probes=[]
    # 216 finite operating/OFF/source-limited combinations plus extremes.
    for cap in (8.,1e-300,1e-309):
        for request in (.1,.5,1.,2.):
            for source in (.03,.5,1.):
                for penalty in (0.,.3,.8):
                    for minimum in (1.2,3.5):
                        probes.append(dict(id=f'hp_{len(probes):03d}',cap_MW=cap,request_MW=cap*request,
                            source_MW=cap*source,penalty=penalty,cop_min=minimum,expected_reject=False))
    probes += [dict(id='huge_request_tiny_capacity',cap_MW=1e-309,request_MW=1e308,source_MW=1.,penalty=.3,cop_min=1.2,expected_reject=False),
        dict(id='electric_underflow',cap_MW=math.ulp(0.),request_MW=math.ulp(0.),source_MW=math.ulp(0.),penalty=.3,cop_min=1.2,expected_reject=True),
        dict(id='zero_capacity',cap_MW=0.,request_MW=8.,source_MW=8.,penalty=.3,cop_min=1.2,expected_reject=False)]
    base=copy.deepcopy(stress['cases'][6])
    for name,clock in [('bad_low',[0.,1.,1e-4,0.]),('bad_bound',[0.,1.,0.,1e-7]),('unresolved_age',[0.,1e12,0.,0.])]:
        c=copy.deepcopy(base);c.update(id=name,kind='clock_domain',initial_clock=clock,expected_reject=True);cases.append(c)
    # Dwell exactly straddled by a signed residual: no one-ulp early restart.
    for low in (-math.ulp(.25)/4,0.,math.ulp(.25)/4):
        c=copy.deepcopy(base);c.update(id=f'dwell_residual_{low:g}',kind='dwell',initial_energy_MWh=6.,
            initial_clock=[0.,.25,low,0.],expected_reject=False)
        c['p'][0]=.01;c['inputs']=[[6.,35.,75.,1.,45.]];cases.append(c)
    for c in cases:
        if len(c['initial_clock'])==2:c['initial_clock'] += [0.,0.]
    folder=ROOT/'audit'/('stateflow_spec_v38_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'));folder.mkdir()
    spec=dict(version='0.38',cases=cases,hp_probes=probes,assumptions='Engineering/numerical fixtures only; no calibrated equipment or article values',
        prior_reference='v34 independent Decimal/bisection model, v36 preserved executed fixture set',clock_accuracy_budget_h=1e-8)
    (folder/'cases.json').write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8')
    with (folder/'vectors.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=vectors[0]);w.writeheader();w.writerows(vectors)
    print('SPEC='+str(folder.relative_to(ROOT)))
if __name__=='__main__':main()
