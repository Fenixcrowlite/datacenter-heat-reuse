"""Independent rational reporting and Decimal TES equations from saved evidence.

No production or preparation imports. Same agent, independent algorithms;
this is implementation QA, not independent personnel or physical validation.
"""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from fractions import Fraction as F
import copy, csv, hashlib, json, math, shutil, sys, zipfile
ROOT=Path(__file__).resolve().parents[1]
COLS=['Heat_Demand_MW','HP_Direct_MW','Storage_Charge_MW','Storage_Discharge_MW',
      'Gas_Heat_MW','Unmet_Heat_MW','HP_Heat_MW','HP_Electric_MW']
def exact(x):return x if isinstance(x,F) else F(str(x))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def near(a,b):
    if b is None:return a is None
    return a is not None and math.isfinite(float(a)) and abs(exact(a)-exact(b))<=F('3e-11')*max(1,abs(exact(b)))
def dictrows(path):
    with path.open(newline='') as f:return list(csv.DictReader(f))
def numeric(path):
    with path.open(newline='') as f:return [[float(x) for x in r] for r in csv.reader(f)]
def energy_expected(rows,dt):
    if isinstance(dt,(int,float)):dt=[dt]*len(rows)
    dt=list(map(exact,dt));E=[sum(exact(r[j])*d for r,d in zip(rows,dt)) for j in range(8)]
    names=['heat_demand_MWh','hp_direct_MWh','storage_charge_MWh','storage_discharge_MWh',
           'gas_heat_MWh','unmet_heat_MWh','hp_heat_MWh','hp_electric_MWh']
    m=dict(zip(names,E));m.update(reported_period_h=sum(dt),intervals=len(rows),
        nonboiler_delivered_MWh=E[1]+E[3],total_delivered_MWh=E[1]+E[3]+E[4])
    m['nonboiler_coverage_fraction']=(E[1]+E[3])/E[0] if E[0] else None
    m['unmet_fraction']=E[5]/E[0] if E[0] else None
    m['hp_heating_COP_integrated']=E[6]/E[7] if E[7] else None
    m['hp_heat_weighted_COP_diagnostic']=sum(exact(r[6])**2/exact(r[7])*d for r,d in zip(rows,dt) if exact(r[7])>0)/E[6] if E[6] else None
    return m
def comparison_expected(e):
    eta=F(9,10);gas=F(50);elec=F(100);carbon=F(101,500);grid=F(1,5)
    supplied=e['total_delivered_MWh'];boiler=e['gas_heat_MWh'];work=e['hp_electric_MWh'];unmet=e['unmet_heat_MWh'];demand=e['heat_demand_MWh']
    baseline=supplied/eta;fuel=boiler/eta
    return dict(gas_boiler_efficiency=eta,gas_price_EUR_per_MWh_fuel=gas,electricity_price_EUR_per_MWh=elec,
        gas_tCO2_per_MWh_fuel=carbon,grid_tCO2_per_MWh=grid,
        equal_delivered_service_gas_fuel_MWh=baseline,scenario_gas_fuel_MWh=fuel,
        equal_delivered_service_baseline_opex_EUR=baseline*gas,
        scenario_active_HP_boiler_opex_EUR=fuel*gas+work*elec,
        equal_delivered_service_opex_difference_EUR=(supplied-boiler)/eta*gas-work*elec,
        equal_delivered_service_baseline_CO2_t=baseline*carbon,
        scenario_active_HP_boiler_CO2_t=fuel*carbon+work*grid,
        equal_delivered_service_CO2_difference_t=(supplied-boiler)/eta*carbon-work*grid,
        full_demand_baseline_opex_EUR=demand/eta*gas,full_demand_baseline_CO2_t=demand/eta*carbon,
        unmet_baseline_opex_credit_EUR=unmet/eta*gas,unmet_baseline_CO2_credit_t=unmet/eta*carbon)
def metrics_valid(rows,dt,m):
    e=energy_expected(rows,dt)
    return all(near(m['energy'][k],v) for k,v in e.items()) and all(near(m[k],v) for k,v in comparison_expected(e).items())
def ode_endpoint(A,P,k,t):
    with localcontext() as ctx:
        ctx.prec=50;A,P,k,t=map(lambda x:Decimal(str(x)),[A,P,k,t])
        if not k:return float(A+P*t)
        # Integrating-factor expression, independent of MATLAB's phi/beta code.
        q=(k*t).exp();return float((A+P*(q-1)/k)/q)
def main():
    folder=(ROOT/Path(sys.argv[1])).resolve();assert folder.is_relative_to(ROOT/'results')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');checks=[];mutations=[]
    def check(kind,name,ok):checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    report=json.loads((folder/'period_v46.json').read_text());spec=json.loads((folder/'spec.json').read_text())
    mat_folder=sorted(folder.glob('mat_reopen_v46_*'))[-1]
    reopened=json.loads((mat_folder/'mat_reexport_v46.json').read_text())
    check('MAT','corrected_export_source',sha(mat_folder/'export_period_evidence_v46.m')==sha(ROOT/'matlab/export_period_evidence_v46.m'))
    check('MAT','report_reopened',reopened['report']==report)
    check('execution','harness_pass',report['summary']['harness_failed']==0 and all(x['passed'] for x in report['assertions']))
    check('scope','synthetic_and_preserved_model',spec['fixture_class']=='SYNTHETIC_ENGINEERING_NOT_MEASURED' and not report['summary']['new_model'])
    check('execution','license_observed',report['metadata']['stateflow_license_test']==1)
    check('execution','normal_mode',report['metadata']['simulation_mode']=='normal')
    check('execution','scenario_counts',len(report['stateflow'])==7 and len(report['annual'])==3)
    max_balance=0;all_modes=set();period_transitions=0
    def review_metrics(id,rows,dt,m):
        expected=energy_expected(rows,dt)
        for k,v in expected.items():check('energy',id+'_'+k,near(m['energy'][k],v))
        for k,v in comparison_expected(expected).items():check('comparison',id+'_'+k,near(m[k],v))
        check('boundary',id+'_explicit_boundaries',
            m['service_boundary']=='EQUAL_ACTUALLY_DELIVERED_NETWORK_INLET_HEAT' and
            m['accounting_boundary']=='ACTIVE_HP_AND_BOILER_ONLY_CAPEX_AUXILIARIES_UNSPECIFIED' and
            m['comparator_boiler_capacity_policy']=='IDEAL_GAS_ONLY_COMPARATOR_SIZED_FOR_SAME_DELIVERED_PROFILE' and
            m['heat_inventory_boundary']=='INITIAL_TES_PROVENANCE_AND_TERMINAL_VALUE_UNPRICED' and
            not m['energy']['auxiliary_electricity_included'])
        return expected
    for item,mat in zip(report['stateflow'],reopened['stateflow']):
        id=item['id'];p=item['p'];n=item['intervals'];dt=item['dt_h'];rows=dictrows(folder/(id+'_ports.csv'))
        ports=[[r[k] for k in COLS] for r in rows];dispatch=numeric(folder/(id+'_dispatch.csv'));segments=numeric(folder/(id+'_segments.csv'))
        # Off-state COP is NaN; Python float equality would reject identical NaNs.
        # Exact CSV bytes certify every reopened value and spelling, including NaN.
        check('MAT',id+'_dispatch',sha(mat_folder/(id+'_mat_dispatch.csv'))==sha(folder/(id+'_dispatch.csv')))
        check('MAT',id+'_segments',sha(mat_folder/(id+'_mat_segments.csv'))==sha(folder/(id+'_segments.csv')))
        check('execution',id+'_error_and_sample_count',item['error_message']==mat['error_message']=='' and len(dispatch)==len(ports)==n)
        times=mat['sample_time_h'];times=[times] if isinstance(times,(int,float)) else times
        check('timing',id+'_sample_time',len(times)==n and all(near(t,i*dt) for i,t in enumerate(times)))
        review_metrics(id,ports,dt,item['report']);previous=item['initial_energy_MWh'];previous_mode=None
        inputs=item['inputs'];inputs=[inputs] if not isinstance(inputs[0],list) else inputs
        for i,(d,row) in enumerate(zip(dispatch,ports),1):
            check('adapter',id+f'_interval_{i}',all(near(a,b) for a,b in zip(row,[d[j] for j in [17,1,2,3,4,5,18,19]])))
            group=[r[2:] for r in segments if r[0]==i];check('timing',id+f'_partition_{i}',near(sum(z[1] for z in group),dt))
            for k,z in enumerate(group):
                mode,t,offset,A,B=z[:5];direct,qc,qd,gas,unmet,Q,W,source=z[5:13];x=inputs[i-1]
                all_modes.add(int(mode));P=p[4]*qc-qd/p[5];end=ode_endpoint(A,P,p[6],t)
                check('ODE',id+f'_endpoint_{i}_{k}',near(B,end))
                check('continuity',id+f'_energy_{i}_{k}',near(A,previous));previous=B
                check('equation',id+f'_service_{i}_{k}',near(x[3],direct+qd+gas+unmet) and near(Q,direct+qc) and near(Q,W+source))
                check('equation',id+f'_losses_{i}_{k}',near(z[16],A+P*t-B) and near(z[17],(1-p[4])*qc*t) and near(z[18],(1/p[5]-1)*qd*t))
                residual=exact(A)+(exact(source)+exact(W)+exact(gas)-exact(z[19]))*exact(t)-exact(B)-sum(map(exact,z[16:19]))
                max_balance=max(max_balance,abs(float(residual)))
                check('equation',id+f'_balance_{i}_{k}',abs(residual)<F('1e-10'))
                expected_mode=5 if unmet>0 else 4 if gas>0 else 3 if qd>0 else 2 if qc>0 else 1 if direct>0 else 0
                check('mode',id+f'_mode_{i}_{k}',mode==expected_mode)
                check('bounds',id+f'_bounds_{i}_{k}',0<=A<=p[1]+1e-10 and 0<=B<=p[1]+1e-10 and qc<=p[2]+1e-10 and qd<=p[3]+1e-10 and gas<=p[10] and qc*qd==0 and (qd==0 or min(A,B)>=p[7]-1e-10))
                if id==spec['period']['id'] and previous_mode is not None and mode!=previous_mode:period_transitions+=1
                previous_mode=mode
            check('trace',id+f'_terminal_{i}',near(d[7],previous))
            for a,b in [(1,5),(2,6),(3,7),(4,8),(5,9),(18,10),(19,11),(20,12)]:
                check('trace',id+f'_integral_{i}_{a}',near(d[a],sum(exact(z[b])*exact(z[1]) for z in group)/exact(dt)))
    check('execution','six_modes_observed',all_modes==set(range(6)))
    check('execution','period_actual_mode_transitions',period_transitions>=6)
    for item,mat in zip(report['annual'],reopened['annual']):
        id=item['id'];rows=dictrows(folder/(id+'_ports.csv'));legacy=dictrows(folder/(id+'_legacy.csv'))
        ports=[[r[k] for k in COLS] for r in rows];e=review_metrics(id,ports,mat['dt_h'],item['report'])
        check('MAT',id+'_ports',dictrows(mat_folder/(id+'_mat_ports.csv'))==rows)
        check('MAT',id+'_legacy',dictrows(mat_folder/(id+'_mat_legacy.csv'))==legacy)
        check('MAT',id+'_reports',mat['report']==item['report'] and mat['legacy_report']==item['legacy_report'])
        check('period',id+'_8760_intervals',len(rows)==len(legacy)==8760 and e['reported_period_h']==8760)
        cap=item['boiler_cap_MW'];valid=True;state_valid=True;E=0.;max_error=0
        for row,old in zip(rows,legacy):
            q=list(map(float,[row[k] for k in COLS]));potential=float(old['HP_Heat_MW']);actual=float(old['HP_Heat_Used_MW'])
            demand=q[0];direct=min(potential,demand);surplus=max(0,potential-demand);deficit=max(0,demand-potential)
            Eafter=E*(1-.0001);charge=dis=0.
            if surplus>0:charge=min(surplus,5,(50-Eafter)/.95)
            elif deficit>0:dis=min(deficit,5,Eafter*.95)
            Enext=Eafter+.95*charge-dis/.95;needed=max(0,demand-direct-dis);gas=min(cap,needed)
            state_valid &= all(near(a,b) for a,b in [(old['Storage_E_MWh'],E),(q[2],charge),(q[3],dis),(q[1],direct),(q[6],direct+charge),(q[4],gas),(q[5],needed-gas)])
            E=Enext
            valid &= near(q[6],actual) and near(q[1],actual-q[2]) and 0<=q[4]<=cap and all(v>=0 and math.isfinite(v) for v in q)
            residual=q[0]-q[1]-q[3]-q[4]-q[5];max_error=max(max_error,abs(residual));valid &= abs(residual)<1e-10
        check('reference',id+'_independent_8760_dispatch_recurrence',state_valid)
        check('adapter',id+'_all_actual_ports_and_finite_backup',valid)
        check('legacy_defect',id+'_unmet_reuse_credit',near(item['legacy_report']['reused_to_network_MWh'],e['nonboiler_delivered_MWh']+e['unmet_heat_MWh']))
        check('legacy_defect',id+'_unmet_cost_credit',near(item['legacy_report']['opex_saving_EUR'],item['report']['equal_delivered_service_opex_difference_EUR']+item['report']['unmet_baseline_opex_credit_EUR']))
        check('legacy_defect',id+'_unmet_carbon_credit',near(item['legacy_report']['CO2_saving_t'],item['report']['equal_delivered_service_CO2_difference_t']+item['report']['unmet_baseline_CO2_credit_t']))
    v=spec['reporting_fixture'];fixture_rows=[[r[0],r[1]-r[2],r[2],r[3],r[4],r[5],r[1],r[7]] for r in v['legacy_rows']]
    review_metrics('schema_trap',fixture_rows,v['dt_h'],report['fixture'])
    check('adapter','potential_not_actual',near(report['fixture']['energy']['hp_heat_MWh'],17))
    for fault in report['faults']:check('rejection','fault_'+str(fault['index']),fault['rejected'] and fault['error_id'] and fault['message'])
    check('rejection','12_actual_faults',len(report['faults'])==12)
    for entry in json.loads((folder/'preservation.json').read_text()):
        p=ROOT/entry['path'];check('preservation',entry['path'],p.is_file() and p.stat().st_size==entry['bytes'] and sha(p)==entry['sha256'])
    for p in (folder/'source_snapshot'/'matlab').rglob('*'):
        if not p.is_file():continue
        if p.name=='export_period_evidence_v46.m':
            prior=ROOT/'results/period_v46_20261010T175910_522076Z/source_snapshot/matlab/export_period_evidence_v46.m'
            check('snapshot','original_failed_export_source_preserved',sha(p)==sha(prior))
        else:check('snapshot',p.relative_to(folder/'source_snapshot').as_posix(),sha(p)==sha(ROOT/p.relative_to(folder/'source_snapshot')))
    with zipfile.ZipFile(ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx') as z:
        xml='\n'.join(z.read(n).decode(errors='replace') for n in z.namelist() if n.endswith('.xml'))
    for name in ['IDLE','HEAT_RECOVERY','STORAGE_CHARGE','STORAGE_DISCHARGE','BACKUP','UNMET_DEMAND','HP_ON','HP_OFF']:check('archive',name,name in xml)
    receipts=[];failed=[]
    for p in ROOT.glob('audit/Period_execution_v46_*.json'):
        r=json.loads(p.read_text(encoding='utf-8-sig'))
        if folder.name not in r['command']:continue
        if r['exit_code']:failed.append(p.relative_to(ROOT).as_posix());continue
        log=(ROOT/r['log_path']).read_text(encoding='utf-8-sig');receipts.append(p.relative_to(ROOT).as_posix())
        full_run='run_period_experiment_v46' in r['command']
        check('execution',p.name,'MAT_REEXPORT_V46 stateflow=7 annual=3' in log and (not full_run or ('PERIOD_V46 passed=' in log and 'failed=0' in log)))
        if not full_run:check('execution','corrected_MAT_receipt',mat_folder.name in log)
    check('execution','successful_batch_receipt',bool(receipts))
    bad=copy.deepcopy(report['fixture']);bad['energy']['hp_heat_MWh']*=10
    mutations.append(dict(name='potential_as_actual_detected',passed=not metrics_valid(fixture_rows,v['dt_h'],bad)))
    item=report['stateflow'][5];rows=[[r[k] for k in COLS] for r in dictrows(folder/(item['id']+'_ports.csv'))]
    bad=copy.deepcopy(item['report']);bad['equal_delivered_service_opex_difference_EUR']+=bad['unmet_baseline_opex_credit_EUR']
    mutations.append(dict(name='unmet_fuel_credit_detected',passed=not metrics_valid(rows,item['dt_h'],bad)))
    bad=copy.deepcopy(item['report']);bad['energy']['nonboiler_delivered_MWh']+=bad['energy']['unmet_heat_MWh']
    mutations.append(dict(name='unmet_reuse_detected',passed=not metrics_valid(rows,item['dt_h'],bad)))
    bad=copy.deepcopy(report['fixture']);bad['energy']['hp_heating_COP_integrated']=bad['energy']['hp_heat_weighted_COP_diagnostic']
    mutations.append(dict(name='diagnostic_as_integrated_detected',passed=not metrics_valid(fixture_rows,v['dt_h'],bad)))
    dest=folder/'qa_source'/stamp;dest.mkdir(parents=True);shutil.copy2(__file__,dest)
    summary=dict(version='0.46',timestamp_utc=datetime.now(timezone.utc).isoformat(),
        actual_passed=sum(c['passed'] for c in checks),actual_failed=sum(not c['passed'] for c in checks),
        reviewer_selfchecks_passed=sum(c['passed'] for c in mutations),reviewer_selfchecks_failed=sum(not c['passed'] for c in mutations),
        max_independent_balance_residual_MWh=max_balance,period_mode_transitions=period_transitions,mat_reopen_directory=mat_folder.relative_to(ROOT).as_posix(),
        successful_receipts=receipts,failed_receipts=failed,independent_personnel=False,physical_validation=False,
        checks=checks,reviewer_selfchecks=mutations)
    path=folder/('independent_QA_v46_'+stamp+'.json');path.write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['checks','reviewer_selfchecks']},indent=2));print('QA_REPORT='+path.relative_to(ROOT).as_posix())
    if summary['actual_failed'] or summary['reviewer_selfchecks_failed']:
        print(json.dumps([x for x in checks+mutations if not x['passed']],indent=2));raise SystemExit(1)
if __name__=='__main__':main()
