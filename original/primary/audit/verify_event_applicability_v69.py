"""Independent closed-form QA of saved-v68 event applicability defects.

Exact binary inputs, Decimal exp/log; no production MATLAB functions imported.
Original MAT is reopened/exported by MATLAB, not parsed independently here.
"""
from pathlib import Path
from datetime import datetime, timezone
from fractions import Fraction as F
from decimal import Decimal as D, localcontext
import copy, csv, hashlib, json, struct, sys, zipfile
import xml.etree.ElementTree as ET
from verify_interval_dispatch_v66 import analyze, storage
from verify_span_repair_v68r2 import review
from verify_capacity_chain_v63 import dec, contains

ROOT = Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(v): return [v] if isinstance(v[0], (int, float)) else v

def witness(kind, cfg, inputs, trace):
    """Classify using ACTUAL allocated forcing and retained incoming state."""
    p=list(map(F,cfg[35:60]));u=inputs[-1];r=trace[-1]
    E=dec(F(r[159]));B=p[6]*F(r[121])-F(r[122])/p[7]
    t=dec(F(u[4]));end,_=storage(E,B,p[5],t)
    cut=p[0]*(p[3]-p[1]);restart=p[0]*(p[4]-p[1]);stop=p[0]*(p[24]-p[1])
    if kind=='inactive_cutoff':
        return dict(no_actual_discharge=r[122]==0, actual_HP_direct=r[120]==u[5]>0,
                    actual_inventory_constant=B==0 and p[5]==0 and end==E,
                    hypothetical_cutoff_classification=r[220] in [0,2],
                    separated_from_actual_cutoff=E>dec(cut),
                    strict_control_eligible=r[220]!=2 or u[3]==0)
    if kind=='inactive_stop':
        return dict(HP_stays_OFF=r[54]==r[163]==0, zero_charge=r[121]==0,
                    OFF_dwell_blocks_restart=F(r[162])<p[22],
                    hypothetical_stop_certified=r[205]==1 and r[216]==1,
                    actual_inventory_constant=B==0 and p[5]==0 and end==E,
                    actual_below_stop=end<dec(stop))
    if kind=='missing_forced_restart':
        eq=dec(B/p[5]) if p[5] else None
        target=dec(restart)
        root=-((target-eq)/(E-eq)).ln()/dec(p[5]) if p[5] else (target-E)/dec(B)
        wait=max(D(0),dec(p[22])-dec(F(r[161])))
        ready=max(root,wait)
        return dict(HP_initially_OFF=r[163]==0, actual_discharge=B<0 and r[122]>0,
                    actual_restart_crossing=0<root<t and end<target<E,
                    dwell_ready_before_end=ready<t,
                    discharge_above_cutoff=end>dec(cut),
                    enabled_available_HP=u[7]==1 and u[6]>0,
                    passive_restart_has_no_event=r[235]==0 and r[246]==0,
                    sampled_HP_stays_OFF=r[54]==0)
    return {}

def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    report=json.loads((folder/'report.json').read_text());checks=[];mutations=[];numeric=[];defects=[]
    def check(kind,name,ok): checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    check('MAT','reopened',report==json.loads((folder/'mat_reopen.json').read_text()))
    check('MAT','original_report',(folder/'event_applicability_v69.mat').stat().st_size>1000)
    runs={r['id']:r for r in report['runs']};binary={}
    for rec in json.loads((folder/'binary_manifest.json').read_text()):
        raw=(folder/rec['file']).read_bytes();flat=[x[0] for x in struct.iter_unpack('<d',raw)];n=rec['columns']
        value=[flat[k:k+n] for k in range(0,len(flat),n)]
        if rec['rows']==1:value=value[0]
        key=rec['id'],rec['field'];check('binary','unique_'+str(key),key not in binary)
        check('binary',str(key),value==runs[key[0]][key[1]] and len(flat)==rec['rows']*n);binary[key]=value
    certificates=[]
    with localcontext() as ctx:
        ctx.prec=160
        for id,r in runs.items():
            cfg=binary[id,'cfg'];u=rows(binary[id,'input']);tr=rows(binary[id,'trace'])
            ac,nums=analyze(cfg,u,[x[:205] for x in tr])
            for name,ok in ac.items():check('actual_analytic',id+'_'+name,ok)
            with localcontext() as less:
                less.prec=120;ac120,_=analyze(cfg,u,[x[:205] for x in tr])
            check('precision',id+'_120_160_decisions',ac==ac120)
            for v in nums:numeric.append(dict(id=id,**v))
            check('MAT',id+'_original',(folder/(id+'.mat')).stat().st_size>1000)
            wc=witness(r['audit_kind'],cfg,u,tr)
            for name,ok in wc.items():check('defect',id+'_'+name,ok)
            if wc:defects.append(dict(id=id,kind=r['audit_kind'],checks=wc,
                actual_forcing=str(F(cfg[41])*F(tr[-1][121])-F(tr[-1][122])/F(cfg[42])),
                inventory_in=tr[-1][159:161],inventory_out=tr[-1][36:38],
                actual_charge=tr[-1][121],actual_discharge=tr[-1][122],
                HP_ON=tr[-1][54],stop_status=tr[-1][205],cutoff_status=tr[-1][220],restart_status=tr[-1][235]))
            p=cfg[35:60]
            for tick,(uu,row) in enumerate(zip(u,tr)):
                for j,label in enumerate(['stop','cutoff','restart']):
                    z=row[205+15*j:220+15*j]
                    if z[12]==0:
                        check('unused',f'{id}_{tick}_{label}',all(v==0 for v in z));continue
                    args=(row[159:161],row[250+2*j:252+2*j],p[5],z[13:15],1 if j==0 else -1,uu[4],p[22] if j==2 else 0,row[161:163] if j==2 else [0,0],z)
                    c,_=review(*args)
                    for name,ok in c.items():check('hypothetical_root',f'{id}_{tick}_{label}_{name}',ok)
                    certificates.append(args)
            for ref in r['references_v30']:
                pp=list(map(F,ref['parameters']));out=ref['output'];B=pp[4]*F(out[0])-F(out[1])/pp[5]
                en,_=storage(dec(F(ref['initial'])),B,pp[6],dec(pp[0]))
                check('v30',id+'_'+str(ref['initial']),abs(en-dec(F(out[3])))<D('1e-12')*max(D(1),abs(en)))
        for probe in report['root_probes']:
            args=tuple(probe[k] for k in ['E','B','lambda','target','direction','horizon','dwell','age','output'])
            c,roots=review(*args)
            for name,ok in c.items():check('forced_root_probe',probe['id']+'_'+name,ok)
            check('forced_root_probe',probe['id']+'_actual_not_passive',probe['B'][1]<0 and probe['output'][0]==1 and probe['output'][11]==1)
            defects.append(dict(id=probe['id'],kind='independent_forced_restart_root',root_lower=str(min(roots)),root_upper=str(max(roots)),certificate=probe['output']))
            certificates.append(args)
        base=runs['HP_only_contact_strict0'];cfg=base['cfg'];u=rows(base['input']);tr=rows(base['trace'])
        for label,index,change in [('inventory_erased',36,'zero'),('direct_service_corrupted',120,'plus'),('source_energy_erased',42,'zero'),('mode_corrupted',114,'plus')]:
            altered=copy.deepcopy(tr)
            if change=='zero':altered[0][index:index+2]=[0,0]
            else:altered[0][index]+=1
            ac,_=analyze(cfg,u,[x[:205] for x in altered]);mutations.append(dict(name=label,passed=not all(ac.values())))
        base=next(v for v in certificates if v[-1][0]==1)
        altered=copy.deepcopy(base);altered[-1][1]=altered[-1][2]
        c,_=review(*altered);mutations.append(dict(name='root_bracket_collapsed',passed=not all(c.values())))
        base=runs['OFF_discharge_restart_0p0'];tr=rows(base['trace']);altered=copy.deepcopy(tr);altered[-1][235]=1
        wc=witness(base['audit_kind'],base['cfg'],rows(base['input']),altered)
        mutations.append(dict(name='omission_witness_falsified',passed=not all(wc.values())))
    for f in report['faults']:
        check('execution',f['id']+'_actual_guard',bool(f['identifier']) and f['expected_guard'] in f['message'])
        if f['prefix']:
            check('execution',f['id']+'_prefix',rows(f['prefix'])==rows(runs[f['base_id']]['trace'])[:-1])
    check('coverage','six_modes',report['mode_coverage']==list(range(6)))
    check('MATLAB','all_assertions',report['summary']['failed']==0 and all(c['passed'] for c in report['assertions']))
    check('metadata','actual_Stateflow',report['metadata']['license_observed']==1 and report['metadata']['chart_count']==1 and report['metadata']['simulation_mode']=='normal')
    mdl=ROOT/'matlab/simulink/DCHR_Span_Repair_Stateflow_v68.slx'
    with zipfile.ZipFile(mdl) as ar:
        scripts=[];text=''
        for name in ar.namelist():
            if name.endswith('.xml'):
                data=ar.read(name);text+=data.decode(errors='replace')
                scripts.extend(p.text for p in ET.fromstring(data).iter('P') if p.attrib.get('Name')=='script')
    for name in ['event_observer_v68','interval_dispatch_kernel_v68']:
        check('SLX',name,(ROOT/f'matlab/simulink/{name}.m').read_text() in scripts)
    for name in report['metadata']['states']:check('SLX',name,name in text)
    for name in ['preservation.json','source_hashes.json']:
        for rec in json.loads((folder/name).read_text()):
            ok=sha(ROOT/rec['path'])==rec['sha256']
            if name=='source_hashes.json':ok=ok and sha(folder/'source_snapshot'/rec['path'])==rec['sha256']
            check(name,rec['path'],ok)
    receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')]
    check('receipt','exit0',any(v['exit_code']==0 and v['evidence_class']=='OBSERVED_LOCAL_MATLAB_BATCH' for v in receipts))
    check('receipt','log_present',any(p.stat().st_size>0 for p in folder.glob('matlab_*.log')))
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    csvpath=folder/f'actual_traces_v69_{stamp}.csv'
    with csvpath.open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(numeric[0]));w.writeheader();w.writerows(numeric)
    result=dict(version='0.69',timestamp_utc=datetime.now(timezone.utc).isoformat(),checks=checks,
        reviewer_selfchecks=mutations,defect_witnesses=defects,model_sha256=sha(mdl),numeric_csv=csvpath.name,
        independence='Same-agent closed-form Fraction/Decimal algorithms; not independent personnel. MATLAB-reopened original MAT binary export, no independent HDF5 parser.',
        summary=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks)))
    out=folder/f'independent_QA_v69_{stamp}.json'
    with out.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(dict(qa=out.relative_to(ROOT).as_posix(),summary=result['summary'],mutations=mutations)))
    failed=[c for c in checks if not c['passed']]
    if failed:print(json.dumps(failed,indent=2))
    return int(bool(failed) or not all(v['passed'] for v in mutations))
if __name__=='__main__':sys.exit(main())
