"""Independent saved-Stateflow port/ODE/event/clock/annual-report QA.

60-digit Decimal endpoint, closed-form HP quadratic and loss-first comparison.
Uses preserved independent v48 audit helpers, never production MATLAB/planner.
Independent algorithm/evidence QA by the same agent, not independent personnel.
"""
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal as D,localcontext
import collections,copy,csv,hashlib,json,math,shutil,sys,zipfile
from verify_annual_dispatch_v48 import maximal,endpoint,expected_row,near,dec
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def numeric(p):
    with p.open(newline='') as f:return [[float(v) for v in r] for r in csv.reader(f)]
def rows(p):
    with p.open(newline='') as f:return list(csv.DictReader(f))
def restart_ok(age,bound,E,c,Q):
    return dec(age)-dec(bound)>=dec(c[2]) and dec(E)<=dec(c[0])+D('1e-9') and Q>0
def physical(z,x,p,h):
    mode,t,offset,E,end=z[:5];direct,qc,qd,gas,unmet,Q,W,S=z[5:13]
    P=dec(p[4])*dec(qc)-dec(qd)/dec(p[5]);span=dec(t)
    nominal=min(dec(h[3]),dec(h[1])*(dec(x[2])+D('273.15'))/(dec(x[2])-dec(x[1]))) if h[5]==0 else min(dec(h[3]),dec(h[6])+dec(h[7])*(dec(x[2])-dec(x[1]))+dec(h[8])*(dec(x[2])-dec(x[1]))**2)
    want=maximal(x[0],z[13],h[0],nominal,h[4],h[2])
    wantmode=5 if unmet else 4 if gas else 3 if qd else 2 if qc else 1 if direct else 0
    law=dec(E)+(dec(S)+dec(W)+dec(gas)-dec(z[19]))*span-dec(end)-sum(map(dec,z[16:19]))
    return dict(ode=near(end,endpoint(E,P,p[6],t)),
        hp=near(Q,want) and near(Q,W+S) and (near(z[14],nominal*(1-dec(h[4])+dec(h[4])*dec(Q)/dec(h[0]))) if Q else math.isnan(z[14])) and S<=x[0]+1e-9,
        allocation=near(Q,direct+qc) and near(direct,min(x[3],Q)) and near(x[3],direct+qd+gas+unmet) and near(gas,min(p[10],max(0,x[3]-direct-qd))) and near(z[19],direct+qd+gas) and int(mode)==wantmode,
        bounds=min(E,end,direct,qc,qd,gas,unmet,Q,W,S)>=-1e-9 and max(E,end)<=p[1]+1e-9 and qc*qd==0 and qc<=p[2]+1e-9 and qd<=p[3]+1e-9 and gas<=p[10]+1e-9 and (not qd or min(E,end)>=p[7]-1e-9),
        loss=near(z[16],dec(E)+P*span-dec(end)) and near(z[17],(1-dec(p[4]))*dec(qc)*span) and near(z[18],(1/dec(p[5])-1)*dec(qd)*span),
        balance=abs(law)<D('2e-9') and near(z[20],law),
        temperature=near(z[21],dec(p[9])+dec(E)/dec(p[8])) and near(z[22],dec(p[9])+dec(end)/dec(p[8])),
        event=(int(z[23]) in range(5)) and (int(z[23])!=1 or near(end,p[1])) and (int(z[23])!=2 or near(end,p[7])))
def main():
    folder=(ROOT/Path(sys.argv[1])).resolve();assert folder.is_relative_to(ROOT/'results')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');checks=[];selfchecks=[]
    def check(kind,name,ok):checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    report=json.loads((folder/'annual_stateflow_v49.json').read_text());spec=json.loads((folder/'spec.json').read_text())
    check('execution','harness',report['summary']['harness_failed']==0 and all(v['passed'] for v in report['assertions']))
    check('execution','normal_actual_license',report['metadata']['simulation_mode']=='normal' and report['metadata']['stateflow_license_test']==1)
    check('MAT','report',json.loads((folder/'mat_reopen/report.json').read_text())==report)
    for p in folder.glob('*.csv'):check('MAT',p.name,sha(p)==sha(folder/'mat_reopen'/p.name))
    inputs=numeric(folder/'annual_inputs.csv');paired=rows(folder/'paired_loss_first_v48.csv')
    fixed=rows(folder/'fixed_preflight.csv');scheduled=rows(folder/'scheduled_preflight.csv');policy=spec['policy']
    check('scope','full_year',len(inputs)==len(fixed)==len(scheduled)==len(paired)==8760 and report['summary']['annual_stateflow_executed'])
    check('scope','preserved_release',report['summary']['model_version']=='0.42' and report['summary']['new_model'] is False)
    transitions=0;annual_modes=set();all_modes=set();max_res=D(0);positive=0;intervals=0;actual_dwell_transitions=0
    with localcontext() as ctx:
        ctx.prec=60
        cfg=report['cfg'];previous=D(0);pairedtot=collections.defaultdict(lambda:D(0))
        for i,(x,b,f,s) in enumerate(zip(inputs,paired,fixed,scheduled)):
            # Re-derive original seasonal schedule and demand from generated Tout.
            tout=dec(b['Tout_C']);dh=cfg['dh'];frac=max(D(0),min(D(1),(dec(dh['temperature_balance_C'])-tout)/(dec(dh['temperature_balance_C'])-dec(dh['design_outdoor_temp_C']))))
            delivery=dec(dh['supply_min_C'])+frac*(dec(dh['supply_max_C'])-dec(dh['supply_min_C']))
            shape=max(D(0),min(D('1.15'),(dec(dh['balance_temp_C'])-tout)/(dec(dh['balance_temp_C'])-dec(dh['design_outdoor_temp_C']))))
            demand=(dec(dh['base_hot_water_MW'])+dec(dh['space_heat_design_MW'])*shape)/dec(dh['network_efficiency'])
            source=min(dec(b['IT_MW'])*dec(cfg['dc']['recovery_fraction'])*dec(cfg['hx']['effectiveness']),dec(cfg['hx']['max_heat_MW']))
            expected_input=[source,dec(cfg['dc']['source_temp_C'])-dec(cfg['hx']['approach_K']),dec(policy['condenser_C']),demand,delivery]
            admissible=delivery<=dec(policy['delivery_cutoff_C']) and dec(policy['condenser_C'])>=dec(policy['max_temperature_C'])
            original_ok=delivery>=dec(policy['max_temperature_C']) and delivery<=dec(policy['delivery_cutoff_C'])
            check('adapter_equations',str(i),all(near(v,e) for v,e in zip(x,expected_input)))
            check('preflight',str(i),int(f['Admissible'])==int(admissible)==1 and int(s['Admissible'])==int(original_ok)==0 and bool(s['Error_ID']))
            expected,_=expected_row(b,report['paired_cfg'],previous)
            check('paired_annual_equations',str(i),all(near(b[k],v) for k,v in expected.items()))
            previous=expected['Storage_E_Next_MWh']
            for key in ['Heat_Demand_MW','HP_Direct_MW','Storage_Charge_MW','Storage_Discharge_MW','Gas_Heat_MW','Unmet_Heat_MW','HP_Heat_MW','HP_Electric_MW']:pairedtot[key]+=dec(b[key])*dec(cfg['sim']['dt_h'])
        active=None
        for item in report['stateflow']:
            c=item['case'];id=item['id'];p,h,control=c['p'],c['h'],c['c'];xs=c['inputs'];xs=[xs] if not isinstance(xs[0],list) else xs
            ds=numeric(folder/(id+'_dispatch.csv'));ss=numeric(folder/(id+'_segments.csv'));starts=numeric(folder/(id+'_clock_start.csv'));ends=numeric(folder/(id+'_clock_end.csv'))
            indexed=collections.defaultdict(list)
            for z in ss:indexed[int(z[0])-1].append(z[2:])
            check('shape',id,len(ds)==len(starts)==len(ends)==len(xs)==item['intervals'] and len(ss)==item['positive_segments'])
            E=dec(c['initial_energy_MWh']);clock=c['initial_clock'];exact_age=dec(clock[1])+dec(clock[2]);tot=collections.defaultdict(lambda:D(0));modes=[]
            for i,row in enumerate(ds):
                segs=indexed[i];span_sum=D(0);integrals=[D(0)]*8;loss=[D(0)]*3;startE=E
                check('clock_handoff',f'{id}_{i}',all(near(v,w) for v,w in zip(starts[i],clock)))
                latch=int(starts[i][0]);bound=max(dec(starts[i][3]),dec(ends[i][3]))
                for j,z in enumerate(segs):
                    positive+=1;mode,span,offset,start,end=z[:5];t=dec(span)
                    check('segment_schedule',f'{id}_{i}_{j}',span>0 and near(offset,span_sum) and near(start,E))
                    for kind,ok in physical(z,xs[i],p,h).items():check('segment_'+kind,f'{id}_{i}_{j}',ok)
                    new_latch=int(z[25]);before=exact_age
                    if new_latch!=latch:
                        # Physical duration is summed in Decimal independently of
                        # production compensated addition. No tolerance grants dwell.
                        if new_latch==1:
                            valid=restart_ok(before,bound,start,control,z[10])
                        else:
                            cap_stop=near(start,p[1]) and before-bound>=dec(control[1])
                            # Safety OFF is legitimate if a demand+charge HP is unavailable.
                            x=xs[i];nom=min(dec(h[3]),dec(h[1])*(dec(x[2])+D('273.15'))/(dec(x[2])-dec(x[1]))) if h[5]==0 else dec(h[6])+dec(h[7])*(dec(x[2])-dec(x[1]))+dec(h[8])*(dec(x[2])-dec(x[1]))**2
                            high=maximal(x[0],x[3]+p[2],h[0],nom,h[4],h[2]);valid=cap_stop or high==0
                        check('certified_dwell',f'{id}_{i}_{j}',valid);actual_dwell_transitions+=1;exact_age=D(0)
                    check('clock_age',f'{id}_{i}_{j}',near(z[26],exact_age) and near(z[27],exact_age+t) and new_latch in [0,1] and ((new_latch==0 and z[10]==0) or (new_latch==1 and z[10]>0)))
                    exact_age+=t;latch=new_latch;E=dec(end);span_sum+=t;all_modes.add(int(mode));modes.append(int(mode))
                    for k,v in enumerate(z[5:13]):integrals[k]+=dec(v)*t
                    for k,v in enumerate(z[16:19]):loss[k]+=dec(v)
                    if active is None and z[10]>0:active=(z,xs[i],p,h,control)
                observed=[row[1],row[2],row[3],row[4],row[5],row[18],row[19],row[20]]
                check('aggregate',f'{id}_{i}',near(span_sum,p[0]) and near(row[7],E) and all(near(v,integrals[k]/dec(p[0])) for k,v in enumerate(observed)) and all(near(v,w) for v,w in zip(row[8:11],loss)))
                delivered=integrals[0]+integrals[2]+integrals[3]
                residual=startE+integrals[6]+integrals[7]+integrals[3]-delivered-E-sum(loss);max_res=max(max_res,abs(residual))
                check('macro_first_law',f'{id}_{i}',abs(residual)<D('2e-9') and near(row[12],residual) and near(row[17],xs[i][3]))
                check('clock_enclosure',f'{id}_{i}',int(ends[i][0])==latch and abs(dec(ends[i][1])+dec(ends[i][2])-exact_age)<=dec(ends[i][3])+D('5e-12') and ends[i][3]>=0 and abs(ends[i][2])+ends[i][3]<=1e-8)
                clock=ends[i]
                for key,val in zip(['HP_Direct_MW','Storage_Charge_MW','Storage_Discharge_MW','Gas_Heat_MW','Unmet_Heat_MW','HP_Heat_MW','HP_Electric_MW'],integrals[:7]):tot[key]+=val
                tot['Heat_Demand_MW']+=dec(xs[i][3])*dec(p[0])
            intervals+=len(ds)
            verify_report(check,id,item['report'],tot,cfg)
            if id=='annual_8760h':
                annual_modes=set(modes);transitions=sum(v!=w for v,w in zip(modes,modes[1:]));check('annual','duration',len(ds)==8760 and item['report']['energy']['reported_period_h']==8760)
                cold=numeric(folder/'cold_72h_dispatch.csv');check('annual','cold_prefix',all(near(v,w) or math.isnan(v) and math.isnan(w) for r,s in zip(ds[:72],cold) for v,w in zip(r,s)))
                check('annual','input_equality',len(xs)==len(inputs) and all(near(v,w) for r,s in zip(xs,inputs) for v,w in zip(r,s)));annual_tot=tot
        verify_report(check,'paired_loss_first_v48',report['paired_report'],pairedtot,cfg)
        check('modes','six_executed',all_modes==set(range(6)))
        check('annual','real_transitions',transitions>0 and actual_dwell_transitions>0)
        z,x,p,h,control=active
        for name,col,delta in [('HP_nonmaximal',10,-.1),('TES_endpoint',4,1),('service_credit',9,1),('event_target',23,1)]:
            bad=copy.deepcopy(z);bad[col]+=delta
            selfchecks.append(dict(name=name,passed=not all(physical(bad,x,p,h).values())))
        cc=[policy['restart_energy_MWh'],policy['min_on_h'],policy['min_off_h'],64]
        selfchecks.append(dict(name='premature_restart',passed=restart_ok(.25,0,cc[0],cc,1) and not restart_ok(.1,0,cc[0],cc,1)))
    for f in report['faults']:check('domain',str(f['index']),f['rejected'] and bool(f['error_id'] or f['message']))
    for a in json.loads((folder/'preservation.json').read_text()):
        p=ROOT/a['path'];check('preservation',a['path'],p.stat().st_size==a['bytes'] and sha(p)==a['sha256'])
    revisions=json.loads((folder/'snapshot_revisions_v49.json').read_text())
    for p in (folder/'source_snapshot').rglob('*'):
        if p.is_file():
            rel=p.relative_to(folder/'source_snapshot').as_posix();revision=revisions.get(rel)
            ok=sha(p)==sha(ROOT/rel)
            if revision:
                ok=rel.endswith('.md') and rel.startswith('audit/') and sha(p)==revision['initial_snapshot_sha256'] and sha(ROOT/rel)==revision['final_sha256'] and bool(revision['reason'])
            check('snapshot',p.relative_to(folder).as_posix(),ok)
    model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx';check('archive','accepted_hash',sha(model)==json.loads((ROOT/'STATUS_stateflow_v42.json').read_text())['model_sha256'])
    with zipfile.ZipFile(model) as z:check('archive','CRC',z.testzip() is None)
    receipts=[]
    for path in sorted((ROOT/'audit').glob('Annual_stateflow_execution_v49_*.json')):
        r=json.loads(path.read_text(encoding='utf-8-sig'))
        if folder.relative_to(ROOT).as_posix() in r['command'] and r['exit_code']==0:
            log=(ROOT/r['log_path']).read_text(encoding='utf-8-sig',errors='replace');check('execution',path.name,'ANNUAL_STATEFLOW_V49' in log and 'MAT_REOPEN_V49 complete' in log);receipts.append(path.relative_to(ROOT).as_posix())
    check('execution','receipt',bool(receipts))
    snap=folder/'qa_source'/stamp;snap.mkdir(parents=True)
    for file in [Path(__file__),ROOT/'audit/verify_annual_dispatch_v48.py']:shutil.copyfile(file,snap/file.name)
    deltas={k:float(annual_tot[k]-pairedtot[k]) for k in annual_tot}
    qa=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),evidence_class='SAME_AGENT_INDEPENDENT_ALGORITHMIC_QA_NOT_PHYSICAL_VALIDATION',
        actual_passed=sum(x['passed'] for x in checks),actual_failed=sum(not x['passed'] for x in checks),
        reviewer_selfchecks_passed=sum(x['passed'] for x in selfchecks),reviewer_selfchecks_failed=sum(not x['passed'] for x in selfchecks),
        saved_intervals=intervals,positive_segments=positive,annual_modes=sorted(annual_modes),annual_mode_transitions=transitions,
        actual_latch_transitions=actual_dwell_transitions,max_independent_macro_residual_MWh=float(max_res),
        joint_policy_delta_MWh=deltas,successful_receipts=receipts,breakdown=dict(collections.Counter(x['kind'] for x in checks)),checks=checks,reviewer_selfchecks=selfchecks)
    path=folder/('independent_QA_v49_'+stamp+'.json');path.write_text(json.dumps(qa,indent=2)+'\n')
    print(json.dumps({k:v for k,v in qa.items() if k not in ['checks','reviewer_selfchecks']},indent=2))
    if qa['actual_failed'] or qa['reviewer_selfchecks_failed']:
        print(json.dumps([x for x in checks if not x['passed']][:20],indent=2));raise SystemExit(1)
def verify_report(check,id,m,tot,cfg):
    mapping={'heat_demand_MWh':'Heat_Demand_MW','hp_direct_MWh':'HP_Direct_MW','storage_charge_MWh':'Storage_Charge_MW','storage_discharge_MWh':'Storage_Discharge_MW','gas_heat_MWh':'Gas_Heat_MW','unmet_heat_MWh':'Unmet_Heat_MW','hp_heat_MWh':'HP_Heat_MW','hp_electric_MWh':'HP_Electric_MW'}
    check('energy_report',id,all(near(m['energy'][k],tot[v]) for k,v in mapping.items()))
    if tot['HP_Electric_MW']>0:check('COP_report',id,near(m['energy']['hp_heating_COP_integrated'],tot['HP_Heat_MW']/tot['HP_Electric_MW']))
    eta=dec(cfg['backup']['gas_boiler_efficiency']);ec=cfg['econ'];delivered=tot['Heat_Demand_MW']-tot['Unmet_Heat_MW'];gas=tot['Gas_Heat_MW'];work=tot['HP_Electric_MW']
    cost=(delivered-gas)/eta*dec(ec['gas_EUR_per_MWh_fuel'])-work*dec(ec['electricity_EUR_per_MWh']);co2=(delivered-gas)/eta*dec(ec['gas_tCO2_per_MWh_fuel'])-work*dec(ec['grid_tCO2_per_MWh'])
    check('service_report',id,near(m['equal_delivered_service_opex_difference_EUR'],cost) and near(m['equal_delivered_service_CO2_difference_t'],co2))
if __name__=='__main__':main()
