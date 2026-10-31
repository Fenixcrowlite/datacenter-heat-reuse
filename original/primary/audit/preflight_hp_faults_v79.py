"""Check fixture algebra before expensive runtime fault compilations."""
import copy,json,math,sys
from hp_partition_v79 import ROOT,dump,stamp
from energy_checks_v78 import energy_checks
from hp_partition_checks_v79 import hp_checks
from earliest_closed_form_v73 import rows

folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
prior=json.loads((ROOT/'results/energy_commit_v78_20261013T050754_608388Z/report.json').read_text())
base=next(r for r in prior['runs'] if r['id']=='HP_only')
checks=[]
def mul(x,s):
    if s==0 or x==[0,0]:return [0,0]
    v=[t*s for t in x];return [v[0]-2*math.ulp(v[0]),v[1]+2*math.ulp(v[1])]
for w in [0.,1.,.5,.01,'wide']:
    bad=copy.deepcopy(base);r=rows(bad['trace'])[0];h=r[131:133]
    work=mul(h,w) if w!='wide' else [0,0]
    source=mul(h,1-w) if w!='wide' else [0,h[1]]
    aux=mul(work,base['p'][20])
    for offset in [133,16,32]:r[offset:offset+4]=source+work
    for offset in [149,48]:r[offset:offset+2]=aux
    cs=energy_checks(bad);hs=hp_checks(bad)
    checks.append(dict(name=str(w)+'_v78_algebra_passes',passed=all(c['passed'] for c in cs),failed=[c for c in cs if not c['passed']]))
    checks.append(dict(name=str(w)+'_v79_rejects',passed=any(not c['passed'] for c in hs)))
off=copy.deepcopy(next(r for r in prior['runs'] if r['id']=='zero_demand'));r=rows(off['trace'])[0]
for offset in [133,16,32]:r[offset:offset+4]=[0,.01,0,0]
for offset in [149,48]:r[offset:offset+2]=[0,0]
checks.append(dict(name='OFF_v78_algebra_passes',passed=all(c['passed'] for c in energy_checks(off))))
checks.append(dict(name='OFF_v79_rejects',passed=any(not c['passed'] for c in hp_checks(off))))
result=dict(evidence_class='SYNTHETIC_FIXTURE_PREFLIGHT_NOT_RUNTIME_ACCEPTANCE',checks=checks,
    summary=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks)))
dump(folder/('fixture_preflight_'+stamp()+'.json'),result);print(json.dumps(result));sys.exit(int(result['summary']['failed']>0))
