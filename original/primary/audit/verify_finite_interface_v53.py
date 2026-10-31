"""Independent 70-digit finite-boundary, actual Stateflow port/ODE and evidence QA.
No production imports. Same-agent algorithmic review, not independent personnel.
"""
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal as D,localcontext
import copy,hashlib,json,math,sys,zipfile
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dec(x):return D.from_float(x) if isinstance(x,float) else D(x)
def near(a,b):return a is not None and math.isfinite(float(a)) and abs(dec(a)-dec(b))<=D('2e-12')*max(D(1),abs(dec(b)))
def matrix(v):return [v] if v and not isinstance(v[0],list) else v
def expected(s):
    s={k:dec(v) for k,v in s.items()};out=s['source_in_C']-s['source_glide_K'];evap=out-s['evaporator_approach_K']
    hot=max(s['tank_max_C']+s['charge_approach_K'],s['delivery_C']+s['direct_approach_K'])
    cond=hot+s['condenser_approach_K'];tl=evap+D('273.15');th=cond+D('273.15');lift=th-tl
    eer=s['cooling_factor']*tl/lift;cop=1+eer;source=s['source_capacity_MW_per_K']*s['source_glide_K']
    hotbudget=s['hot_capacity_MW_per_K']*(hot-s['hot_in_C']);cap=min(s['hp_capacity_MW'],hotbudget)
    q=min(cap,source*cop/eer);w=q/cop;ql=q-w;aux=s['aux_per_compressor']*w
    return dict(source_out_C=out,evaporator_C=evap,condenser_C=cond,hot_out_C=hot,
        cutoff_C=s['delivery_C']+s['discharge_approach_K'],TL_K=tl,TH_K=th,lift_K=lift,
        eer_compressor=eer,cop_compressor=cop,heating_factor=(lift+s['cooling_factor']*tl)/th,
        source_budget_MW=source,hot_budget_MW=hotbudget,hp_capacity_MW=cap,rated_heat_MW=q,
        rated_source_MW=ql,rated_compressor_MW=w,rated_aux_MW=aux,
        rated_counted_heat_MW=q+s['aux_hot_fraction']*aux,rated_aux_rejected_MW=(1-s['aux_hot_fraction'])*aux,
        rated_system_cop=(q+s['aux_hot_fraction']*aux)/(w+aux) if w+aux else None,
        required_source_capacity_MW_per_K=ql/s['source_glide_K'],required_hot_capacity_MW_per_K=q/(hot-s['hot_in_C']))
def segment_checks(z,x,p,h,s):
    mode,t,offset,A,B=z[:5];direct,qc,qd,gas,unmet,q,w,ql=z[5:13]
    cop=dec(h[1])*(dec(x[2])+D('273.15'))/(dec(x[2])-dec(x[1]))
    want=min(dec(z[13]),dec(h[0]),dec(x[0])*cop/(cop-1))
    P=dec(p[4])*dec(qc)-dec(qd)/dec(p[5]);rate=dec(p[6]);span=dec(t)
    retention=(-rate*span).exp();end=dec(A)*retention+P*(1-retention)/rate if rate else dec(A)+P*span
    budget=72*dec(math.ulp(max(1.,p[1])))
    law=dec(A)+(dec(ql)+dec(w)+dec(gas)-dec(z[19]))*span-dec(B)-sum(map(dec,z[16:19]))
    wanted_mode=5 if unmet else 4 if gas else 3 if qd else 2 if qc else 1 if direct else 0
    return dict(ode=abs(dec(B)-end)<=budget,
        first_law=abs(law)<=budget and near(z[20],law),
        hp=near(q,want) and near(q,dec(w)+dec(ql)) and (near(z[14],cop) if q else z[14] is None) and near(w,dec(q)/cop),
        allocation=near(q,direct+qc) and near(direct,min(x[3],q)) and near(x[3],direct+qd+gas+unmet) and
            near(gas,min(p[10],max(0,x[3]-direct-qd))) and near(z[19],direct+qd+gas) and int(mode)==wanted_mode,
        bounds=min(A,B,direct,qc,qd,gas,unmet,q,w,ql)>=0 and max(A,B)<=p[1] and qc*qd==0 and qc<=p[2] and qd<=p[3] and gas<=p[10] and (not qd or min(A,B)>=p[7]-float(budget)),
        losses=near(z[16],dec(A)+P*span-end) and near(z[17],(1-dec(p[4]))*dec(qc)*span) and near(z[18],(1/dec(p[5])-1)*dec(qd)*span),
        water_flows=dec(ql)/dec(s['source_glide_K'])<=dec(s['source_capacity_MW_per_K'])+D('1e-12') and
            dec(q)/(max(dec(s['tank_max_C'])+dec(s['charge_approach_K']),dec(s['delivery_C'])+dec(s['direct_approach_K']))-dec(s['hot_in_C']))<=dec(s['hot_capacity_MW_per_K'])+D('1e-12'),
        temperature=near(z[21],dec(p[9])+dec(A)/dec(p[8])) and near(z[22],dec(p[9])+dec(B)/dec(p[8])))
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    name=sys.argv[2] if len(sys.argv)>2 else 'report.json'
    report=json.loads((folder/name).read_text());checks=[];selfchecks=[]
    def check(kind,name,ok):checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    reopened='reviewed_mat_reopen.json' if name=='reviewed_report.json' else 'mat_reopen.json'
    check('MAT','report_reopen',json.loads((folder/reopened).read_text())==report)
    check('execution','MATLAB_assertions',report['summary']['failed']==0 and all(c['passed'] for c in report['assertions']))
    check('execution','actual_Stateflow',report['metadata']['stateflow_license_test']==1 and report['metadata']['chart_count']==2 and report['metadata']['simulation_mode']=='normal')
    check('scope','saved_model_preserved',report['model_version']=='0.52' and report['new_model'] is False)
    check('scope','sweep_count',len(report['vectors'])==216)
    with localcontext() as ctx:
        ctx.prec=70
        for i,v in enumerate(report['vectors']):
            want=expected(v['spec']);b=v['boundary']
            for k,val in want.items():check('component_equation',f'{i}_{k}',b[k] is None if val is None else near(b[k],val))
            check('component_second_law',str(i),b['cop_compressor']<=b['TH_K']/b['lift_K']+1e-12)
            check('component_expanded_balance',str(i),near(b['rated_source_MW']+b['rated_compressor_MW']+b['rated_aux_MW'],b['rated_counted_heat_MW']+b['rated_aux_rejected_MW']))
        check('domain','count',len(report['faults'])==12 and all(f['rejected'] and f['identifier'] and f['message'] for f in report['faults']))
        for f in report['faults']:
            check('domain',f['id'],f['identifier'].startswith('DCHR:v53:') or (f['id']=='negative_demand' and f['identifier'].startswith('MATLAB:')))
        modes=set();intervals=0;positive=0;active=None;maxres=D(0);latch_changes=0
        originals=json.loads((folder/'simulation_reopen.json').read_text()) if (folder/'simulation_reopen.json').exists() else None
        if name=='reviewed_report.json':check('MAT','original_simulation_count',originals is not None and len(originals)==11)
        for item in report['cases']:
            id=item['id'];a=item['adapter'];s=a['boundary_spec'];policy=a['policy'];p,h,c=a['p'],a['h'],a['c']
            xs=matrix(a['inputs']);ds=matrix(item['dispatch']);ss=matrix(item['segments']);plans=matrix(item['plans']);n=len(xs)
            starts=matrix(item['clock_start']);ends=matrix(item['clock_end']);b=a['boundary'];want=expected(s)
            check('adapter',id,all(near(b[k],v) for k,v in want.items() if v is not None) and s['aux_hot_fraction']==0 and h[4]==0 and h[5]==0 and near(h[1],want['heating_factor']))
            check('adapter_temperatures',id,near(p[1],dec(policy['heat_capacity_MWh_per_K'])*(dec(s['tank_max_C'])-dec(policy['ambient_C']))) and near(p[7],dec(policy['heat_capacity_MWh_per_K'])*(dec(s['delivery_C'])+dec(s['discharge_approach_K'])-dec(policy['ambient_C']))) and all(near(x[1],want['evaporator_C']) and near(x[2],want['condenser_C']) and near(x[4],s['delivery_C']) and near(x[0],want['source_budget_MW']) for x in xs))
            check('shape',id,len(ds)==len(starts)==len(ends)==n and len(ss)==len(plans))
            if originals:
                o=next(v for v in originals if v['id']==id)
                check('MAT',id,o['adapter']==a and o['dispatch']==item['dispatch'] and o['segments']==item['segments'] and o['plans']==item['plans'] and o['clock_start']==item['clock_start'] and o['clock_end']==item['clock_end'] and not o['error_message'])
                raw=matrix(o['raw_segments']);rawplan=matrix(o['raw_plans']);pad=0;bound_segments=[];bound_plans=[]
                for i,rr in enumerate(raw):
                    zs=[rr[k:k+28] for k in range(0,1792,28)];qs=[rawplan[i][k:k+23] for k in range(0,1472,23)]
                    check('exact_handoff',f'{id}_{i}',all(zs[k][4]==zs[k+1][3] for k in range(63)) and all(q[1]==z[3] and q[22]==z[4] for q,z in zip(qs,zs)) and ds[i][7]==zs[-1][4])
                    for k,z in enumerate(zs):
                        if z[1]==0:
                            pad+=1;check('padding',f'{id}_{i}_{k}',z[0]==0 and z[3]==z[4] and all(v==0 for v in z[5:14]+z[16:21]) and z[26]==z[27])
                        else:
                            bound_segments.append([i+1]+z);bound_plans.append([i+1]+qs[k])
                check('MAT_positive_binding',id,bound_segments==ss and bound_plans==plans)
                check('padding_count',id,pad==item['padding_count'])
            energy=dec(a['initial_energy_MWh']);age=dec(a['initial_clock'][1]);last_latch=a['initial_clock'][0];lastclock=a['initial_clock'];work=D(0)
            for i in range(n):
                rows=[z[1:] for z in ss if z[0]==i+1];qplans=[q[1:] for q in plans if q[0]==i+1];duration=D(0);total=[D(0)]*8;loss=[D(0)]*3;start=energy
                check('clock_handoff',f'{id}_{i}',starts[i]==lastclock)
                for j,(z,qp) in enumerate(zip(rows,qplans)):
                    positive+=1;mode,t,offset,A,B=z[:5];modes.add(mode)
                    check('schedule',f'{id}_{i}_{j}',t>0 and near(offset,duration) and near(A,energy))
                    for kind,ok in segment_checks(z,xs[i],p,h,s).items():check(kind,f'{id}_{i}_{j}',ok)
                    if z[10]>0 and active is None:active=(z,xs[i],p,h,s)
                    if z[25]!=last_latch:
                        latch_changes+=1
                        bound=max(dec(qp[20]),dec(ends[i][3]));lower=age-bound
                        if z[25]==1:valid=lower>=dec(c[2]) and dec(A)<=dec(c[0])+64*dec(math.ulp(max(1.,p[1]))) and z[10]>0
                        else:valid=qp[16]==1 or (lower>=dec(c[1]) and near(A,p[1]))
                        check('dwell',f'{id}_{i}_{j}',valid);age=D(0);last_latch=z[25]
                    check('clock_age',f'{id}_{i}_{j}',near(z[26],age) and near(z[27],age+dec(t)))
                    age+=dec(t);energy=dec(B);duration+=dec(t);work+=dec(z[11])*dec(t)
                    for k,v in enumerate(z[5:13]):total[k]+=dec(v)*dec(t)
                    for k,v in enumerate(z[16:19]):loss[k]+=dec(v)
                row=ds[i]
                check('macro',f'{id}_{i}',near(duration,p[0]) and near(row[7],energy) and all(near(row[k],total[j]/dec(p[0])) for j,k in enumerate([1,2,3,4,5,18,19,20])) and all(near(row[k],loss[j]) for j,k in enumerate([8,9,10])))
                residual=start+total[6]+total[7]+total[3]-total[0]-total[2]-total[3]-energy-sum(loss);maxres=max(maxres,abs(residual))
                check('macro_first_law',f'{id}_{i}',abs(residual)<=100*dec(math.ulp(max(1.,p[1]))) and near(row[12],residual))
                check('clock_enclosure',f'{id}_{i}',abs(dec(ends[i][1])+dec(ends[i][2])-age)<=dec(ends[i][3])+D('1e-15') and ends[i][0]==last_latch)
                lastclock=ends[i]
            intervals+=n
            aux=dec(s['aux_per_compressor'])*work
            check('aux_report',id,near(item['compressor_energy_MWh'],work) and near(item['aux_energy_MWh'],aux))
            check('expanded_aux_balance',id,near(work+aux,work+aux*(1-dec(s['aux_hot_fraction']))))
        check('modes','all_six',modes==set(range(6)))
        check('scope','executions',intervals==34 and len(report['cases'])==11)
        # Separate mutation tests exercise reviewer power, never add to actual pass count.
        z,x,p,h,s=active
        for mutation_name,index,delta in [('electric_port',11,.05),('source_port',12,.05),('endpoint',4,.05),('storage_port',6,.05)]:
            altered=z.copy();altered[index]+=delta
            selfchecks.append(dict(name=mutation_name,passed=not all(segment_checks(altered,x,p,h,s).values())))
        altered=copy.deepcopy(report['vectors'][0]);altered['boundary']['evaporator_C']+=1
        selfchecks.append(dict(name='temperature_axis',passed=not near(altered['boundary']['evaporator_C'],expected(altered['spec'])['evaporator_C'])))
        check('sensitivity','approach_COP_strict_decrease',all(report['cases'][j]['adapter']['boundary']['cop_compressor']>report['cases'][j+1]['adapter']['boundary']['cop_compressor'] for j in [6,7]))
        hot=report['cases'][9]['adapter']['boundary'];check('sensitivity','finite_hot_budget_binding',near(hot['rated_heat_MW'],hot['hot_budget_MW']) and hot['rated_heat_MW']<8)
    for v in json.loads((folder/'preservation.json').read_text()):check('preservation',v['path'],sha(ROOT/v['path'])==v['sha256'] and (ROOT/v['path']).stat().st_size==v['size'])
    with zipfile.ZipFile(ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v52.slx') as archive:
        payload=b' '.join(archive.read(n) for n in archive.namelist() if n.endswith('.xml'))
        check('artifact','saved_chart_states',all(n.encode() in payload for n in ['IDLE','HEAT_RECOVERY','STORAGE_CHARGE','STORAGE_DISCHARGE','BACKUP','UNMET_DEMAND']))
    receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')]
    check('execution','successful_batch_receipt',any(r['exit_code']==0 and 'run_finite_interface_v53' in r['command'] for r in receipts))
    reference=json.loads((folder/'reference_v53.json').read_text()) if (folder/'reference_v53.json').exists() else None
    check('reference','six_physical_comparisons',reference is not None and reference['passed']==6 and reference['failed']==0)
    if reference:
        check('MAT','reference_reopen',reference==json.loads((folder/'reference_mat_reopen.json').read_text()))
        for item in reference['items']:
            actual=next(v for v in report['cases'] if v['id']==item['id'])['dispatch']
            check('reference_binding',item['id'],actual==item['actual'] and item['columns']==list(range(1,22))+list(range(23,26)))
            aa,bb=matrix(item['actual']),matrix(item['reference'])
            check('reference_values',item['id'],all((a[j-1] is None and b[j-1] is None) or near(a[j-1],b[j-1]) for a,b in zip(aa,bb) for j in item['columns']))
    observations=json.loads((folder/'source_observations.json').read_text())
    check('source','primary_bytes',observations['local_primary_pdf_sha256']==sha(ROOT/'sources/papers/20_Verzino_Varna_2026.pdf'))
    check('source','scope_unverified_upstream',observations['upstream62_equations_verified'] is False and observations['full_primary_signoffs']==0)
    if (folder/'source_hashes.json').exists():
        for item in json.loads((folder/'source_hashes.json').read_text()):
            check('source_snapshot',item['path'],sha(ROOT/item['path'])==item['sha256'] and sha(folder/'source_snapshot'/item['snapshot'])==item['sha256'])
    result=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),report=name,report_sha256=sha(folder/name),
        actual_passed=sum(c['passed'] for c in checks),actual_failed=sum(not c['passed'] for c in checks),
        reviewer_selfchecks_passed=sum(c['passed'] for c in selfchecks),reviewer_selfchecks_failed=sum(not c['passed'] for c in selfchecks),
        intervals=intervals,positive_segments=positive,latch_changes=latch_changes,max_macro_residual_MWh=str(maxres),
        required_modes=sorted(modes),checks=checks,selfchecks=selfchecks,
        independence='70-digit independent equations, no production import; same-agent algorithmic QA, no physical validation')
    path=folder/('independent_QA_v53_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')+'.json');path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['checks','selfchecks']}));print(path.relative_to(ROOT).as_posix())
    sys.exit(1 if result['actual_failed'] or result['reviewer_selfchecks_failed'] else 0)
if __name__=='__main__':main()
