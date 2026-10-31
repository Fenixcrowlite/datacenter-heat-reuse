"""Independent exact-binary logarithmic/corner QA of compiled root witnesses.

No production MATLAB functions imported. Reuses the independent v66 analytic
reviewer only for the unchanged sampled plant, and its closed source integral.
"""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal as D, localcontext
from datetime import datetime, timezone
from itertools import product
import json, struct, hashlib, zipfile, csv, copy, sys
import xml.etree.ElementTree as ET
from verify_interval_dispatch_v66 import analyze, storage
from verify_capacity_chain_v63 import dec, contains
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def review(E,B,lam,target,direction,H,dwell,age,z):
    """All 8 box corners using exp/log, unlike production Taylor/bisection."""
    E,B,target,age=[list(map(F,v)) for v in [E,B,target,age]]
    lam,H,dwell=map(F,[lam,H,dwell]);s=int(z[0]);checks={}
    before=lambda v: v<dec(target[0]) if direction==1 else v>dec(target[1])
    after=lambda v: v>dec(target[1]) if direction==1 else v<dec(target[0])
    checks['finite']=all(abs(v)<float('inf') for v in z)
    checks['target_direction']=z[12]==direction and list(map(F,z[13:15]))==target
    waits=[max(F(0),dwell-v) for v in age]
    checks['wait']=all(contains(z[7:9],v) for v in waits)
    rootvalues=[];cornerdata=[]
    for e,b,g in product(E,B,target):
        if (direction==1 and e>=g) or (direction==-1 and e<=g):t=D(0)
        elif not lam:
            t=dec((g-e)/b) if b else D('Infinity')
        else:
            eq=b/lam;ratio=dec(g-eq)/dec(e-eq) if e!=eq else D(-1)
            t=-ratio.ln()/dec(lam) if 0<ratio<1 else D('Infinity')
        rootvalues.append(t);cornerdata.append((e,b,g,t))
    if s==1:
        checks['root_box']=all(contains(z[1:3],t) and 0<t<dec(H) for t in rootvalues)
        checks['positive_bracket']=0<=z[1]<z[2]<float(H)
        for n,(e,b,g,t) in enumerate(cornerdata):
            elo,_=storage(dec(e),b,lam,dec(F(z[1])));ehi,_=storage(dec(e),b,lam,dec(F(z[2])))
            checks[f'corner_{n}_left']=before(elo) and contains(z[3:5],elo)
            checks[f'corner_{n}_right']=after(ehi) and contains(z[5:7],ehi)
            checks[f'corner_{n}_derivative']=direction*(b-lam*e)>0 and direction*(b-lam*g)>0
        readiness=[max(t,dec(w)) for t,w in product(rootvalues,waits)]
        checks['ready_box']=all(contains(z[9:11],v) for v in readiness)
    elif s==0:
        checks['no_crossing']=all(t>dec(H) for t in rootvalues)
        checks['no_order_claim']=z[11]==0
        for n,(e,b,g,t) in enumerate(cornerdata):
            end,_=storage(dec(e),b,lam,dec(H))
            checks[f'corner_{n}_no_crossing']=before(end) and contains(z[3:5],end)
    elif s==3:
        checks['already_reached']=all(t==0 for t in rootvalues) and z[1]==z[2]==0
        checks['ready_wait']=all(contains(z[9:11],w) for w in waits)
    elif s==2:
        # Unresolved enclosures may include an exact-root tie OR a very small
        # nonzero binary gap; never call an approximate coincidence exact.
        checks['refused_order']=z[11]==2 and z[1]==0 and F(z[2])==H
    else:checks['valid_status']=False
    if s in [1,3]:
        order=1 if F(z[10])<H else 3 if F(z[9])>H else 2
        checks['ordering']=z[11]==order
    return checks,rootvalues

def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    report=json.loads((folder/'report.json').read_text());checks=[];mutations=[];numeric=[]
    def check(kind,name,ok):checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    check('MAT','reopened',report==json.loads((folder/'mat_reopen.json').read_text()))
    check('MAT','original',(folder/'event_brackets_v67.mat').stat().st_size>1000)
    binary={}
    runs={r['id']:r for r in report['runs']}
    for rec in json.loads((folder/'binary_manifest.json').read_text()):
        flat=[v[0] for v in struct.iter_unpack('<d',(folder/rec['file']).read_bytes())];c=rec['columns']
        value=[flat[k:k+c] for k in range(0,len(flat),c)]
        if rec['rows']==1:value=value[0]
        key=rec['id'],rec['field'];binary[key]=value
        check('binary',str(key),value==runs[key[0]][key[1]] and len(flat)==rec['rows']*c)
    certificates=[];statuscounts={};orderingcounts={}
    with localcontext() as ctx:
        ctx.prec=160
        for id,r in runs.items():
            cfg=binary[id,'cfg'];u=binary[id,'input'];tr=binary[id,'trace']
            if isinstance(u[0],(int,float)):u=[u]
            if isinstance(tr[0],(int,float)):tr=[tr]
            ac,nums=analyze(cfg,u,[row[:205] for row in tr])
            for name,ok in ac.items():check('sampled_analytic',id+'_'+name,ok)
            check('MAT',id+'_original',(folder/(id+'.mat')).stat().st_size>1000)
            p=cfg[35:60]
            for tick,(uu,row) in enumerate(zip(u,tr)):
                if uu[0]==0:continue
                for j,label in enumerate(['stop','cutoff','restart']):
                    z=row[205+15*j:220+15*j]
                    if z[12]==0:
                        check('inactive',f'{id}_{tick}_{label}',all(v==0 for v in z));continue
                    B=row[250+2*j:252+2*j]
                    age=row[161:163] if j==2 else [0,0]
                    dwell=p[22] if j==2 else 0
                    E=row[159:161];H=uu[4];direction=1 if j==0 else -1
                    c,roots=review(E,B,p[5],z[13:15],direction,H,dwell,age,z)
                    for name,ok in c.items():check('root',f'{id}_{tick}_{label}_{name}',ok)
                    target=F(p[0])*(F(p[{0:24,1:3,2:4}[j]])-F(p[1]))
                    check('threshold',f'{id}_{tick}_{label}',contains(z[13:15],target))
                    statuscounts[str(int(z[0]))]=statuscounts.get(str(int(z[0])),0)+1
                    orderingcounts[str(int(z[11]))]=orderingcounts.get(str(int(z[11])),0)+1
                    numeric.append(dict(id=id,tick=tick,event=label,status=int(z[0]),order=int(z[11]),
                        root_lo=z[1],root_hi=z[2],ready_lo=z[9],ready_hi=z[10],
                        exact_corner_root_lo=str(min(roots)),exact_corner_root_hi=str(max(roots))))
                    certificates.append((E,B,p[5],z[13:15],direction,H,dwell,age,z))
            # SAME saved chart retains the exact sampled plant numeric contract.
            check('scope',id+'_schema66_preserved',all(row[179]==66 for row in tr))
        for r in report['root_probes']:
            c,roots=review(r['E'],r['B'],r['lambda'],r['target'],r['direction'],r['horizon'],r['dwell'],r['age'],r['output'])
            for name,ok in c.items():check('probe',r['id']+'_'+name,ok)
            certificates.append(tuple(r[k] for k in ['E','B','lambda','target','direction','horizon','dwell','age','output']))
        for label,index in [('root_collapsed',1),('false_order',11),('left_witness_erased',3),('ready_erased',9),('target_corrupted',13)]:
            base=next(v for v in certificates if v[-1][0]==1)
            altered=copy.deepcopy(base);z=altered[-1]
            if index==1:z[1]=z[2]
            elif index==11:z[11]=3
            elif index in [3,9]:z[index:index+2]=[0,0]
            else:z[13:15]=[v+1 for v in z[13:15]]
            c,_=review(*altered);mutations.append(dict(name=label,passed=not all(c.values())))
        # Clock/readiness corruption has its own passive thermal restart case.
        base=next(v for v in certificates if v[6]>0 and v[-1][0]==1)
        altered=copy.deepcopy(base);altered[-1][7:9]=[0,0]
        c,_=review(*altered);mutations.append(dict(name='OFF_dwell_wait_erased',passed=not all(c.values())))
    check('coverage','six_modes',report['mode_coverage']==list(range(6)))
    for status in ['0','1','2','3']:check('coverage','root_status_'+status,statuscounts.get(status,0)>0)
    check('MATLAB','assertions',report['summary']['failed']==0 and all(c['passed'] for c in report['assertions']))
    check('faults','actual_rejections',len(report['faults'])==12 and all(f['identifier'] and f['expected_guard'] in f['message'] for f in report['faults']))
    check('metadata','chart',report['metadata']['chart_count']==1 and report['metadata']['license_observed']==1 and report['metadata']['simulation_mode']=='normal')
    mdl=ROOT/'matlab/simulink/DCHR_Event_Brackets_Stateflow_v67r2.slx'
    with zipfile.ZipFile(mdl) as ar:
        scripts=[];xml=''
        for n in ar.namelist():
            if n.endswith('.xml'):
                data=ar.read(n);xml+=data.decode(errors='replace')
                scripts.extend(p.text for p in ET.fromstring(data).iter('P') if p.attrib.get('Name')=='script')
        for file in ['interval_dispatch_kernel_v66.m','event_observer_v67.m']:
            check('SLX','embedded_'+file,any(s and s.strip()==(ROOT/'matlab/simulink'/file).read_text().strip() for s in scripts))
        for name in ['IDLE','HEAT_RECOVERY','STORAGE_CHARGE','STORAGE_DISCHARGE','BACKUP','UNMET_DEMAND']:check('SLX',name,name in xml)
    for name in ['preservation.json','source_hashes.json']:
        for rec in json.loads((folder/name).read_text()):
            ok=sha(ROOT/rec['path'])==rec['sha256']
            if name=='source_hashes.json':ok=ok and sha(folder/'source_snapshot'/rec['path'])==rec['sha256']
            check(name,rec['path'],ok)
    receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')]
    check('execution','observed_batch_exit0',any(r['exit_code']==0 and r.get('evidence_class')=='OBSERVED_LOCAL_MATLAB_BATCH' for r in receipts))
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    csvpath=folder/f'root_traces_v67_{stamp}.csv'
    with csvpath.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(numeric[0]));w.writeheader();w.writerows(numeric)
    result=dict(version='0.67',timestamp_utc=datetime.now(timezone.utc).isoformat(),checks=checks,reviewer_selfchecks=mutations,
        model_sha256=sha(mdl),root_status_counts=statuscounts,ordering_counts=orderingcounts,
        active_certificates=len(numeric),runs=len(runs),root_probes=len(report['root_probes']),
        summary=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks)),numeric_csv=csvpath.name,
        independence='Same-agent independent Fraction/160-digit closed exp/log and all corner algorithms; unchanged sampled plant uses prior independent analytic QA. Not independent personnel or measured evidence.')
    (folder/f'independent_QA_v67_{stamp}.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(summary=result['summary'],mutations=mutations,failures=[c for c in checks if not c['passed']][:30]),indent=2))
    assert result['summary']['failed']==0 and all(v['passed'] for v in mutations)

if __name__=='__main__':main()
