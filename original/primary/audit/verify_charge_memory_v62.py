"""Independent exact binary Fraction + 120/160-digit analytic QA.
No production imports. Same-agent algorithmic review, not physical validation.
"""
from pathlib import Path
from datetime import datetime, timezone
from fractions import Fraction as F
from decimal import Decimal as D, localcontext
import json, struct, hashlib, sys, csv, copy, zipfile, xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dec(x):
    if isinstance(x,D):return x
    if isinstance(x,F):return D(x.numerator)/D(x.denominator)
    return D.from_float(x)
def contains(iv,x):return dec(iv[0])<=dec(x)<=dec(iv[1])
def exact(cfg,horizon,stage):
    e,q,eta,lam,C,Ta,delivery,direct,d,cond,source,glide,evap,fc,H,nom,Sc,port,Tmax,aux,age0,age1,total,tag,tlo,thi,*ties=map(F,cfg)
    floor=delivery+direct;star=C*(floor-Ta-d);cap=C*(Tmax-Ta);B=eta*q
    Te=source-glide-evap;a=fc*(Te+F(273.15));lf=floor+cond-Te;l0=Ta+d+cond-Te
    if lam:
        event=-dec((B-lam*star)/(B-lam*e)).ln()/dec(lam)
    else:event=dec((star-e)/B)
    t=D(0) if stage==0 else event if stage==1 else dec(horizon)
    if not lam:
        en=dec(e)+dec(B)*t;integral=dec(e)*t+dec(B)*t*t/2
    else:
        eq=dec(B/lam);r=(-dec(lam)*t).exp();en=eq+(dec(e)-eq)*r;integral=eq*t+(dec(e)-eq)*(1-r)/dec(lam)
    if stage<2:src=dec(q*a/(a+lf))*t
    else:
        duration=t-event;y0=dec(a+l0+star/C);y1=dec(a+l0)+en/dec(C)
        cc=dec(B/C+lam*(a+l0));J=((y1/y0).ln()+dec(lam)*duration)/cc
        src=dec(q*a/(a+lf))*event+dec(q*a)*J
    heat=dec(q)*t;work=heat-src;standing=dec(lam)*integral;loss=dec((1-eta)*q)*t
    tank=dec(Ta)+en/dec(C);hot=max(dec(floor),tank+dec(d));water=dec(q)/(hot-tank)
    values={32:dec(star),35:t,37:en,39:dec(age0)+t,41:heat,43:src,45:work,47:standing,49:loss,51:dec(aux)*work,
            53:dec(e)+heat-en-standing-loss,58:dec(cap),60:water,62:hot}
    limits=[q,nom,H*d,Sc*glide*(1+lf/a),port]
    expected_ties=[int(x==q) for x in limits]
    return values,event,star,expected_ties,dec(age1)+t
def validation(cfg,steps,trace):
    checks={}
    for i,row in enumerate(trace):
        stage=[0,1,2,2,2][i];values,event,star,ties,agehi=exact(cfg,steps[i][2],stage)
        for index,value in values.items():checks[f'{i}_analytic_{index}']=contains(row[index-1:index+1],value)
        checks[f'{i}_exact_provenance']=row[:31]==cfg
        checks[f'{i}_phase']=row[33]==stage
        checks[f'{i}_event_root']=contains(cfg[24:26],event)
        checks[f'{i}_tie_set']=list(map(int,row[26:31]))==ties
        checks[f'{i}_age_upper']=contains(row[38:40],agehi)
        checks[f'{i}_latch_scalar_schema']=row[54:57]==[1,0,62]
        checks[f'{i}_quadrature']=row[63]==128
        checks[f'{i}_bounds']=row[36]>=0 and row[37]<row[57]
        checks[f'{i}_firstlaw']=row[52]<=0<=row[53]
        checks[f'{i}_positive_ports']=all(x>=0 for x in row[40:52])
        checks[f'{i}_ordered_enclosures']=all(row[j]<=row[j+1] for j in [31,34,36,38,40,42,44,46,48,50,52,57,59,61])
        if i:
            checks[f'{i}_age_advances']=row[38]>trace[i-1][38] and row[39]>trace[i-1][39]
        if i>1:
            checks[f'{i}_outgoing_strict']=row[36]>row[32] and row[34]>cfg[25]
            checks[f'{i}_continuous_hot']=row[61]>trace[i-1][61]
    return checks
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    report=json.loads((folder/'report.json').read_text());manifest=json.loads((folder/'binary_manifest.json').read_text())
    checks=[];binary={};hashes=[]
    def check(kind,name,ok):checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    check('MAT','original_reopened_equal',report==json.loads((folder/'mat_reopen.json').read_text()))
    check('MAT','original_artifact',(folder/'charge_memory_v62.mat').stat().st_size>1000)
    check('MATLAB','actual_assertions',report['summary']['failed']==0 and all(c['passed'] for c in report['assertions']))
    runs={r['id']:r for r in report['runs']}
    for record in manifest:
        key=(record['id'],record['field']);path=folder/record['file'];flat=[x[0] for x in struct.iter_unpack('<d',path.read_bytes())]
        columns=record['columns'];value=[flat[j:j+columns] for j in range(0,len(flat),columns)]
        if record['rows']==1:value=value[0]
        check('original_binary',str(key),value==runs[record['id']][record['field']] and len(flat)==record['rows']*columns)
        check('original_binary','unique_'+str(key),key not in binary);binary[key]=value;hashes.append(dict(path=record['file'],sha256=sha(path)))
    numeric=[];nonrepresentable=0;ties_seen=set()
    with localcontext() as ctx:
        ctx.prec=120
        for id,item in runs.items():
            cfg=binary[(id,'cfg')];steps=binary[(id,'steps')];trace=binary[(id,'trace')]
            for name,ok in validation(cfg,steps,trace).items():check('analytic_protocol',id+'_'+name,ok)
            values,event,star,ties,_=exact(cfg,steps[-1][2],2);ties_seen.add(sum(ties));nonrepresentable+=F(float(star))!=star
            # Exact manifold is the retained operand expression, not rounded star.
            host=item['host_certificate']['exact_branch_energy_MWh'];check('host_certificate',id,F(int(host['numerator']),int(host['denominator']))==star)
            check('host_certificate','mask_'+id,ties==list(map(int,cfg[26:31])))
            for index,row in enumerate(trace):
                vals,_,_,_,_=exact(cfg,steps[index][2],int(row[33]))
                with localcontext() as more:
                    more.prec=160;again,_,_,_,_=exact(cfg,steps[index][2],int(row[33]))
                    for field,v in vals.items():check('precision_stability',f'{id}_{index}_{field}',abs(v-again[field])<D('1e-100')*max(D(1),abs(v)))
                numeric.append(dict(id=id,protocol_tick=index,phase=int(row[33]),physical_time_h=str(vals[35]),time_lo_h=row[34],time_hi_h=row[35],
                    exact_star=str(star),inventory_MWh=str(vals[37]),inventory_lo_MWh=row[36],inventory_hi_MWh=row[37],
                    source_MWh=str(vals[43]),source_lo_MWh=row[42],source_hi_MWh=row[43],compressor_MWh=str(vals[45]),
                    hp_age_lo_h=row[38],hp_age_hi_h=row[39],hot_inlet_C=str(vals[62]),hot_lo_C=row[61],hot_hi_C=row[62]))
        first=next(iter(runs));cfg=binary[(first,'cfg')];steps=binary[(first,'steps')];tr=binary[(first,'trace')];selfchecks=[]
        mutations=[]
        for label,index,field in [('inventory_snap',1,36),('source_corruption',4,42),('age_reset',2,38),('scalar_credit',2,55),('provenance',2,6),('missing_tie',2,28)]:
            changed=copy.deepcopy(tr)
            if label=='inventory_snap':changed[index][field:field+2]=[float(F(cfg[4])*(F(cfg[6])+F(cfg[7])-F(cfg[5])-F(cfg[8])))]*2
            elif label=='source_corruption':changed[index][field:field+2]=[x+1 for x in changed[index][field:field+2]]
            elif label=='age_reset':changed[index][field:field+2]=[0,0]
            else:changed[index][field]=1 if label=='scalar_credit' else 0 if label=='missing_tie' else changed[index][field]+1
            mutations.append((label,changed))
        for label,changed in mutations:selfchecks.append(dict(name=label,passed=not all(validation(cfg,steps,changed).values())))
    check('coverage','actual_24_runs',len(runs)==24);check('coverage','nonrepresentable_fixture',nonrepresentable>0)
    check('coverage','unique_and_equivalent_ties',ties_seen=={1,2})
    check('runtime_faults','actual_twelve_rejections',len(report['faults'])==12 and all(f['identifier'] and 'v62' in f['message'] for f in report['faults']))
    check('metadata','actual_chart',report['metadata']['chart_count']==1 and report['metadata']['license_observed']==1)
    check('scope','scoped_memory_only',report['new_model'] and not report['coupled_six_mode_plant_acceptance'])
    mdl=ROOT/'matlab/simulink/DCHR_Charge_Memory_Stateflow_v62.slx'
    with zipfile.ZipFile(mdl) as archive:
        text='\n'.join(archive.read(n).decode('utf-8',errors='replace') for n in archive.namelist() if n.endswith('.xml'))
        for name in ['FLOOR_CHARGE','CORRELATED_CONTACT','TANK_CHARGE','charge_memory_kernel_v62','retained_memory']:
            check('archive',name,name in text)
        check('archive','global_source_port_quadrature','for j=1:128' in text)
        check('archive','provenance_gate','immutable manifold provenance' in text)
        scripts=[]
        for name in archive.namelist():
            if name.endswith('.xml'):
                doc=ET.fromstring(archive.read(name))
                scripts.extend(p.text for p in doc.iter('P') if p.attrib.get('Name')=='script')
        kernel=(ROOT/'matlab/simulink/charge_memory_kernel_v62.m').read_text()
        check('archive','embedded_kernel_bound_to_source',any(s and s.strip()==kernel.strip() for s in scripts))
    for record in json.loads((folder/'preservation.json').read_text()):check('preservation',record['path'],sha(ROOT/record['path'])==record['sha256'])
    for record in json.loads((folder/'source_hashes.json').read_text()):check('sealed_sources',record['path'],sha(ROOT/record['path'])==record['sha256']==sha(folder/'source_snapshot'/record['path']))
    receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')]
    check('execution','batch_exit_zero',any(r['exit_code']==0 for r in receipts))
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');csvpath=folder/f'numeric_traces_v62_{stamp}.csv'
    with csvpath.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(numeric[0]));w.writeheader();w.writerows(numeric)
    result=dict(version='0.62',timestamp_utc=datetime.now(timezone.utc).isoformat(),model_sha256=sha(mdl),runs=len(runs),protocol_ticks=len(numeric),
        nonrepresentable_runs=nonrepresentable,summary=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks)),
        reviewer_selfchecks=selfchecks,checks=checks,binary_hashes=hashes,numeric_traces=csvpath.name,
        limitations=['Scoped compiled constant-request charge branch memory; not six-mode coupled plant acceptance.',
                    'Exact operand provenance relies on host rational adapter certificate; runtime interval equality alone is not exact tie proof.',
                    'Conditional binary64 arithmetic and |lambda*t|<=1; no measured validation or independent personnel QA.'])
    out=folder/f'independent_QA_v62_{stamp}.json';out.write_text(json.dumps(result,indent=2)+'\n')
    failures=[c for c in checks if not c['passed']];print(json.dumps(dict(summary=result['summary'],reviewer_selfchecks=selfchecks,failures=failures[:15]),indent=2))
    assert not failures and all(c['passed'] for c in selfchecks),f'Inspect {out}'
if __name__=='__main__':main()
