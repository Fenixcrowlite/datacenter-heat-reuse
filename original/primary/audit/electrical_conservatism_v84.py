"""Saved-Stateflow execution review and independent conditioned-limit comparator."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal as D, localcontext
from fractions import Fraction as F
import copy, csv, hashlib, json, shutil, struct, sys, zipfile
import xml.etree.ElementTree as ET
from earliest_closed_form_v73 import analyze, rows, dec
from verify_held_schedule_v74 import total_earliest, review_report
from electrical_ceiling_v83r2 import electrical_checks
from temporal_reporting_v76 import temporal_checks
from energy_checks_v78 import energy_checks
from hp_partition_checks_v79 import hp_checks
from standing_loss_checks_v80 import loss_checks

ROOT=Path(__file__).resolve().parents[1]
MODEL='matlab/simulink/DCHR_Electrical_Dispatch_Stateflow_v83r2.slx'
LEDGERS=['automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md','audit/research_frontier_2026_10_08.md']
def stamp(): return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):
    with p.open('x',encoding='utf-8') as f: json.dump(v,f,indent=2);f.write('\n')

def prepare():
    old=json.loads((ROOT/'results/electrical_ceiling_v83r2_20261013T104142_686092Z/spec.json').read_text())
    cases=copy.deepcopy(old['cases'][:6])
    for c in cases: c['compare80']=c['id']=='HP_only'
    event=copy.deepcopy(next(c for c in old['cases'] if c['id']=='cycles_P1000.0'))
    event['family']='event_control';event['compare80']=False;cases.append(event)
    for family in ['service','charge']:
        for E in [3.,4.95,8.5]:
            for approach in [1.,10.]:
                p=cases[1]['p'].copy()
                p[5]=0.;p[9]=0.;p[23]=0.;p[13]=p[17]=approach
                schedule=[[.25,(i+1)*.25,2. if family=='service' else 0.,20.,1.,float(family=='charge')] for i in range(4)]
                cases.append(dict(id=f'{family}_E{E}_a{approach}',family=family,p=p,ceiling_MW=.05,
                    compare80=False,initial=[E,1,1],schedule=schedule))
    folder=ROOT/'results'/('electrical_conservatism_v84_'+stamp());folder.mkdir()
    dump(folder/'spec.json',dict(version='0.84',cases=cases,comparison_scope='INDEPENDENT_HYPOTHETICAL_CONDITIONED_LIMIT_NOT_STATEFLOW_IMPLEMENTATION',
        precision_digits=[120,160],precision_budget='1e-100',RK4_budget_MWh='1e-10',RK4_steps=[1024,2048]))
    preserved=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    dump(folder/'preservation.json',[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in preserved])
    dump(folder/'ledger_prefixes.json',[dict(path=p,size=(ROOT/p).stat().st_size,sha256=sha(ROOT/p)) for p in LEDGERS])
    sources=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'audit').glob('*.py'))+list((ROOT/'audit').glob('*v84.ps1'))+[ROOT/'audit/Electrical_conservatism_derivation_v84.md']
    records=[]
    for p in sources:
        rel=p.relative_to(ROOT);dest=folder/'source_snapshot'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
        records.append(dict(path=rel.as_posix(),sha256=sha(p)))
    dump(folder/'source_hashes.json',records)
    print(folder.relative_to(ROOT).as_posix())

def axes(p):
    Te=p[11]-p[12]-p[13];A=p[14]*(Te+dec(273.15))
    lf=p[18]+p[19]+p[17]-Te;b=p[1]+p[16]+p[17]-Te
    switch=p[0]*(p[18]+p[19]-p[1]-p[16])
    return A,lf,b,switch

def conditioned(c):
    """Closed separated charging ODE or exact constant-temperature service."""
    p=list(map(dec,c['p']));P=dec(c['ceiling_MW']);E0=dec(c['initial'][0])
    t=sum((dec(s[0]) for s in c['schedule']),D(0));A,lf,b,switch=axes(p)
    def lift(E):return max(lf,b+E/p[0])
    q0=P*(1+A/lift(E0));E=E0;cross=D(0);residual=D(0)
    if c['family']=='service': heat=q0*t;service=heat
    else:
        assert p[5]==0 and P>0
        remaining=t
        if E<switch:
            cross=min(remaining,(switch-E)/(p[6]*P*(1+A/lf)))
            E+=p[6]*P*(1+A/lf)*cross;remaining-=cross
        if remaining>0:
            L0=lift(E);target=p[6]*P*remaining/p[0]
            # Newton inversion of a strictly increasing implicit primitive.
            L=L0+target*(1+A/L0)
            for _ in range(50):
                residual=L-L0-A*((L+A)/(L0+A)).ln()-target
                updated=L-residual*(L+A)/L
                if updated==L:break
                L=updated
            residual=L-L0-A*((L+A)/(L0+A)).ln()-target
            E=p[0]*(L-b)
        heat=(E-E0)/p[6];service=D(0)
    work=P*t;source=heat-work
    return dict(hp_heat=heat,recovered_source=source,compressor_work=work,delivered_service=service,
        final_inventory=E,charge_loss=(1-p[6])*heat if c['family']=='charge' else D(0),
        initial_heat_rate=q0,final_heat_rate=P*(1+A/lift(E)),floor_crossing_h=cross,
        inversion_residual=residual,duration=t)

def dynamic_checks(c,v):
    p=list(map(dec,c['p']));P=dec(c['ceiling_MW']);E0=dec(c['initial'][0]);A,lf,b,_=axes(p)
    E=v['final_inventory'];qlo=v['final_heat_rate'];qhi=v['initial_heat_rate']
    limits=[p[10],p[15]*p[16],min(dec(s[3]) for s in c['schedule'])*p[12]*(1+lf/A)]
    if c['family']=='charge':limits.append(p[8])
    else:limits.append(min(dec(s[2]) for s in c['schedule']))
    eps=D('1e-110')
    return dict(positive_axes=A>0 and lf>0,within_tank=0<=E0<=E<p[0]*(p[2]-p[1]),
        below_stop=E<p[0]*(p[24]-p[1]),no_discharge_or_boiler=p[9]==p[23]==0,
        zero_loss=p[5]==0,other_limits_nonbinding=0<qlo<=qhi<min(limits),
        source_feasible=P*A/max(lf,b+E0/p[0]) <= min(dec(s[3])*p[12] for s in c['schedule']),
        electrical_endpoints=abs(qlo*(max(lf,b+E/p[0]))/(A+max(lf,b+E/p[0]))-P)<eps and
            abs(qhi*max(lf,b+E0/p[0])/(A+max(lf,b+E0/p[0]))-P)<eps,
        source_work_balance=abs(v['hp_heat']-v['recovered_source']-v['compressor_work'])<eps,
        electrical_energy=abs(v['compressor_work']-P*v['duration'])<eps,
        inventory_balance=abs(E-E0-v['hp_heat']+v['charge_loss'])<eps if c['family']=='charge' else E==E0,
        service_definition=v['delivered_service']==(v['hp_heat'] if c['family']=='service' else 0),
        inverse_residual=abs(v['inversion_residual'])<eps)

def rk4(c,n):
    p=list(map(float,c['p']));P=float(c['ceiling_MW']);E=float(c['initial'][0]);t=sum(s[0] for s in c['schedule'])
    Te=p[11]-p[12]-p[13];A=p[14]*(Te+273.15);lf=p[18]+p[19]+p[17]-Te;b=p[1]+p[16]+p[17]-Te
    switch=p[0]*(p[18]+p[19]-p[1]-p[16]);floor_time=0.
    if E<switch:
        floor_time=min(t,(switch-E)/(p[6]*P*(1+A/lf)));E+=floor_time*p[6]*P*(1+A/lf)
    h=(t-floor_time)/n
    def rate(e):return p[6]*P*(1+A/max(lf,b+e/p[0]))
    for _ in range(n):
        k1=rate(E);k2=rate(E+h*k1/2);k3=rate(E+h*k2/2);k4=rate(E+h*k3)
        E+=h*(k1+2*k2+2*k3+k4)/6
    return E

def verify(folder):
    report=json.loads((folder/'report.json').read_text());spec=json.loads((folder/'spec.json').read_text());checks=[];comparisons=[];numeric=[]
    def check(kind,name,ok):checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    check('MAT','reopened_equal',report==json.loads((folder/'mat_reopen.json').read_text()))
    check('MAT','original_present',(folder/'electrical_conservatism_v84.mat').stat().st_size>1000)
    for e in json.loads((folder/'binary_manifest.json').read_text()):
        values=[x[0] for x in struct.iter_unpack('<d',(folder/e['file']).read_bytes())];m,n=e['rows'],e['columns']
        matrix=[values[k:k+n] for k in range(0,len(values),n)] if n else []
        value=matrix[0] if m==1 else matrix;r=report['runs'][e['index']-1]
        check('binary',e['file'],len(values)==m*n and value==r[e['field']]);r[e['field']]=value
    by={c['id']:c for c in spec['cases']};totals={}
    with localcontext() as ctx:
        ctx.prec=160
        for r in report['runs']:
            id=r['id'];c=by[id]
            for a in electrical_checks(r)+temporal_checks(r)+energy_checks(r)+hp_checks(r)+loss_checks(r):check('binary_equations',a['name'],a['passed'])
            mapped=copy.deepcopy(r)
            for row in rows(mapped['trace']):row[1]=73;row[72:75]=[0,0,0]
            cs,ns=analyze(mapped);numeric+=ns
            for a in cs:check('closed_equations',a['name'],a['passed'])
            with localcontext() as less:
                less.prec=120;cs120,_=analyze(mapped)
            check('precision',id+'_actual',[a['passed'] for a in cs]==[a['passed'] for a in cs120])
            total=total_earliest(mapped,ns);totals[id]=total
            for name,ok in review_report(r,total).items():check('report',id+'_'+name,ok)
            check('provenance',id,r['raw_policy']==c['p']+[c['ceiling_MW']] and rows(r['adapter']['schedule'])==c['schedule'] and r['adapter']['initial']==c['initial'])
            check('MAT',id,(folder/(id+'.mat')).stat().st_size>1000)
            if c['compare80']:check('reference',id,rows(r['trace'])==rows(r['reference_trace']))
            if c['family'] not in ['service','charge']:continue
            v=conditioned(c)
            for name,ok in dynamic_checks(c,v).items():check('conditioned_equations',id+'_'+name,ok)
            with localcontext() as less:
                less.prec=120;low=conditioned(c)
                for name,ok in dynamic_checks(c,low).items():check('conditioned_120',id+'_'+name,ok)
            check('precision',id+'_conditioned',all(abs(v[k]-low[k])<D('1e-100')*max(D(1),abs(v[k])) for k in v))
            check('scope',id+'_actual_no_interior_event',sum(row[13] for row in rows(r['trace']))==0)
            check('scope',id+'_all_HP_on',all(row[6]==1 for row in rows(r['trace'])))
            check('comparison',id+'_more_heat',v['hp_heat']>total['hp_heat'])
            check('comparison',id+'_more_source',v['recovered_source']>total['recovered_source'])
            check('comparison',id+'_more_work',v['compressor_work']>total['compressor_work'])
            # Require actual reported upper hull below the reconstructed comparator.
            check('comparison',id+'_disjoint_heat',v['hp_heat']>dec(r['summary']['hp_heat_MWh_hull'][1]))
            check('comparison',id+'_disjoint_source',v['recovered_source']>dec(r['summary']['recovered_source_MWh_hull'][1]))
            if c['family']=='charge':
                coarse=abs(D(str(rk4(c,1024)))-v['final_inventory']);fine=abs(D(str(rk4(c,2048)))-v['final_inventory'])
                check('RK4',id+'_endpoint',max(coarse,fine)<D('1e-10'))
                check('RK4',id+'_refinement',fine<=coarse+D('1e-12'))
            else:coarse=fine=D(0)
            comparisons.append(dict(id=id,family=c['family'],initial_inventory=str(dec(c['initial'][0])),approach=c['p'][13],
                actual_global={k:str(total[k]) for k in ['hp_heat','recovered_source','compressor_work','delivered_service','final_inventory']},
                hypothetical_conditioned={k:str(v[k]) for k in v},
                foregone={k:str(v[k]-total[k]) for k in ['hp_heat','recovered_source','delivered_service','final_inventory']},
                heat_increase_percent=str(100*(v['hp_heat']/total['hp_heat']-1)),
                RK4_error_1024_MWh=str(coarse),RK4_error_2048_MWh=str(fine)))
        victim=copy.deepcopy(next(c for c in spec['cases'] if c['family']=='charge'))
        good=conditioned(victim);mutations=[]
        for name,field in [('excess_compressor','compressor_work'),('missing_charge_loss','charge_loss'),('wrong_inventory','final_inventory')]:
            bad=good.copy();bad[field]+=D('.001')
            mutations.append(dict(name=name,passed=any(not x for x in dynamic_checks(victim,bad).values())))
    check('Stateflow','six_actual_modes',report['mode_coverage']==list(range(6)))
    check('Stateflow','actual_API',report['metadata']['license_observed']==1 and report['metadata']['chart_count']==1 and report['metadata']['simulation_mode']=='normal')
    check('scope','nineteen_schedules',len(report['runs'])==19)
    check('scope','twelve_comparisons',len(comparisons)==12)
    check('scope','actual_interior_events',sum(row[13] for r in report['runs'] for row in rows(r['trace']))>0)
    for manifest in ['preservation.json','source_hashes.json']:
        for e in json.loads((folder/manifest).read_text()):check('preservation',e['path'],sha(ROOT/e['path'])==e['sha256'] and (manifest!='source_hashes.json' or sha(folder/'source_snapshot'/e['path'])==e['sha256']))
    for e in json.loads((folder/'ledger_prefixes.json').read_text()):check('preservation',e['path'],hashlib.sha256((ROOT/e['path']).read_bytes()[:e['size']]).hexdigest()==e['sha256'])
    check('execution','successful_batch',any(json.loads(p.read_text(encoding='utf-8-sig'))['exit_code']==0 for p in folder.glob('execution_*.json')))
    check('MATLAB','assertions',report['summary']['failed']==0 and all(c['passed'] for c in report['assertions']))
    with zipfile.ZipFile(ROOT/MODEL) as archive:
        charts=[n for n in archive.namelist() if n.startswith('simulink/stateflow/chart_') and n.endswith('.xml')]
        check('SLX','one_chart',len(charts)==1)
        xml=ET.fromstring(archive.read(charts[0]));scripts=[p.text or '' for p in xml.iter('P') if p.attrib.get('Name')=='script']
        for path in ['electrical_policy_v83r2.m','earliest_dispatch_kernel_v75.m','monitor_standing_loss_v80.m']:
            check('SLX','embedded_'+path,(ROOT/'matlab/simulink'/path).read_text() in scripts)
    result=dict(version='0.84',timestamp_utc=datetime.now(timezone.utc).isoformat(),checks=checks,
        summary=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks)),
        reviewer_selfchecks=mutations,model_sha256=sha(ROOT/MODEL),comparisons=comparisons,
        reconstructed_totals={k:{key:str(v) for key,v in t.items()} for k,t in totals.items()})
    dump(folder/('independent_QA_v84_'+stamp()+'.json'),result)
    with (folder/('closed_numeric_v84_'+stamp()+'.csv')).open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(numeric[0]));w.writeheader();w.writerows(numeric)
    with (folder/('comparison_numeric_v84_'+stamp()+'.csv')).open('x',encoding='utf-8',newline='') as f:
        data=[dict(id=c['id'],family=c['family'],heat_increase_percent=c['heat_increase_percent'],**{'foregone_'+k:v for k,v in c['foregone'].items()}) for c in comparisons]
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    print(json.dumps(result['summary']))
    for c in checks:
        if not c['passed']:print(c)
    if result['summary']['failed'] or not all(c['passed'] for c in mutations):raise SystemExit(1)

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='verify':verify((ROOT/sys.argv[2]).resolve())
    else:raise SystemExit('prepare | verify results/folder')
