"""Independent exact-binary and 120/160-digit analytic review; no production imports."""
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
    e,q,eta,lam,C,Ta,delivery,direct,d,cond,source,glide,evap,fc,H,nom,Sc,port,Tmax,aux,age0,age1,total,tag,tlo,thi,*ties=map(F,cfg[:31])
    floor=delivery+direct;star=C*(floor-Ta-d);cap=C*(Tmax-Ta);B=eta*q
    Te=source-glide-evap;a=fc*(Te+F(273.15));lf=floor+cond-Te;l0=Ta+d+cond-Te
    def root(E):return -dec((B-lam*E)/(B-lam*e)).ln()/dec(lam) if lam else dec((E-e)/B)
    event=root(star);capacity_event=root(cap)
    t=D(0) if stage==0 else event if stage==1 else capacity_event if stage>=3 else dec(horizon)
    if not lam:en=dec(e)+dec(B)*t;integral=dec(e)*t+dec(B)*t*t/2
    else:
        eq=dec(B/lam);r=(-dec(lam)*t).exp();en=eq+(dec(e)-eq)*r;integral=eq*t+(dec(e)-eq)*(1-r)/dec(lam)
    if stage<2:src=dec(q*a/(a+lf))*t
    else:
        duration=t-event;y0=dec(a+l0+star/C);y1=dec(a+l0)+en/dec(C)
        cc=dec(B/C+lam*(a+l0));J=((y1/y0).ln()+dec(lam)*duration)/cc
        src=dec(q*a/(a+lf))*event+dec(q*a)*J
    heat=dec(q)*t;work=heat-src;standing=dec(lam)*integral;loss=dec((1-eta)*q)*t;offage=D(0)
    if stage>=3:en=dec(cap)
    if stage==4:
        offage=dec(horizon)-capacity_event;en=dec(cap)*(-dec(lam)*offage).exp();standing+=dec(cap)-en
    tank=dec(Ta)+en/dec(C);hot=max(dec(floor),tank+dec(d));water=dec(q)/(hot-tank)
    if stage>=3:water=D(0);hot=D(0)
    clock_age=dec(age0)+t;clock_hi=dec(age1)+t;physical_time=dec(horizon) if stage==4 else t
    values={32:dec(star),35:physical_time,37:en,39:clock_age,41:heat,43:src,45:work,47:standing,49:loss,
            51:dec(aux)*work,53:D(0),58:dec(cap),60:water,62:hot,68:capacity_event,70:offage,74:dec(age0),76:event,78:dec(cap)}
    return values,event,capacity_event,star,cap,[int(x==q) for x in [q,nom,H*d,Sc*glide*(1+lf/a),port]],clock_hi
def validation(cfg,steps,trace):
    checks={}
    for i,row in enumerate(trace):
        stage=[0,1,2,3,4,4,4][i];values,event,tc,star,cap,ties,agehi=exact(cfg,steps[i][2],stage)
        for index,value in values.items():checks[f'{i}_analytic_{index}']=contains(row[index-1:index+1],value)
        checks[f'{i}_exact_provenance']=row[:31]==cfg[:31] and row[64:67]==cfg[31:34]
        checks[f'{i}_phase']=row[33]==stage
        checks[f'{i}_root_order']=contains(cfg[24:26],event) and contains(cfg[31:33],tc) and cfg[25]<cfg[31]
        checks[f'{i}_exact_ties']=list(map(int,row[26:31]))==ties
        q,eta,lam,C=map(F,cfg[1:5]);capexact=F(cfg[4])*(F(cfg[18])-F(cfg[5]));Te=F(cfg[10])-F(cfg[11])-F(cfg[12])
        aa=F(cfg[13])*(Te+F(273.15));floor=F(cfg[6])+F(cfg[7]);lift=floor+F(cfg[9])-Te
        checks[f'{i}_independent_admissibility']=eta*q-lam*capexact>0 and q<=F(cfg[15]) and q<=F(cfg[17]) and q<=F(cfg[14])*F(cfg[8]) and q*aa/(aa+lift)<=F(cfg[16])*F(cfg[11])
        checks[f'{i}_ON_age_upper']=contains(row[38:40],agehi)
        checks[f'{i}_latch']=row[54]==int(stage<3)
        checks[f'{i}_no_scalar_restart']=row[55:57]==[0,63] and row[79]==0
        checks[f'{i}_capacity_schema']=row[72]==3 and row[67:69]==cfg[31:33]
        checks[f'{i}_bounds']=row[36]>=0 and row[37]<=row[58]
        checks[f'{i}_positive_ports']=all(x>=0 for x in row[40:52])
        checks[f'{i}_firstlaw']=row[52]<=0<=row[53]
        checks[f'{i}_ordered']=all(row[j]<=row[j+1] for j in [31,34,36,38,40,42,44,46,48,50,52,57,59,61,67,69,73,75,77])
        dwell=cfg[33];off=row[69:71]
        expected=1 if off[0]>=dwell else 0 if off[1]<dwell else 2
        checks[f'{i}_conservative_dwell']=row[71]==expected
        checks[f'{i}_no_premature_ready']=row[71]!=1 or values[70]>=dec(dwell)
        if stage>=3:
            checks[f'{i}_OFF_water']=row[59:63]==[0]*4
            checks[f'{i}_frozen_energies']=row[40:46]+row[48:52]==trace[3][40:46]+trace[3][48:52]
            checks[f'{i}_frozen_ON_age']=row[38:40]==trace[3][38:40]
        if stage==4:
            checks[f'{i}_correlated_OFF_age']=contains(off,dec(steps[i][2])-tc) and off[0]>0
            checks[f'{i}_passive_order']=row[36]<=trace[i-1][36] and row[46]>=trace[i-1][46]
    checks['capacity_symbolic_equal']=trace[3][36:38]==trace[3][57:59]
    checks['threeway_dwell_coverage']=[r[71] for r in trace[4:]]==[0,2,1]
    return checks
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    report=json.loads((folder/'report.json').read_text());manifest=json.loads((folder/'binary_manifest.json').read_text());checks=[];binary={}
    def check(kind,name,ok):checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    check('MAT','reopened_equal',report==json.loads((folder/'mat_reopen.json').read_text()))
    check('MAT','original',(folder/'capacity_chain_v63.mat').stat().st_size>1000)
    check('MATLAB','assertions',report['summary']['failed']==0 and all(c['passed'] for c in report['assertions']))
    runs={r['id']:r for r in report['runs']};binary_hashes=[]
    for rec in manifest:
        key=(rec['id'],rec['field']);p=folder/rec['file'];flat=[v[0] for v in struct.iter_unpack('<d',p.read_bytes())];cols=rec['columns']
        value=[flat[j:j+cols] for j in range(0,len(flat),cols)]
        if rec['rows']==1:value=value[0]
        check('binary',str(key),value==runs[rec['id']][rec['field']] and len(flat)==rec['rows']*cols)
        check('binary','unique_'+str(key),key not in binary);binary[key]=value;binary_hashes.append(dict(path=rec['file'],sha256=sha(p)))
    numeric=[];nonrepresentable_branch=0;nonrepresentable_cap=0;losses=set();selfchecks=[]
    with localcontext() as ctx:
        ctx.prec=120
        for id,item in runs.items():
            cfg=binary[id,'cfg'];steps=binary[id,'steps'];trace=binary[id,'trace'];losses.add(cfg[3])
            for name,ok in validation(cfg,steps,trace).items():check('analytic_protocol',id+'_'+name,ok)
            vals,event,tc,star,cap,ties,_=exact(cfg,0,3)
            nonrepresentable_branch+=F(float(star))!=star;nonrepresentable_cap+=F(float(cap))!=cap
            host=item['host_certificate']['exact_branch_energy_MWh']
            check('host_certificate',id,F(int(host['numerator']),int(host['denominator']))==star)
            refs=item['references_v30'];check('reference',id+'_four_comparisons',len(refs)==4)
            for ref in refs:
                p=list(map(F,ref['parameters']));A=F(ref['initial']);dt,capref,_,_,etaC,etaD,lam,cut,C,Ta=p
                out=list(map(F,ref['output']));power=etaC*out[0]-out[1]/etaD
                r=(-dec(lam)*dec(dt)).exp();phi=(1-r)/dec(lam) if lam else dec(dt)
                en=dec(A)*r+dec(power)*phi;loss=dec(A)+dec(power)*dec(dt)-en
                check('reference',f'{id}_{ref["tick"]}_independent_v30_energy',abs(dec(out[3])-en)<D('1e-12')*max(D(1),abs(en)))
                check('reference',f'{id}_{ref["tick"]}_independent_v30_loss',abs(dec(out[4])-loss)<D('1e-12')*max(D(1),abs(loss)))
                check('reference',f'{id}_{ref["tick"]}_enclosure_contains_scalar_reference',contains(trace[ref['tick']-1][36:38],float(out[3])))
            for i,row in enumerate(trace):
                values,*_=exact(cfg,steps[i][2],int(row[33]))
                with localcontext() as more:
                    more.prec=160;again,*_=exact(cfg,steps[i][2],int(row[33]))
                    for field,v in values.items():check('precision',f'{id}_{i}_{field}',abs(v-again[field])<D('1e-100')*max(D(1),abs(v)))
                numeric.append(dict(id=id,protocol_tick=i,phase=int(row[33]),time_h=str(values[35]),exact_capacity=str(cap),capacity_root_h=str(tc),
                    energy_MWh=str(values[37]),energy_lo_MWh=row[36],energy_hi_MWh=row[37],heat_MWh=str(values[41]),source_MWh=str(values[43]),
                    source_lo_MWh=row[42],source_hi_MWh=row[43],standing_loss_MWh=str(values[47]),off_age_h=str(values[70]),
                    off_age_lo_h=row[69],off_age_hi_h=row[70],dwell_ready=row[71],hp_latch=row[54],firstlaw_lo=row[52],firstlaw_hi=row[53]))
        first=next(iter(runs));cfg=binary[first,'cfg'];steps=binary[first,'steps'];tr=binary[first,'trace']
        for label in ['capacity_snap','post_OFF_heat','age_reset','premature_ready','erase_ambiguity','capacity_provenance','OFF_water','scalar_credit']:
            changed=copy.deepcopy(tr)
            if label=='capacity_snap':changed[3][36:38]=[float(F(cfg[4])*(F(cfg[18])-F(cfg[5])))]*2
            elif label=='post_OFF_heat':changed[6][40:42]=[x+1 for x in changed[6][40:42]]
            elif label=='age_reset':changed[5][69:71]=[0,0]
            elif label=='premature_ready':changed[4][71]=1
            elif label=='erase_ambiguity':changed[5][71]=1
            elif label=='capacity_provenance':changed[5][64]+=1
            elif label=='OFF_water':changed[5][59:61]=[1,1]
            else:changed[5][55]=1
            selfchecks.append(dict(name=label,passed=not all(validation(cfg,steps,changed).values())))
    check('coverage','14_actual_runs',len(runs)==14)
    check('coverage','zero_positive_loss',losses=={0.,.01})
    check('coverage','nonrepresentable_expressions',nonrepresentable_branch>0 and nonrepresentable_cap>0)
    check('faults','14_specific_rejections',len(report['faults'])==14 and all(f['identifier'] and f['expected_guard'] in f['message'] and 'v63' in f['message'] for f in report['faults']))
    check('temporal','four_tick_prefix',report['valid_prefix']==next(iter(runs.values()))['trace'][:4])
    check('metadata','actual_chart',report['metadata']['chart_count']==1 and report['metadata']['license_observed']==1)
    check('scope','no_full_plant_claim',not report['coupled_six_mode_plant_acceptance'])
    mdl=ROOT/'matlab/simulink/DCHR_Capacity_Chain_Stateflow_v63.slx'
    with zipfile.ZipFile(mdl) as archive:
        txt='\n'.join(archive.read(n).decode('utf-8',errors='replace') for n in archive.namelist() if n.endswith('.xml'))
        for name in ['FLOOR_CHARGE','CORRELATED_CONTACT','TANK_CHARGE','CAPACITY_CONTACT','PASSIVE_COOLING','retained_memory']:
            check('SLX',name,name in txt)
        scripts=[]
        for n in archive.namelist():
            if n.endswith('.xml'):scripts.extend(p.text for p in ET.fromstring(archive.read(n)).iter('P') if p.attrib.get('Name')=='script')
        kernel=(ROOT/'matlab/simulink/charge_memory_kernel_v63.m').read_text()
        check('SLX','embedded_source',any(s and s.strip()==kernel.strip() for s in scripts))
    for rec in json.loads((folder/'preservation.json').read_text()):check('preservation',rec['path'],sha(ROOT/rec['path'])==rec['sha256'])
    for rec in json.loads((folder/'source_hashes.json').read_text()):check('sealed',rec['path'],sha(ROOT/rec['path'])==rec['sha256']==sha(folder/'source_snapshot'/rec['path']))
    receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')]
    check('execution','zero_exit',any(r['exit_code']==0 for r in receipts))
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');csvpath=folder/f'numeric_traces_v63_{stamp}.csv'
    with csvpath.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(numeric[0]));w.writeheader();w.writerows(numeric)
    result=dict(version='0.63',timestamp_utc=datetime.now(timezone.utc).isoformat(),model_sha256=sha(mdl),runs=len(runs),protocol_ticks=len(numeric),
        nonrepresentable_branch_runs=nonrepresentable_branch,nonrepresentable_capacity_runs=nonrepresentable_cap,
        summary=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks)),reviewer_selfchecks=selfchecks,
        checks=checks,binary_hashes=binary_hashes,numeric_traces=csvpath.name,independence='Same-agent distinct exact Fraction and Decimal analytic algorithms; no production import, no independent personnel or physical validation.')
    out=folder/f'independent_QA_v63_{stamp}.json';out.write_text(json.dumps(result,indent=2)+'\n')
    failures=[c for c in checks if not c['passed']];print(json.dumps(dict(summary=result['summary'],selfchecks=selfchecks,failures=failures[:20]),indent=2))
    assert not failures and all(c['passed'] for c in selfchecks),f'Inspect {out}'
if __name__=='__main__':main()
