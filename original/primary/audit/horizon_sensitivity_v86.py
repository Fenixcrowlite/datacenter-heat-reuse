"""Predeclare saved-v85 horizon experiments and independently review original MAT."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal as D, localcontext
from fractions import Fraction as F
import copy, csv, hashlib, json, shutil, struct, sys, zipfile
import xml.etree.ElementTree as ET
from earliest_closed_form_v73 import analyze, rows, dec
from verify_held_schedule_v74 import total_earliest, review_report
from reachable_cap_v85 import electrical_checks
from temporal_reporting_v76 import temporal_checks
from energy_checks_v78 import energy_checks
from hp_partition_checks_v79 import hp_checks
from standing_loss_checks_v80 import loss_checks
from electrical_conservatism_v84 import conditioned, dynamic_checks, rk4

ROOT=Path(__file__).resolve().parents[1]
MODEL='matlab/simulink/DCHR_Electrical_Dispatch_Stateflow_v85.slx'
LEDGERS=['automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md','audit/research_frontier_2026_10_08.md']
def stamp():return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2);f.write('\n')

def prepare():
    old=json.loads((ROOT/'results/reachable_cap_v85_20261013T111338_510493Z/spec.json').read_text())
    cases=[copy.deepcopy(c) for c in old['cases'] if c['family'] not in ['service','charge']]
    histories=[c for c in old['cases'] if c['family'] in ['service','charge']]
    for base in histories:
        partitions=[.125,.25,.5] if base['id'] in ['service_E3.0_a1.0','charge_E4.95_a1.0'] else [.25]
        for H in [1,2,4]:
            for dt in partitions:
                c=copy.deepcopy(base);c['history_id']=base['id'];c['nominal_horizon_h']=H
                c['horizon_h']=1+2**-40 if H==1 else H;c['partition_h']=dt
                c['id']=f"{base['id']}_H{H}_dt{dt}"
                s=base['schedule'][0];c['schedule']=[[dt,(j+1)*dt,*s[2:]] for j in range(round(1/dt))]
                cases.append(c)
    folder=ROOT/'results'/('horizon_sensitivity_v86_'+stamp());folder.mkdir()
    dump(folder/'spec.json',dict(version='0.86',saved_model_version='0.85',cases=cases,
        nominal_horizons_h=[1,2,4],H1_certificate_margin_h=2**-40,
        comparison_scope='HYPOTHETICAL_ZERO_LOSS_NONLINEAR_COMPARATOR_NOT_RENEWAL_IMPLEMENTATION',
        precision_digits=[120,160],precision_budget='1e-100',partition_budget='1e-90',
        RK4_budget_MWh='1e-10',RK4_steps=[1024,2048]))
    preserved=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    dump(folder/'preservation.json',[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in preserved])
    dump(folder/'ledger_prefixes.json',[dict(path=p,size=(ROOT/p).stat().st_size,sha256=sha(ROOT/p)) for p in LEDGERS])
    sources=list((ROOT/'audit').glob('*.py'))+list((ROOT/'matlab/simulink').glob('*.m'))
    sources += [ROOT/'matlab/run_horizon_sensitivity_v86.m', ROOT/'matlab/+dchr/adapt_held_schedule_v74.m',
        ROOT/'matlab/+dchr/report_held_schedule_v76.m',ROOT/'audit/run_horizon_sensitivity_v86.ps1',ROOT/'audit/Horizon_renewal_derivation_v86.md']
    records=[]
    for p in sources:
        rel=p.relative_to(ROOT);dst=folder/'source_snapshot'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
        records.append(dict(path=rel.as_posix(),sha256=sha(p)))
    dump(folder/'source_hashes.json',records);print(folder.relative_to(ROOT).as_posix())

def verify(folder):
    report=json.loads((folder/'report.json').read_text());spec=json.loads((folder/'spec.json').read_text())
    checks=[];numeric=[];totals={};comparisons=[];partition_results=[];groups={}
    def check(kind,name,ok):checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    check('MAT','reopened_equal',report==json.loads((folder/'mat_reopen.json').read_text()))
    check('MAT','aggregate_present',(folder/'horizon_sensitivity_v86.mat').stat().st_size>1000)
    for e in json.loads((folder/'binary_manifest.json').read_text()):
        values=[v[0] for v in struct.iter_unpack('<d',(folder/e['file']).read_bytes())];m,n=e['rows'],e['columns']
        matrix=[values[k:k+n] for k in range(0,len(values),n)] if n else []
        value=matrix[0] if m==1 else matrix;r=report['runs'][e['index']-1]
        check('binary',e['file'],len(values)==m*n and value==r[e['field']]);r[e['field']]=value
    by={c['id']:c for c in spec['cases']}
    def closed(r):
        mapped=copy.deepcopy(r)
        for row in rows(mapped['trace']):row[1]=73;row[72:75]=[0,0,0]
        cs,ns=analyze(mapped)
        for a in cs:check('closed_equations',a['name'],a['passed'])
        with localcontext() as lo:
            lo.prec=120;low,_=analyze(mapped)
        check('precision',r['id'],[a['passed'] for a in cs]==[a['passed'] for a in low])
        return total_earliest(mapped,ns),ns
    with localcontext() as ctx:
        ctx.prec=160
        for r in report['runs']:
            id=r['id'];c=by[id]
            for a in electrical_checks(r)+temporal_checks(r)+energy_checks(r)+hp_checks(r)+loss_checks(r):check('binary_equations',a['name'],a['passed'])
            t,ns=closed(r);totals[id]=t;numeric+=ns
            for name,ok in review_report(r,t).items():check('report',id+'_'+name,ok)
            check('provenance',id,r['raw_policy']==c['p']+[c['ceiling_MW'],c['horizon_h']] and rows(r['adapter']['schedule'])==c['schedule'] and r['adapter']['initial']==c['initial'])
            check('MAT',id,(folder/(id+'.mat')).stat().st_size>1000)
            if c['compare80']:check('reference',id,rows(r['trace'])==rows(r['reference_trace']) and r['p']==c['p'])
            g=copy.deepcopy(r);g['id']=id+'_global';g['trace']=rows(g['global_trace']);g['p']=g['trace'][0][75:100]
            gt,_=closed(g)
            check('cap',id+'_ge_global',r['p'][10]>=g['p'][10])
            if 'history_id' not in c:continue
            groups.setdefault(c['history_id'],[]).append((c,r,t))
            v=conditioned(c)
            for name,ok in dynamic_checks(c,v).items():check('dynamic',id+'_'+name,ok)
            with localcontext() as lo:
                lo.prec=120;low=conditioned(c)
            check('precision',id+'_dynamic',all(abs(v[k]-low[k])<D('1e-100')*max(D(1),abs(v[k])) for k in v))
            check('scope',id+'_no_interior_switch',sum(row[13] for row in rows(r['trace']))==0)
            check('scope',id+'_all_HP_on',all(row[6]==1 for row in rows(r['trace'])))
            check('comparison',id+'_heat_below_dynamic',t['hp_heat']<=v['hp_heat']+D('1e-100'))
            check('comparison',id+'_heat_ge_global',t['hp_heat']>=gt['hp_heat'])
            if c['family']=='charge':
                err=[abs(D(str(rk4(c,n)))-v['final_inventory']) for n in [1024,2048]]
                check('RK4',id+'_endpoint',max(err)<D('1e-10'))
                check('RK4',id+'_refinement',err[1]<=err[0]+D('1e-12'))
            else:err=[D(0),D(0)]
            keys=['hp_heat','recovered_source','compressor_work','delivered_service','final_inventory']
            comparisons.append(dict(id=id,history_id=c['history_id'],nominal_horizon_h=c['nominal_horizon_h'],
                actual_horizon_h=c['horizon_h'],partition_h=c['partition_h'],cap_MW=r['p'][10],
                actual={k:str(t[k]) for k in keys},global_cap={k:str(gt[k]) for k in keys},
                hypothetical_dynamic={k:str(v[k]) for k in v},
                dynamic_heat_gap_MWh=str(v['hp_heat']-t['hp_heat']),RK4_errors_MWh=list(map(str,err))))
        for history,entries in groups.items():
            standard=sorted((e for e in entries if e[0]['partition_h']==.25),key=lambda e:e[0]['nominal_horizon_h'])
            check('horizon',history+'_complete_H124',[e[0]['nominal_horizon_h'] for e in standard]==[1,2,4])
            for a,b in zip(standard,standard[1:]):
                check('horizon',history+f"_H{a[0]['nominal_horizon_h']}_to_{b[0]['nominal_horizon_h']}",
                    a[1]['p'][10]>=b[1]['p'][10] and a[2]['hp_heat']>=b[2]['hp_heat'])
            for c,r,t in entries:
                if c['partition_h']==.25:continue
                base=next(e for e in standard if e[0]['nominal_horizon_h']==c['nominal_horizon_h'])
                delta=max(abs(t[k]-base[2][k]) for k in t)
                check('partition',r['id']+'_same_cap',r['p'][10]==base[1]['p'][10])
                check('partition',r['id']+'_closed_trajectory',delta<D('1e-90'))
                hullkeys=['hp_heat','recovered_source','compressor_work','delivered_service','final_inventory']
                for key in hullkeys:
                    field='final_inventory_hull' if key=='final_inventory' else key+'_MWh_hull'
                    x=r['summary'][field];y=base[1]['summary'][field]
                    check('partition',r['id']+'_'+key+'_hull_overlap',max(x[0],y[0])<=min(x[1],y[1]))
                partition_results.append(dict(id=r['id'],baseline=base[1]['id'],max_closed_difference=str(delta)))
        # Strict independent witness: start-temperature cap exceeds rating after charging.
        c=next(c for c in spec['cases'] if c['id']=='charge_E4.95_a1.0_H1_dt0.25')
        p=list(map(F,c['p']));Te=p[11]-p[12]-p[13];A=p[14]*(Te+F(273.15));Lf=p[18]+p[19]+p[17]-Te
        def lift(E):return max(Lf,p[1]+E/p[0]+p[16]+p[17]-Te)
        P=F(c['ceiling_MW']);E0=F(c['initial'][0]);q=P*(1+A/lift(E0));E1=E0+p[6]*q
        W1=q*lift(E1)/(A+lift(E1))
        check('contract','uncertified_start_cap_unsafe',W1>P)
        witness=dict(evidence_class='SYNTHETIC_EXACT_RATIONAL_COUNTEREXAMPLE_NOT_MODEL_EXECUTION',
            initial_inventory=str(E0),end_inventory=str(E1),start_heat_rate=str(q),rating=str(P),end_work_rate=str(W1),
            excess_MW=str(dec(W1-P)))
    probe=json.loads((folder/'exact_horizon_probe.json').read_text())
    check('endpoint','actual_probe_retained',(folder/'exact_horizon_probe.mat').stat().st_size>1000)
    check('endpoint','exact_one_hour_inputs',sum((F(s[0]) for s in rows(probe['adapter']['schedule'])),F(0))==1 and probe['raw_policy'][26]==1)
    check('endpoint','classified',probe['accepted'] or 'v85 declared horizon exceeded' in probe['message'])
    selfchecks=[]
    for name in ['cap','heat','certificate']:
        victim=copy.deepcopy(next(r for r in report['runs'] if r['raw_policy'][25]==.05))
        if name=='cap':victim['p'][10]=1
        elif name=='heat':victim['trace']=rows(victim['trace']);victim['trace'][0][123]=1
        else:victim['certificate']=rows(victim['certificate']);victim['certificate'][0][25]=0
        selfchecks.append(dict(name=name+'_mutation_detected',passed=any(not a['passed'] for a in electrical_checks(victim))))
    check('Stateflow','six_modes',report['mode_coverage']==list(range(6)))
    check('Stateflow','actual_API',report['metadata']['license_observed']==1 and report['metadata']['chart_count']==1 and report['metadata']['simulation_mode']=='normal')
    check('scope','all_predeclared',len(report['runs'])==len(spec['cases']))
    check('scope','48_comparisons',len(comparisons)==48 and len(groups)==12 and len(partition_results)==12)
    events={row[100+80*j+2] for r in report['runs'] for row in rows(r['trace']) for j in range(int(row[12]))}
    check('scope','stop_cutoff_restart',set([1,2,3])<=events)
    check('faults','seven_actual_refusals',len(report['faults'])==7 and all(f['rejected'] and f['expected_guard'] in (folder/('fault_'+f['id']+'.txt')).read_text() for f in report['faults']))
    for manifest in ['preservation.json','source_hashes.json']:
        for e in json.loads((folder/manifest).read_text()):
            check('preservation',e['path'],sha(ROOT/e['path'])==e['sha256'] and (manifest!='source_hashes.json' or sha(folder/'source_snapshot'/e['path'])==e['sha256']))
    for e in json.loads((folder/'ledger_prefixes.json').read_text()):check('preservation',e['path'],hashlib.sha256((ROOT/e['path']).read_bytes()[:e['size']]).hexdigest()==e['sha256'])
    check('execution','successful_batch',any(json.loads(p.read_text(encoding='utf-8-sig'))['exit_code']==0 for p in folder.glob('execution_*.json')))
    check('MATLAB','assertions',report['summary']['failed']==0 and all(a['passed'] for a in report['assertions']))
    with zipfile.ZipFile(ROOT/MODEL) as archive:
        charts=[n for n in archive.namelist() if n.startswith('simulink/stateflow/chart_') and n.endswith('.xml')]
        check('SLX','one_chart',len(charts)==1)
        xml=ET.fromstring(archive.read(charts[0]));scripts=[p.text or '' for p in xml.iter('P') if p.attrib.get('Name')=='script']
        for path in ['electrical_policy_v85.m','earliest_dispatch_kernel_v75.m','monitor_standing_loss_v80.m']:
            check('SLX','embedded_'+path,(ROOT/'matlab/simulink'/path).read_text() in scripts)
    result=dict(version='0.86',timestamp_utc=datetime.now(timezone.utc).isoformat(),checks=checks,
        summary=dict(passed=sum(a['passed'] for a in checks),failed=sum(not a['passed'] for a in checks)),
        reviewer_selfchecks=selfchecks,model_sha256=sha(ROOT/MODEL),comparisons=comparisons,partition_results=partition_results,
        uncertified_cap_witness=witness,exact_horizon_probe_accepted=probe['accepted'],
        reconstructed_totals={id:{k:str(v) for k,v in t.items()} for id,t in totals.items()})
    dump(folder/('independent_QA_v86_'+stamp()+'.json'),result)
    dump(folder/'comparisons_v86.json',comparisons)
    with (folder/('closed_numeric_v86_'+stamp()+'.csv')).open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(numeric[0]));w.writeheader();w.writerows(numeric)
    print(json.dumps(result['summary']))
    for a in checks:
        if not a['passed']:print(a)
    if result['summary']['failed'] or not all(a['passed'] for a in selfchecks):raise SystemExit(1)

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='verify':
        target=(ROOT/sys.argv[2]).resolve();assert target.is_relative_to(ROOT/'results');verify(target)
    else:raise SystemExit('prepare | verify results/folder')
