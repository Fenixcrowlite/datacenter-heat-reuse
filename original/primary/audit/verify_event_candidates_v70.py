"""Independent exact-binary/closed-form QA; never calls production MATLAB."""
from pathlib import Path
from datetime import datetime, timezone
from fractions import Fraction as F
from decimal import Decimal as D, localcontext
import copy, csv, hashlib, json, struct, sys, zipfile
import xml.etree.ElementTree as ET
from verify_interval_dispatch_v66 import analyze
from verify_span_repair_v68r2 import review
from verify_capacity_chain_v63 import dec, contains
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(v):return [v] if isinstance(v[0],(int,float)) else v

def candidate_review(cfg,u,row):
    p=list(map(F,cfg[35:60]));E=list(map(F,row[159:161]));age=list(map(F,row[161:163]));z=row[205:]
    stop,cut,restart=[p[0]*(p[k]-p[1]) for k in [24,3,4]]
    Te=p[11]-p[12]-p[13];a=p[14]*(Te+F(273.15));floor=p[18]+p[19]
    exactlimit=min(p[10],F(u[6])*p[12]*(1+(floor+p[17]-Te)/a),p[15]*p[16])
    exactpotential=max(F(0),min(p[8],exactlimit-min(F(u[5]),exactlimit)))
    hp,direct,charge,dis=map(F,z[54:58]);B=p[6]*charge-dis/p[7];potential=F(z[64])
    chargeeligible=u[8]==1 and E[1]<F(z[67]) and potential>0
    request=float(u[5]+z[64]) if chargeeligible else u[5]
    on=int(row[163]);effective=on;reason=0
    if on==0:
        if u[7]==1 and request>0 and exactlimit>0 and age[0]>=p[22] and E[1]<=F(z[71]):effective=1;reason=1
    elif request==0 or exactlimit==0:effective=0;reason=3
    elif u[7]==0:effective=0;reason=2
    enabled=[charge>0,dis>0,effective==0 and u[7]==1 and exactlimit>0 and (u[5]>0 or u[8]==1 and potential>0)]
    c={
        'schema':len(z)==78 and z[77]==70,
        'incoming_hulls':z[73:77]==row[159:163],
        'held_boundary':z[60:62]==[u[4],u[4]],
        'thresholds':all(contains(z[67+2*j:69+2*j],v) for j,v in enumerate([stop,cut,restart])),
        'latch':z[62]==on and z[63]==effective and z[65]==reason,
        'eligible_flags':z[51:54]==[int(v) for v in enabled],
        'finite_nonnegative_ports':all(v>=0 for v in [hp,direct,charge,dis,potential]),
        'HP_bound':hp<=exactlimit and (effective==1 or hp==0),
        'HP_priority':direct==min(F(u[5]),hp),
        'potential_bound':potential<=exactpotential,
        'potential_maximal':abs(dec(potential-exactpotential))<D('1e-12')*max(D(1),dec(exactpotential)),
        'HP_maximal':abs(dec(hp)-(min(dec(F(request)),dec(exactlimit)) if effective else D(0)))<D('1e-12')*max(D(1),dec(exactlimit)),
        'charge_eligibility':charge==0 or chargeeligible and effective==1,
        'charge_allocation':charge==F(min(float(potential),max(0.,float(hp-direct)))) if chargeeligible else charge==0,
        'discharge_allocation':dis==F(min(float(p[9]),max(0.,float(F(u[5])-direct)))) if charge==0 and E[0]>F(z[70]) else dis==0,
        'exclusive':charge*dis==0,
        'forcing':contains(z[58:60],B),
        'dwell_disable':reason!=2 or age[0]>=p[21],
    }
    certs=[]
    for j in range(3):
        zz=z[15*j:15*j+15];bb=z[45+2*j:47+2*j];flag=enabled[j]
        c[f'{j}_disabled_zero']=flag or all(v==0 for v in zz+bb)
        c[f'{j}_forcing']=not flag or bb==z[58:60]
        if zz[12]==0:
            c[f'{j}_no_root_record']=all(v==0 for v in zz)
            # A root may be skipped only when the enabled path cannot reach
            # its threshold in the direction required, for the complete box.
            if flag:
                target=[stop,cut,restart][j]
                if j==0:
                    c[f'{j}_skipped_monotonicity']=F(bb[1])-p[5]*F(z[67])<=0
                elif j==2:
                    c[f'{j}_skipped_monotonicity']=E[1]>F(z[71]) and F(bb[0])-p[5]*F(z[72])>=0
                else:c[f'{j}_skipped_cutoff']=False
            continue
        args=(row[159:161],bb,float(p[5]),zz[13:15],1 if j==0 else -1,u[4],float(p[22]) if j==2 else 0,row[161:163] if j==2 else [0,0],zz)
        rc,_=review(*args)
        for name,ok in rc.items():c[f'{j}_root_{name}']=ok
        c[f'{j}_root_enabled']=flag
        c[f'{j}_threshold_record']=zz[13:15]==z[67+2*j:69+2*j]
        certs.append(args)
    pair=0
    if enabled[1] and enabled[2] and z[15] in [1,3] and z[30] in [1,3]:
        pair=1 if z[25]<z[39] else 2 if z[40]<z[24] else 3
    c['pair_order']=z[66]==pair
    c['strict_enabled_order']=u[3]==0 or all(z[k]!=2 for k in [0,15,30,11,26,41]) and pair!=3
    return c,certs

def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    report=json.loads((folder/'report.json').read_text());checks=[];mutations=[];numeric=[];certs=[]
    def check(kind,name,ok):checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    check('MAT','reopened',report==json.loads((folder/'mat_reopen.json').read_text()))
    check('MAT','original',(folder/'event_candidates_v70.mat').stat().st_size>1000)
    runs={r['id']:r for r in report['runs']};binary={}
    for rec in json.loads((folder/'binary_manifest.json').read_text()):
        flat=[x[0] for x in struct.iter_unpack('<d',(folder/rec['file']).read_bytes())];n=rec['columns']
        value=[flat[k:k+n] for k in range(0,len(flat),n)]
        if rec['rows']==1:value=value[0]
        key=rec['id'],rec['field'];check('binary','unique_'+str(key),key not in binary)
        check('binary',str(key),value==runs[key[0]][key[1]] and len(flat)==rec['rows']*n);binary[key]=value
    with localcontext() as ctx:
        ctx.prec=160
        for id,r in runs.items():
            cfg=binary[id,'cfg'];u=rows(binary[id,'input']);tr=rows(binary[id,'trace'])
            ac,nums=analyze(cfg,u,[x[:205] for x in tr])
            for name,ok in ac.items():check('actual_analytic',id+'_'+name,ok)
            numeric.extend(dict(id=id,**v) for v in nums)
            check('MAT',id+'_original',(folder/(id+'.mat')).stat().st_size>1000)
            for tick,(uu,row) in enumerate(zip(u,tr)):
                if uu[0]==0:
                    check('prefix',f'{id}_{tick}',all(x==0 for x in row[205:]));continue
                c,cc=candidate_review(cfg,uu,row);certs.extend(cc)
                for name,ok in c.items():check('candidate',f'{id}_{tick}_{name}',ok)
                with localcontext() as less:
                    less.prec=120;c120,_=candidate_review(cfg,uu,row)
                check('precision',f'{id}_{tick}',c==c120)
            if r['audit_kind']=='inactive_cutoff':
                check('repair',id,all(x[257]==0 and all(v==0 for v in x[220:235]) for x in tr))
            elif r['audit_kind']=='inactive_stop':
                check('repair',id,tr[-1][256]==0 and tr[-1][268]==0 and all(v==0 for v in tr[-1][205:220]))
            elif r['audit_kind']=='missing_forced_restart':
                check('repair',id,tr[-1][235]==1 and tr[-1][246]==1 and tr[-1][254]<0)
            for ref in r['references_v30']:
                from verify_interval_dispatch_v66 import storage
                pp=list(map(F,ref['parameters']));out=ref['output'];b=pp[4]*F(out[0])-F(out[1])/pp[5]
                en,_=storage(dec(F(ref['initial'])),b,pp[6],dec(pp[0]))
                check('v30',id+'_'+str(ref['initial']),abs(en-dec(F(out[3])))<D('1e-12')*max(D(1),abs(en)))
        for label,index in [('root_collapsed',1),('ready_erased',9),('threshold_corrupted',13)]:
            b=copy.deepcopy(next(v for v in certs if v[-1][0]==1));zz=b[-1]
            if index==1:zz[1]=zz[2]
            elif index==9:zz[9:11]=[0,0]
            else:zz[13:15]=[v+1 for v in zz[13:15]]
            c,_=review(*b);mutations.append(dict(name=label,passed=not all(c.values())))
        for label,id,index in [('inactive_enabled','HP_only_contact_strict0',257),('forced_B_erased','OFF_discharge_restart_0p0',254),('latch_corrupted','OFF_blocked_hypothetical_stop',268),('boundary_corrupted','HP_only_contact_strict0',265)]:
            r=runs[id];tr=copy.deepcopy(rows(r['trace']));tr[-1][index]+=1
            c,_=candidate_review(r['cfg'],rows(r['input'])[-1],tr[-1]);mutations.append(dict(name=label,passed=not all(c.values())))
        r=runs['HP_only'];tr=copy.deepcopy(rows(r['trace']));tr[0][36:38]=[0,0]
        ac,_=analyze(r['cfg'],rows(r['input']),[x[:205] for x in tr]);mutations.append(dict(name='inventory_erased',passed=not all(ac.values())))
    for f in report['faults']:
        check('execution',f['id'],bool(f['identifier']) and f['expected_guard'] in f['message'])
        if f['prefix']:check('execution',f['id']+'_prefix',rows(f['prefix'])==rows(runs[f['base_id']]['trace'])[:len(rows(f['prefix']))])
    check('coverage','six_modes',report['mode_coverage']==list(range(6)))
    check('MATLAB','assertions',report['summary']['failed']==0 and all(c['passed'] for c in report['assertions']))
    check('metadata','actual_Stateflow',report['metadata']['license_observed']==1 and report['metadata']['chart_count']==1 and report['metadata']['simulation_mode']=='normal')
    model=ROOT/'matlab/simulink/DCHR_Event_Candidates_Stateflow_v70r2.slx'
    with zipfile.ZipFile(model) as ar:
        scripts=[];xml=''
        for name in ar.namelist():
            if name.endswith('.xml'):
                data=ar.read(name);xml+=data.decode(errors='replace');scripts.extend(p.text for p in ET.fromstring(data).iter('P') if p.attrib.get('Name')=='script')
    for name in ['event_candidates_v70','interval_dispatch_kernel_v70']:check('SLX',name,(ROOT/f'matlab/simulink/{name}.m').read_text() in scripts)
    for state in report['metadata']['states']:check('SLX',state,state in xml)
    for name in ['preservation.json','source_hashes.json']:
        for rec in json.loads((folder/name).read_text()):
            ok=sha(ROOT/rec['path'])==rec['sha256']
            if name=='source_hashes.json':ok=ok and sha(folder/'source_snapshot'/rec['path'])==rec['sha256']
            check(name,rec['path'],ok)
    receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')]
    check('receipt','exit0',any(v['exit_code']==0 for v in receipts));check('receipt','log',any(p.stat().st_size>0 for p in folder.glob('matlab_*.log')))
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');csvpath=folder/f'actual_traces_v70_{stamp}.csv'
    with csvpath.open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(numeric[0]));w.writeheader();w.writerows(numeric)
    result=dict(version='0.70',timestamp_utc=datetime.now(timezone.utc).isoformat(),checks=checks,reviewer_selfchecks=mutations,model_sha256=sha(model),numeric_csv=csvpath.name,
        independence='Same-agent Fraction/Decimal closed-form algorithms, not independent personnel. Original MAT reopened/exported by MATLAB, no independent HDF5 parser.',
        summary=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks)))
    out=folder/f'independent_QA_v70_{stamp}.json';out.write_text(json.dumps(result,indent=2)+'\n')
    failed=[c for c in checks if not c['passed']]
    print(json.dumps(dict(qa=out.relative_to(ROOT).as_posix(),summary=result['summary'],mutations=mutations,failed=failed[:60])))
    return int(bool(failed) or not all(v['passed'] for v in mutations))
if __name__=='__main__':sys.exit(main())
