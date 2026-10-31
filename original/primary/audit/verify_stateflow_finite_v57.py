"""Independent 80-digit equations and exact-binary event/dwell review.

Standard library only; no production imports. Evidence comes from binary exports
made by reopening original MATLAB SimulationOutputs. Same-agent independent
algorithms, not independent personnel or measured physical validation.
"""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal as D, localcontext
from fractions import Fraction as F
import copy, csv, hashlib, json, math, struct, sys, zipfile

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def d(v):return v if isinstance(v,D) else D.from_float(v)
def near(a,b,budget=D('2e-11')):
    return math.isfinite(a) and abs(d(a)-b)<=budget*max(D(1),abs(b))
def boundary(v):
    v=list(map(d,v));out=v[0]-v[1];evap=out-v[2];hot=max(v[4]+v[6],v[5]+v[8]);cond=hot+v[3]
    tl=evap+D('273.15');th=cond+D('273.15');lift=cond-evap
    cop=1+v[13]*tl/lift;eta=(lift+v[13]*tl)/th
    source=v[10]*v[1];hotbudget=v[11]*(hot-v[9]);cap=min(v[12],hotbudget)
    return [out,evap,cond,hot,v[5]+v[7],cop,eta,source,hotbudget,cap,v[14],v[1],hot-v[9]]
def segment(z,v,p):
    b=boundary(v);mode,t,offset,A,B=z[:5];direct,qc,qd,gas,unmet,q,w,ql=z[5:13]
    span=d(t);P=d(p[4])*d(qc)-d(qd)/d(p[5]);rate=d(p[6]);r=(-rate*span).exp()
    endpoint=d(A)*r+P*((1-r)/rate if rate else span)
    budget=72*d(math.ulp(max(1.,p[1])))
    wanted=min(d(z[13]),b[9],b[7]*b[5]/(b[5]-1))
    firstlaw=d(A)+(d(ql)+d(w)+d(gas)-d(z[19]))*span-d(B)-sum(map(d,z[16:19]))
    expected=5 if unmet else 4 if gas else 3 if qd else 2 if qc else 1 if direct else 0
    return dict(
        ode=abs(d(B)-endpoint)<=budget,
        first_law=abs(firstlaw)<=budget and near(z[20],firstlaw),
        hp=near(q,wanted) and near(q,d(w)+d(ql)) and near(w,d(q)/b[5]) and
            (near(z[14],b[5]) if q else math.isnan(z[14])),
        mode=mode==expected,
        demand=near(v[16],d(direct)+d(qd)+d(gas)+d(unmet)),
        allocation=near(q,d(direct)+d(qc)) and near(direct,min(d(v[16]),d(q))) and
            near(gas,min(d(p[10]),max(D(0),d(v[16])-d(direct)-d(qd)))) and near(z[19],d(direct)+d(qd)+d(gas)),
        physical_bounds=min(A,B,direct,qc,qd,gas,unmet,q,w,ql)>=0 and max(A,B)<=p[1] and
            qc*qd==0 and qc<=p[2] and qd<=p[3] and gas<=p[10] and (not qd or min(A,B)>=p[7]-float(budget)),
        water_ports=d(ql)/b[11]<=d(v[10])+D('1e-11') and d(q)/b[12]<=d(v[11])+D('1e-11'),
        losses=near(z[16],d(A)+P*span-endpoint) and near(z[17],(1-d(p[4]))*d(qc)*span) and
            near(z[18],(1/d(p[5])-1)*d(qd)*span),
        temperatures=near(z[21],d(p[9])+d(A)/d(p[8])) and near(z[22],d(p[9])+d(B)/d(p[8])),
        source_unused=near(z[15],b[7]-d(ql)),
    )
def lower(clock):return F(clock[1])+F(clock[2])-F(clock[3])
def same(a,b):return all((math.isnan(x) and math.isnan(y)) or struct.pack('<d',x)==struct.pack('<d',y) for x,y in zip(a,b)) and len(a)==len(b)

def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    report=json.loads((folder/'report.json').read_text());manifest=json.loads((folder/'binary_manifest.json').read_text())
    checks=[];selfchecks=[];hashes=[];data={};originals=set();values=0
    def check(kind,name,ok):checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    check('MAT','report_reopen',report==json.loads((folder/'mat_reopen.json').read_text()))
    check('MATLAB','acceptance_assertions',report['summary']['failed']==0 and all(x['passed'] for x in report['assertions']))
    check('Stateflow','actual_license_charts',report['metadata']['stateflow_license_test']==1 and report['metadata']['chart_count']==2 and report['metadata']['simulation_mode']=='normal')
    check('scope','held_boundary_explicit',report['new_model'] and report['model_version']=='0.57' and 'NOT_CONTINUOUS' in report['scope'])
    for rec in manifest['records']:
        key=(rec['id'],rec['field']);path=(folder/rec['file']).resolve();assert path.is_relative_to(folder/'binary')
        payload=path.read_bytes();vals=[x[0] for x in struct.iter_unpack('<d',payload)]
        check('binary',str(key),len(vals)==rec['rows']*rec['columns'] and key not in data)
        data[key]=[vals[i:i+rec['columns']] for i in range(0,len(vals),rec['columns'])]
        values+=len(vals);originals.add(rec['source_mat']);hashes.append(dict(path=rec['file'],sha256=sha(path)))
    for path in originals:check('original_MAT',path,(folder/path).is_file() and (folder/path).stat().st_size>1000)
    all_modes=set();intervals=0;positive=0;latch_changes=0;macro_transitions=0;maxres=D(0);active_fixture=None;trace_rows=[]
    with localcontext() as ctx:
        ctx.prec=80
        for item in report['cases']:
            id=item['id'];get=lambda key:data[(id,key)]
            inputs=get('input.inputs');p=get('input.p')[0];c=get('input.c')[0];dt=get('input.dt')[0][0]
            initial=get('input.E0')[0][0];memory=[x[0] for x in get('input.m0')]
            dispatch=get('dispatch');raw=get('raw_segments');plans=get('raw_plans');bs=get('boundary');accounts=get('accounting')
            starts=get('clock_start');ends=get('clock_end');energy_starts=get('energy_start')
            n=len(inputs);intervals+=n;previous_energy=initial;last_mode=None
            check('shape',id,len(dispatch)==len(raw)==len(plans)==len(bs)==len(accounts)==len(starts)==len(ends)==n)
            for i,v in enumerate(inputs):
                name=f'{id}_{i}';want=boundary(v);b=bs[i];account=accounts[i];ds=dispatch[i]
                check('finite_equations',name,all(near(x,y) for x,y in zip(b,want)))
                check('tank_definition',name,near(p[1],d(p[8])*(d(v[4])-d(p[9]))) and near(p[7],d(p[8])*(d(v[5])+d(v[7])-d(p[9]))) and v[15]==0)
                check('macro_memory',name,same(starts[i],memory) and energy_starts[i][0]==previous_energy)
                zs=[raw[i][k:k+28] for k in range(0,1792,28)];qs=[plans[i][k:k+23] for k in range(0,1472,23)]
                check('exact_handoff',name,zs[0][3]==previous_energy and all(zs[j][4]==zs[j+1][3] for j in range(63)) and
                    all(q[1]==z[3] and q[22]==z[4] for q,z in zip(qs,zs)) and ds[7]==zs[-1][4])
                total=[D(0)]*9;loss=[D(0)]*3;duration=D(0);high=0;work=D(0);source_rate=D(0);hot_rate=D(0);law=D(0)
                for j,(z,q) in enumerate(zip(zs,qs)):
                    zn=f'{name}_{j}';span=z[1]
                    check('schedule',zn,span==q[0] and z[2]==q[13] and near(z[2],duration) and z[25]==q[14])
                    if span==0:
                        check('exact_padding',zn,z[0]==0 and z[3]==z[4] and all(x==0 for x in z[5:14]+z[16:21]) and
                            q[14]==memory[0] and q[15]==memory[1] and q[18]==memory[2] and q[20]==memory[3] and z[26]==z[27])
                        continue
                    positive+=1;all_modes.add(int(z[0]));high=max(high,z[0])
                    for kind,ok in segment(z,v,p).items():check(kind,zn,ok)
                    if active_fixture is None and z[10]>0:active_fixture=(z,v,p)
                    if q[14]!=memory[0]:
                        latch_changes+=1;reason=q[16];target=q[14]
                        if target==1:authorized=reason==3 and lower(memory)>=F(c[2]) and z[3]<=c[0]+64*math.ulp(max(1,p[1]))
                        elif reason==1:authorized=q[3]==0
                        else:authorized=reason==2 and lower(memory)>=F(c[1]) and z[3]>=p[1]-64*math.ulp(max(1,p[1]))
                        check('dwell_authorization',zn,authorized and q[15]==q[18]==q[20]==0)
                    else:check('clock_segment_start',zn,same([q[14],q[15],q[18],q[20]],memory))
                    start_age=F(q[15])+F(q[18]);end_age=F(q[17])+F(q[19]);roundoff=F(q[21])-F(q[20])
                    check('clock_increment',zn,roundoff>=0 and abs(end_age-start_age-F(span))<=roundoff)
                    check('clock_output',zn,z[25]==q[14] and z[26]==q[15] and z[27]==q[17])
                    memory=[q[14],q[17],q[19],q[21]];duration+=d(span)
                    for k,index in enumerate([5,6,7,8,9,10,11,12,13]):total[k]+=d(z[index])*d(span)
                    for k in range(3):loss[k]+=d(z[16+k])
                    work+=d(z[11])*d(span);source_rate=max(source_rate,d(z[12])/want[11]);hot_rate=max(hot_rate,d(z[10])/want[12])
                    law+=d(z[20]);maxres=max(maxres,abs(d(z[20])))
                check('macro_duration',name,near(dt,duration))
                check('macro_powers',name,ds[0]==high and all(near(ds[k+1],total[k]/d(dt)) for k in range(5)) and
                    all(near(ds[k+18],total[k+5]/d(dt)) for k in range(4)))
                check('macro_losses',name,all(near(ds[k+8],loss[k]) for k in range(3)))
                expected_aux=d(v[14])*work
                check('auxiliary_accounting',name,near(account[0],work) and near(account[1],expected_aux) and
                    account[1]==account[2] and near(account[3],work+expected_aux) and near(account[4],law) and
                    near(account[5],source_rate) and near(account[6],hot_rate))
                check('macro_clock_end',name,same(ends[i],memory))
                check('macro_first_law',name,near(ds[12],law))
                trace_rows.append([id,i,dt,ds[0],previous_energy,ds[7],v[16],ds[11],ds[12],account[0],account[1],b[1],b[2],b[3],account[5],account[6],starts[i][0],ends[i][0]])
                if last_mode is not None:macro_transitions+=ds[0]!=last_mode
                last_mode=ds[0];previous_energy=ds[7]
            if (id,'reference') in data:
                ref=get('reference');cols=list(range(21))+[22,23,24]
                check('v30_reference',id,all((math.isnan(a[k]) and math.isnan(b[k])) or abs(a[k]-b[k])<1e-10 for a,b in zip(ref,dispatch) for k in cols))
        check('six_modes','coverage',all_modes==set(range(6)))
        check('temporal','actual_latch_changes',latch_changes>0 and macro_transitions>0)
        check('runtime_faults','twelve_rejected',len(report['faults'])==12 and all(x['rejected'] and 'finite' in x['error_message'].lower() for x in report['faults']))
        delayed=next(x for x in report['faults'] if x['id']=='delayed_capacity')
        check('runtime_faults','delayed_prefix_two',delayed['completed_samples']==2)
        check('runtime_faults','delayed_prefix_binary',len(data[('fault_delayed_capacity','dispatch')])==2)
        # Mutations are separate synthetic reviewer self-checks, not simulations.
        z,v,p=active_fixture
        for label,index,delta in [('compressor',11,.1),('storage_endpoint',4,.1),('mode',0,1),('loss',16,.1),('source',12,.1)]:
            corrupt=copy.deepcopy(z);corrupt[index]+=delta
            selfchecks.append(dict(name=label,passed=not all(segment(corrupt,v,p).values())))
        vv=copy.deepcopy(v);vv[13]*=.8
        selfchecks.append(dict(name='water_factor',passed=not all(near(a,b) for a,b in zip(boundary(v),boundary(vv)))))
        selfchecks.append(dict(name='auxiliary_energy',passed=not near(float(d(v[14])*d(z[11])+D('.1')),d(v[14])*d(z[11]))))
    for row in json.loads((folder/'preservation.json').read_text()):check('preservation',row['path'],sha(ROOT/row['path'])==row['sha256'])
    for row in json.loads((folder/'source_hashes.json').read_text()):check('source_snapshot',row['path'],sha(folder/'source_snapshot'/row['path'])==row['sha256'] and sha(ROOT/row['path'])==row['sha256'])
    model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v57.slx'
    with zipfile.ZipFile(model) as archive:
        texts='\n'.join(archive.read(n).decode('utf-8','ignore') for n in archive.namelist() if n.endswith('.xml'))
        check('saved_model','runtime_water_and_accounting',all(x in texts for x in ['stateflow_finite_boundary_v57','stateflow_finite_ports_v57','Finite_Temperature_Boundary','Finite_Port_Accounting']))
        check('saved_model','six_guarded_modes',all(x in texts for x in ['IDLE','HEAT_RECOVERY','STORAGE_CHARGE','STORAGE_DISCHARGE','BACKUP','UNMET_DEMAND']))
    executions=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')]
    check('execution_receipt','batch_exit_zero',any(x['exit_code']==0 for x in executions))
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    csv_path=folder/f'numeric_traces_v57_{stamp}.csv'
    with csv_path.open('w',newline='',encoding='utf-8') as stream:
        writer=csv.writer(stream);writer.writerow(['case','interval','dt_h','mode','E_start_MWh','E_end_MWh','demand_MW','served_MWh','residual_MWh','compressor_MWh','auxiliary_MWh','evaporator_C','condenser_C','hot_out_C','required_source_MW_per_K','required_hot_MW_per_K','HP_start_latch','HP_end_latch']);writer.writerows(trace_rows)
    result=dict(version='0.57',timestamp_utc=datetime.now(timezone.utc).isoformat(),
        counts=dict(intervals=intervals,positive_segments=positive,mode_coverage=sorted(all_modes),latch_changes=latch_changes,
            macro_transitions=macro_transitions,binary_records=len(data),binary_values=values,original_MATs=len(originals)),
        max_segment_residual_MWh=str(maxres),model_sha256=sha(model),numeric_traces=csv_path.relative_to(folder).as_posix(),
        summary=dict(passed=sum(x['passed'] for x in checks),failed=sum(not x['passed'] for x in checks)),
        reviewer_selfchecks=selfchecks,checks=checks,binary_hashes=hashes,
        limitations=['Held-macro finite-water model; not continuously tank-coupled propagation.',
            'Same-agent independent algorithms; no independent personnel or physical validation.'])
    path=folder/f'independent_QA_v57_{stamp}.json'
    path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['summary','counts','reviewer_selfchecks']},indent=2))
    failures=[x for x in checks if not x['passed']];print('First failures:',json.dumps(failures[:15]))
    assert not failures and all(x['passed'] for x in selfchecks),f'Inspect retained {path}'
if __name__=='__main__':main()
