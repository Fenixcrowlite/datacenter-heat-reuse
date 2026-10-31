"""Independent closed exp/log QA of the saved v73 model and original MAT.

Uses exact binary inputs and 120/160-digit arithmetic. No production MATLAB
function, polynomial or bisection is called. Same-agent algorithmic QA.
"""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal as D, localcontext
from fractions import Fraction as F
import copy,csv,hashlib,json,shutil,struct,sys,zipfile
import xml.etree.ElementTree as ET
from earliest_closed_form_v73 import analyze, contains, dec, rows, storage
ROOT=Path(__file__).resolve().parents[1]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    report=json.loads((folder/'report.json').read_text());spec=json.loads((folder/'spec.json').read_text())
    checks=[];numeric=[];mutations=[];findings=[]
    def check(kind,name,ok):checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    runs={r['id']:r for r in report['runs']};probes={r['id']:r for r in report['probes']};binary={}
    check('MAT','reopened',report==json.loads((folder/'mat_reopen.json').read_text()))
    check('MAT','original',(folder/'earliest_admissibility_v73.mat').stat().st_size>1000)
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
        for name,index in [('root_midpoint_collapse',106),('threshold_corrupted',175),('source_erased',133),('offset_corrupted',151),('latch_corrupted',119),('event_kind_corrupted',102),('age_corrupted',116),('final_inventory_erased',4),('limiter_erased',67),('age_certificate_corrupted',62)]:
            r=copy.deepcopy(target);tr=rows(r['trace']);r['trace']=tr
            if name=='root_midpoint_collapse':tr[0][index:index+2]=[sum(tr[0][index:index+2])/2]*2
            elif name in ['source_erased','limiter_erased']:tr[0][index:index+2]=[0,0]
            elif name=='age_certificate_corrupted':
                r=copy.deepcopy(runs['disable_exact_dwell']);tr=rows(r['trace']);r['trace']=tr;tr[1][index]+=1
            else:tr[0][index]+=1
            cs,_=analyze(r);mutations.append(dict(name=name,passed=not all(v['passed'] for v in cs)))
        for id in ['passive_service_lambda_0p2','passive_service_lambda_1p0']:
            r=runs[id];p=list(map(dec,r['p']));tr=rows(r['trace']);u=rows(r['input']);t=sum((dec(v[4]) for v in u),D(0))
            en,_=storage(dec(u[0][9]),D(0),p[5],t)
            check('repair',id+'_full_schedule',len(tr)==len(u) and 0<en and contains(tr[-1][4:6],en))
            findings.append(dict(id=id,classification='REPAIRED_PASSIVE_WRAPPING_TESTED',held_intervals=len(u),time_h=str(t),exact_final_inventory=str(en),final_inventory_hull=tr[-1][4:6]))
        r=runs['disable_exact_dwell'];u=rows(r['input']);p=list(map(dec,r['p']));tr=rows(r['trace'])
        exactAge=dec(u[0][11])+sum((dec(v[4]) for v in u[:2]),D(0))
        check('repair','inclusive_ON_equality',exactAge==p[21] and tr[2][122]==2 and tr[1][61]==1 and contains(tr[1][63:65],exactAge-dec(tr[1][62])))
        findings.append(dict(id='disable_exact_dwell',classification='REPAIRED_INCLUSIVE_ON_DWELL_TESTED',exact_age=str(exactAge),age_hi=tr[1][62],age_residual=tr[1][63:65]))
        for id in ['source_limited','rounded_source_water_tie','source_below_tie']:
            r=runs[id];u=rows(r['input'])[0];p=list(map(dec,r['p']));z=rows(r['trace'])[0][100:180]
            q=dec(z[24])+dec(z[25]);E=dec(u[9]);Te=p[11]-p[12]-p[13];a=p[14]*(Te+dec(273.15))
            hot=max(p[18]+p[19],p[1]+E/p[0]+p[16]);rate=q*a/(a+hot+p[17]-Te);capacity=dec(u[6])*p[12]
            check('repair',id+'_exact_source_limit',0<rate<=capacity and q<=p[15]*p[16])
            findings.append(dict(id=id,classification='REPAIRED_SOURCE_LIMIT_PROOF_TESTED',selected_power=str(q),exact_source_power=str(rate),source_capacity=str(capacity),margin=str(capacity-rate)))
        ns=[n for n in numeric if n['id']=='restart_band_2m42'];z=rows(runs['restart_band_2m42']['trace'])[0][100:180]
        check('repair','tiny_correlated_work',D(ns[0]['work'])>0 and z[35]>=0 and contains(z[35:37],D(ns[0]['work'])))
        findings.append(dict(id='restart_band_2m42',classification='REPAIRED_POSITIVE_CORRELATED_WORK_TESTED',exact_first_work=ns[0]['work'],work_hull=z[35:37]))
        # Matched held schedules have identical boundary forcing; compare the
        # independently integrated trajectory, with original-MAT containment
        # already required above without tolerance.
        aggregate={}
        for id in ['repeated_0p25','repeated_0p5','repeated_1p0']:
            ns=[v for v in numeric if v['id']==id]
            aggregate[id]={k:sum((D(v[k]) for v in ns),D(0)) for k in ['heat','source','work','standing','service','unmet']}
            aggregate[id]['inventory']=D(ns[-1]['inventory'])
        for id in ['repeated_0p5','repeated_1p0']:
            for key,v in aggregate[id].items():check('partition',id+'_'+key,abs(v-aggregate['repeated_0p25'][key])<D('1e-90')*max(D(1),abs(v)))
    for c in spec['cases']:
        p=probes[c['id']];check('runtime',c['id']+'_expected',p['accepted']==c['expected_accept'])
        check('inputs',c['id'],rows(p['input'])==c['input'] and p['p']==c['p'])
        if not c['expected_accept']:
            check('runtime',c['id']+'_guard',bool(p['identifier']) and c['expected_guard'] in p['message'] and c['expected_guard'] in p['host_message'])
    check('coverage','six_modes',report['mode_coverage']==list(range(6)))
    check('MATLAB','assertions',report['summary']['failed']==0 and all(v['passed'] for v in report['assertions']))
    check('metadata','actual_chart',report['metadata']['license_observed']==1 and report['metadata']['chart_count']==1 and report['metadata']['simulation_mode']=='normal')
    model=ROOT/'matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v73r2.slx'
    with zipfile.ZipFile(model) as ar:
        scripts=[];xml=''
        for name in ar.namelist():
            if name.endswith('.xml'):
                data=ar.read(name);xml+=data.decode(errors='replace');scripts.extend(v.text for v in ET.fromstring(data).iter('P') if v.attrib.get('Name')=='script')
    for name in ['earliest_dispatch_kernel_v73r2','certify_event_root_v73','inventory_flow_v73','passive_contact_root_v73r2']:check('SLX',name,(ROOT/f'matlab/simulink/{name}.m').read_text() in scripts)
    for name in report['metadata']['states']:check('SLX',name,name in xml)
    for manifest in ['preservation.json','source_hashes.json','reviewer_sources.json']:
        for r in json.loads((folder/manifest).read_text()):
            ok=sha(ROOT/r['path'])==r['sha256']
            if manifest!='preservation.json':
                base='reviewer_source_snapshot' if manifest=='reviewer_sources.json' else 'source_snapshot'
                ok=ok and sha(folder/base/r['path'])==r['sha256']
            check(manifest,r['path'],ok)
    receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')]
    check('receipt','model_exit0',any(r['exit_code']==0 for r in receipts));check('receipt','model_log',any(p.stat().st_size>0 for p in folder.glob('matlab_*.log')))
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');csvpath=folder/f'closed_event_traces_v73_{stamp}.csv'
    with csvpath.open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(numeric[0]));w.writeheader();w.writerows(numeric)
    result=dict(version='0.73',timestamp_utc=datetime.now(timezone.utc).isoformat(),checks=checks,reviewer_selfchecks=mutations,findings=findings,partition_totals={id:{k:str(v) for k,v in vs.items()} for id,vs in aggregate.items()},model_sha256=sha(model),numeric_csv=csvpath.name,
        independence='Same-agent exact-binary Fraction/120/160-digit closed exp/log trajectories and analytic source integrals. No production function called. Original MAT reopened/exported by MATLAB, no independent HDF5 parser.',
        summary=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks)))
    out=folder/f'independent_QA_v73_{stamp}.json';out.write_text(json.dumps(result,indent=2)+'\n')
    failed=[c for c in checks if not c['passed']];print(json.dumps(dict(qa=out.relative_to(ROOT).as_posix(),summary=result['summary'],selfchecks=mutations,findings=findings,failed=failed[:50])))
    (folder/f'independent_QA_v73_{stamp}.log').write_text(json.dumps(dict(summary=result['summary'],selfchecks=mutations,failed=failed[:100]),indent=2)+'\n')
    return int(bool(failed) or not all(r['passed'] for r in mutations))

if __name__=='__main__':sys.exit(main())
