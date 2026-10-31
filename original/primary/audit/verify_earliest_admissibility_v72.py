"""Closed-form QA of actual saved-v71 traces and four numerical blockers.

Inherits the independent Fraction/Decimal exp/log/source-integral reviewer,
never calls production MATLAB. Instrumented host replay is labelled separately
and only supplies branch operands; actual failures come from saved-model sim.
"""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal as D, localcontext
from fractions import Fraction as F
import copy, csv, hashlib, json, struct, sys, zipfile
import xml.etree.ElementTree as ET
from verify_earliest_dispatch_v71 import analyze, contains, dec, root, rows, source_integral, storage
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    report=json.loads((folder/'report.json').read_text());checks=[];numeric=[];mutations=[];findings=[]
    def check(kind,name,ok):checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    runs={r['id']:r for r in report['runs']};probes={r['id']:r for r in report['probes']};binary={}
    check('MAT','reopened',report==json.loads((folder/'mat_reopen.json').read_text()))
    check('MAT','original',(folder/'earliest_admissibility_v72.mat').stat().st_size>1000)
    for rec in json.loads((folder/'binary_manifest.json').read_text()):
        vals=[v[0] for v in struct.iter_unpack('<d',(folder/rec['file']).read_bytes())];n=rec['columns']
        data=[vals[k:k+n] for k in range(0,len(vals),n)]
        if rec['rows']==1:data=data[0]
        obj=probes[rec['id'][6:]] if rec['id'].startswith('probe_') else runs[rec['id']]
        check('binary',rec['id']+'_'+rec['field'],data==obj[rec['field']] and len(vals)==n*rec['rows'])
        binary[rec['id'],rec['field']]=data
    with localcontext() as ctx:
        ctx.prec=160
        for id,r in runs.items():
            rr=dict(r,**{k:binary[id,k] for k in ['p','input','trace']});cs,ns=analyze(rr);numeric+=ns
            for cc in cs:check('trajectory',cc['name'],cc['passed'])
            with localcontext() as less:
                less.prec=120;cs120,_=analyze(rr)
            check('precision',id,[v['passed'] for v in cs]==[v['passed'] for v in cs120])
            check('MAT',id,(folder/(id+'.mat')).stat().st_size>1000)
            for j,ref in enumerate(r['reference_v30']):
                pp=list(map(dec,ref['parameters']));B=pp[4]*dec(ref['charge'])-dec(ref['discharge'])/pp[5]
                en,_=storage(dec(ref['initial']),B,pp[6],pp[0])
                check('v30',id+f'_{j}',abs(en-dec(ref['output'][3]))<D('1e-12')*max(D(1),abs(en)))
        target=runs['multiple_cycles_one_call']
        for name,index in [('root_midpoint_collapse',106),('threshold_corrupted',175),('source_erased',133),('offset_corrupted',151),('latch_corrupted',119),('event_kind_corrupted',102),('age_corrupted',116),('final_inventory_erased',4)]:
            r=copy.deepcopy(target);tr=rows(r['trace']);r['trace']=tr
            if name=='root_midpoint_collapse':tr[0][index:index+2]=[sum(tr[0][index:index+2])/2]*2
            elif name=='source_erased':tr[0][index:index+2]=[0,0]
            else:tr[0][index]+=1
            cs,_=analyze(r);mutations.append(dict(name=name,passed=not all(v['passed'] for v in cs)))
        expected={
            'passive_service_lambda_0p2':(91,'v71 TES bounds'),
            'passive_service_lambda_1p0':(23,'v71 TES bounds'),
            'disable_exact_dwell':(3,'v71 ON dwell not certified'),
            'disable_before_dwell':(2,'v71 ON dwell not certified'),
            'source_limited':(1,'v71 finite source capacity'),
            'rounded_source_water_tie':(1,'v71 finite source capacity'),
            'source_below_tie':(1,'v71 finite source capacity'),
            'restart_band_2m42':(1,'v71 nonnegative energy'),
            'segment_budget_exhaustion':(1,'v71 event segment budget')}
        check('runtime','exact_rejection_set',{id for id,p in probes.items() if not p['accepted']}==set(expected))
        for id,(tick,guard) in expected.items():
            p=probes[id];check('runtime',id,p['fault_tick']==tick and bool(p['identifier']) and guard in p['message'] and guard in p['host_message'])
            if tick>1:
                pr=runs[id+'_valid_prefix'];check('runtime',id+'_prefix',len(rows(pr['trace']))==tick-1 and rows(pr['input'])==rows(p['input'])[:tick-1])
        # Exact passive trajectories never reach zero/capacity at these finite times.
        for id in ['passive_service_lambda_0p2','passive_service_lambda_1p0']:
            p=list(map(dec,binary['probe_'+id,'p']));u=rows(binary['probe_'+id,'input']);n=probes[id]['fault_tick'];dt=dec(u[0][4]);initial=dec(u[0][9])
            time=sum((dec(r[4]) for r in u[:n]),D(0));E,_=storage(initial,D(0),p[5],time)
            last=rows(binary[id+'_valid_prefix','trace'])[-1];exactPrefix,_=storage(initial,D(0),p[5],time-dt)
            cap=p[0]*(p[2]-p[1]);check('passive_defect',id+'_exact_positive',0<E<cap)
            check('passive_defect',id+'_prefix_encloses',contains(last[4:6],exactPrefix))
            check('passive_defect',id+'_passive_service',all(r[5]==.5 and r[7]==1 and r[8]==0 for r in u))
            exactDecay=(-p[5]*dt).exp();wrappingFactor=2-exactDecay
            findings.append(dict(id=id,classification='OPEN_PASSIVE_INTERVAL_WRAPPING_FALSE_REJECTION',first_rejected_tick=n,time_h=str(time),exact_inventory=str(E),last_accepted_inventory_hull=last[4:6],exact_prefix_inventory=str(exactPrefix),exact_contraction=str(exactDecay),dependency_width_factor=str(wrappingFactor)))
        id='disable_exact_dwell';p=list(map(dec,binary['probe_'+id,'p']));u=rows(binary['probe_'+id,'input']);pre=runs[id+'_valid_prefix'];last=rows(pre['trace'])[-1]
        exactAge=dec(u[0][11])+sum((dec(r[4]) for r in u[:2]),D(0))
        check('dwell_defect','equality',exactAge==p[21] and dec(last[7])<p[21]<=dec(last[8]))
        findings.append(dict(id=id,classification='OPEN_EXACT_ON_DWELL_FALSE_REJECTION',exact_age_h=str(exactAge),minimum_ON_h=str(p[21]),retained_age_hull=last[7:9]))
        early=rows(binary['probe_disable_before_dwell','input']);check('control','early_disable_correct_rejection',dec(early[0][4])<p[21])
        check('control','disable_after_dwell_accepted',probes['disable_after_dwell']['accepted'])
        diagnostics=json.loads((folder/'rejection_diagnostics_v72.json').read_text());dg={p['id']:p for p in diagnostics['probes']}
        check('diagnostic','label',diagnostics['evidence_class']=='INSTRUMENTED_HOST_REPLAY_ONLY_NOT_STATEFLOW_OR_INDEPENDENT_QA')
        check('diagnostic','MAT',(folder/'rejection_diagnostics_v72.mat').stat().st_size>1000)
        for rec in json.loads((folder/'diagnostic_manifest_v72.json').read_text()):
            data=[v[0] for v in struct.iter_unpack('<d',(folder/rec['file']).read_bytes())]
            check('diagnostic','binary_'+rec['id'],len(data)==1380 and data==dg[rec['id']]['diagnostic']);dg[rec['id']]['diagnostic']=data
        for id in ['source_limited','rounded_source_water_tie','source_below_tie']:
            d=dg[id]['diagnostic'];p=list(map(dec,binary['probe_'+id,'p']));u=rows(binary['probe_'+id,'input'])[0];q=dec(d[67]);E=dec(u[9])
            Te=p[11]-p[12]-p[13];a=p[14]*(Te+dec(273.15));hot=max(p[18]+p[19],p[1]+E/p[0]+p[16]);rate=q*a/(a+hot+p[17]-Te);cap=dec(u[6])*p[12]
            check('source_defect',id+'_exact_admissible',0<rate<=cap and q<=p[10] and q<=p[15]*p[16])
            check('source_defect',id+'_constant_floor',p[1]+E/p[0]+p[16]<=p[18]+p[19] and p[5]==0 and u[8]==0)
            check('source_defect',id+'_outward_guard_conflict',d[61]==72 and dec(d[64])>dec(d[66]) and contains(d[63:65],rate) and contains(d[65:67],cap))
            findings.append(dict(id=id,classification='OPEN_SOURCE_LIMIT_PROOF_FALSE_REJECTION',host_replay_heat_power=str(q),exact_source_power=str(rate),exact_source_capacity=str(cap),exact_margin=str(cap-rate),source_rate_hull=d[63:65],capacity_hull=d[65:67]))
        id='restart_band_2m42';d=dg[id]['diagnostic'];p=list(map(dec,binary['probe_'+id,'p']));u=rows(binary['probe_'+id,'input'])[0]
        q=dec(d[62]);initial=dec(u[9]);stop=p[0]*(p[24]-p[1]);B=p[6]*q;t=root(initial,B,p[5],stop,1)
        src=source_integral(initial,B,p[5],t,q,p);heat=q*t;work=heat-src;endpoint,integral=storage(initial,B,p[5],t)
        check('energy_defect','positive_exact_work',0<work<heat and contains(d[67:69],work) and d[67]<0)
        check('energy_defect','root_enclosed',d[61]==73 and d[73]==1 and d[74]==1 and contains(d[69:71],t))
        check('energy_defect','exact_storage_law',abs(initial+heat-endpoint-p[5]*integral-(1-p[6])*heat)<D('1e-100'))
        findings.append(dict(id=id,classification='OPEN_CORRELATED_WORK_NONNEGATIVITY_FALSE_REJECTION',exact_stop_time_h=str(t),root_time_hull=d[69:71],exact_heat=str(heat),exact_source=str(src),exact_work=str(work),work_hull=d[67:69],restart_temperature_band=str(p[24]-p[4])))
        # Explicit segment budget is a fail-closed resource domain, not a physics bug.
        id='segment_budget_exhaustion';p=list(map(dec,binary['probe_'+id,'p']));u=rows(binary['probe_'+id,'input'])[0]
        C,Ta=p[:2];E=dec(u[9]);restart=C*(p[4]-Ta);stop=C*(p[24]-Ta);remaining=dec(u[4]);on=1;count=events=0
        Te=p[11]-p[12]-p[13];a=p[14]*(Te+dec(273.15));L=min(p[10],dec(u[6])*p[12]*(1+(p[18]+p[19]+p[17]-Te)/a),p[15]*p[16])
        while remaining>0 and count<100:
            B=p[6]*min(p[8],L) if on else D(0);target=stop if on else restart
            duration=root(E,B,p[5],target,1 if on else -1)
            if duration>=remaining:count+=1;remaining=D(0);break
            check('budget_control',f'positive_segment_{count}',duration>0);remaining-=duration;E=target;on=1-on;count+=1;events+=1
        check('budget_control','exceeds_16',count>16 and remaining==0)
        findings.append(dict(id=id,classification='EXPLICIT_FAIL_CLOSED_SEGMENT_BUDGET_LIMIT',independent_ideal_policy_segments=count,interior_events=events,scope='Ideal exact mathematical policy only; no trace claimed for rejected call.'))
    check('coverage','six_modes',report['mode_coverage']==list(range(6)))
    check('MATLAB','assertions',report['summary']['failed']==0 and all(v['passed'] for v in report['assertions']))
    check('metadata','chart',report['metadata']['license_observed']==1 and report['metadata']['chart_count']==1 and report['metadata']['simulation_mode']=='normal')
    model=ROOT/'matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v71.slx'
    with zipfile.ZipFile(model) as ar:
        scripts=[];xml=''
        for name in ar.namelist():
            if name.endswith('.xml'):
                data=ar.read(name);xml+=data.decode(errors='replace');scripts.extend(v.text for v in ET.fromstring(data).iter('P') if v.attrib.get('Name')=='script')
    for name in ['earliest_dispatch_kernel_v71','certify_event_root_v71']:check('SLX',name,(ROOT/f'matlab/simulink/{name}.m').read_text() in scripts)
    for name in report['metadata']['states']:check('SLX',name,name in xml)
    for manifest in ['preservation.json','source_hashes.json']:
        for r in json.loads((folder/manifest).read_text()):
            ok=sha(ROOT/r['path'])==r['sha256']
            if manifest=='source_hashes.json':ok=ok and sha(folder/'source_snapshot'/r['path'])==r['sha256']
            check(manifest,r['path'],ok)
    for r in json.loads((folder/'reviewer_sources.json').read_text()):
        check('reviewer_sources',r['path'],sha(ROOT/r['path'])==r['sha256'] and sha(folder/'reviewer_source_snapshot'/r['path'])==r['sha256'])
    receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')]
    check('receipt','model_exit0',any(r['exit_code']==0 for r in receipts));check('receipt','model_log',any(p.stat().st_size>0 for p in folder.glob('matlab_*.log')))
    receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('diagnostic_execution_*.json')];check('receipt','diagnostic_exit0',any(r['exit_code']==0 for r in receipts))
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');csvpath=folder/f'closed_event_traces_v72_{stamp}.csv'
    with csvpath.open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(numeric[0]));w.writeheader();w.writerows(numeric)
    result=dict(version='0.72',timestamp_utc=datetime.now(timezone.utc).isoformat(),checks=checks,reviewer_selfchecks=mutations,findings=findings,model_sha256=sha(model),numeric_csv=csvpath.name,
        independence='Same-agent exact-binary Fraction/120/160-digit closed exp/log trajectories and analytic source integrals. No production function called. Original MAT reopened/exported by MATLAB. Diagnostic host replay supplies branch operands and is not independent QA or saved-model execution.',
        summary=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks)))
    out=folder/f'independent_QA_v72_{stamp}.json';out.write_text(json.dumps(result,indent=2)+'\n')
    failed=[c for c in checks if not c['passed']];print(json.dumps(dict(qa=out.relative_to(ROOT).as_posix(),summary=result['summary'],selfchecks=mutations,findings=findings,failed=failed[:40])))
    return int(bool(failed) or not all(r['passed'] for r in mutations))
if __name__=='__main__':sys.exit(main())
