"""Independent exact-input analytic HP, TES ODE and preserved-artifact QA.

Every analytic implementation comparison must pass for repair acceptance. Independent algorithms in one agent, not independent people.
"""
from decimal import Decimal, localcontext
from datetime import datetime, timezone
from pathlib import Path
import fnmatch, hashlib, json, math, shutil, sys, zipfile
from stateflow_reference_v34 import dispatch as baseline_reference

ROOT = Path(__file__).resolve().parents[1]
D = lambda x: Decimal.from_float(float(x))

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def matrix(v):
    return [] if not v else v if isinstance(v[0], list) else [v]

def near(a, b):
    return abs(a-b) <= 64*max(math.ulp(a), math.ulp(b)) + 1e-13*abs(b)

def root(q):
    """Stable quadratic on Q itself; exact binary64 input interpretation.

    Avoid division source/cap and slope=penalty/cap in the oracle too.
    Multiply the law by cap: b QВІ + [(a-1)cap-bS]Q-a cap S=0.
    """
    with localcontext() as ctx:
        ctx.prec = 150
        cap, req, source = map(D, (q['cap_MW'], q['request_MW'], q['source_MW']))
        p, minimum = D(q['penalty']), D(q['cop_min'])
        nominal = D(q.get('nominal_cop', 4.))
        a, b = nominal*(1-p), nominal*p
        if min(cap, req, source) == 0:
            return None
        lower = max(Decimal(0), cap*(minimum-a)/b) if b else Decimal(0)
        upper = min(cap, req)
        evap = lambda Q: Q*((a+b*Q/cap-1)/(a+b*Q/cap)) if Q else Decimal(0)
        if lower > upper or evap(lower) > source:
            return None
        Q = upper
        source_limited = evap(upper) > source
        if source_limited:
            B = (a-1)*cap-b*source
            if not b:
                Q = source*a/(a-1)
            else:
                disc = (B*B+4*b*a*cap*source).sqrt()
                Q = 2*a*cap*source/(B+disc) if B >= 0 else (disc-B)/(2*b)
        cop = a+b*Q/cap
        return dict(heat=float(Q), cop=float(cop), electric=float(Q/cop),
            source=float(evap(Q)), source_limited=source_limited,
            equation_relative_residual=float(abs(evap(Q)-source)/source) if source_limited else 0.)

def main():
    folder = ROOT/Path(sys.argv[1]); receipts = [read(ROOT/Path(x)) for x in sys.argv[2:]]
    spec = read(folder/'source_snapshot/spec/cases.json')
    executions = read(folder/'execution_v40.json')
    probes = read(folder/'hp_components_v40.json')
    mat = read(folder/'mat_audit_v40.json')  # reused read-only saved-v40 schema
    metadata = read(folder/'metadata_v40.json')
    summary = read(folder/'summary_v40.json')
    groups, impl, ledger, plant_ledger = {}, [], [], []
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    snapshot = folder/'qa_source'/stamp; snapshot.mkdir(parents=True)
    shutil.copy2(__file__, snapshot/Path(__file__).name)
    def ck(group, name, ok):
        groups.setdefault(group, []).append(dict(name=name, passed=bool(ok)))
    def compare(name, ok):
        impl.append(dict(name=name, passed=bool(ok)))
    ck('artifact', 'two_observed_zero_exit_batches', len(receipts)==2 and all(r['exit_code']==0 for r in receipts))
    ck('artifact', 'actual_saved_model_batch', 'run_stateflow_hp_domain_v40' in receipts[0]['command'])
    ck('artifact', 'separate_read_only_MAT_export', 'export_stateflow_resolution_v40' in receipts[1]['command'])
    ck('artifact', 'Stateflow_license', metadata['stateflow_license_test']==1)
    ck('artifact', 'six_saved_thermal_states', set(metadata['thermal_state_names'])==
       {'IDLE','HEAT_RECOVERY','STORAGE_CHARGE','STORAGE_DISCHARGE','BACKUP','UNMET_DEMAND'})
    ck('artifact', 'two_saved_supervisor_states', set(metadata['supervisor_state_names'])=={'HP_OFF','HP_ON'})
    ck('execution', 'MATLAB_execution_harness', summary['harness_failed']==0 and summary['harness_passed']>0)
    ck('execution', 'all_completed', len(executions)==len(spec['cases'])==summary['completed_scenarios'] and not any(a['rejected'] for a in executions))
    saved = {a['id']: a for a in mat['simulations']}
    all_modes, max_balance = set(), 0.
    for c, a in zip(spec['cases'], executions):
        ck('artifact', c['id']+'_MAT_binding', all(a[k]==saved[a['id']][k] for k in a))
        ck('artifact', c['id']+'_MAT_file', (folder/(c['id']+'_simulation.mat')).stat().st_size>0)
        yy, ss = matrix(a['dispatch']), matrix(a['segments']); p=c['p']
        ck('execution', c['id']+'_samples', len(yy)==len(c['inputs']))
        previousE = c['initial_energy_MWh']
        etol = 1e-10+128*math.ulp(max(1.,p[1]))
        with localcontext() as ctx:
            ctx.prec = 150
            for i, y in enumerate(yy):
                parts = [r for r in ss if r[0]==i]
                ck('numeric', c['id']+f'_{i}_complete_partition', near(sum(r[3] for r in parts), p[0]))
                for k, r in enumerate(parts):
                    z=r[2:30];name=c['id']+f'_{i}_{k}';all_modes.add(int(z[0]))
                    ck('numeric', name+'_nonnegative_ports', min(z[5:14])>=0)
                    ck('numeric', name+'_limits', z[6]<=p[2] and z[7]<=p[3] and z[8]<=p[10] and z[6]*z[7]==0)
                    ck('numeric', name+'_TES_bounds', min(z[3:5])>=0 and max(z[3:5])<=p[1]+etol)
                    ck('numeric', name+'_energy_handoff', abs(z[3]-previousE)<=etol)
                    span=D(z[1]);E=D(z[3]);power=D(p[4])*D(z[6])-D(z[7])/D(p[5]);rate=D(p[6])
                    decay=(-rate*span).exp();phi=(1-decay)/rate if rate else span
                    ideal=E*decay+power*phi
                    ck('equation', name+'_Decimal_TES_ODE', abs(D(z[4])-ideal)<=D(etol))
                    ck('equation', name+'_standing_loss', abs(D(z[16])-(E+power*span-ideal))<=D(etol))
                    ck('equation', name+'_HP_firstlaw', near(z[10], z[11]+z[12]))
                    ck('equation', name+'_service_firstlaw', near(c['inputs'][i][3],sum(z[j] for j in (5,7,8,9))))
                    balance=E+(D(z[11])+D(z[12])+D(z[8])-D(z[19]))*span-D(z[4])-sum(D(v) for v in z[16:19])
                    max_balance=max(max_balance,float(abs(balance)))
                    ck('equation', name+'_system_firstlaw', abs(balance)<=D(etol))
                    previousE=z[4]
            if c['kind']=='baseline':
                E=c['initial_energy_MWh'];clock=c['initial_clock'][:2]
                for i, x in enumerate(c['inputs']):
                    y, _, clock=baseline_reference(E,x,c['p'],c['h'],clock,c['c']);E=y[7]
                    for k,(actual,expected) in enumerate(zip(yy[i],y)):
                        ck('reference',c['id']+f'_{i}_{k}', actual is None and math.isnan(expected) or
                           actual is not None and abs(actual-expected)<=2e-9+2e-11*abs(expected))
            else:
                x=c['inputs'][0]
                q=dict(cap_MW=c['h'][0],request_MW=x[3]+p[2],source_MW=x[0],penalty=c['h'][4],cop_min=c['h'][2])
                expected=root(q);ck('equation',c['id']+'_analytic_feasible',expected is not None)
                ideal_direct=min(x[3],expected['heat']);ideal_unmet=max(0.,x[3]-ideal_direct)
                ideal_mode=5 if ideal_unmet else 2 if expected['heat']>ideal_direct else 1
                for i,y in enumerate(yy):
                    compare(c['id']+f'_{i}_HP_output',near(y[18],expected['heat']))
                    compare(c['id']+f'_{i}_direct_service',near(y[1],ideal_direct))
                    compare(c['id']+f'_{i}_unmet',near(y[5],ideal_unmet))
                    compare(c['id']+f'_{i}_mode',y[0]==ideal_mode)
                plant_ledger.append(dict(id=c['id'],expected_HP_heat_MW=expected['heat'],actual_HP_heat_MW=yy[0][18],
                    demand_MW=x[3],expected_unmet_MW=ideal_unmet,actual_unmet_MW=yy[0][5],
                    expected_mode=ideal_mode,actual_mode=yy[0][0],source_ratio=x[0]/q['cap_MW']))
    ck('execution','six_actual_modes',all_modes==set(range(6)))
    ck('artifact','component_MAT_binding',probes==mat['component_probes'])
    ck('execution','all_probe_count',len(probes)==len(spec['hp_probes'])==summary['hp_probes'])
    for q, a in zip(spec['hp_probes'],probes):
        expected=root(q)
        should_reject=q.get('expected_reject',False)
        ck('execution',q['id']+'_expected_domain',a['rejected']==should_reject)
        if should_reject:
            ck('equation',q['id']+'_oracle_unrepresentable_electricity',expected is not None and expected['heat']>0 and expected['electric']==0)
            ck('execution',q['id']+'_specific_resolution_diagnostic',a['error_identifier']=='DCHR:v40:HPResolution')
            ledger.append(dict(id=q['id'],kind=q['kind'],expected=expected,actual_rejection=a))
            continue
        hp=a['output']
        ck('execution',q['id']+'_not_rejected',not a['rejected'])
        if a['rejected']:continue
        ck('numeric',q['id']+'_positive_representable_flows',not hp['available'] or
           hp['heat_output_MW']>0 and hp['electric_MW']>0 and hp['source_used_MW']>0)
        ck('numeric',q['id']+'_finite_ports',all(math.isfinite(hp[k]) for k in ('heat_output_MW','electric_MW','source_used_MW')))
        ck('numeric',q['id']+'_actual_firstlaw',near(hp['heat_output_MW'],hp['electric_MW']+hp['source_used_MW']))
        ck('numeric',q['id']+'_actual_limits',0<=hp['source_used_MW']<=q['source_MW']+2*math.ulp(q['source_MW']) and
           0<=hp['heat_output_MW']<=min(q['request_MW'],q['cap_MW']))
        if expected:
            ck('equation',q['id']+'_analytic_source_equation',expected['equation_relative_residual']<1e-140)
        ambiguous=q.get('boundary_ambiguous',False)
        if not ambiguous:
            compare(q['id']+'_availability',hp['available']==bool(expected))
            for key,oracle_key in (('heat_output_MW','heat'),('electric_MW','electric'),('source_used_MW','source')):
                compare(q['id']+'_'+key,near(hp[key],expected[oracle_key] if expected else 0.))
        ledger.append(dict(id=q['id'],kind=q['kind'],cap_MW=q['cap_MW'],source_MW=q['source_MW'],request_MW=q['request_MW'],
            penalty=q['penalty'],expected=expected,actual=hp,excluded_boundary_comparison=ambiguous,
            output_relative_error=abs(hp['heat_output_MW']-expected['heat'])/expected['heat'] if expected else None))
    controls={r['id']:r for r in plant_ledger}
    for bits in (90,120):
        wide,tight=controls[f'wide_request_{bits}'],controls[f'tight_request_{bits}']
        ck('repair',f'{bits}_wide_positive_maximum',near(wide['actual_HP_heat_MW'],wide['expected_HP_heat_MW']) and wide['actual_HP_heat_MW']>0)
        ck('repair',f'{bits}_no_lost_service',wide['actual_unmet_MW']==tight['actual_unmet_MW']==0)
    pairs={}
    for q,a in zip(spec['hp_probes'],probes):
        if q.get('pair'):pairs.setdefault(q['pair'],[]).append(a)
    for name,pair in pairs.items():
        ck('repair',name+'_source_limited_request_invariance',len(pair)==2 and all(not a['rejected'] for a in pair) and
           near(pair[0]['output']['heat_output_MW'],pair[1]['output']['heat_output_MW']) and
           pair[0]['output']['heat_output_MW']>0)
    faults=read(folder/'runtime_faults_v40.json')
    ck('execution','30_actual_runtime_fault_rejections',len(faults)==30 and all(a['rejected'] for a in faults))
    for a in faults:
        b=saved[a['id']+'_fault']
        ck('artifact',a['id']+'_fault_MAT_binding',a['error_message']==b['error_message'] and a['phase']==b['phase'] and a['time_h']==b['time_h'])
        ck('execution',a['id']+'_execution_rejection',b['rejected'] and b['phase']=='Execution')
    for key in ('dispatch','segments','clock_start','clock_end'):
        ck('repair','fault_restoration_'+key,saved['pre_fault_clean'][key]==saved['post_fault_clean'][key])
    model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v40.slx'
    old=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v38.slx'
    ck('preservation','v38_checkpoint_hash',sha(old)==read(ROOT/'STATUS_stateflow_v38.json')['model_sha256'])
    ck('artifact','new_v40_model',sha(model)!=sha(old))
    for p in (folder/'source_snapshot').glob('*'):
        if not p.is_file():continue
        choices=(ROOT/'matlab/simulink'/p.name,ROOT/'matlab/+dchr/+components'/p.name,ROOT/'audit'/p.name)
        current=next((x for x in choices if x.is_file()),None)
        ck('artifact',p.name+'_source_binding',current is not None and sha(p)==sha(current))
    with zipfile.ZipFile(model) as z:
        xml='\n'.join(z.read(n).decode('utf-8') for n in z.namelist() if n.endswith('.xml'))
        ck('artifact','saved_guarded_dispatch','stateflow_choose_mode_v40(segmentInput,parameters)' in xml)
        ck('artifact','saved_v40_host_planner','dchr_segment_plan_v40' in xml)
    component=(ROOT/'matlab/+dchr/+components/heat_pump_step_v40.m').read_text()
    ck('repair','source_relative_adjacent_search_in_bound_source','sourceFraction=' in component and 'middle==lower || middle==upper' in component and 'for iteration=1:80' not in component)
    previous={}
    for pattern in ('Stateflow*manifest*v*.json','TES_event_manifest_v31_*.json'):
        for manifest in (ROOT/'audit').glob(pattern):
            for item in read(manifest)['files']:previous[item['path']]=item
    # Corrected v22 manifest explicitly supersedes its original open-log seal.
    # Honor its declared mutable ledger/active-log exclusions, retaining them
    # visibly in this report rather than falsely calling their old hashes sealed.
    corrected=read(ROOT/'audit/Stateflow_evidence_manifest_v22_20261009T030247_850694Z.json')
    ck('artifact','legacy_v22_declared_supersession',corrected['supersedes']==
       'audit/Stateflow_evidence_manifest_v22_20261009T030008_883989Z.json')
    excluded={}
    for name in list(previous):
        normalized=name.replace('\\','/')
        if normalized==corrected['mutable_ledger'] or fnmatch.fnmatch(normalized,corrected['excluded_active_receipts']):
            excluded[name]=dict(reason='Explicit exclusion in corrected v22 manifest',old_entry=previous.pop(name))
    for name,item in previous.items():
        p=Path(name);p=p if p.is_absolute() else ROOT/p
        ck('preservation',name,p.is_file() and p.stat().st_size==item.get('bytes',item.get('size_bytes')) and sha(p)==item['sha256'])
    # Separately labelled synthetic oracle self-checks, never called executions.
    q=dict(cap_MW=8.,request_MW=8.,source_MW=.75,penalty=0.,cop_min=1.2)
    ck('synthetic','constant_COP_closed_form',root(q)['heat']==1.)
    q.update(source_MW=6.,penalty=.3)
    ck('synthetic','full_load_root',root(q)['heat']==8.)
    q.update(request_MW=1.,cop_min=3.5)
    ck('synthetic','cutoff_OFF',root(q) is None)
    counts={g:dict(passed=sum(r['passed'] for r in rows),failed=sum(not r['passed'] for r in rows)) for g,rows in groups.items()}
    comparison=dict(passed=sum(r['passed'] for r in impl),failed=sum(not r['passed'] for r in impl))
    report=dict(version='0.40',model_release='0.40',evidence_class='independent_algorithm_and_artifact_QA_same_agent',
        timestamp_utc=datetime.now(timezone.utc).isoformat(),counts=counts,implementation_comparisons=comparison,
        implementation_status='PASS_SCOPED_HP_REPAIR',new_model=True,model_sha256=sha(model),
        result_directory=str(folder.relative_to(ROOT)),previous_immutable_entries=len(previous),
        preservation_exclusions=excluded,
        max_balance_residual_MWh=max_balance,component_ledger=ledger,plant_ledger=plant_ledger,checks=groups,
        implementation_checks=impl,physical_validation=False,article_replication=False)
    path=folder/('independent_QA_v40_'+stamp+'.json');path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('QA='+str(path.relative_to(ROOT)));print('QA_COUNTS='+json.dumps(counts));print('IMPLEMENTATION_COMPARISONS='+json.dumps(comparison))
    for g,items in groups.items():
        failed=[r['name'] for r in items if not r['passed']]
        if failed:print('QA_FAIL='+g+':'+json.dumps(failed[:12]))
    assert not sum(v['failed'] for v in counts.values()),'Independent evidence QA failed'
    assert comparison['failed']==0,'HP repair analytic implementation comparisons failed'

if __name__=='__main__':
    main()
