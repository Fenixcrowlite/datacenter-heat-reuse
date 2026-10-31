"""Independent exact-binary and high precision equations; no production imports.
Reuses only the independent v63 analytic reviewer for the unchanged prefix.
"""
from pathlib import Path
from datetime import datetime,timezone
from fractions import Fraction as F
from decimal import Decimal as D,localcontext
import json,struct,hashlib,sys,csv,copy,zipfile,xml.etree.ElementTree as ET
from verify_capacity_chain_v63 import exact,validation,dec,contains
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def resumed(cfg,steps,tick):
    prior,*_=exact(cfg[:34],steps[6][2],4)
    tr=dec(steps[6][2]);tau=dec(steps[tick][2])-tr
    e,q,eta,lam,C,Ta=map(F,cfg[:6]);B=eta*q;initial=prior[37]
    r=(-dec(lam)*tau).exp();eq=dec(B/lam)
    en=eq+(initial-eq)*r;integ=eq*tau+(initial-eq)*(1-r)/dec(lam)
    Te=F(cfg[10])-F(cfg[11])-F(cfg[12]);a=F(cfg[13])*(Te+F(273.15))
    l0=Ta+F(cfg[8])+F(cfg[9])-Te
    y0=dec(a+l0)+initial/dec(C);y1=dec(a+l0)+en/dec(C)
    cc=dec(B/C+lam*(a+l0));src=dec(q*a)*((y1/y0).ln()+dec(lam)*tau)/cc
    heat=dec(q)*tau;work=heat-src;standing=dec(lam)*integ
    vals={35:dec(steps[tick][2]),37:en,39:tau,41:prior[41]+heat,43:prior[43]+src,
          45:prior[45]+work,47:prior[47]+standing,49:prior[49]+dec((1-eta)*q)*tau,
          51:prior[51]+dec(F(cfg[19]))*work,53:D(0),60:dec(q/F(cfg[8])),
          62:dec(Ta)+en/dec(C)+dec(F(cfg[8])),82:initial,96:prior[70],
          98:dec(Ta)+initial/dec(C),100:tau,102:initial,104:heat,106:src,108:work,110:standing}
    return vals,prior
def review(cfg,steps,trace):
    checks=validation(cfg[:34],steps[:7],[r[:80] for r in trace[:7]])
    for i,row in enumerate(trace):
        checks[f'{i}_outer_schema']=row[111:114]==[64,cfg[34],row[33]]
        checks[f'{i}_solver_phase']=row[33]==[0,1,2,3,4,4,4,5,6,6][i]
    for i in range(7,10):
        row=trace[i];vals,prior=resumed(cfg,steps,i)
        for ix,v in vals.items():checks[f'{i}_analytic_{ix}']=contains(row[ix-1:ix+1],v)
        checks[f'{i}_offsets']=row[83:95]==trace[6][40:52]
        checks[f'{i}_inventory_retained']=row[81:83]==trace[6][36:38] and row[81]<row[82]
        checks[f'{i}_origin']=row[80]==steps[6][2]
        checks[f'{i}_thermal_certified']=row[98]<=cfg[34] and prior[37]/dec(F(cfg[4]))+dec(F(cfg[5]))<=dec(F(cfg[34]))
        checks[f'{i}_dwell_certified']=row[95]>=cfg[33] and prior[70]>=dec(F(cfg[33]))
        checks[f'{i}_firstlaw']=row[52]<=0<=row[53] and abs(dec(F(cfg[0]))+vals[41]-vals[37]-vals[47]-vals[49])<D('1e-100')
        checks[f'{i}_nonnegative_bounds']=all(v>=0 for v in row[40:52]) and 0<=row[36]<row[37]<row[57]
        checks[f'{i}_latch']=row[54]==1 and row[79]==1 and row[55]==0 and row[69:72]==[0,0,0]
        checks[f'{i}_monotonic']=row[36]>trace[i-1][36] and row[40]>trace[i-1][40]
        checks[f'{i}_water_feasible']=row[59]>=0 and row[59]<=cfg[14] and row[60]>=cfg[1]/cfg[8]
        checks[f'{i}_provenance']=row[:31]==cfg[:31] and row[64:67]==cfg[31:34]
    return checks
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    report=json.loads((folder/'report.json').read_text());checks=[];binary={};numeric=[];selfchecks=[]
    def check(kind,name,ok):checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    check('MAT','reopen',report==json.loads((folder/'mat_reopen.json').read_text()))
    check('MAT','original',(folder/'restart_chain_v64.mat').stat().st_size>1000)
    check('MATLAB','assertions',report['summary']['failed']==0 and all(x['passed'] for x in report['assertions']))
    runs={r['id']:r for r in report['runs']}
    for rec in json.loads((folder/'binary_manifest.json').read_text()):
        flat=[v[0] for v in struct.iter_unpack('<d',(folder/rec['file']).read_bytes())];cols=rec['columns']
        value=[flat[j:j+cols] for j in range(0,len(flat),cols)]
        if rec['rows']==1:value=value[0]
        key=(rec['id'],rec['field']);check('binary',str(key),value==runs[key[0]][key[1]] and len(flat)==rec['rows']*cols)
        check('binary','unique_'+str(key),key not in binary);binary[key]=value
    with localcontext() as ctx:
        ctx.prec=120
        for id,item in runs.items():
            cfg=binary[id,'cfg'];steps=binary[id,'steps'];trace=binary[id,'trace']
            for name,ok in review(cfg,steps,trace).items():check('analytic',id+'_'+name,ok)
            for i,row in enumerate(trace):
                vals,*_=exact(cfg[:34],steps[i][2],int(row[33])) if i<7 else resumed(cfg,steps,i)
                with localcontext() as more:
                    more.prec=160
                    again,*_=exact(cfg[:34],steps[i][2],int(row[33])) if i<7 else resumed(cfg,steps,i)
                for ix,v in vals.items():check('precision',f'{id}_{i}_{ix}',abs(v-again[ix])<D('1e-100')*max(D(1),abs(v)))
                numeric.append(dict(id=id,protocol_tick=i,phase=int(row[33]),time_h=str(vals[35]),energy_MWh=str(vals[37]),
                    energy_lo_MWh=row[36],energy_hi_MWh=row[37],heat_MWh=str(vals[41]),source_MWh=str(vals[43]),
                    source_lo_MWh=row[42],source_hi_MWh=row[43],compressor_MWh=str(vals[45]),standing_loss_MWh=str(vals[47]),
                    firstlaw_lo=row[52],firstlaw_hi=row[53],HP_ON=row[54],restart_origin_h=row[80]))
            for ref in item['references_v30']:
                p=list(map(F,ref['parameters']));dt,cap,_,_,etaC,etaD,lam,cut,C,Ta=p
                out=list(map(F,ref['output']));power=etaC*out[0]-out[1]/etaD
                rr=(-dec(lam)*dec(dt)).exp();en=dec(F(ref['initial']))*rr+dec(power)*(1-rr)/dec(lam)
                loss=dec(F(ref['initial']))+dec(power)*dec(dt)-en
                for label,v,k in [('energy',en,3),('loss',loss,4)]:
                    check('reference',f'{id}_{ref["tick"]}_{label}',abs(dec(out[k])-v)<D('1e-12')*max(D(1),abs(v)))
                check('reference',f'{id}_{ref["tick"]}_enclosure',contains(trace[ref['tick']-1][36:38],float(out[3])))
        first=next(iter(runs));cfg=binary[first,'cfg'];steps=binary[first,'steps'];tr=binary[first,'trace']
        for label in ['scalar_restart_inventory','offset_loss','origin_shift','ON_age_reset','OFF_dwell_erased','thermal_guard_erased','heat_credit','compressor_credit']:
            changed=copy.deepcopy(tr)
            if label=='scalar_restart_inventory':changed[7][81:83]=[sum(changed[7][81:83])/2]*2
            elif label=='offset_loss':changed[7][89]+=1
            elif label=='origin_shift':changed[8][80]+=.001
            elif label=='ON_age_reset':changed[8][38:40]=[0,0]
            elif label=='OFF_dwell_erased':changed[7][95:97]=[0,0]
            elif label=='thermal_guard_erased':changed[7][98]=cfg[34]+1
            elif label=='heat_credit':changed[8][40:42]=[x+1 for x in changed[8][40:42]]
            else:changed[8][44:46]=[x+1 for x in changed[8][44:46]]
            selfchecks.append(dict(name=label,passed=not all(review(cfg,steps,changed).values())))
    check('coverage','seven_runs',len(runs)==7)
    check('faults','specific_runtime',len(report['faults'])==14 and all(f['identifier'] and f['expected_guard'] in f['message'] for f in report['faults']))
    check('temporal','actual_prefix',report['valid_prefix']==next(iter(runs.values()))['trace'][:7])
    check('metadata','actual_chart',report['metadata']['chart_count']==1 and report['metadata']['license_observed']==1)
    check('scope','component_only',not report['coupled_six_mode_plant_acceptance'])
    mdl=ROOT/'matlab/simulink/DCHR_Restart_Chain_Stateflow_v64.slx'
    with zipfile.ZipFile(mdl) as ar:
        scripts=[];text=''
        for n in ar.namelist():
            if n.endswith('.xml'):
                body=ar.read(n);text+=body.decode('utf-8',errors='replace')
                scripts.extend(p.text for p in ET.fromstring(body).iter('P') if p.attrib.get('Name')=='script')
        check('SLX','bound_embedded_source',any(s and s.strip()==(ROOT/'matlab/simulink/restart_chain_kernel_v64.m').read_text().strip() for s in scripts))
        for name in ['RESTART_CHARGE','RECHARGE_CONTINUATION','PASSIVE_COOLING']:check('SLX',name,name in text)
    for rec in json.loads((folder/'preservation.json').read_text()):check('preservation',rec['path'],sha(ROOT/rec['path'])==rec['sha256'])
    for rec in json.loads((folder/'source_hashes.json').read_text()):check('sealed',rec['path'],sha(ROOT/rec['path'])==rec['sha256']==sha(folder/'source_snapshot'/rec['path']))
    receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')]
    check('execution','batch_exit',any(r['exit_code']==0 for r in receipts))
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    with (folder/f'numeric_traces_v64_{stamp}.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(numeric[0]));w.writeheader();w.writerows(numeric)
    result=dict(version='0.64',timestamp_utc=datetime.now(timezone.utc).isoformat(),model_sha256=sha(mdl),
        runs=len(runs),protocol_ticks=len(numeric),checks=checks,reviewer_selfchecks=selfchecks,
        summary=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks)))
    (folder/f'independent_QA_v64_{stamp}.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(summary=result['summary'],reviewer_selfchecks=selfchecks),indent=2))
    assert result['summary']['failed']==0 and all(c['passed'] for c in selfchecks)
if __name__=='__main__':main()
