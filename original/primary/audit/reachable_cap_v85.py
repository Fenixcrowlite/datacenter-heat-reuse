"""Prepare and independently review the conservative compiled compressor ceiling."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import localcontext
from fractions import Fraction as F
import copy, csv, hashlib, itertools, json, shutil, struct, sys, zipfile
import xml.etree.ElementTree as ET
from earliest_closed_form_v73 import analyze, rows
from verify_held_schedule_v74 import total_earliest, review_report
from temporal_reporting_v76 import temporal_checks
from energy_checks_v78 import energy_checks
from hp_partition_checks_v79 import hp_checks
from standing_loss_checks_v80 import loss_checks

ROOT=Path(__file__).resolve().parents[1]
MODEL='matlab/simulink/DCHR_Electrical_Dispatch_Stateflow_v85.slx'
LEDGERS=['automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md','audit/research_frontier_2026_10_08.md']
def stamp():return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):
    with p.open('x',encoding='utf-8') as out:json.dump(v,out,indent=2);out.write('\n')

def prepare():
    old=json.loads((ROOT/'results/electrical_conservatism_v84_20261013T105537_783028Z/spec.json').read_text())
    cases=copy.deepcopy(old['cases'])
    for c in cases:c['compare80']=c['family']=='six_mode' or c['family']=='event_control'
    for c in copy.deepcopy(cases):
        if c['family']=='charge':
            c['id']='loss_'+c['id'];c['p'][5]=.01;c['family']='positive_loss_charge';cases.append(c)
    c=copy.deepcopy(cases[1]);c.update(id='binding_stop',family='binding_stop',compare80=False,ceiling_MW=.2,initial=[9.5,1,1])
    c['p'][9]=c['p'][23]=0.;c['schedule']=[[.25,(j+1)*.25,0.,20.,1.,1.] for j in range(4)];cases.append(c)
    c=copy.deepcopy(cases[1]);c.update(id='zero_ceiling',family='zero',compare80=False,ceiling_MW=0.);cases.append(c)
    c=copy.deepcopy(cases[3]);c.update(id='cutoff_event',family='cutoff_event',compare80=True,initial=[5.65,0,1])
    c['schedule']=[[.25,.25,.5,0.,0.,0.]];cases.append(c)
    for c in cases:c['horizon_h']=sum(s[0] for s in c['schedule'])*1.01
    folder=ROOT/'results'/('reachable_cap_v85_'+stamp());folder.mkdir()
    dump(folder/'spec.json',dict(version='0.85',cases=cases,evidence_class='SYNTHETIC_CERTIFIED_WHOLE_SCHEDULE_CAP_NOT_DYNAMIC_MAXIMUM',
        required_modes=list(range(6)),required_events=[1,2,3],required_floor_crossing=True))
    preserved=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    dump(folder/'preservation.json',[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in preserved])
    dump(folder/'ledger_prefixes.json',[dict(path=p,size=(ROOT/p).stat().st_size,sha256=sha(ROOT/p)) for p in LEDGERS])
    sources=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'audit').glob('*.py'))+[ROOT/'audit/run_electrical_ceiling_v85.ps1',ROOT/'audit/run_electrical_ceiling_v85r2.ps1',ROOT/'audit/Reachable_cap_derivation_v85.md']
    records=[]
    for p in sources:
        rel=p.relative_to(ROOT);dst=folder/'source_snapshot'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
        records.append(dict(path=rel.as_posix(),sha256=sha(p)))
    dump(folder/'source_hashes.json',records);print(folder.relative_to(ROOT).as_posix())

def electrical_checks(r):
    p=list(map(F,r['raw_policy']));pe=list(map(F,r['p']));checks=[]
    def check(name,ok):checks.append(dict(name=r['id']+'_'+name,passed=bool(ok)))
    certs=rows(r['certificate']);Eb=F(certs[0][28]);E0=F(r['adapter']['initial'][0])
    Te=p[11]-p[12]-p[13];A=p[14]*(Te+F(273.15));Lf=p[18]+p[19]+p[17]-Te
    universal=p[25]*(1+A/Lf);charge=min(p[8],p[10],universal)
    reach=min(p[0]*(p[2]-p[1]),E0+p[6]*charge*p[26])
    Lmax=max(p[18]+p[19],p[1]+Eb/p[0]+p[16])+p[17]-Te
    exact_cap=min(p[10],p[25]*(1+A/Lmax))
    check('reachable_upper_enclosure',Eb>=reach)
    check('cap_safe',0<=pe[10]<=exact_cap)
    check('cap_tight',exact_cap-pe[10]<=max(F(1),abs(exact_cap))*F(1,10**12))
    check('only_thermal_cap_changed',pe[:10]+pe[11:]==p[:10]+p[11:25])
    check('declared_horizon_covers_exact_holds',sum((F(v[4]) for v in rows(r['input'])),F(0))<=p[26])
    for k,(row,cert) in enumerate(zip(rows(r['trace']),certs)):
        check(f'{k}_raw_certificate',list(map(F,cert))==p+[pe[10],Eb])
        check(f'{k}_committed_clock_within_horizon',F(row[60])<=p[26])
        for j in range(int(row[12])):
            z=list(map(F,row[100+80*j:180+80*j]));q=z[23];ehi=max(z[11],z[13])
            Lhi=max(p[18]+p[19],p[1]+ehi/p[0]+p[16])+p[17]-Te
            check(f'{k}_{j}_selected_cap',q<=pe[10])
            check(f'{k}_{j}_reachable_segment',ehi<=Eb)
            check(f'{k}_{j}_pointwise_electricity',q*Lhi/(A+Lhi)<=p[25])
            if p[25]==0:check(f'{k}_{j}_zero_exact',q==0 and z[35]==z[36]==0)
    return checks

def verify(folder):
    report=json.loads((folder/'report.json').read_text());checks=[];numeric=[];totals={}
    def check(kind,name,ok):checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    check('MAT','reopened_equal',report==json.loads((folder/'mat_reopen.json').read_text()))
    check('MAT','original_present',(folder/'electrical_ceiling_v85.mat').stat().st_size>1000)
    for e in json.loads((folder/'binary_manifest.json').read_text()):
        values=[v[0] for v in struct.iter_unpack('<d',(folder/e['file']).read_bytes())]
        m,n=e['rows'],e['columns'];matrix=[values[k:k+n] for k in range(0,len(values),n)] if n else []
        value=matrix[0] if m==1 else matrix;r=report['runs'][e['index']-1]
        check('binary',e['file'],len(values)==m*n and value==r[e['field']]);r[e['field']]=value
    spec=json.loads((folder/'spec.json').read_text());by={c['id']:c for c in spec['cases']}
    with localcontext() as ctx:
        ctx.prec=160
        for r in report['runs']:
            for c in electrical_checks(r)+temporal_checks(r)+energy_checks(r)+hp_checks(r)+loss_checks(r):check('binary_equations',c['name'],c['passed'])
            mapped=copy.deepcopy(r)
            for row in rows(mapped['trace']):row[1]=73;row[72:75]=[0,0,0]
            cs,ns=analyze(mapped);numeric+=ns
            for c in cs:check('closed_equations',c['name'],c['passed'])
            with localcontext() as low:
                low.prec=120;cs120,_=analyze(mapped)
            check('precision',r['id'],[c['passed'] for c in cs]==[c['passed'] for c in cs120])
            totals[r['id']]=total_earliest(mapped,ns)
            for name,ok in review_report(r,totals[r['id']]).items():check('report',r['id']+'_'+name,ok)
            c=by[r['id']]
            check('provenance',r['id'],r['raw_policy']==c['p']+[c['ceiling_MW'],c['horizon_h']] and rows(r['adapter']['schedule'])==c['schedule'] and r['adapter']['initial']==c['initial'])
            check('MAT',r['id'],(folder/(r['id']+'.mat')).stat().st_size>1000)
            if c['compare80']:
                check('reference',r['id'],rows(r['trace'])==rows(r['reference_trace']) and r['p']==c['p'])
    comparisons=[];observed_events=set();floor_crossings=0
    with localcontext() as ctx:
        ctx.prec=160
        for r in report['runs']:
            g=copy.deepcopy(r);g['trace']=rows(r['global_trace']);g['p']=g['trace'][0][75:100]
            for row in g['trace']:row[1]=73;row[72:75]=[0,0,0]
            gc,gn=analyze(g)
            for c in gc:check('global_closed_equations',c['name'],c['passed'])
            gt=total_earliest(g,gn);nt=totals[r['id']]
            if r['family'] in ['service','charge','positive_loss_charge']:
                check('comparison',r['id']+'_greater_heat',nt['hp_heat']>gt['hp_heat'])
                check('comparison',r['id']+'_greater_recovered_source',nt['recovered_source']>gt['recovered_source'])
                check('comparison',r['id']+'_greater_compressor_work',nt['compressor_work']>gt['compressor_work'])
            comparisons.append(dict(id=r['id'],new_cap=r['p'][10],global_cap=g['p'][10],
                new_totals={k:str(v) for k,v in nt.items()},global_totals={k:str(v) for k,v in gt.items()}))
            check('comparison',r['id']+'_cap_ge_global',r['p'][10]>=g['p'][10])
            p=list(map(F,r['p']));floorE=p[0]*(p[18]+p[19]-p[1]-p[16])
            for row in rows(r['trace']):
                for j in range(int(row[12])):
                    z=row[100+80*j:180+80*j];observed_events.add(z[2])
                    if r['family']=='positive_loss_charge' and F(z[11])<floorE<F(z[12]):floor_crossings+=1
    check('scope','stop_cutoff_restart_events',set([1,2,3])<=observed_events)
    check('scope','positive_loss_floor_crossing',floor_crossings>0)
    check('scope','binding_stop_event',any(row[102]==1 for r in report['runs'] if r['family']=='binding_stop' for row in rows(r['trace'])))
    dump(folder/'comparisons_v85.json',comparisons)
    selfchecks=[]
    victim=copy.deepcopy(next(r for r in report['runs'] if r['raw_policy'][25]==.05))
    victim['p'][10]=1
    selfchecks.append(dict(name='excessive_effective_cap_detected',passed=any(not c['passed'] for c in electrical_checks(victim))))
    victim=copy.deepcopy(next(r for r in report['runs'] if r['raw_policy'][25]==.05));victim['trace']=rows(victim['trace']);victim['trace'][0][123]=1
    selfchecks.append(dict(name='excessive_segment_heat_detected',passed=any(not c['passed'] for c in electrical_checks(victim))))
    victim=copy.deepcopy(report['runs'][0]);victim['certificate']=rows(victim['certificate']);victim['certificate'][0][25]=0
    selfchecks.append(dict(name='raw_certificate_corruption_detected',passed=any(not c['passed'] for c in electrical_checks(victim))))
    check('Stateflow','six_actual_modes',report['mode_coverage']==list(range(6)))
    check('Stateflow','actual_API',report['metadata']['license_observed']==1 and report['metadata']['chart_count']==1 and report['metadata']['simulation_mode']=='normal')
    check('scope','all_predeclared_schedules',len(report['runs'])==len(spec['cases']))
    check('scope','positive_interior_event_coverage',sum(row[13] for r in report['runs'] for row in rows(r['trace']))>0)
    check('faults','seven_actual_refusals',len(report['faults'])==7 and all(f['rejected'] and f['expected_guard'] in (folder/('fault_'+f['id']+'.txt')).read_text() for f in report['faults']))
    check('provenance','correct_model_release_label',report['saved_model_version']=='0.85')
    for manifest in ['preservation.json','source_hashes.json']:
        for e in json.loads((folder/manifest).read_text()):
            check('preservation',e['path'],sha(ROOT/e['path'])==e['sha256'] and (manifest!='source_hashes.json' or sha(folder/'source_snapshot'/e['path'])==e['sha256']))
    for e in json.loads((folder/'ledger_prefixes.json').read_text()):check('preservation',e['path'],hashlib.sha256((ROOT/e['path']).read_bytes()[:e['size']]).hexdigest()==e['sha256'])
    check('execution','successful_batch',any(json.loads(p.read_text(encoding='utf-8-sig'))['exit_code']==0 for p in folder.glob('execution_*.json')))
    check('MATLAB','assertions',report['summary']['failed']==0 and all(c['passed'] for c in report['assertions']))
    with zipfile.ZipFile(ROOT/MODEL) as archive:
        names=[n for n in archive.namelist() if n.startswith('simulink/stateflow/chart_') and n.endswith('.xml')]
        check('SLX','one_chart',len(names)==1)
        xml=ET.fromstring(archive.read(names[0]));scripts=[p.text or '' for p in xml.iter('P') if p.attrib.get('Name')=='script']
        for path in ['electrical_policy_v85.m','earliest_dispatch_kernel_v75.m','monitor_standing_loss_v80.m']:
            check('SLX','embedded_'+path,(ROOT/'matlab/simulink'/path).read_text() in scripts)
    result=dict(version='0.85',timestamp_utc=datetime.now(timezone.utc).isoformat(),checks=checks,
        summary=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks)),
        reviewer_selfchecks=selfchecks,model_sha256=sha(ROOT/MODEL),
        reconstructed_totals={k:{name:str(value) for name,value in t.items()} for k,t in totals.items()})
    dump(folder/('independent_QA_v85_'+stamp()+'.json'),result)
    with (folder/('closed_numeric_v85_'+stamp()+'.csv')).open('x',newline='',encoding='utf-8') as out:
        writer=csv.DictWriter(out,fieldnames=list(numeric[0]));writer.writeheader();writer.writerows(numeric)
    print(json.dumps(result['summary']))
    for c in checks:
        if not c['passed']:print(c)
    if result['summary']['failed'] or not all(c['passed'] for c in selfchecks):raise SystemExit(1)

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='verify':verify((ROOT/sys.argv[2]).resolve())
    else:raise SystemExit('prepare | verify results/folder')
