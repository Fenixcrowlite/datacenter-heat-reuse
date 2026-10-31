"""Fresh saved-v36 numerical-domain experiment; constants are assumptions.

Clock oracle uses exact binary64 inputs in Decimal, never the host planner.
HP oracle uses dimensionless part load, never a COP/MW slope coefficient.
"""
from datetime import datetime, timezone
from pathlib import Path
import copy, csv, json, math
from stateflow_reference_v34 import scenarios, dispatch, PORTS, HP

ROOT = Path(__file__).resolve().parents[1]

def main():
    folder = ROOT/'audit'/('stateflow_spec_v37_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'))
    folder.mkdir()
    cases = scenarios()[:6]
    for c in cases: c['kind'] = 'baseline'
    vectors = []
    for c in cases:
        e, m = c['initial_energy_MWh'], c['initial_clock']
        for step, x in enumerate(c['inputs']):
            y, _, m = dispatch(e,x,c['p'],c['h'],m,c['c'])
            vectors.append(dict(scenario_id=c['id'],step=step,**dict(zip(PORTS+HP,y))))
            e = y[7]
    base = dict(p=[1.,10.,0.,4.,.9,.8,0.,5.,.2,20.,0.],
                h=[8.,.45,1.2,8.,0.,1.,4.,0.,0.],c=[8.,.25,.25,64.],
                initial_energy_MWh=6.,initial_clock=[0.,1e6])
    horizon = 1024*1e-10
    for age in (0.,1e6):
        for count in (1,16,128,1024):
            c = copy.deepcopy(base)
            c.update(id=f'clock_age_{age:g}_n_{count}',kind='clock',horizon_h=horizon)
            c['p'][0] = horizon/count
            c['initial_clock'][1] = age
            c['inputs'] = [[0.,35.,75.,0.,45.]]*count
            cases.append(c)
    c = copy.deepcopy(base)
    c.update(id='clock_changing_demand_n_1024',kind='clock',horizon_h=horizon)
    c['p'][0] = horizon/1024
    c['inputs'] = [[0.,35.,75.,0. if i<512 else .1,45.] for i in range(1024)]
    cases.append(c)
    c = copy.deepcopy(base)
    c.update(id='clock_nonadvancing',kind='nonadvancing')
    c['p'][0]=1e-12;c['inputs']=[[0.,35.,75.,0.,45.]]
    cases.append(c)
    for gap in (1,32,64,65,128,256):
        c = copy.deepcopy(base)
        c.update(id=f'band_gap_{gap}_ulp',kind='band',gap_ulps=gap,initial_energy_MWh=10.)
        c['p'][0]=.001;c['p'][2]=3.;c['c'][0]=10.-gap*math.ulp(10.)
        c['initial_clock']=[0.,.25];c['inputs']=[[6.,35.,75.,0.,45.]]*2
        cases.append(c)
    for cap in (1e-300,1e-309):
        c = copy.deepcopy(base)
        c.update(id=f'hp_runtime_{cap:g}',kind='hp_runtime')
        c['p'][0]=.001;c['initial_clock']=[1.,0.]
        c['h'][0]=cap;c['h'][4]=.3
        c['inputs']=[[cap,35.,75.,cap,45.]]
        cases.append(c)
    probes = [dict(id=f'hp_component_{cap:g}',cap_MW=cap,source_MW=cap,request_MW=cap)
              for cap in (8.,1e-300,1e-308,1e-309)]
    spec = dict(version='0.37',model_version='0.36',cases=cases,hp_probes=probes,
                assumptions='Numerical stress fixtures only, no calibrated hardware or article values',
                question='Does local positive clock progress bound global drift; do band/HP domains reject unsupported resolution?')
    (folder/'cases.json').write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8')
    with (folder/'baseline_vectors.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=vectors[0]);w.writeheader();w.writerows(vectors)
    print('SPEC='+str(folder.relative_to(ROOT)))

if __name__=='__main__':main()
