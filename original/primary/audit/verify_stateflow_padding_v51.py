"""Independent per-segment equations, physical clock, matched-design/evidence QA.

No production dispatch import/call. Inherited independent 60-digit Decimal
quadratic/ODE reviewer functions. Same-agent algorithmic QA, not personnel or
measured physical validation. Reviewer mutations are separately counted.
"""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal as D, localcontext
import collections, copy, csv, hashlib, json, math, shutil, sys, zipfile, struct
import xml.etree.ElementTree as ET
from verify_annual_stateflow_v49 import physical, restart_ok, verify_report
from verify_annual_dispatch_v48 import maximal, expected_row, near, dec

ROOT = Path(__file__).resolve().parents[1]

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def numeric(p):
    with p.open(newline='') as f:
        return [[float(v) for v in r] for r in csv.reader(f)]

def rows(p):
    with p.open(newline='') as f:
        return list(csv.DictReader(f))

def dwell_transition(z, x, p, h, control, age, bound, previous_latch):
    """Independent policy at a change; physical elapsed spans, no production clock."""
    new_latch = int(z[25])
    if new_latch == previous_latch:
        return True
    if new_latch == 1:
        return restart_ok(age, bound, z[3], control, z[10])
    nominal = min(dec(h[3]), dec(h[1])*(dec(x[2])+D('273.15'))/(dec(x[2])-dec(x[1])))
    high = maximal(x[0], x[3]+p[2], h[0], nominal, h[4], h[2])
    return (near(z[3], p[1]) and age-bound >= dec(control[1])) or high == 0

def main():
    folder = (ROOT/Path(sys.argv[1])).resolve()
    assert folder.is_relative_to(ROOT/'results')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    checks, selfchecks = [], []
    def check(kind, name, ok):
        checks.append(dict(kind=kind, name=name, passed=bool(ok)))
    r = json.loads((folder/'annual_sensitivity_v51.json').read_text())
    spec = json.loads((folder/'spec.json').read_text())
    cfg = r['cfg'];base = spec['scenarios'][0]['policy']
    check('execution', 'harness', r['summary']['harness_failed']==0 and all(x['passed'] for x in r['assertions']))
    check('execution', 'actual_Stateflow', r['metadata']['simulation_mode']=='normal' and r['metadata']['stateflow_license_test']==1)
    check('MAT', 'report', json.loads((folder/'mat_reopen/report.json').read_text())==r)
    for p in folder.glob('*.csv'):
        check('MAT', p.name, sha(p)==sha(folder/'mat_reopen'/p.name))
    check('scope', 'version', spec['model_version']==r['summary']['model_version']=='0.51' and r['summary']['new_model'])
    check('scope', 'matrix_nine', len(spec['scenarios'])==len(r['stateflow'])==len(r['matrix'])==9)
    xs = numeric(folder/'annual_inputs.csv');paired=rows(folder/'paired_loss_first_v48.csv')
    check('scope', 'full_year', len(xs)==len(paired)==8760)
    scenarios, total_segments, total_intervals, maxres, active = [], 0, 0, D(0), None
    with localcontext() as ctx:
        ctx.prec=60
        previous=dec(cfg['storage']['initial_soc'])*dec(cfg['storage']['capacity_MWh'])
        pairedtot=collections.defaultdict(lambda:D(0))
        keys=['HP_Direct_MW','Storage_Charge_MW','Storage_Discharge_MW','Gas_Heat_MW','Unmet_Heat_MW','HP_Heat_MW','HP_Electric_MW']
        for i,(x,b) in enumerate(zip(xs,paired)):
            dh=cfg['dh'];tout=dec(b['Tout_C'])
            frac=max(D(0),min(D(1),(dec(dh['temperature_balance_C'])-tout)/(dec(dh['temperature_balance_C'])-dec(dh['design_outdoor_temp_C']))))
            delivery=dec(dh['supply_min_C'])+frac*(dec(dh['supply_max_C'])-dec(dh['supply_min_C']))
            expected,_=expected_row(b,r['paired_cfg'],previous)
            check('paired_equations', str(i), all(near(b[k],v) for k,v in expected.items()))
            previous=expected['Storage_E_Next_MWh']
            expected_input=[expected['HX_Heat_to_HP_MW'],expected['HP_Source_C'],base['condenser_C'],expected['Heat_Demand_MW'],delivery]
            check('adapter_equations', str(i), all(near(v,e) for v,e in zip(x,expected_input)))
            for key in keys+['Heat_Demand_MW']:
                pairedtot[key]+=dec(b[key])*dec(cfg['sim']['dt_h'])
        verify_report(check,'paired_loss_first_v48',r['paired_report'],pairedtot,cfg)
        old=numeric(ROOT/spec['baseline_evidence']/'annual_8760h_dispatch.csv')
        dsbaseline=numeric(folder/'baseline_dispatch.csv')
        check('reproduction', 'v49_baseline', len(old)==len(dsbaseline)==8760 and all(
            near(a,b) or math.isnan(a) and math.isnan(b) for v,w in zip(old,dsbaseline) for a,b in zip(v,w)))
        for item,definition,matrix in zip(r['stateflow'],spec['scenarios'],r['matrix']):
            id=item['id'];p,h,control=item['p'],item['h'],item['c'];policy=item['policy']
            changed={k for k in base if policy[k]!=base[k]}
            wanted={definition['changed_coordinate']} if id!='baseline' else set()
            check('matched_design', id, item['execution_success'] and policy==definition['policy'] and changed==wanted)
            expectedC=dec(cfg['storage']['capacity_MWh'])/(dec(policy['max_temperature_C'])-dec(policy['ambient_C']))
            cutoff=expectedC*(dec(policy['delivery_cutoff_C'])-dec(policy['ambient_C']))
            check('policy', id, near(p[7],cutoff) and near(p[8],expectedC) and control==[policy['restart_energy_MWh'],policy['min_on_h'],policy['min_off_h'],64] and control[0]>p[7] and control[0]<p[1])
            check('matched_parameters', id, item['initial_energy_MWh']==cfg['storage']['initial_soc']*cfg['storage']['capacity_MWh']==0 and item['initial_clock']==base['initial_clock'] and h==r['stateflow'][0]['h'] and all(p[k]==r['stateflow'][0]['p'][k] for k in range(11) if k!=7))
            preflight=rows(folder/(id+'_preflight.csv'))
            check('preflight', id, len(preflight)==8760 and all(int(v['Admissible'])==1 and not v['Error_ID'] for v in preflight) and max(x[4] for x in xs)<=policy['delivery_cutoff_C'])
            ds=numeric(folder/(id+'_dispatch.csv'));ss=numeric(folder/(id+'_segments.csv'))
            starts=numeric(folder/(id+'_clock_start.csv'));ends=numeric(folder/(id+'_clock_end.csv'))
            with (folder/'binary_reopen'/(id+'_spans_hex.csv')).open(newline='') as f:
                span_rows=list(csv.reader(f))
            exact_spans={(int(v[0])-1,int(v[1])):exact_float(v[2]) for v in span_rows}
            with (folder/'binary_reopen'/(id+'_clocks_hex.csv')).open(newline='') as f:
                binary_clocks=list(csv.reader(f))
            exact_starts=[[exact_float(v) for v in row[1:5]] for row in binary_clocks]
            exact_ends=[[exact_float(v) for v in row[5:9]] for row in binary_clocks]
            check('binary_MAT_reopen',id,len(span_rows)==len(exact_spans)==len(ss) and
                  len(binary_clocks)==len(starts)==len(ends) and
                  all(int(row[0])==i+1 for i,row in enumerate(binary_clocks)) and
                  all(near(v,w) for a,b in zip(starts,exact_starts) for v,w in zip(a,b)) and
                  all(near(v,w) for a,b in zip(ends,exact_ends) for v,w in zip(a,b)))
            # Dwell thresholds require exact binary spans; CSV serialization
            # can round a certified 0.5h decision to a value just below 0.5h.
            # Retain CSV physical-equation checks and bind every exact span to it.
            starts,ends=exact_starts,exact_ends
            indexed=collections.defaultdict(list)
            for z in ss:
                indexed[int(z[0])-1].append((int(z[1]),z[2:]))
            check('shape', id, len(ds)==len(starts)==len(ends)==item['intervals']==8760 and len(ss)==item['positive_segments'])
            E=dec(item['initial_energy_MWh']);clock=item['initial_clock'];age=dec(clock[1])+dec(clock[2])
            tot=collections.defaultdict(lambda:D(0));modes=[];latchChanges=0;onChanges=0;offChanges=0
            standing=D(0);maxslots=0;case_res=D(0)
            for i,row in enumerate(ds):
                segs=indexed[i];span_sum=D(0);integrals=[D(0)]*8;loss=[D(0)]*3;startE=E
                check('schedule_slots', f'{id}_{i}', bool(segs) and len(segs)<=64 and [slot for slot,z in segs]==list(range(1,len(segs)+1)))
                maxslots=max(maxslots,len(segs))
                check('clock_handoff', f'{id}_{i}', all(near(v,w) for v,w in zip(starts[i],clock)))
                latch=int(starts[i][0]);bound=max(D.from_float(starts[i][3]),D.from_float(ends[i][3]))
                for j,(slot,z) in enumerate(segs):
                    total_segments+=1;t=D.from_float(exact_spans[(i,slot)]);new_latch=int(z[25])
                    check('binary_span_binding',f'{id}_{i}_{j}',near(z[1],t))
                    check('segment_schedule', f'{id}_{i}_{j}', t>0 and near(z[2],span_sum) and near(z[3],E))
                    for kind,ok in physical(z,xs[i],p,h).items():
                        check('segment_'+kind, f'{id}_{i}_{j}', ok)
                    if new_latch!=latch:
                        check('certified_dwell', f'{id}_{i}_{j}', dwell_transition(z,xs[i],p,h,control,age,bound,latch))
                        latchChanges+=1;onChanges+=int(new_latch==1);offChanges+=int(new_latch==0);age=D(0)
                    check('clock_age', f'{id}_{i}_{j}', near(z[26],age) and near(z[27],age+t) and new_latch in [0,1] and ((new_latch==0 and z[10]==0) or (new_latch==1 and z[10]>0)))
                    age+=t;latch=new_latch;E=dec(z[4]);span_sum+=t;modes.append(int(z[0]))
                    for k,v in enumerate(z[5:13]):integrals[k]+=dec(v)*t
                    for k,v in enumerate(z[16:19]):loss[k]+=dec(v)
                    if active is None and z[10]>0:active=(z,xs[i],p,h,control)
                observed=[row[1],row[2],row[3],row[4],row[5],row[18],row[19],row[20]]
                check('aggregate', f'{id}_{i}', near(span_sum,p[0]) and near(row[7],E) and all(near(v,integrals[k]/dec(p[0])) for k,v in enumerate(observed)) and all(near(v,w) for v,w in zip(row[8:11],loss)))
                delivered=integrals[0]+integrals[2]+integrals[3]
                residual=startE+integrals[6]+integrals[7]+integrals[3]-delivered-E-sum(loss)
                maxres=max(maxres,abs(residual));case_res=max(case_res,abs(residual));standing+=loss[0]
                check('macro_first_law', f'{id}_{i}', abs(residual)<D('2e-9') and near(row[12],residual) and near(row[17],xs[i][3]))
                check('clock_enclosure', f'{id}_{i}', int(ends[i][0])==latch and abs(dec(ends[i][1])+dec(ends[i][2])-age)<=dec(ends[i][3])+D('5e-12') and ends[i][3]>=0 and abs(ends[i][2])+ends[i][3]<=1e-8)
                clock=ends[i]
                for key,val in zip(keys,integrals[:7]):tot[key]+=val
                tot['Heat_Demand_MW']+=dec(xs[i][3])*dec(p[0])
            verify_report(check,id,item['report'],tot,cfg)
            total_intervals+=len(ds);modeChanges=sum(a!=b for a,b in zip(modes,modes[1:]))
            check('matrix', id, matrix['id']==id and near(matrix['cutoff_inventory_MWh'],cutoff) and near(matrix['maximum_usable_inventory_MWh'],dec(p[1])-cutoff) and near(matrix['terminal_inventory_MWh'],E) and near(item['terminal_inventory_MWh'],E) and matrix['latch_changes']==latchChanges and matrix['mode_changes']==modeChanges and matrix['positive_segments']==len(ss) and near(matrix['standing_loss_MWh'],standing) and near(matrix['unmet_MWh'],tot['Unmet_Heat_MW']) and near(matrix['hp_electric_MWh'],tot['HP_Electric_MW']) and near(matrix['gas_heat_MWh'],tot['Gas_Heat_MW']) and near(matrix['charge_MWh'],tot['Storage_Charge_MW']) and near(matrix['discharge_MWh'],tot['Storage_Discharge_MW']))
            if id=='baseline':basetot=copy.deepcopy(tot)
            check('delta', id, near(matrix['unmet_delta_baseline_MWh'],tot['Unmet_Heat_MW']-basetot['Unmet_Heat_MW']) and near(matrix['unmet_delta_lossfirst_MWh'],tot['Unmet_Heat_MW']-pairedtot['Unmet_Heat_MW']))
            scenarios.append(dict(id=id,intervals=len(ds),positive_segments=len(ss),modes=sorted(set(modes)),mode_changes=modeChanges,latch_changes=latchChanges,on_changes=onChanges,off_changes=offChanges,max_slots_used=maxslots,terminal_inventory_MWh=float(E),maximum_usable_inventory_MWh=float(dec(p[1])-cutoff),unmet_MWh=float(tot['Unmet_Heat_MW']),unmet_delta_baseline_MWh=float(tot['Unmet_Heat_MW']-basetot['Unmet_Heat_MW']),unmet_delta_lossfirst_MWh=float(tot['Unmet_Heat_MW']-pairedtot['Unmet_Heat_MW']),max_first_law_residual_MWh=float(case_res)))
        z,x,p,h,control=active
        for name,col,delta in [('HP_nonmaximal',10,-.1),('TES_endpoint',4,1.),('unmet_credit',9,1.),('event_target',23,1.)]:
            bad=copy.deepcopy(z);bad[col]+=delta
            selfchecks.append(dict(name=name,passed=not all(physical(bad,x,p,h).values())))
        # A valid/invalid pair shows sensitivity to clock age, even when
        # conservation equations alone cannot identify the invalid restart.
        on=copy.deepcopy(z);on[3]=control[0];on[25]=1;on[10]=1
        selfchecks.append(dict(name='premature_restart',passed=dwell_transition(on,x,p,h,control,dec(control[2]),D(0),0) and not dwell_transition(on,x,p,h,control,dec(control[2])/2,D(0),0)))
        wrong=copy.deepcopy(spec['scenarios'][1]['policy']);wrong['min_off_h']=0
        selfchecks.append(dict(name='confounded_variant',passed={k for k in base if wrong[k]!=base[k]}!={'delivery_cutoff_C'}))
    for a in json.loads((folder/'preservation.json').read_text()):
        p=ROOT/a['path'];check('preservation',a['path'],p.stat().st_size==a['bytes'] and sha(p)==a['sha256'])
    for p in (folder/'source_snapshot').rglob('*'):
        if p.is_file():check('snapshot',p.relative_to(folder).as_posix(),sha(p)==sha(ROOT/p.relative_to(folder/'source_snapshot')))
    model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v51.slx'
    check('archive','snapshot_hash',sha(model)==sha(folder/'source_snapshot/matlab/simulink/DCHR_Dispatch_Stateflow_v51.slx'))
    with zipfile.ZipFile(model) as z:
        check('archive','CRC',z.testzip() is None)
        embedded=[e.text for name in z.namelist() if name.endswith('.xml') and 'stateflow' in name for e in ET.fromstring(z.read(name)).iter('P') if e.attrib.get('Name')=='script']
        for stem in ('stateflow_tes_endpoint_v51','stateflow_allocate_v51','stateflow_collect_v51','stateflow_choose_mode_v51','stateflow_contract_gate_v51','stateflow_supervisor_guard_v42','stateflow_clock_add_v42','stateflow_dwell_ready_v42'):
            source=(ROOT/'matlab/simulink'/(stem+'.m')).read_text().strip()
            check('archive_source_binding',stem,source in [s.strip() for s in embedded if s])
    receipts=[]
    for path in sorted((ROOT/'audit').glob('Stateflow_padding_execution_v51_*.json')):
        receipt=json.loads(path.read_text(encoding='utf-8-sig'))
        if folder.relative_to(ROOT).as_posix() in receipt['command'] and receipt['exit_code']==0:
            log=(ROOT/receipt['log_path']).read_text(encoding='utf-8-sig',errors='replace')
            check('execution',path.name,any(tag in log for tag in ['ANNUAL_SENSITIVITY_V51','MAT_REOPEN_V51 complete','PADDING_REPAIR_V51']))
            receipts.append(path.relative_to(ROOT).as_posix())
    check('execution','receipt',bool(receipts))
    verify_repair(folder,check,selfchecks)
    check('scope','all_annual_executed',total_intervals==9*8760 and r['summary']['completed_annual_scenarios']==9 and total_segments==r['summary']['positive_segments'])
    snap=folder/'qa_source'/stamp;snap.mkdir(parents=True)
    for file in [Path(__file__),ROOT/'audit/verify_annual_stateflow_v49.py',ROOT/'audit/verify_annual_dispatch_v48.py']:
        shutil.copyfile(file,snap/file.name)
    qa=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),evidence_class='SAME_AGENT_INDEPENDENT_ALGORITHMIC_QA_NOT_PHYSICAL_VALIDATION',actual_passed=sum(v['passed'] for v in checks),actual_failed=sum(not v['passed'] for v in checks),reviewer_selfchecks_passed=sum(v['passed'] for v in selfchecks),reviewer_selfchecks_failed=sum(not v['passed'] for v in selfchecks),saved_intervals=total_intervals,positive_segments=total_segments,max_independent_macro_residual_MWh=float(maxres),scenarios=scenarios,successful_receipts=receipts,breakdown=dict(collections.Counter(v['kind'] for v in checks)),checks=checks,reviewer_selfchecks=selfchecks)
    path=folder/('independent_QA_v51_'+stamp+'.json');path.write_text(json.dumps(qa,indent=2)+'\n')
    print(json.dumps({k:v for k,v in qa.items() if k not in ['checks','reviewer_selfchecks']},indent=2))
    if qa['actual_failed'] or qa['reviewer_selfchecks_failed']:
        print(json.dumps([v for v in checks if not v['passed']][:20],indent=2));raise SystemExit(1)


def exact_float(hex_value):
    return struct.unpack('>d',bytes.fromhex(hex_value))[0]

def verify_repair(folder,check,selfchecks):
    fixtures=json.loads((folder/'fixtures_v51.json').read_text())
    check('fixtures','all_six_modes',{int(v['dispatch'][0]) for v in fixtures}==set(range(6)))
    for item in fixtures + [json.loads((folder/(id+'_exact_seed_v51_evidence.json')).read_text()) for id in ('restart_49','on_05')]:
        c=item['case'];xs=c['inputs'];xs=xs if isinstance(xs[0],list) else [xs]
        segs=item['segments'];segs=segs if isinstance(segs[0],list) else [segs]
        for j,z in enumerate(segs):
            z=[float('nan') if v is None else v for v in z]
            for kind,ok in physical(z,xs[0],c['p'],c['h']).items():check('repair_'+kind,f'{item["id"]}_{j}',ok)
        starts=list(map(exact_float,item['start_hex']));ends=list(map(exact_float,item['endpoint_hex']))
        check('repair_binary',item['id'],all(a==b for a,b in zip(starts[1:],ends[:-1])) and all(0<=v<=c['p'][1] for v in starts+ends) and item['strict_padding_identity'] and item['exact_handoff'])
        if 'reference' in item:
            check('MATLAB_reference',item['id'],all(a is None and b is None or a is not None and b is not None and near(a,b) for k,(a,b) in enumerate(zip(item['dispatch'],item['reference'])) if k!=21))
    for id in ('restart_49','on_05'):
        old=json.loads((folder/(id+'_exact_seed_v42_evidence.json')).read_text())
        new=json.loads((folder/(id+'_exact_seed_v51_evidence.json')).read_text())
        check('exact_counterexample',id,old['expected_rejection'] and 'Zero-span segment has service.' in old['error_message'] and not new['error_message'] and new['padding_slots']>0)
    faults=json.loads((folder/'faults_v51.json').read_text())
    check('runtime_faults','all_observed',len(faults)==32 and all(v['rejected'] and v['phase']=='Execution' and v['error_message'] for v in faults))
    check('strict_padding_faults','ULP_endpoint_and_residual',all('Zero-span segment has service.' in v['error_message'] for v in faults if v['id'] in ('monitor_corruption_12','monitor_corruption_13')))
    assertions=json.loads((folder/'repair_assertions_v51.json').read_text())
    reviewed=json.loads((folder/'reference_review_v51.json').read_text())
    expected={id+'_independent_MATLAB_reference' for id in ('zero_demand','tes_discharge','boiler_limit','insufficient_heat')}
    check('repair_execution','original_diagnostic_mismatch_retained',{v['name'] for v in assertions if not v['passed']}==expected)
    check('repair_execution','reviewed_harness',reviewed['failed']==0 and all(v['passed'] for v in reviewed['corrected_assertions']) and all(v['shared_columns']==list(range(1,22))+list(range(23,26)) and v['passed'] for v in reviewed['reviews']))
    spec=json.loads((folder/'spec.json').read_text())
    for item in spec['scenarios']:
        id=item['id'];rows_=rows(folder/'binary_reopen'/(id+'_padding_identity.csv'))
        check('annual_padding',id,len(rows_)==8760 and all(int(v['Identity']) and int(v['EnergyHandoff']) and int(v['ClockIdentity']) and int(v['MacroMemory']) and int(v['Bounds']) for v in rows_))
        for v in rows_:
            state=[exact_float(v[k]) for k in ('PaddingStartHex','PaddingEndHex','PhysicalEndHex','MacroEndHex')]
            zero=[exact_float(v[k]) for k in ('ResidualMaxHex','ServiceMaxHex','ClockDeltaMaxHex')]
            check('annual_padding_binary',f'{id}_{v["Interval"]}',len(set(state))==1 and state[0]>=0 and int(v['PaddingSlots'])>0 and all(w==0 for w in zero))
    selfchecks.append(dict(name='one_ULP_padding_identity',passed=exact_float('4049000000000001')!=exact_float('4049000000000000')))

if __name__=='__main__':
    main()
