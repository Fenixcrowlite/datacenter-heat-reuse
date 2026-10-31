"""Fresh saved-Stateflow boundary experiment; independent Fraction/closed QA."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal as D, localcontext
from fractions import Fraction as F
import copy, csv, hashlib, itertools, json, shutil, struct, sys
from earliest_closed_form_v73 import analyze, dec, rows, contains
from verify_held_schedule_v74 import total_earliest, review_report
from temporal_reporting_v76 import temporal_checks
from energy_checks_v78 import energy_checks
from hp_partition_checks_v79 import hp_checks
from standing_loss_checks_v80 import loss_checks

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v80.slx'
LEDGERS = ['automation/engineering_progress.md', 'automation/STATEFLOW_ACCEPTANCE.md',
           'audit/research_frontier_2026_10_08.md']
def stamp(): return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):
    with p.open('x',encoding='utf-8') as out: json.dump(v,out,indent=2); out.write('\n')

def prepare():
    previous = ROOT/'results/standing_loss_v80_20261013T054910_671296Z/spec.json'
    cases0=json.loads(previous.read_text())['cases'];by={c['id']:c for c in cases0}
    cases=[]
    for name in ['zero_demand','HP_only','TES_charge','TES_discharge','boiler_limit','insufficient_heat']:
        c=copy.deepcopy(by[name]);c.update(family='acceptance',factor=1);cases.append(c)
    for boundary,T,e,h in itertools.product(['fixed_output','source_limited'],[30,40],[1,5,10],[1,5,10]):
        p=by['HP_only']['p'].copy();p[11]=T;p[13]=e;p[17]=h;p[23]=0
        demand,source=(.5,20) if boundary=='fixed_output' else (2,.02)
        cases.append(dict(id=f'{boundary}_T{T}_e{e}_h{h}',family=boundary,factor=1,p=p,
            source_C=T,evaporator_K=e,condenser_K=h,initial=[3,1,1],
            schedule=[[.25,.25,demand,source,1,0],[.25,.5,demand,source,1,0]]))
    folder=ROOT/'results'/('hp_approach_v82_'+stamp());folder.mkdir()
    dump(folder/'spec.json',dict(version='0.82',model_version='0.80',cases=cases,
        evidence_class='SYNTHETIC_BOUNDARY_SENSITIVITY_NOT_CALIBRATION'))
    preserved=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))
    preserved+=list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    preserved += [ROOT/'sources/papers/20_Verzino_Varna_2026.pdf']
    dump(folder/'preservation.json',[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in preserved])
    dump(folder/'ledger_prefixes.json',[dict(path=p,size=(ROOT/p).stat().st_size,sha256=sha(ROOT/p)) for p in LEDGERS])
    sources=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'audit').glob('*.py'))
    sources += [ROOT/'audit/run_hp_approach_sensitivity_v82.ps1', ROOT/'audit/HP_approach_derivation_v82.md']
    records=[]
    for p in sources:
        rel=p.relative_to(ROOT);dst=folder/'source_snapshot'/rel;dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,dst);records.append(dict(path=rel.as_posix(),sha256=sha(p)))
    dump(folder/'source_hashes.json',records)
    dump(folder/'primary_observations.json',dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),
        local_primary=dict(file='sources/papers/20_Verzino_Varna_2026.pdf',sha256=sha(ROOT/'sources/papers/20_Verzino_Varna_2026.pdf'),
            visual_pages=[8,27],equations_verified=[4,5,6,7],full_signoff=False),
        routes=[dict(url='https://flore.unifi.it/handle/2158/1432822',classification='METADATA_ABSTRACT_ONLY',observation='No attached files stated'),
            dict(url='https://www.dief.unifi.it/vp-278-research.html',classification='RESEARCH_GROUP_BIBLIOGRAPHY_ONLY',observation='New route links DOI, not supplement'),
            dict(url='https://www.sciencedirect.com/science/article/pii/S2451904925003038',classification='DIRECT_OPEN_FAILURE',observation='Web tool returned 403; indexed abstract is not full text'),
            dict(url='https://www.sciencedirect.com/science/article/pii/S2451904925003038/pdfft',classification='TOOL_CACHE_MISS',observation='Not an observed publisher HTTP denial')],
        upstream_supplement_acquired=False,equipment_calibrated=False))
    print(folder.relative_to(ROOT).as_posix())

def axes(r):
    p=list(map(F,r['p']));Te=p[11]-p[12]-p[13]+F(273.15)
    H=p[18]+p[19]+p[17]+F(273.15);L=H-Te;a=p[14]*Te
    return p,Te,H,L,a

def verify(folder):
    report=json.loads((folder/'report.json').read_text());checks=[];numeric=[];comparisons=[];selfchecks=[]
    def check(kind,name,ok):checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    check('MAT','reopened_report_equal',report==json.loads((folder/'mat_reopen.json').read_text()))
    check('MAT','original_present',(folder/'hp_approach_sensitivity_v82.mat').stat().st_size>1000)
    for e in json.loads((folder/'binary_manifest.json').read_text()):
        values=[v[0] for v in struct.iter_unpack('<d',(folder/e['file']).read_bytes())]
        m,n=e['rows'],e['columns'];matrix=[values[k:k+n] for k in range(0,len(values),n)]
        value=matrix[0] if m==1 else matrix;r=report['runs'][e['index']-1]
        check('binary',e['file'],len(values)==m*n and value==r[e['field']]);r[e['field']]=value
    totals={};runs={r['id']:r for r in report['runs']};spec=json.loads((folder/'spec.json').read_text())
    with localcontext() as ctx:
        ctx.prec=160
        for r in report['runs']:
            for c in temporal_checks(r)+energy_checks(r)+hp_checks(r)+loss_checks(r):check('binary_equations',c['name'],c['passed'])
            mapped=copy.deepcopy(r)
            for row in rows(mapped['trace']):row[1]=73;row[72:75]=[0,0,0]
            cs,ns=analyze(mapped);numeric+=ns
            for c in cs:check('closed_equations',c['name'],c['passed'])
            with localcontext() as low:
                low.prec=120;cs120,_=analyze(mapped)
            check('precision',r['id'],[c['passed'] for c in cs]==[c['passed'] for c in cs120])
            totals[r['id']]=total_earliest(mapped,ns)
            for name,ok in review_report(r,totals[r['id']]).items():check('report',r['id']+'_'+name,ok)
            check('MAT',r['id'],(folder/(r['id']+'.mat')).stat().st_size>1000)
            c=next(v for v in spec['cases'] if v['id']==r['id'])
            check('provenance',r['id'],r['p']==c['p'] and rows(r['adapter']['schedule'])==c['schedule'] and r['adapter']['initial']==c['initial'])
            p,Te,H,L,a=axes(r);cap=p[0]*(p[2]-p[1])
            for k,row in enumerate(rows(r['trace'])):
                check('capacity',r['id']+f'_{k}',0<=F(row[4])<=F(row[5])<cap)
            if r['family']=='acceptance':continue
            check('boundary',r['id']+'_positive_kelvin',Te>0 and L>0 and 0<p[14]<=1)
            # Independent algebra with exact binary operands and no quadrature.
            direct=F(0);work=F(0);source=F(0)
            for tick,(u,row) in enumerate(zip(rows(r['input']),rows(r['trace']))):
                check('boundary',r['id']+f'_{tick}_two_single_segments',row[12]==1 and row[13]==0)
                z=list(map(F,row[100:180]));dt=F(u[4]);q=z[23]
                check('boundary',r['id']+f'_{tick}_constant_floor',p[1]+max(z[10:14])/p[0]+p[16]<p[18]+p[19])
                check('boundary',r['id']+f'_{tick}_no_TES_service',z[25]==0 and z[26]==0 and z[27]==0)
                direct+=q*dt;source+=q*a/(a+L)*dt;work+=q*L/(a+L)*dt
            s=r['summary'];q_source=F(rows(r['input'])[0][6])*p[12]*(1+L/a)
            for key,value in [('hp_heat',direct),('compressor_work',work),('recovered_source',source)]:
                check('algebra',r['id']+'_'+key,contains(s[key+'_MWh_hull'],dec(value)))
            check('algebra',r['id']+'_COP',contains(s['delivered_HP_heating_COP_hull'],dec(1+a/L)))
            check('algebra',r['id']+'_cycle_first_law',direct==source+work)
            check('algebra',r['id']+'_heating_factor_conversion',(L+p[14]*Te)/H==p[14]+(1-p[14])*L/H)
            # Both derivative numerators are positive for the declared domain.
            check('derivatives',r['id'],p[14]*H/L**2>0 and a/L**2>0 and H/(p[14]*Te**2)>0 and 1/a>0)
            if r['family']=='source_limited':
                S=F(rows(r['input'])[0][6])*p[12];duration=sum((F(u[4]) for u in rows(r['input'])),F(0))
                check('boundary',r['id']+'_source_binding',q_source<min(p[10],p[15]*p[16],F(2)))
                check('boundary',r['id']+'_source_budget',0<=source<=S*duration and S*duration-source<F(1,10**12))
            else:check('boundary',r['id']+'_fixed_output',direct==F(1,4))
        for family,T,axis,other in itertools.product(['fixed_output','source_limited'],[30,40],['e','h'],[1,5,10]):
            for left,right in [(1,5),(5,10)]:
                def name(v):return f'{family}_T{T}_e{v if axis=="e" else other}_h{v if axis=="h" else other}'
                lo,hi=runs[name(left)],runs[name(right)];ls,hs=lo['summary'],hi['summary']
                work_order=hs['compressor_work_MWh_hull'][0]>ls['compressor_work_MWh_hull'][1]
                lp,lTe,lH,lL,la=axes(lo);hp,hTe,hH,hL,ha=axes(hi)
                cop_order=1+ha/hL<1+la/lL
                if family=='fixed_output':
                    service=totals[lo['id']]['delivered_service']==totals[hi['id']]['delivered_service']==D('.25')
                    source_order=hs['recovered_source_MWh_hull'][1]<ls['recovered_source_MWh_hull'][0]
                else:
                    service=hs['delivered_service_MWh_hull'][0]>ls['delivered_service_MWh_hull'][1]
                    source_order=hs['unmet_demand_MWh_hull'][1]<ls['unmet_demand_MWh_hull'][0]
                ok=work_order and cop_order and service and source_order
                comparisons.append(dict(family=family,axis=axis,low=lo['id'],high=hi['id'],passed=ok))
                check('monotonicity',lo['id']+'__'+hi['id'],ok)
        victim=copy.deepcopy(next(r for r in report['runs'] if r['family']=='fixed_output'))
        victim['trace']=rows(victim['trace']);victim['trace'][0][4:6]=[-1,-1]
        for row in victim['trace']:row[1]=73;row[72:75]=[0,0,0]
        cs,_=analyze(victim);selfchecks.append(dict(name='wrong_endpoint_detected',passed=any(not c['passed'] for c in cs)))
        victim=next(r for r in report['runs'] if r['family']=='fixed_output');_,Te,H,L,a=axes(victim)
        selfchecks.append(dict(name='cooling_factor_as_heating_factor_rejected',passed=1+a/L!=F(victim['p'][14])*H/L))
        selfchecks.append(dict(name='Celsius_Carnot_numerator_rejected',passed=1+a/L!=1+F(victim['p'][14])*(Te-F(273.15))/L))
        damaged=copy.deepcopy(victim);damaged['trace']=rows(damaged['trace'])
        damaged['trace'][0][135:137]=[1.,1.]
        selfchecks.append(dict(name='corrupt_compressor_port_detected',passed=any(not c['passed'] for c in hp_checks(damaged))))
    check('Stateflow','six_actual_modes',report['mode_coverage']==list(range(6)))
    check('Stateflow','actual_API',report['metadata']['license_observed']==1 and report['metadata']['chart_count']==1 and report['metadata']['simulation_mode']=='normal')
    check('scope','42_schedules',len(report['runs'])==42 and len(comparisons)==48)
    for manifest in ['preservation.json','source_hashes.json']:
        for e in json.loads((folder/manifest).read_text()):
            ok=sha(ROOT/e['path'])==e['sha256']
            if manifest=='source_hashes.json':
                # Preserve original execution/reviewer snapshot and explicitly seal
                # the one post-execution reviewer shape repair; no model rerun needed.
                revision_path=folder/'reviewer_revision.json'
                if not ok and revision_path.exists():
                    rev=json.loads(revision_path.read_text())
                    ok=(e['path']==rev['source_path'] and e['sha256']==rev['previous_sha256']
                        and sha(ROOT/e['path'])==rev['current_sha256']
                        and sha(folder/rev['current_snapshot'])==rev['current_sha256'])
                ok=ok and sha(folder/'source_snapshot'/e['path'])==e['sha256']
            check('preservation',e['path'],ok)
    for e in json.loads((folder/'ledger_prefixes.json').read_text()):
        check('preservation',e['path'],hashlib.sha256((ROOT/e['path']).read_bytes()[:e['size']]).hexdigest()==e['sha256'])
    receipts=list(folder.glob('execution_*.json'))
    check('execution','successful_batch',any(json.loads(p.read_text(encoding='utf-8-sig'))['exit_code']==0 for p in receipts))
    check('MATLAB','all_assertions',report['summary']['failed']==0 and all(c['passed'] for c in report['assertions']))
    result=dict(version='0.82',timestamp_utc=datetime.now(timezone.utc).isoformat(),checks=checks,
        summary=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks)),
        comparisons=comparisons,reviewer_selfchecks=selfchecks,
        reconstructed_totals={k:{name:str(value) for name,value in t.items()} for k,t in totals.items()})
    dump(folder/('independent_QA_v82_'+stamp()+'.json'),result)
    with (folder/('closed_numeric_v82_'+stamp()+'.csv')).open('x',newline='',encoding='utf-8') as out:
        writer=csv.DictWriter(out,fieldnames=list(numeric[0]));writer.writeheader();writer.writerows(numeric)
    print(json.dumps(result['summary']));print('COMPARISONS='+str(len(comparisons)))
    if result['summary']['failed'] or not all(c['passed'] for c in selfchecks):raise SystemExit(1)

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='verify':verify((ROOT/sys.argv[2]).resolve())
    else:raise SystemExit('prepare | verify results/folder')
