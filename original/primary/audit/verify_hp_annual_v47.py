"""Independent Decimal analytic-root and saved-trace QA; no production imports.
Same agent, separate algorithm. Not independent personnel or physical validation.
"""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal as D, localcontext
import collections, copy, csv, hashlib, json, math, shutil, sys, zipfile
ROOT = Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dec(x): return D(str(x))
def near(a,b):
    return math.isfinite(float(a)) and abs(dec(a)-dec(b)) <= D('3e-11')*max(D(1),abs(dec(b)))
def rows(p):
    with p.open(newline='') as f: return list(csv.DictReader(f))
def numeric(p):
    with p.open(newline='') as f: return [[float(x) for x in r] for r in csv.reader(f)]
def maximal(S,R,H,C0,r,Cmin):
    """Independent closed-form root, restricted to no lower-COP clipping."""
    with localcontext() as ctx:
        ctx.prec=60
        S,R,H,C0,r,Cmin=map(dec,[S,R,H,C0,r,Cmin]);a=C0*(1-r)
        assert H>0 and a>=Cmin>1 and S>=0 and R>=0
        if S==0 or R==0: return D(0)
        b=C0*r/H
        if b==0: root=S*a/(a-1)
        else:
            B=a-1-b*S; discriminant=(B*B+4*b*a*S).sqrt()
            root=2*a*S/(B+discriminant) if B>=0 else (-B+discriminant)/(2*b)
        return min(R,H,root)
def probe_valid(row):
    q=maximal(row['Source_MW'],row['Request_MW'],12,row['Nominal_COP'],row['Penalty'],2.2)
    return near(row['Verified_Heat_MW'],q) and dec(row['Verified_Source_MW'])<=dec(row['Source_MW'])+D('1e-11')
def endpoint(E,P,k,t):
    with localcontext() as ctx:
        ctx.prec=60;E,P,k,t=map(dec,[E,P,k,t])
        return E+P*t if k==0 else (E+P*((k*t).exp()-1)/k)/(k*t).exp()
def main():
    folder=(ROOT/Path(sys.argv[1])).resolve();assert folder.is_relative_to(ROOT/'results')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');checks=[];selfchecks=[]
    def check(kind,name,ok): checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    report=json.loads((folder/'hp_annual_v47.json').read_text());spec=json.loads((folder/'spec.json').read_text())
    cfg=report['cfg'];hp=cfg['hp'];storage=cfg['storage'];dt=cfg['sim']['dt_h'];H=hp['max_heat_output_MW'];r=hp['part_load_penalty']
    check('execution','harness_pass',report['summary']['harness_failed']==0 and all(x['passed'] for x in report['assertions']))
    check('scope','unchanged_model_synthetic',not report['summary']['new_model'] and spec['evidence_class']=='SYNTHETIC_ENGINEERING_NOT_MEASURED')
    check('execution','actual_license_and_normal_mode',report['metadata']['stateflow_license_test']==1 and report['metadata']['simulation_mode']=='normal')
    check('MAT','report_reopened',json.loads((folder/'mat_reopen/report.json').read_text())==report)
    for p in folder.glob('*.csv'): check('MAT',p.name,sha(p)==sha(folder/'mat_reopen'/p.name))
    annual=rows(folder/'annual_legacy.csv');caps=rows(folder/'annual_capability.csv');previous=D(str(storage['initial_soc']*storage['capacity_MWh']))
    check('annual','8760_rows',len(annual)==len(caps)==8760)
    violations=0;nonmaximal=0;static_gap=D(0);max_gap=D(0);max_source_excess=D(0);first_opportunity=None
    with localcontext() as ctx:
        ctx.prec=60
        for i,(a,b) in enumerate(zip(annual,caps)):
            q=dec(a['HP_Heat_Used_MW']);work=dec(a['HP_Electric_MW']);S=dec(a['HX_Heat_to_HP_MW']);src=dec(b['HP_Source_C']);sink=dec(a['DH_Supply_C'])
            nominal=min(dec(hp['cop_max']),max(dec(hp['cop_min']),dec(hp['carnot_efficiency'])*(sink+D('273.15'))/(sink-src)))
            expected_source=dec(a['IT_MW'])*dec(cfg['dc']['recovery_fraction'])*dec(cfg['hx']['effectiveness'])
            expected_source=min(expected_source,dec(cfg['hx']['max_heat_MW']))
            check('annual_equations',f'row_{i}_source_nominal',near(S,expected_source) and near(b['COP_Nominal'],nominal) and near(src,dec(cfg['dc']['source_temp_C'])-dec(cfg['hx']['approach_K'])))
            E=dec(a['Storage_E_MWh']);E0=E*(1-dec(storage['loss_fraction_per_h'])*dec(dt))
            room=(dec(storage['capacity_MWh'])-E0)/(dec(storage['eta_charge'])*dec(dt))
            demand=dec(a['Heat_Demand_MW']);req=demand+min(dec(storage['charge_limit_MW']),max(D(0),room))
            potential=min(dec(H),S*nominal/(nominal-1));expected_q=min(potential,req)
            operating=min(dec(hp['cop_max']),max(dec(hp['cop_min']),nominal*(1-dec(r)+dec(r)*q/dec(H))))
            evap=q-work
            check('annual_equations',f'row_{i}_legacy',near(q,expected_q) and near(a['HP_Heat_MW'],potential) and near(a['COP'],operating) and near(work,q/operating) and near(a['HP_Source_Used_MW'],evap))
            optimum=maximal(S,req,H,nominal,r,hp['cop_min']);gap=optimum-q
            check('annual_maximum',f'row_{i}_analytic',near(b['Request_MW'],req) and near(b['Verified_Max_Heat_MW'],optimum) and gap>=D('-1e-10'))
            max_source_excess=max(max_source_excess,evap-S)
            violations+=int(evap>S+D('1e-10'));nonmaximal+=int(gap>D('1e-8'))
            static_gap+=max(D(0),gap)*dec(dt);max_gap=max(max_gap,gap)
            charge=dec(a['Storage_Charge_MW']);discharge=dec(a['Storage_Discharge_MW']);gas=dec(a['Gas_Heat_MW']);unmet=dec(a['Unmet_Heat_MW'])
            check('annual_dispatch',f'row_{i}_continuity_service',near(E,previous) and near(demand,q-charge+discharge+gas+unmet) and charge*discharge==0 and gas<=dec(cfg['backup']['max_heat_MW'])+D('1e-11'))
            previous=E0+dec(storage['eta_charge'])*charge*dec(dt)-discharge*dec(dt)/dec(storage['eta_discharge'])
            if first_opportunity is None and gap>D('1e-5') and gas+unmet>0:
                first_opportunity=dict(interval=i+1,time=a['Time'],source_MW=float(S),legacy_output_MW=float(q),analytic_max_MW=float(optimum),extra_capability_MW=float(gap),legacy_gas_MW=float(gas),legacy_unmet_MW=float(unmet),source_unused_MW=float(S-evap))
    check('annual_summary','source_feasible',violations==report['summary']['source_feasibility_violations']==0)
    check('annual_summary','nonmaximal_count',nonmaximal==report['summary']['nonmaximal_intervals'] and nonmaximal>0)
    check('annual_summary','static_only_gap',near(report['summary']['static_extra_heat_MWh'],static_gap))
    probe_rows=rows(folder/'hp_probes.csv')
    check('probes','72_vectors',len(probe_rows)==72)
    for i,p in enumerate(probe_rows):
        check('probes',f'probe_{i}_maximal',probe_valid(p))
        C0=dec(p['Nominal_COP']);q=dec(p['Legacy_Heat_MW']);cop=C0*(1-dec(p['Penalty'])+dec(p['Penalty'])*q/dec(H))
        check('probes',f'probe_{i}_legacy',near(p['Legacy_COP'],cop) and near(p['Legacy_Source_MW'],q-q/cop) and dec(p['Legacy_Source_MW'])<=dec(p['Source_MW'])+D('1e-11'))
    all_modes=set();source_cases=[];max_balance=D(0)
    for item in report['stateflow']:
        c=item['case'];x=c['inputs'];x=x[0] if isinstance(x[0],list) else x;p=c['p'];h=c['h'];id=item['id']
        ds=numeric(folder/(id+'_dispatch.csv'));segments=numeric(folder/(id+'_segments.csv'));E=dec(c['initial_energy_MWh']);span_sum=D(0)
        check('stateflow',id+'_saved_execution',item['error_message']=='' and len(ds)==item['intervals']==1 and int(ds[0][0])==c['expected_mode'])
        for j,row in enumerate(segments):
            z=row[2:];mode,span,offset,start,end=z[:5];direct,qc,qd,gas,unmet,Q,W,source=z[5:13]
            all_modes.add(int(mode));P=dec(p[4])*dec(qc)-dec(qd)/dec(p[5]);wanted=endpoint(start,P,p[6],span)
            check('stateflow_ODE',id+f'_{j}',near(start,E) and near(end,wanted) and near(offset,span_sum));E=dec(end);span_sum+=dec(span)
            check('stateflow_equations',id+f'_{j}',near(Q,W+source) and near(Q,direct+qc) and near(x[3],direct+qd+gas+unmet) and source<=x[0]+1e-10)
            check('stateflow_bounds',id+f'_{j}',min(start,end)>=-1e-10 and max(start,end)<=p[1]+1e-10 and min(z[5:13])>=-1e-10 and qc*qd==0 and qc<=p[2]+1e-10 and qd<=p[3]+1e-10 and gas<=p[10]+1e-10)
            expected_mode=5 if unmet>0 else 4 if gas>0 else 3 if qd>0 else 2 if qc>0 else 1 if direct>0 else 0
            residual=dec(start)+(dec(source)+dec(W)+dec(gas)-dec(z[19]))*dec(span)-dec(end)-sum(map(dec,z[16:19]))
            max_balance=max(max_balance,abs(residual))
            check('stateflow_mode_balance',id+f'_{j}',int(mode)==expected_mode and abs(residual)<D('1e-10'))
            check('stateflow_losses',id+f'_{j}',near(z[16],dec(start)+P*dec(span)-dec(end)) and near(z[17],(1-dec(p[4]))*dec(qc)*dec(span)) and near(z[18],(1/dec(p[5])-1)*dec(qd)*dec(span)))
        check('stateflow_partition',id,near(span_sum,p[0]))
        if id.startswith('source_limited'):
            nominal=min(dec(h[3]),dec(h[1])*(dec(x[2])+D('273.15'))/(dec(x[2])-dec(x[1])))
            optimum=maximal(x[0],x[3],h[0],nominal,h[4],h[2]);old=dec(x[0])*nominal/(nominal-1)
            check('saved_vs_analytic',id,near(ds[0][18],optimum) and optimum>old+D('1e-5'))
            source_cases.append(dict(id=id,source_MW=x[0],legacy_max_MW=float(old),saved_v42_MW=ds[0][18],analytic_max_MW=float(optimum),difference_MW=float(optimum-old)))
    check('stateflow_modes','all_six_actual',all_modes==set(range(6)))
    check('stateflow_modes','two_source_comparisons',len(source_cases)==2)
    preservation=json.loads((folder/'preservation.json').read_text())
    for a in preservation:
        path=ROOT/a['path'];check('preservation',a['path'],path.stat().st_size==a['bytes'] and sha(path)==a['sha256'])
    for path in (folder/'source_snapshot').rglob('*'):
        if path.is_file(): check('snapshot',path.relative_to(folder).as_posix(),sha(path)==sha(ROOT/path.relative_to(folder/'source_snapshot')))
    model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx';accepted=json.loads((ROOT/'STATUS_stateflow_v42.json').read_text())
    check('archive','accepted_hash',sha(model)==accepted['model_sha256'])
    with zipfile.ZipFile(model) as z:
        check('archive','crc',z.testzip() is None)
        xml='\n'.join(z.read(n).decode('utf-8') for n in z.namelist() if n.endswith('.xml'))
        for name in ['IDLE','HEAT_RECOVERY','STORAGE_CHARGE','STORAGE_DISCHARGE','BACKUP','UNMET_DEMAND']:
            check('archive',name,name in xml)
    receipts=[]
    for path in sorted((ROOT/'audit').glob('HP_annual_execution_v47_*.json')):
        receipt=json.loads(path.read_text(encoding='utf-8-sig'))
        if folder.relative_to(ROOT).as_posix() in receipt['command'] and receipt['exit_code']==0:
            log=(ROOT/receipt['log_path']).read_text(encoding='utf-8-sig',errors='replace')
            check('execution',path.name,'HP_ANNUAL_V47' in log and 'MAT_REOPEN_V47 complete' in log)
            receipts.append(path.relative_to(ROOT).as_posix())
    check('execution','successful_receipt',bool(receipts))
    active=next(p for p in probe_rows if float(p['Source_MW'])==1 and float(p['Request_MW'])==20 and float(p['Penalty'])==.08)
    for name,field,value in [('nonmaximal_output','Verified_Heat_MW',active['Legacy_Heat_MW']),('source_overdraw','Verified_Source_MW',2),('wrong_penalty','Penalty',0),('wrong_nominal_COP','Nominal_COP',7)]:
        bad=copy.deepcopy(active);bad[field]=value;selfchecks.append(dict(name=name,passed=not probe_valid(bad)))
    snapshot=folder/'qa_source'/stamp;snapshot.mkdir(parents=True);shutil.copyfile(__file__,snapshot/Path(__file__).name)
    qa=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),evidence_class='SAME_AGENT_INDEPENDENT_DECIMAL_ALGORITHM_NOT_PHYSICAL_VALIDATION',
        actual_passed=sum(x['passed'] for x in checks),actual_failed=sum(not x['passed'] for x in checks),
        reviewer_selfchecks_passed=sum(x['passed'] for x in selfchecks),reviewer_selfchecks_failed=sum(not x['passed'] for x in selfchecks),
        annual_source_feasibility_violations=violations,annual_nonmaximal_intervals=nonmaximal,
        static_extra_capability_MWh=float(static_gap),max_interval_capability_gap_MW=float(max_gap),
        max_source_excess_MW=float(max_source_excess),first_opportunity=first_opportunity,
        source_comparisons=source_cases,max_independent_balance_residual_MWh=float(max_balance),successful_receipts=receipts,
        breakdown=dict(collections.Counter(x['kind'] for x in checks)),checks=checks,reviewer_selfchecks=selfchecks)
    path=folder/('independent_QA_v47_'+stamp+'.json');assert not path.exists();path.write_text(json.dumps(qa,indent=2)+'\n')
    print(json.dumps({k:v for k,v in qa.items() if k not in ['checks','reviewer_selfchecks']},indent=2))
    if qa['actual_failed'] or qa['reviewer_selfchecks_failed']:
        print(json.dumps([x for x in checks if not x['passed']][:15],indent=2));raise SystemExit(1)
if __name__=='__main__':main()
