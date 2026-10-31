"""Same-agent independent exact-binary/Decimal analytic QA; no plant imports.

Reuses only the independent analytic v64 reviewer for its unchanged prefix.
This is algorithmic independence, not independent personnel or physical evidence.
"""
from pathlib import Path
from datetime import datetime, timezone
from fractions import Fraction as F
from decimal import Decimal as D, localcontext
import json, struct, hashlib, sys, csv, copy, zipfile
import xml.etree.ElementTree as ET
from verify_restart_chain_v64 import review as prefix_review, resumed
from verify_capacity_chain_v63 import exact, dec, contains
from earliest_service_reference_v66 import compare
from verify_interval_dispatch_v65 import analyze as baseline_analyze
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def storage(E,B,lam,t):
    if not lam:return E+dec(B)*t,E*t+dec(B)*t*t/2
    r=(-dec(lam)*t).exp();eq=dec(B/lam)
    return eq+(E-eq)*r,eq*t+(E-eq)*(1-r)/dec(lam)

def source_integral(E,B,lam,C,Ta,floor,approach,cond,Te,a,q,t):
    """Analytic max(floor,tank+approach) split; handles both motion directions."""
    if not q:return D(0)
    end,_=storage(E,B,lam,t);star=dec(C*(floor-Ta-approach));points=[D(0),t]
    if (E-star)*(end-star)<0:
        if lam:
            eq=dec(B/lam);root=-((star-eq)/(E-eq)).ln()/dec(lam)
        else:root=(star-E)/dec(B)
        assert 0<root<t;points.insert(1,root)
    out=D(0);l0=a+Ta+approach+cond-Te;lf=a+floor+cond-Te
    for lo,hi in zip(points,points[1:]):
        dt=hi-lo;e0,_=storage(E,B,lam,lo);e1,_=storage(E,B,lam,hi)
        mid,_=storage(E,B,lam,(lo+hi)/2)
        if mid<=star:out+=dec(q*a/lf)*dt;continue
        y0=dec(l0)+e0/dec(C);y1=dec(l0)+e1/dec(C);cc=B/C+lam*l0
        if cc:out+=dec(q*a)*((y1/y0).ln()+dec(lam)*dt)/dec(cc)
        elif lam:out+=dec(q*a)*((dec(lam)*dt).exp()-1)/(dec(lam)*y0)
        else:out+=dec(q*a)*dt/y0
    return out

def analyze(cfg,inputs,trace):
    p=list(map(F,cfg[35:60]));C,Ta,Tmax,cutT,restart,lam,etaC,etaD,chargeMax,disMax,nom,sourceIn,glide,evap,fc,H,approach,cond,delivery,directApp,aux,minON,minOFF,boilerMax,stopT=p
    cap=C*(Tmax-Ta);cut=C*(cutT-Ta);Te=sourceIn-glide-evap;a=fc*(Te+F(273.15));floor=delivery+directApp
    checks={};numeric=[];E=None;age=None;on=None
    cumulative={41:D(0),43:D(0),45:D(0),47:D(0),49:D(0),51:D(0),140:D(0),142:D(0),144:D(0),146:D(0),148:D(0),150:D(0)}
    npre=sum(u[0]==0 for u in inputs)
    if npre:
        assert npre==10 and all(u[0]==0 for u in inputs[:10])
        steps=[[i,u[1],u[2],u[3]] for i,u in enumerate(inputs[:10])]
        for name,ok in prefix_review(cfg[:35],steps,[r[:114] for r in trace[:10]]).items():checks['prefix_'+name]=ok
        vals,_=resumed(cfg[:35],steps,9);E=vals[37];age=vals[39];on=1;initial=dec(F(cfg[0]))
        for k in [41,43,45,47,49,51]:cumulative[k]=vals[k]
    else:
        initial=E=dec(F(inputs[0][9]));on=int(inputs[0][10]);age=dec(F(inputs[0][11]))
    for i,(u,row) in enumerate(zip(inputs,trace)):
        checks[f'{i}_policy_memory']=row[179]==66 and row[180:205]==cfg[35:60]
        checks[f'{i}_finite']=all(abs(x)<float('inf') for x in row)
        if u[0]==0:continue
        t=dec(F(u[4]));demand=F(u[5]);direct,charge,dis,boiler,unmet=map(F,row[120:125]);q=direct+charge;B=etaC*charge-dis/etaD
        en,integ=storage(E,B,lam,t);src=source_integral(E,B,lam,C,Ta,floor,approach,cond,Te,a,q,t)
        heat=dec(q)*t;work=heat-src;standing=dec(lam)*integ;closs=dec((1-etaC)*charge)*t;dloss=dec((1/etaD-1)*dis)*t
        values={37:en,116:E,128:heat,130:src,132:work,134:standing,136:closs,138:dloss,158:dec(Ta)+en/dec(C),160:E,162:age,174:initial}
        increments={41:heat,43:src,45:work,47:standing,49:closs,51:dec(aux)*work,140:dloss,
                    142:dec(direct+dis+boiler)*t,144:dec(boiler)*t,146:dec(direct)*t,148:dec(dis)*t,150:dec(unmet)*t}
        for k,v in increments.items():cumulative[k]+=v;values[k]=cumulative[k]
        expected_mode=5 if unmet>0 else 4 if boiler>0 else 3 if dis>0 else 2 if charge>0 else 1 if direct>0 else 0
        newon=int(row[54]);reason=int(row[164]);newage=age+t if newon==on else t;values[39]=newage
        for k,v in values.items():checks[f'{i}_equation_{k}']=contains(row[k-1:k+1],v)
        checks[f'{i}_mode']=row[114]==expected_mode
        checks[f'{i}_scalar_powers']=all(x>=0 for x in [direct,charge,dis,boiler,unmet]) and charge*dis==0 and charge<=chargeMax and dis<=disMax and boiler<=boilerMax
        checks[f'{i}_demand']=abs(dec(demand-direct-dis-boiler-unmet))<=D('1e-12')*max(D(1),dec(demand))
        checks[f'{i}_inventory']=0<=row[36]<=row[37]<dec(cap) and row[36]<=en<=row[37]
        # Review the full retained input box, in addition to the correlated
        # original trajectory. This independently checks scalar-service safety.
        lower,_=storage(dec(F(row[159])),B,lam,t);upper,_=storage(dec(F(row[160])),B,lam,t)
        checks[f'{i}_whole_inventory_box']=dec(F(row[36]))<=lower<=upper<=dec(F(row[37]))
        checks[f'{i}_cutoff']=not dis or min(E,en)>=dec(cut)
        checks[f'{i}_thermal_stop']=not charge or max(E,en)<dec(C*(stopT-Ta))
        checks[f'{i}_finite_nameplate']=q<=nom
        sourcecap=F(u[6])*glide
        for label,inventory in [('begin',E),('end',en),('box_begin_lower',dec(F(row[159]))),
                                ('box_begin_upper',dec(F(row[160]))),('box_end_lower',lower),('box_end_upper',upper)]:
            tank=dec(Ta)+inventory/dec(C);hot=max(dec(floor),tank+dec(approach));lift=hot+dec(cond)-dec(Te)
            sr=dec(q*a)/(dec(a)+lift) if q else D(0);water=dec(q)/(hot-tank) if q else D(0)
            checks[f'{i}_{label}_finite_source']=sr<=dec(sourcecap)
            checks[f'{i}_{label}_finite_water']=water<=dec(H)
            checks[f'{i}_{label}_COP_domain']=not q or dec(Te)>D('-273.15') and lift>0 and 0<fc<=1
        checks[f'{i}_source_work']=contains(row[127:129],src+work)
        law=initial+cumulative[41]+cumulative[144]-cumulative[142]-en-cumulative[47]-cumulative[49]-cumulative[140]
        checks[f'{i}_firstlaw']=abs(law)<D('1e-100')*max(D(1),initial) and contains(row[52:54],D(0))
        checks[f'{i}_aux_external']=contains(row[50:52],dec(aux)*cumulative[45])
        checks[f'{i}_latch_old']=row[163]==on
        checks[f'{i}_no_OFF_heat']=newon==1 or q==0
        if on==0 and newon==1:
            checks[f'{i}_restart']=reason==1 and age>=dec(minOFF) and E<=dec(C*(restart-Ta)) and u[7]==1
        elif on==1 and newon==0:
            checks[f'{i}_shutdown']=reason==3 or reason==2 and age>=dec(minON) and u[7]==0
        else:checks[f'{i}_latch_reason']=reason==0
        if i>0:
            checks[f'{i}_no_midpoint']=row[159:161]==trace[i-1][36:38]
            checks[f'{i}_retained_age']=row[161:163]==trace[i-1][38:40]
        checks[f'{i}_physical_time']=contains(row[175:177],F(u[2]))
        numeric.append(dict(tick=i,time_h=u[2],mode=expected_mode,energy_MWh=str(en),energy_lower=row[36],energy_upper=row[37],
                            direct_MW=float(direct),charge_MW=float(charge),discharge_MW=float(dis),boiler_MW=float(boiler),unmet_MW=float(unmet),
                            heat_MWh=str(heat),source_MWh=str(src),compressor_MWh=str(work),standing_MWh=str(standing),HP_ON=newon,age_h=str(newage)))
        E=en;age=newage;on=newon
    return checks,numeric

def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    report=json.loads((folder/'report.json').read_text());runs={r['id']:r for r in report['runs']};checks=[];binary={};selfchecks=[];numeric=[]
    def check(kind,name,ok):checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    check('MAT','reopened_equal',report==json.loads((folder/'mat_reopen.json').read_text()))
    check('MAT','original_report',(folder/'interval_dispatch_v66.mat').stat().st_size>1000)
    for rec in json.loads((folder/'binary_manifest.json').read_text()):
        raw=(folder/rec['file']).read_bytes();flat=[v[0] for v in struct.iter_unpack('<d',raw)];cols=rec['columns'];value=[flat[k:k+cols] for k in range(0,len(flat),cols)]
        if rec['rows']==1:value=value[0]
        key=rec['id'],rec['field'];check('binary',str(key),value==runs[key[0]][key[1]] and len(flat)==rec['rows']*cols);check('binary','unique_'+str(key),key not in binary);binary[key]=value
    with localcontext() as ctx:
        ctx.prec=120
        for id,r in runs.items():
            cfg=binary[id,'cfg'];u=binary[id,'input'];tr=binary[id,'trace']
            if isinstance(u[0],(int,float)):u=[u]
            if isinstance(tr[0],(int,float)):tr=[tr]
            assertions,nums=analyze(cfg,u,tr)
            for name,ok in assertions.items():check('analytic',id+'_'+name,ok)
            with localcontext() as more:
                more.prec=160;again,nums2=analyze(cfg,u,tr)
            check('precision',id+'_assertions_agree',assertions==again)
            for a,b in zip(nums,nums2):
                for key in ['energy_MWh','heat_MWh','source_MWh','compressor_MWh','standing_MWh','age_h']:
                    check('precision',f'{id}_{a["tick"]}_{key}',abs(D(a[key])-D(b[key]))<D('1e-100')*max(D(1),abs(D(a[key]))))
                numeric.append(dict(id=id,**a))
            check('MAT',id+'_original',(folder/(id+'.mat')).stat().st_size>1000)
            for ref in r['references_v30']:
                p=list(map(F,ref['parameters']));dt,cap,_,_,ec,ed,l,cut,cc,ta=p;out=ref['output'];B=ec*F(out[0])-F(out[1])/ed
                en,_=storage(dec(F(ref['initial'])),B,l,dec(dt));check('v30',f'{id}_{ref["tick"]}',abs(en-dec(F(out[3])))<D('1e-12')*max(D(1),abs(en)))
        id=next(k for k in runs if k.startswith('retained_'));cfg=binary[id,'cfg'];u=binary[id,'input'];tr=binary[id,'trace']
        for label,index,change in [('inventory_midpoint',159,'collapse'),('discharge_credit',122,'plus'),('boiler_credit',123,'plus'),
                                   ('loss_erased',46,'zero_pair'),('source_credit',129,'pair'),('clock_reset',38,'zero_pair'),
                                   ('port_offset_erased',40,'zero_pair'),('mode_corrupted',114,'plus')]:
            altered=copy.deepcopy(tr);row=altered[11]
            if change=='collapse':row[index:index+2]=[sum(row[index:index+2])/2]*2
            elif change=='plus':row[index]+=1
            elif change=='zero_pair':row[index:index+2]=[0,0]
            else:row[index:index+2]=[x+1 for x in row[index:index+2]]
            found,_=analyze(cfg,u,altered);selfchecks.append(dict(name=label,passed=not all(found.values())))
    
    bw=json.loads((folder/'baseline_witness.json').read_text());bu=[bw['input']];bt=[bw['trace']] if isinstance(bw['trace'][0],(int,float)) else bw['trace']
    with localcontext() as ctx:
        ctx.prec=160;bc,bn=baseline_analyze(bw['cfg'],bu,bt)
    check('baseline','saved_v65_independent_equations',all(bc.values()))
    stop=F(bw['cfg'][35])*(F(bw['cfg'][59])-F(bw['cfg'][36]))
    check('baseline','v65_actual_stop_overshoot',F(bt[0][36])>stop)
    rr=runs['stop_overshoot_repair'];tr=rr['trace'];tr=[tr] if isinstance(tr[0],(int,float)) else tr
    check('repair','same_binary_equipment_input',rr['cfg']==bw['cfg'] and rr['input']==bw['input'])
    check('repair','v66_stop_withholds_charge',tr[0][121]==0 and F(tr[0][37])<stop and tr[0][54]==0)
    comparisons=[]
    for id,r in runs.items():
        if not id.startswith('repeated_'):continue
        tr=r['trace'];on=[int(x[54]) for x in tr];ons=sum(a==0 and b==1 for a,b in zip(on,on[1:]));offs=sum(a==1 and b==0 for a,b in zip(on,on[1:]))
        check('repeated',id+'_four_restarts',ons>=3 and offs>=4)
        check('repeated',id+'_cutoff_no_credit',sum(x[122]==0 and x[124]>0 for x in tr)>=4)
        check('repeated',id+'_port_handoffs',all(x[159:161]==old[36:38] for old,x in zip(tr,tr[1:])))
        with localcontext() as ctx:
            ctx.prec=120;ev=compare(r['cfg'],r['input'])
            ctx.prec=160;ev2=compare(r['cfg'],r['input'])
            check('earliest',id+'_event_types',[x['kind'] for x in ev['events']]==[x['kind'] for x in ev2['events']])
            for key in ev['ports']:
                check('earliest',id+'_precision_'+key,abs(D(ev['ports'][key])-D(ev2['ports'][key]))<D('1e-95'))
            for a,b in zip(ev['events'],ev2['events']):
                check('earliest',id+'_root_'+str(a['tick'])+'_'+a['kind'],abs(D(a['time'])-D(b['time']))<D('1e-95'))
        check('earliest',id+'_repeated_stop_cutoff',sum(x['kind']=='thermal_stop_OFF' for x in ev['events'])>=4 and sum(x['kind']=='cutoff' for x in ev['events'])>=4)
        sampled={name:[tr[-1][idx-1],tr[-1][idx]] for name,idx in [('heat',41),('delivered',142),('boiler',144),('unmet',150)]}
        comparisons.append(dict(id=id,dt=r['input'][0][4],sampled_enclosures=sampled,earliest=ev2,observed_restarts=ons,observed_shutdowns=offs))
    with localcontext() as ctx:
        ctx.prec=160
        for other in comparisons[1:]:
            for key,value in comparisons[0]['earliest']['ports'].items():
                check('earliest','schedule_invariant_'+other['id']+'_'+key,abs(D(value)-D(other['earliest']['ports'][key]))<D('1e-95'))
        for item in comparisons:
            check('comparison',item['id']+'_service_gap',D(item['earliest']['ports']['delivered'])>D.from_float(item['sampled_enclosures']['delivered'][1]))
    (folder/'earliest_comparisons_v66.json').write_text(json.dumps(comparisons,indent=2)+'\n')

    check('coverage','six_modes',report['mode_coverage']==list(range(6)))
    check('coverage','retained_chain_all_modes',all(set(range(6)).issubset({row[114] for row in r['trace']}) for id,r in runs.items() if id.startswith('retained_')))
    check('MATLAB','assertions',report['summary']['failed']==0 and all(x['passed'] for x in report['assertions']))
    check('faults','runtime_rejections',len(report['faults'])>=10 and all(x['identifier'] and x['expected_guard'] in x['message'] for x in report['faults']))
    check('faults','two_valid_samples',report['valid_prefix']==runs['delayed_fault_control']['trace'][:2])
    check('metadata','actual_chart',report['metadata']['chart_count']==1 and report['metadata']['license_observed']==1 and report['metadata']['simulation_mode']=='normal')
    mdl=ROOT/'matlab/simulink/DCHR_Interval_Dispatch_Stateflow_v66.slx'
    with zipfile.ZipFile(mdl) as ar:
        scripts=[];xml=''
        for n in ar.namelist():
            if n.endswith('.xml'):
                data=ar.read(n);xml+=data.decode('utf-8',errors='replace');scripts.extend(p.text for p in ET.fromstring(data).iter('P') if p.attrib.get('Name')=='script')
        check('SLX','bound_source',any(s and s.strip()==(ROOT/'matlab/simulink/interval_dispatch_kernel_v66.m').read_text().strip() for s in scripts))
        for name in ['IDLE','HEAT_RECOVERY','STORAGE_CHARGE','STORAGE_DISCHARGE','BACKUP','UNMET_DEMAND']:check('SLX',name,name in xml)
    for rec in json.loads((folder/'preservation.json').read_text()):check('preservation',rec['path'],sha(ROOT/rec['path'])==rec['sha256'])
    for rec in json.loads((folder/'source_hashes.json').read_text()):check('sealed',rec['path'],(ROOT/rec['path']).is_file() and sha(ROOT/rec['path'])==rec['sha256']==sha(folder/'source_snapshot'/rec['path']))
    receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')];check('execution','MATLAB_exit',any(r['exit_code']==0 and r.get('evidence_class')=='OBSERVED_LOCAL_MATLAB_BATCH' for r in receipts))
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');csvpath=folder/f'numeric_traces_v66_{stamp}.csv'
    with csvpath.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(numeric[0]));w.writeheader();w.writerows(numeric)
    result=dict(version='0.66',timestamp_utc=datetime.now(timezone.utc).isoformat(),model_sha256=sha(mdl),runs=len(runs),service_intervals=len(numeric),
        checks=checks,reviewer_selfchecks=selfchecks,summary=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks)),
        independence='Same-agent independent Fraction/120-/160-digit analytic algorithms, no production imports. Original MAT reopened and exported by MATLAB; Python HDF5 parser unavailable.',numeric_csv=csvpath.name)
    (folder/f'independent_QA_v66_{stamp}.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(summary=result['summary'],reviewer_selfchecks=selfchecks,failures=[c for c in checks if not c['passed']][:35]),indent=2))
    assert result['summary']['failed']==0 and all(s['passed'] for s in selfchecks)
if __name__=='__main__':main()
