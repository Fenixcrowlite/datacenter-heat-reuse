"""Independent 60-digit closed-form HP and inventory/evidence QA.
No production MATLAB/Python dispatch imports. Same-agent algorithmic QA only.
"""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal as D, localcontext
import collections, copy, csv, hashlib, json, math, shutil, sys, zipfile
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dec(x):return D(str(x))
def near(a,b):
    return math.isfinite(float(a)) and abs(dec(a)-dec(b))<=D('4e-11')*max(D(1),abs(dec(b)))
def rows(p):
    with p.open(newline='') as f:return list(csv.DictReader(f))
def numeric(p):
    with p.open(newline='') as f:return [[float(x) for x in r] for r in csv.reader(f)]
def maximal(S,R,H,C0,r,Cmin):
    S,R,H,C0,r,Cmin=map(dec,[S,R,H,C0,r,Cmin])
    if S==0 or R==0 or H==0 or C0<Cmin:return D(0)
    a=C0*(1-r);b=C0*r/H
    low=max(D(0),(Cmin-a)/b) if b else D(0)
    upper=min(R,H)
    if low>upper or low*(1-1/(a+b*low))>S:return D(0)
    if b==0:root=S*a/(a-1)
    else:
        B=a-1-b*S;disc=(B*B+4*b*a*S).sqrt()
        root=2*a*S/(B+disc) if B>=0 else (-B+disc)/(2*b)
    return min(upper,root)
def endpoint(E,P,k,t):
    E,P,k,t=map(dec,[E,P,k,t]);return E+P*t if k==0 else (E+P*((k*t).exp()-1)/k)/(k*t).exp()
def expected_row(a,cfg,previous):
    hp=cfg['hp'];s=cfg['storage'];dt=dec(cfg['sim']['dt_h']);H=dec(hp['max_heat_output_MW']);r=dec(hp['part_load_penalty'])
    src=dec(cfg['dc']['source_temp_C']);S=dec(a['IT_MW'])*dec(cfg['dc']['recovery_fraction'])
    if cfg['hx']['enabled']:
        S=min(S*dec(cfg['hx']['effectiveness']),dec(cfg['hx']['max_heat_MW']));src-=dec(cfg['hx']['approach_K'])
    dh=cfg['dh'];tout=dec(a['Tout_C'])
    f=max(D(0),min(D('1.15'),(dec(dh['balance_temp_C'])-tout)/(dec(dh['balance_temp_C'])-dec(dh['design_outdoor_temp_C']))))
    demand=(dec(dh['base_hot_water_MW'])+dec(dh['space_heat_design_MW'])*f)/dec(dh['network_efficiency'])
    if cfg['model']['dh_temperature']=='fixed':sink=dec(hp['supply_temp_C'])
    else:
        f=max(D(0),min(D(1),(dec(dh['temperature_balance_C'])-tout)/(dec(dh['temperature_balance_C'])-dec(dh['design_outdoor_temp_C']))))
        sink=dec(dh['supply_min_C'])+f*(dec(dh['supply_max_C'])-dec(dh['supply_min_C']))
    nominal=min(dec(hp['cop_max']),dec(hp['carnot_efficiency'])*(sink+D('273.15'))/(sink-src))
    retained=previous*(1-dec(s['loss_fraction_per_h'])*dt)
    room=max(D(0),(dec(s['capacity_MWh'])-retained)/(dec(s['eta_charge'])*dt))
    request=demand+min(dec(s['charge_limit_MW']),room)
    q=maximal(S,request,H,nominal,r,hp['cop_min']);cop=nominal*(1-r+r*q/H) if H else nominal
    work=q/cop if q else D(0);evap=q-work;direct=min(q,demand)
    charge=min(max(D(0),q-demand),dec(s['charge_limit_MW']),room) if dec(s['capacity_MWh'])>0 else D(0)
    discharge=min(max(D(0),demand-q),dec(s['discharge_limit_MW']),retained*dec(s['eta_discharge'])/dt) if dec(s['capacity_MWh'])>0 else D(0)
    end=retained+dec(s['eta_charge'])*charge*dt-discharge*dt/dec(s['eta_discharge'])
    gas=min(max(D(0),demand-direct-discharge),dec(cfg['backup']['max_heat_MW']));unmet=max(D(0),demand-direct-discharge-gas)
    return dict(Heat_Demand_MW=demand,DH_Supply_C=sink,HP_Source_C=src,HX_Heat_to_HP_MW=S,
        COP_Nominal=nominal,HP_Request_MW=request,HP_Heat_MW=q,HP_Electric_MW=work,HP_Source_Used_MW=evap,
        HP_Direct_MW=direct,Storage_Charge_MW=charge,Storage_Discharge_MW=discharge,Gas_Heat_MW=gas,Unmet_Heat_MW=unmet,
        Storage_E_MWh=previous,Storage_E_Next_MWh=end,Storage_Standing_Loss_MWh=previous-retained,
        Storage_Conversion_Loss_MWh=((1-dec(s['eta_charge']))*charge+(1/dec(s['eta_discharge'])-1)*discharge)*dt),cop
def main():
    folder=(ROOT/Path(sys.argv[1])).resolve();assert folder.is_relative_to(ROOT/'results')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');checks=[];selfchecks=[]
    def check(kind,name,ok):checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    report=json.loads((folder/'annual_dispatch_v48.json').read_text());spec=json.loads((folder/'spec.json').read_text())
    check('execution','harness',report['summary']['harness_failed']==0 and all(x['passed'] for x in report['assertions']))
    check('execution','actual_normal_Stateflow',report['metadata']['stateflow_license_test']==1 and report['metadata']['simulation_mode']=='normal')
    check('scope','annual_not_Stateflow',report['summary']['model_version']=='0.42' and not report['summary']['new_model'])
    check('MAT','report',json.loads((folder/'mat_reopen/report.json').read_text())==report)
    for p in folder.glob('*.csv'):check('MAT',p.name,sha(p)==sha(folder/'mat_reopen'/p.name))
    deltas=[];nonmaximal=0;maxres=D(0);actual_total=0;active_fixture=None
    with localcontext() as ctx:
        ctx.prec=60
        for item in report['annual']+report['fixtures']:
            cfg=item['cfg'];s=cfg['storage'];dt=dec(cfg['sim']['dt_h']);id=item['id']
            data=rows(folder/(id+'.csv'));legacy=rows(folder/(id+'_legacy.csv'))
            previous=dec(s['initial_soc'])*dec(s['capacity_MWh']);tot=collections.defaultdict(lambda:D(0))
            check('shape',id,len(data)==len(legacy)==(8760 if id.startswith('annual') else 3))
            actual_total+=len(data)
            for i,a in enumerate(data):
                expected,cop=expected_row(a,cfg,previous)
                check('annual_equations',f'{id}_{i}',all(near(a[k],v) for k,v in expected.items()))
                q=dec(a['HP_Heat_MW']);Qe=dec(a['HP_Source_Used_MW']);W=dec(a['HP_Electric_MW']);E=dec(a['Storage_E_MWh']);end=dec(a['Storage_E_Next_MWh'])
                delivered=dec(a['HP_Direct_MW'])+dec(a['Storage_Discharge_MW'])+dec(a['Gas_Heat_MW'])
                residual=E+(Qe+W+dec(a['Gas_Heat_MW'])-delivered)*dt-end-dec(a['Storage_Standing_Loss_MWh'])-dec(a['Storage_Conversion_Loss_MWh'])
                maxres=max(maxres,abs(residual));nonmaximal+=int(abs(q-expected['HP_Heat_MW'])>D('1e-8'))
                check('annual_balance',f'{id}_{i}',abs(residual)<D('1e-9') and near(a['First_Law_Residual_MWh'],residual) and near(q,W+Qe))
                check('annual_bounds',f'{id}_{i}',min(Qe,W,q,end)>=D('-1e-10') and end<=dec(s['capacity_MWh'])+D('1e-10') and Qe<=dec(a['HX_Heat_to_HP_MW'])+D('1e-10') and dec(a['Storage_Charge_MW'])*dec(a['Storage_Discharge_MW'])==0 and (near(a['COP'],cop) if q else math.isnan(float(a['COP']))))
                previous=expected['Storage_E_Next_MWh']
                for field in ['Heat_Demand_MW','HP_Direct_MW','Storage_Charge_MW','Storage_Discharge_MW','Gas_Heat_MW','Unmet_Heat_MW','HP_Heat_MW','HP_Electric_MW']:tot[field]+=dec(a[field])*dt
                if id.startswith('annual'):
                    b=legacy[i];nom=dec(a['COP_Nominal']);potential=min(dec(cfg['hp']['max_heat_output_MW']),dec(a['HX_Heat_to_HP_MW'])*nom/(nom-1))
                    bE=dec(b['Storage_E_MWh']);bret=bE*(1-dec(s['loss_fraction_per_h'])*dt);room=max(D(0),(dec(s['capacity_MWh'])-bret)/(dec(s['eta_charge'])*dt))
                    bq=min(potential,dec(b['Heat_Demand_MW'])+min(dec(s['charge_limit_MW']),room));bcop=max(dec(cfg['hp']['cop_min']),nom*(1-dec(cfg['hp']['part_load_penalty'])+dec(cfg['hp']['part_load_penalty'])*bq/dec(cfg['hp']['max_heat_output_MW'])))
                    check('legacy_baseline',f'{id}_{i}',near(b['HP_Heat_Used_MW'],bq) and near(b['HP_Electric_MW'],bq/bcop) and near(b['Heat_Demand_MW'],dec(b['HP_Heat_Used_MW'])-dec(b['Storage_Charge_MW'])+dec(b['Storage_Discharge_MW'])+dec(b['Gas_Heat_MW'])+dec(b['Unmet_Heat_MW'])))
            if 'report' in item:
                m=item['report'];e=m['energy'];mapping={'heat_demand_MWh':'Heat_Demand_MW','hp_direct_MWh':'HP_Direct_MW','storage_charge_MWh':'Storage_Charge_MW','storage_discharge_MWh':'Storage_Discharge_MW','gas_heat_MWh':'Gas_Heat_MW','unmet_heat_MWh':'Unmet_Heat_MW','hp_heat_MWh':'HP_Heat_MW','hp_electric_MWh':'HP_Electric_MW'}
                check('energy_report',id,all(near(e[k],tot[v]) for k,v in mapping.items()) and near(e['hp_heating_COP_integrated'],tot['HP_Heat_MW']/tot['HP_Electric_MW']))
                eta=dec(cfg['backup']['gas_boiler_efficiency']);ec=cfg['econ'];delivered=tot['Heat_Demand_MW']-tot['Unmet_Heat_MW'];gas=tot['Gas_Heat_MW'];work=tot['HP_Electric_MW']
                cost=(delivered-gas)/eta*dec(ec['gas_EUR_per_MWh_fuel'])-work*dec(ec['electricity_EUR_per_MWh']);co2=(delivered-gas)/eta*dec(ec['gas_tCO2_per_MWh_fuel'])-work*dec(ec['grid_tCO2_per_MWh'])
                check('service_report',id,near(m['equal_delivered_service_opex_difference_EUR'],cost) and near(m['equal_delivered_service_CO2_difference_t'],co2) and near(item['terminal_inventory_MWh'],previous))
                lm=item['legacy_report'];le=lm['energy']
                check('legacy_report',id,near(le['unmet_heat_MWh'],sum(dec(b['Unmet_Heat_MW'])*dt for b in legacy)) and near(le['gas_heat_MWh'],sum(dec(b['Gas_Heat_MW'])*dt for b in legacy)))
                deltas.append(dict(id=id,delivered_heat_delta_MWh=float(tot['Heat_Demand_MW']-tot['Unmet_Heat_MW']-dec(le['total_delivered_MWh'])),unmet_reduction_MWh=float(dec(le['unmet_heat_MWh'])-tot['Unmet_Heat_MW']),gas_heat_reduction_MWh=float(dec(le['gas_heat_MWh'])-tot['Gas_Heat_MW']),HP_heat_delta_MWh=float(tot['HP_Heat_MW']-dec(le['hp_heat_MWh'])),HP_electric_delta_MWh=float(tot['HP_Electric_MW']-dec(le['hp_electric_MWh'])),opex_difference_delta_EUR=float(cost-dec(lm['equal_delivered_service_opex_difference_EUR'])),CO2_difference_delta_t=float(co2-dec(lm['equal_delivered_service_CO2_difference_t']))))
            if id=='matched_source_limited':active_fixture=(data[0],cfg)
        check('annual_maximality','zero_nonmaximal',nonmaximal==0)
        modes=set();transition_count=0;saved_intervals=0
        for item in report['stateflow']:
            c=item['case'];id=item['id'];p=c['p'];h=c['h'];x=c['inputs'];x=[x] if not isinstance(x[0],list) else x
            ds=numeric(folder/(id+'_dispatch.csv'));segs=numeric(folder/(id+'_segments.csv'));saved_intervals+=len(ds);E=dec(c['initial_energy_MWh'])
            check('stateflow_execution',id,item['error_message']=='' and len(ds)==item['intervals']==len(x))
            for i,row in enumerate(ds):
                selected=[z[2:] for z in segs if int(z[0])==i+1];span_sum=D(0);integrals=[D(0)]*8
                for j,z in enumerate(selected):
                    mode,span,offset,start,end=z[:5];direct,qc,qd,gas,unmet,Q,W,source=z[5:13];modes.add(int(mode));P=dec(p[4])*dec(qc)-dec(qd)/dec(p[5]);t=dec(span)
                    check('stateflow_ODE',f'{id}_{i}_{j}',near(start,E) and near(end,endpoint(start,P,p[6],span)) and near(offset,span_sum));E=dec(end);span_sum+=t
                    check('stateflow_ports',f'{id}_{i}_{j}',near(Q,W+source) and near(Q,direct+qc) and near(x[i][3],direct+qd+gas+unmet) and source<=x[i][0]+1e-10 and min(start,end,*z[5:13])>=-1e-10 and max(start,end)<=p[1]+1e-10 and qc*qd==0 and qc<=p[2]+1e-10 and qd<=p[3]+1e-10 and gas<=p[10]+1e-10)
                    wantmode=5 if unmet>0 else 4 if gas>0 else 3 if qd>0 else 2 if qc>0 else 1 if direct>0 else 0
                    residual=dec(start)+(dec(source)+dec(W)+dec(gas)-dec(z[19]))*t-dec(end)-sum(map(dec,z[16:19]))
                    check('stateflow_balance',f'{id}_{i}_{j}',int(mode)==wantmode and abs(residual)<D('1e-9') and near(z[16],dec(start)+P*t-dec(end)))
                    for k,v in enumerate(z[5:13]):integrals[k]+=dec(v)*t
                observed=[row[1],row[2],row[3],row[4],row[5],row[18],row[19],row[20]]
                check('stateflow_aggregate',f'{id}_{i}',near(span_sum,p[0]) and near(row[7],E) and all(near(v,integrals[k]/dec(p[0])) for k,v in enumerate(observed)))
            if id.startswith('matched'):
                data=rows(folder/(id+'.csv'));fields=['HP_Heat_MW','HP_Electric_MW','HP_Source_Used_MW','HP_Direct_MW','Gas_Heat_MW','Unmet_Heat_MW'];cols=[18,19,20,1,4,5]
                check('matched_actual',id,all(near(d[col],a[f]) for d,a in zip(ds,data) for col,f in zip(cols,fields)))
            if id==spec['period']['id']:
                sequence=[int(z[2]) for z in segs];transition_count=sum(a!=b for a,b in zip(sequence,sequence[1:]));check('transitions',id,transition_count>=6 and set(sequence)==set(range(6)))
        check('stateflow_modes','six',modes==set(range(6)))
    for fault in report['faults']:check('domain',str(fault['index']),fault['rejected'] and bool(fault['error_id']))
    for a in json.loads((folder/'preservation.json').read_text()):
        p=ROOT/a['path'];check('preservation',a['path'],p.stat().st_size==a['bytes'] and sha(p)==a['sha256'])
    for p in (folder/'source_snapshot').rglob('*'):
        if p.is_file():check('snapshot',p.relative_to(folder).as_posix(),sha(p)==sha(ROOT/p.relative_to(folder/'source_snapshot')))
    model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx'
    check('archive','accepted_hash',sha(model)==json.loads((ROOT/'STATUS_stateflow_v42.json').read_text())['model_sha256'])
    with zipfile.ZipFile(model) as z:check('archive','CRC',z.testzip() is None)
    receipts=[]
    for path in sorted((ROOT/'audit').glob('Annual_dispatch_execution_v48_*.json')):
        r=json.loads(path.read_text(encoding='utf-8-sig'))
        if folder.relative_to(ROOT).as_posix() in r['command'] and r['exit_code']==0:
            log=(ROOT/r['log_path']).read_text(encoding='utf-8-sig',errors='replace');check('execution',path.name,'ANNUAL_DISPATCH_V48' in log and 'MAT_REOPEN_V48 complete' in log);receipts.append(path.relative_to(ROOT).as_posix())
    check('execution','receipt',bool(receipts))
    a,cfg=active_fixture
    with localcontext() as ctx:
        ctx.prec=60
        for name,field,delta in [('nonmaximal','HP_Heat_MW',-.1),('source_overdraw','HP_Source_Used_MW',2),('inventory','Storage_E_Next_MWh',1),('unmet','Unmet_Heat_MW',1)]:
            bad=copy.deepcopy(a);bad[field]=str(dec(a[field])+dec(delta));e,_=expected_row(bad,cfg,D(0));selfchecks.append(dict(name=name,passed=not all(near(bad[k],v) for k,v in e.items())))
    snap=folder/'qa_source'/stamp;snap.mkdir(parents=True);shutil.copyfile(__file__,snap/Path(__file__).name)
    qa=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),evidence_class='SAME_AGENT_INDEPENDENT_DECIMAL_NOT_PHYSICAL_VALIDATION',actual_passed=sum(x['passed'] for x in checks),actual_failed=sum(not x['passed'] for x in checks),reviewer_selfchecks_passed=sum(x['passed'] for x in selfchecks),reviewer_selfchecks_failed=sum(not x['passed'] for x in selfchecks),actual_intervals=actual_total,saved_Stateflow_intervals=saved_intervals,annual_nonmaximal_intervals=nonmaximal,max_independent_first_law_residual_MWh=float(maxres),actual_period_mode_transitions=transition_count,deltas=deltas,successful_receipts=receipts,breakdown=dict(collections.Counter(x['kind'] for x in checks)),checks=checks,reviewer_selfchecks=selfchecks)
    path=folder/('independent_QA_v48_'+stamp+'.json');path.write_text(json.dumps(qa,indent=2)+'\n')
    print(json.dumps({k:v for k,v in qa.items() if k not in ['checks','reviewer_selfchecks']},indent=2))
    if qa['actual_failed'] or qa['reviewer_selfchecks_failed']:
        print(json.dumps([x for x in checks if not x['passed']][:20],indent=2));raise SystemExit(1)
if __name__=='__main__':main()
