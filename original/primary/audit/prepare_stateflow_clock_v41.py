"""Additive saved-v40 uncertainty fixtures; no production/model edits."""
from pathlib import Path
from datetime import datetime, timezone
import copy, hashlib, json, math
ROOT = Path(__file__).resolve().parents[1]

def main():
    prior = json.loads((ROOT/'audit/stateflow_hp_spec_v40_20261010T124353_401821Z/cases.json').read_text())
    cases = [copy.deepcopy(c) for c in prior['cases'] if c['id']=='mode_sequence']
    hp_only=copy.deepcopy(cases[0]);hp_only.update(id='dedicated_heat_recovery',
        initial_energy_MWh=5.,inputs=[[6.,35.,75.,2.,45.]],initial_clock=[1.,0.,0.,0.])
    hp_only['p'][2]=0.
    cases.append(hp_only)
    backup=copy.deepcopy(hp_only);backup.update(id='dedicated_backup',inputs=[[0.,35.,75.,1.,45.]])
    backup['p'][10]=2.
    cases.append(backup)
    # All following numbers are numerical fixtures, not equipment measurements.
    for on in (0, 1):
        for label, age, low, bound in (
            ('exact', 1., 0., 0.),
            ('uncertain_equal', 1., 0., 1e-9),
            ('uncertain_before', 1.-5e-10, 0., 1e-9),
            ('uncertain_after', 1.+5e-10, 0., 1e-9),
            ('certain_before', 1.-2e-9, 0., 1e-9),
            ('certain_after', 1.+2e-9, 0., 1e-9),
            ('negative_residual', 1., -math.ldexp(1.,-55), 0.),
            ('positive_residual', 1., math.ldexp(1.,-55), 0.),
            ('low_bound', 1., 0., math.ldexp(1.,-80)),
            ('invalid_budget', 1., 0., 2e-8),
        ):
            cases.append(dict(id=f'{"on" if on else "off"}_{label}', kind='clock_seed',
                initial_energy_MWh=10. if on else 7., initial_clock=[on,age,low,bound],
                p=[.125,10.,3.,4.,.9,.8,.1,5.,.2,20.,.5],
                h=[8.,.45,1.2,8.,0.,1.,4.,0.,0.],
                c=[8.,1.,1.,64], inputs=[[6.,35.,75.,1.,45.]],
                expected_reject=label=='invalid_budget', clock_label=label))
    # Exact capacity and cutoff/dwell coincidences, and +/- one binary64 ulp.
    # Zero loss makes the boundary times independently rational, avoiding log oracle reuse.
    for event in ('capacity','cutoff'):
        for direction in (-1,0,1):
            dwell=1. if direction==0 else math.nextafter(1., math.inf if direction>0 else -math.inf)
            p=[1.5,10.,3.,4.,1.,1.,0.,5.,.2,20.,.5]
            cases.append(dict(id=f'tie_{event}_{direction+1}',kind='event_tie',
                initial_energy_MWh=7. if event=='capacity' else 6.,
                initial_clock=[1.,0.,0.,0.] if event=='capacity' else [0.,0.,0.,0.],
                p=p,h=[8.,.45,1.2,8.,0.,1.,4.,0.,0.],c=[8.,dwell,dwell,64],
                inputs=[[6.,35.,75.,0. if event=='capacity' else 1.,45.]],
                expected_reject=False,event=event,dwell_direction=direction))
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    folder=ROOT/'audit'/('stateflow_clock_spec_v41_'+stamp);folder.mkdir()
    spec=dict(version='0.41',model_release='0.40',new_model=False,cases=cases,
        assumptions='Valid seed denotes physical age in [hi+lo-bound,hi+lo+bound]. Engineering numerical-domain audit, no measured ages or primary-source equations.')
    (folder/'cases.json').write_text(json.dumps(spec,indent=2)+'\n')
    files=[]
    for parent in ('matlab','audit'):
        for path in (ROOT/parent).rglob('*'):
            if path.is_file() and (path.suffix in ('.m','.slx') and path.parent.name!='slprj'):
                files.append(dict(path=path.relative_to(ROOT).as_posix(),bytes=path.stat().st_size,
                    sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    (folder/'preservation.json').write_text(json.dumps(dict(files=files),indent=2)+'\n')
    print('SPEC='+folder.relative_to(ROOT).as_posix())
if __name__=='__main__':main()
