"""Independent Fraction port integration; no production/preparation imports.

Independent algorithms in the same agent, not independent personnel or measured
physical validation. Reviewer mutations are separate from observed evidence.
"""
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime, timezone
import csv, hashlib, json, math, shutil, sys, zipfile
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def exact(x):return F(str(x))
def near(a,b):
    if b is None:return a is None
    return a is not None and math.isfinite(a) and abs(exact(a)-b)<=F('2e-12')*max(F(1),abs(b))
def ratio(a,b):return a/b if b else None
def expected_metrics(rows,durations):
    if isinstance(durations,(float,int)):durations=[durations]*len(rows)
    durations=list(map(exact,durations))
    energies=[sum(exact(r[j])*dt for r,dt in zip(rows,durations)) for j in range(8)]
    names=['heat_demand_MWh','hp_direct_MWh','storage_charge_MWh','storage_discharge_MWh',
           'gas_heat_MWh','unmet_heat_MWh','hp_heat_MWh','hp_electric_MWh']
    m=dict(zip(names,energies));m['reported_period_h']=sum(durations)
    m['nonboiler_delivered_MWh']=energies[1]+energies[3]
    m['total_delivered_MWh']=m['nonboiler_delivered_MWh']+energies[4]
    m['nonboiler_coverage_fraction']=ratio(m['nonboiler_delivered_MWh'],energies[0])
    m['unmet_fraction']=ratio(energies[5],energies[0])
    m['hp_heating_COP_integrated']=ratio(energies[6],energies[7])
    # Arithmetic diagnostic written independently as E(Q^2/W)/E(Q).
    terms=sum(exact(r[6])**2/exact(r[7])*dt for r,dt in zip(rows,durations) if r[7]>0)
    m['hp_heat_weighted_COP_diagnostic']=ratio(terms,energies[6])
    return m
def metrics_valid(rows,dt,m):return all(near(m[k],v) for k,v in expected_metrics(rows,dt).items())
def segment_valid(z,p,x):
    if z[1]<=0:return True
    t,A,B=map(exact,[z[1],z[3],z[4]])
    direct,qc,qd,gas,unmet,Q,W,source=map(exact,z[5:13])
    return all([
        near(x[3],direct+qd+gas+unmet),near(Q,direct+qc),near(Q,W+source),
        near(float(B),A+(exact(p[4])*qc-qd/exact(p[5]))*t),
        near(z[19],direct+qd+gas),near(z[20],F(0)),
        0<=B<=exact(p[1]),qc<=exact(p[2]),qd<=exact(p[3]),gas<=exact(p[10]),qc*qd==0,
        all(v>=0 for v in [direct,qc,qd,gas,unmet,Q,W,source]),
        qd==0 or B>=exact(p[7]),source<=exact(x[0])+F('1e-12')])
def main():
    folder=(ROOT/Path(sys.argv[1])).resolve();assert folder.is_relative_to(ROOT/'results')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    checks=[];mutations=[]
    def check(kind,name,passed):checks.append(dict(kind=kind,name=name,passed=bool(passed)))
    spec=json.loads((folder/'spec.json').read_text());report=json.loads((folder/'reporting_v45.json').read_text())
    reexport=json.loads((folder/'mat_reexport_v45.json').read_text())
    check('MAT','report_reopened',report==reexport['report'])
    # MATLAB jsonencode flattens a 1x5 matrix to a vector. Normalize only that
    # observed singleton input shape; keep every numeric value/other field exact.
    reopened_spec=json.loads(json.dumps(reexport['spec']))
    check('MAT','singleton_input_shapes',all(len(c['inputs'])==5 and not isinstance(c['inputs'][0],list) for c in reopened_spec['cases']))
    for c in reopened_spec['cases']:c['inputs']=[c['inputs']]
    check('MAT','spec_reopened',spec==reopened_spec)
    check('execution','case_counts',len(spec['cases'])==len(report['cases'])==len(reexport['simulation_outputs'])==6)
    check('execution','vector_counts',len(spec['reporting_vectors'])==len(report['vectors'])==4)
    check('execution','stateflow_license_observed',report['metadata']['stateflow_license_test'])
    check('execution','normal_mode',report['metadata']['simulation_mode']=='normal')
    check('execution','state_names',set(report['metadata']['thermal_states'])=={
          'IDLE','HEAT_RECOVERY','STORAGE_CHARGE','STORAGE_DISCHARGE','BACKUP','UNMET_DEMAND'})
    check('execution','six_modes_observed',{r['dispatch'][0] for r in report['cases']}==set(range(6)))
    check('execution','harness_success',report['summary']['harness_failed']==0 and all(r['passed'] for r in report['assertions']))
    check('scope','not_physical_validation',spec['fixture_class']=='SYNTHETIC_ENGINEERING_NOT_MEASURED' and not report['summary']['new_model'])
    max_residual=0
    for c,item,reopened in zip(spec['cases'],report['cases'],reexport['simulation_outputs']):
        id=c['id'];p=c['p'];x=c['inputs'][0];d=item['dispatch'];segments=item['segments']
        check('numeric',id+'_case_identity',id==item['id']==reopened['id'] and len(d)==25 and len(segments)==64 and all(len(z)==28 for z in segments))
        check('numeric',id+'_duration',item['dt_h']==p[0])
        check('execution',id+'_actual_error_empty',item['error_message']=='')
        check('MAT',id+'_original_dispatch',d==reopened['dispatch'])
        check('MAT',id+'_original_segments',segments==reopened['segments'])
        check('numeric',id+'_port_adapter',item['ports']==[d[j] for j in [17,1,2,3,4,5,18,19]])
        for key,val in expected_metrics([item['ports']],p[0]).items():check('energy',id+'_'+key,near(item['report'][key],val))
        positive=[z for z in segments if z[1]>0]
        check('timing',id+'_partition',near(sum(z[1] for z in positive),exact(p[0])))
        previous=exact(c['initial_energy_MWh'])
        for j,z in enumerate(positive):
            check('equation',id+f'_segment_{j}',segment_valid(z,p,x))
            check('continuity',id+f'_energy_{j}',near(z[3],previous));previous=exact(z[4])
            check('mode',id+f'_state_{j}',z[0]==c['expected_mode'])
        # Independently integrate actual instantaneous ports into macro trace.
        for col,idx in [(1,5),(2,6),(3,7),(4,8),(5,9),(18,10),(19,11),(20,12)]:
            value=sum(exact(z[idx])*exact(z[1]) for z in positive)/exact(p[0])
            check('trace',id+f'_integral_{col}',near(d[col],value))
        check('trace',id+'_terminal_energy',near(d[7],previous))
        residual=exact(c['initial_energy_MWh'])+(exact(d[19])+exact(d[20])+exact(d[4]))*exact(p[0])-exact(d[11])*exact(p[0])-exact(d[7])-sum(map(exact,d[8:11]))
        max_residual=max(max_residual,abs(float(residual)))
        check('equation',id+'_independent_first_law',abs(residual)<F('1e-11'))
        check('mode',id+'_expected',d[0]==c['expected_mode'])
        reference=item['reference']
        for idx in list(range(21))+[23,24]:check('reference',id+f'_v30_{idx}',near(d[idx],exact(reference[idx])))
        check('reference',id+'_COP',near(d[22],exact(reference[22]) if reference[22] is not None else None))
        check('reference',id+'_request_semantics',d[21]==reference[21] if d[23] else d[21]==0 and reference[21]==x[3]+p[2])
        for oldname in ['v1','v2']:
            old=item['legacy'][oldname]
            expected_legacy=(exact(d[17])-exact(d[4]))*exact(p[0])
            check('legacy_defect',id+'_'+oldname+'_reproduced',near(old['reused_to_network_MWh'],expected_legacy))
            check('legacy_defect',id+'_'+oldname+'_unmet_credit',near(old['reused_to_network_MWh']-item['report']['nonboiler_delivered_MWh'],exact(d[5])*exact(p[0])))
    for v in report['vectors']:
        for key,val in expected_metrics(v['ports'],v['dt']).items():check('energy',v['id']+'_'+key,near(v['report'][key],val))
        check('boundary',v['id']+'_aux_unspecified',not v['report']['auxiliary_electricity_included'] and v['report']['electrical_boundary']=='ACTIVE_HP_ONLY_AUXILIARIES_UNSPECIFIED')
    for v,s in zip(report['vectors'],spec['reporting_vectors']):
        check('numeric',v['id']+'_fixture_preserved',v['id']==s['id'] and v['ports']==s['ports'] and v['dt']==s['dt'])
    vector=report['vectors'][0]
    for oldname in ['v1','v2']:
        check('legacy_defect',oldname+'_mean_is_diagnostic',near(vector['legacy'][oldname]['mean_cop'],F(8,3)))
    check('repair','ratio_not_diagnostic',near(vector['report']['hp_heating_COP_integrated'],F(12,5)) and near(vector['report']['hp_heat_weighted_COP_diagnostic'],F(8,3)))
    check('repair','unmet_excluded',report['cases'][5]['report']['nonboiler_delivered_MWh']==0 and report['cases'][5]['report']['unmet_heat_MWh']==3)
    check('execution','12_reporting_faults',len(report['faults'])==12)
    for z in report['faults']:check('execution','report_fault_'+str(z['index']),z['rejected'] and bool(z['error_id']) and bool(z['message']))
    with (folder/'stateflow_numeric_trace_v45.csv').open() as f:csvrows=list(csv.reader(f))
    check('artifact','csv_row_count',len(csvrows)==len(report['cases']))
    for j,(row,c) in enumerate(zip(csvrows,report['cases'])):
        check('artifact',f'csv_numeric_{j}',len(row)==26 and all(near(float(a),exact(b)) if b is not None else math.isnan(float(a)) for a,b in zip(row[1:],c['dispatch'])))
    for x in json.loads((folder/'preservation.json').read_text()):
        path=ROOT/x['path'];check('preservation',x['path'],path.is_file() and path.stat().st_size==x['bytes'] and sha(path)==x['sha256'])
    with zipfile.ZipFile(ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx') as z:
        content='\n'.join(z.read(name).decode('utf-8',errors='replace') for name in z.namelist() if name.endswith('.xml'))
    for name in ['IDLE','HEAT_RECOVERY','STORAGE_CHARGE','STORAGE_DISCHARGE','BACKUP','UNMET_DEMAND','HP_ON','HP_OFF']:
        check('archive',name,name in content)
    for path in (folder/'source_snapshot').glob('*'):
        if path.suffix=='.json':current=folder/'spec.json'
        elif path.name.startswith('default_config'):current=ROOT/'matlab'/path.name
        elif path.name.startswith(('compute_','simulate_')):current=ROOT/'matlab/+dchr'/path.name
        elif path.name.startswith(('heat_pump_step','storage_')):current=ROOT/'matlab/+dchr/+components'/path.name
        else:current=ROOT/'matlab/simulink'/path.name
        check('artifact',path.name,sha(path)==sha(current))
    successful=[];failures=[]
    for path in ROOT.glob('audit/Reporting_execution_v45_*.json'):
        receipt=json.loads(path.read_text(encoding='utf-8-sig'))
        if folder.name not in receipt['command']:continue
        if receipt['exit_code']!=0:failures.append(str(path.relative_to(ROOT)));continue
        log=(ROOT/receipt['log_path']).read_text(encoding='utf-8-sig')
        check('execution',path.name,'REPORTING_V45 scenarios=6' in log and 'failed=0' in log and 'MAT_REEXPORT_V45 saved_cases=6' in log)
        successful.append(str(path.relative_to(ROOT)))
    check('execution','successful_receipt',bool(successful))
    # Separate reviewer selfchecks: corrupt metrics and independently checked trace.
    bad=dict(vector['report']);bad['hp_heating_COP_integrated']=8/3
    mutations.append(dict(name='arithmetic_as_integrated_detected',passed=not metrics_valid(vector['ports'],vector['dt'],bad)))
    unmet=report['cases'][5];bad=dict(unmet['report']);bad['nonboiler_delivered_MWh']=3
    mutations.append(dict(name='unmet_reuse_credit_detected',passed=not metrics_valid([unmet['ports']],unmet['dt_h'],bad)))
    case=report['cases'][2];bad=list(case['segments'][0]);bad[4]+=1
    mutations.append(dict(name='terminal_energy_corruption_detected',passed=not segment_valid(bad,spec['cases'][2]['p'],spec['cases'][2]['inputs'][0])))
    inventory=report['vectors'][2];bad=dict(inventory['report']);bad['hp_heating_COP_integrated']=0
    mutations.append(dict(name='undefined_inventory_cop_detected',passed=not metrics_valid(inventory['ports'],inventory['dt'],bad)))
    qa_source=folder/'qa_source'/stamp;qa_source.mkdir(parents=True);shutil.copy2(__file__,qa_source)
    summary=dict(version='0.45',timestamp_utc=datetime.now(timezone.utc).isoformat(),
                 actual_passed=sum(c['passed'] for c in checks),actual_failed=sum(not c['passed'] for c in checks),
                 reviewer_selfchecks_passed=sum(c['passed'] for c in mutations),reviewer_selfchecks_failed=sum(not c['passed'] for c in mutations),
                 max_independent_balance_residual_MWh=max_residual,successful_receipts=successful,failed_receipts=failures,
                 independent_personnel=False,physical_validation=False,checks=checks,reviewer_selfchecks=mutations)
    outfile=folder/('independent_QA_v45_'+stamp+'.json');outfile.write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['checks','reviewer_selfchecks']},indent=2))
    print('QA_REPORT='+str(outfile.relative_to(ROOT)))
    assert summary['actual_failed']==summary['reviewer_selfchecks_failed']==0
if __name__=='__main__':main()
