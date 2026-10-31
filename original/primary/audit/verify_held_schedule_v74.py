"""Original-MAT independent equations, service reporting and legacy comparisons.

Same-agent algorithmic QA. No production kernel/adapter/report is called.
Binary exports are reopened by MATLAB; this is not an independent MAT parser.
"""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal as D, localcontext
import copy, csv, hashlib, json, math, struct, sys
from earliest_closed_form_v73 import analyze, dec, contains, rows
from verify_interval_dispatch_v66 import analyze as analyze66
from verify_stateflow_finite_v57 import segment as segment57, boundary as boundary57, near
ROOT=Path(__file__).resolve().parents[1]
NAMES=['hp_heat','recovered_source','compressor_work','standing_loss','charge_loss','discharge_loss','delivered_service','backup_heat','unmet_demand','auxiliary_work']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def json_binary_equal(value,json_value):
    if isinstance(value,list):return isinstance(json_value,list) and len(value)==len(json_value) and all(json_binary_equal(a,b) for a,b in zip(value,json_value))
    # MATLAB JSON renders undefined legacy COP diagnostics as null. Binary
    # exports retain the actual NaN; finite earliest model traces forbid NaN.
    if isinstance(value,float) and math.isnan(value):return json_value is None
    return value==json_value
def total_earliest(r,ns):
    tr=rows(r['trace']);p=list(map(dec,r['p']));out={k:D(0) for k in NAMES+['direct_HP_service','TES_service','demand']}
    for v in ns:
        z=tr[v['tick']][100+80*v['segment']:180+80*v['segment']];t=D(v['duration'])
        for k,key in [('hp_heat','heat'),('recovered_source','source'),('compressor_work','work'),('standing_loss','standing'),('delivered_service','service'),('unmet_demand','unmet')]:out[k]+=D(v[key])
        direct,charge,dis,back=map(dec,z[24:28])
        out['charge_loss']+=(1-p[6])*charge*t;out['discharge_loss']+=(1/p[7]-1)*dis*t
        out['backup_heat']+=back*t;out['auxiliary_work']+=p[20]*D(v['work'])
        out['direct_HP_service']+=direct*t;out['TES_service']+=dis*t
    out['demand']=sum((dec(u[4])*dec(u[5]) for u in rows(r['input'])),D(0))
    out['external_electricity']=out['compressor_work']+out['auxiliary_work'];out['service_plus_unmet']=out['delivered_service']+out['unmet_demand']
    out['final_inventory']=D(ns[-1]['inventory'])
    return out
def review_report(r,totals):
    s=r['summary'];checks={}
    for key in NAMES+['direct_HP_service','TES_service','demand','external_electricity','service_plus_unmet']:
        checks[key+'_reported_hull']=contains(s[key+'_MWh_hull'],totals[key])
    for key,num,den in [('delivered_HP_heating_COP','hp_heat','compressor_work'),('electricity_per_delivered_service','external_electricity','delivered_service')]:
        box=s[key+'_hull'];checks[key+'_ratio']=contains(box,totals[num]/totals[den]) if totals[den]>0 else box==[]
    checks['final_inventory']=contains(s['final_inventory_hull'],totals['final_inventory'])
    checks['complete_count']=s['held_intervals']==len(rows(r['input']))
    checks['service_and_unmet_balance']=abs(totals['demand']-totals['service_plus_unmet'])<D('1e-12')*max(D(1),totals['demand'])
    checks['delivered_component_balance']=abs(totals['delivered_service']-totals['direct_HP_service']-totals['TES_service']-totals['backup_heat'])<D('1e-100')*max(D(1),totals['delivered_service'])
    checks['source_work_balance']=abs(totals['hp_heat']-totals['recovered_source']-totals['compressor_work'])<D('1e-100')*max(D(1),totals['hp_heat'])
    return checks
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    report=json.loads((folder/'report.json').read_text());spec=json.loads((folder/'spec.json').read_text());checks=[];mutations=[];numeric=[];aggregates={};comparisons=[]
    def check(kind,name,ok):checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    check('MAT','reopened_equal',report==json.loads((folder/'mat_reopen.json').read_text()))
    check('MAT','original_report',(folder/'held_schedule_v74.mat').stat().st_size>1000)
    data={}
    for rec in json.loads((folder/'binary_manifest.json').read_text()):
        key=rec['group'],rec['index']-1,rec['field'];vals=[v[0] for v in struct.iter_unpack('<d',(folder/rec['file']).read_bytes())];cols=rec['columns']
        value=[vals[k:k+cols] for k in range(0,len(vals),cols)];flat=value[0] if rec['rows']==1 else value
        obj=report[rec['group']][rec['index']-1];json_value=obj[rec['field']]
        compare_value=vals if cols==1 and rec['rows']>1 and json_value and not isinstance(json_value[0],list) else flat
        check('binary',str(key),key not in data and len(vals)==cols*rec['rows'] and json_binary_equal(compare_value,json_value));data[key]=flat
    def original(group,i):
        r=copy.deepcopy(report[group][i])
        for key,value in data.items():
            if key[:2]==(group,i):r[key[2]]=value
        return r
    with localcontext() as ctx:
        ctx.prec=160
        for i in range(len(report['runs'])):
            r=original('runs',i);id=r['id'];cs,ns=analyze(r);numeric+=ns
            for c in cs:check('earliest_equations',c['name'],c['passed'])
            with localcontext() as less:
                less.prec=120;again,ns120=analyze(r)
            check('precision',id,[c['passed'] for c in cs]==[c['passed'] for c in again])
            totals=total_earliest(r,ns);aggregates[id,'v73r2']=totals
            for name,ok in review_report(r,totals).items():check('report',id+'_'+name,ok)
            schedule=rows(r['adapter']['schedule']);uu=rows(r['input']);h=D(0);rounded=0.
            for tick,(s,u) in enumerate(zip(schedule,uu)):
                h+=dec(s[0]);rounded+=s[0]
                check('adapter',f'{id}_{tick}',s[1]==rounded and u==[1,0,s[1],0,s[0],*s[2:],*r['adapter']['initial']] and contains(rows(r['trace'])[tick][9:11],h))
            check('MAT',id,(folder/(id+'.mat')).stat().st_size>1000)
        for i in range(len(report['references'])):
            r=original('references',i);id=r['id'];target=next(v for v in report['runs'] if v['id']==id);p=list(map(dec,target['p']));tr=rows(r.get('trace',r.get('dispatch')));uu=rows(r['input'])
            if r['model']=='v66':
                cfg=r['cfg'];cs,ns=analyze66(cfg,uu,tr)
                for name,ok in cs.items():check('v66_equations',id+'_'+name,ok)
                t={k:D(0) for k in NAMES};t['hp_heat']=sum((D(v['heat_MWh']) for v in ns),D(0));t['recovered_source']=sum((D(v['source_MWh']) for v in ns),D(0));t['compressor_work']=t['hp_heat']-t['recovered_source'];t['standing_loss']=sum((D(v['standing_MWh']) for v in ns),D(0))
                for row,u in zip(tr,uu):
                    dt=dec(u[4]);direct,charge,dis,back,unmet=map(dec,row[120:125])
                    t['charge_loss']+=(1-p[6])*charge*dt;t['discharge_loss']+=(1/p[7]-1)*dis*dt
                    t['delivered_service']+=(direct+dis+back)*dt;t['backup_heat']+=back*dt;t['unmet_demand']+=unmet*dt
                t['auxiliary_work']=p[20]*t['compressor_work'];t['final_inventory']=D(ns[-1]['energy_MWh'])
                check('comparison_inputs',id+'_v66',uu==rows(target['input']) and cfg[35:]==target['p'])
            else:
                pp=r['p'];raw=rows(r['segments']);bs=rows(r['boundary']);acc=rows(r['accounting']);t={k:D(0) for k in NAMES};inventory=dec(r['initial'][0]);elapsed=D(0)
                check('v57_completed_prefix',id,len(tr)==r['completed_intervals'] and all(len(v)>=len(tr) for v in [raw,bs,acc,uu]))
                check('v57_initial_clock_mapping',id,r['m0']==[target['adapter']['initial'][1],target['adapter']['initial'][2],0,0])
                if r['model']=='v57_refusal':
                    check('v57_observed_refusal',id,'Clock cumulative accuracy budget exceeded' in r['error_message'] and 0<len(tr)<len(uu))
                for tick,(row,u,zs,b,ac) in enumerate(zip(tr,uu,raw,bs,acc)):
                    name=f'{id}_{tick}';want=boundary57(u);check('v57_boundary',name,all(near(x,y) for x,y in zip(b,want)))
                    check('v57_handoff',name,abs(dec(r['energy_start'][tick] if isinstance(r['energy_start'][tick],(float,int)) else r['energy_start'][tick][0])-inventory)<D('1e-10'))
                    duration=D(0);macro={k:D(0) for k in NAMES}
                    for slot in range(64):
                        z=zs[28*slot:28*(slot+1)];span=dec(z[1])
                        if span==0:continue
                        for label,ok in segment57(z,u,pp).items():check('v57_'+label,name+f'_{slot}',ok)
                        check('v57_inventory_chain',name+f'_{slot}',abs(dec(z[3])-inventory)<D('1e-10'));inventory=dec(z[4]);duration+=span
                        for key,index in [('hp_heat',10),('recovered_source',12),('compressor_work',11),('delivered_service',19),('backup_heat',8),('unmet_demand',9)]:macro[key]+=dec(z[index])*span
                        for key,index in [('standing_loss',16),('charge_loss',17),('discharge_loss',18)]:macro[key]+=dec(z[index])
                    macro['auxiliary_work']=p[20]*macro['compressor_work'];elapsed+=duration
                    for key in NAMES:t[key]+=macro[key]
                    check('v57_macro',name,abs(duration-dec(r['dt']))<D('1e-10') and near(ac[0],macro['compressor_work']) and near(ac[1],macro['auxiliary_work']))
                    s=rows(target['adapter']['schedule'])[tick]
                    check('comparison_inputs',name+'_v57',u[16]==s[2] and u[10]==s[3] and s[4]==int(s[3]>0))
                t['final_inventory']=inventory;check('MAT',id+'_v57',(folder/(id+'_v57.mat')).stat().st_size>1000)
            t['external_electricity']=t['compressor_work']+t['auxiliary_work'];aggregates[id,r['model']]=t
            base=aggregates[id,'v73r2']
            if r['model']=='v57_refusal':
                matched=copy.deepcopy(target);matched['input']=rows(matched['input'])[:len(tr)];matched['trace']=rows(matched['trace'])[:len(tr)]
                _,matched_ns=analyze(matched);base=total_earliest(matched,matched_ns)
            equal=abs(base['delivered_service']-t['delivered_service'])<=D('1e-10')*max(D(1),base['delivered_service'])
            comparisons.append(dict(id=id,model=r['model'],equal_delivered_service_within_budget=equal,service_budget='1e-10 relative to max(1,base service) MWh',
                delivered_service_delta_MWh=str(base['delivered_service']-t['delivered_service']),external_electricity_delta_MWh=str(base['external_electricity']-t['external_electricity']),unmet_delta_MWh=str(base['unmet_demand']-t['unmet_demand']),
                completed_intervals=len(tr),attempted_intervals=len(uu),full_schedule_accepted=r['model']!='v57_refusal',
                interpretation='VALID_PREFIX_ONLY_FULL_LEGACY_SCHEDULE_REFUSED' if r['model']=='v57_refusal' else 'EQUAL_SERVICE_MODEL_BOUNDARY_COMPARISON' if equal else 'UNEQUAL_SERVICE_NO_COST_OR_EFFICIENCY_RANKING',
                boundary_difference=r.get('boundary_semantics','SAMPLED_CONSERVATIVE_HOLD_POLICY_SAME_DYNAMIC_CONDENSER_BOUNDARY')))
        for model in ['v66','v57']:
            comp=next(c for c in comparisons if c['id']=='equal_service_HP' and c['model'].startswith(model));check('equal_service_control',model,comp['equal_delivered_service_within_budget'] and comp['full_schedule_accepted'])
        base=aggregates['seasonal_0p25','v73r2']
        for id in ['seasonal_0p5','seasonal_1p0']:
            for key,v in aggregates[id,'v73r2'].items():check('partition',id+'_'+key,abs(v-base[key])<D('1e-85')*max(D(1),abs(v)))
        target=next(r for r in report['runs'] if r['id']=='seasonal_0p5');totals=aggregates[target['id'],'v73r2']
        for label,field in [('source_omitted','recovered_source_MWh_hull'),('unmet_service_credit','delivered_service_MWh_hull'),('electricity_omitted','external_electricity_MWh_hull'),('TES_omitted','TES_service_MWh_hull'),('demand_omitted','demand_MWh_hull'),('ratio_midpoint','delivered_HP_heating_COP_hull')]:
            bad=copy.deepcopy(target);box=bad['summary'][field]
            if label=='unmet_service_credit':bad['summary'][field]=[float(totals['delivered_service']+totals['unmet_demand'])]*2
            elif label=='ratio_midpoint':bad['summary'][field]=[sum(box)/2]*2
            else:bad['summary'][field]=[0,0]
            found=review_report(bad,totals);mutations.append(dict(name=label,passed=not all(found.values())))
        bad=copy.deepcopy(target);bad['summary']['held_intervals']-=1;mutations.append(dict(name='incomplete_count',passed=not all(review_report(bad,totals).values())))
    probes={r['id']:r for r in report['probes']}
    for c in spec['cases']:
        p=probes[c['id']];check('runtime',c['id']+'_expected',p['accepted']==(not c['expected_guard']))
        if c['expected_guard']:check('runtime',c['id']+'_observed_guard',p['identifier'] and c['expected_guard'] in p['message'] and c['expected_guard'] in p['host_message'])
    check('Stateflow','actual_modes',report['mode_coverage']==list(range(6)))
    check('Stateflow','observed_license_chart',report['metadata']['license_observed']==1 and report['metadata']['chart_count']==1 and report['metadata']['simulation_mode']=='normal')
    check('MATLAB','all_assertions',report['summary']['failed']==0 and all(c['passed'] for c in report['assertions']))
    for manifest in ['preservation.json','source_hashes.json']:
        for r in json.loads((folder/manifest).read_text()):
            # The reviewer was developed after the run's initial snapshot.
            # Only its own initial draft may differ; production sources and
            # prior artifacts still require their original live hashes.
            current=sha(ROOT/r['path'])==r['sha256'] or (manifest=='source_hashes.json' and r['path']=='audit/verify_held_schedule_v74.py')
            check(manifest,r['path'],current and (manifest=='preservation.json' or sha(folder/'source_snapshot'/r['path'])==r['sha256']))
    reviewer=json.loads(sorted(folder.glob('reviewer_manifest_*.json'))[-1].read_text())
    for r in reviewer['records']:check('executed_reviewer_seal',r['path'],sha(ROOT/r['path'])==r['sha256'] and sha(folder/reviewer['snapshot']/r['path'])==r['sha256'])
    receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')];check('receipt','successful_batch',any(r['exit_code']==0 for r in receipts))
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');csvpath=folder/f'closed_schedule_traces_v74_{stamp}.csv'
    with csvpath.open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(numeric[0]));w.writeheader();w.writerows(numeric)
    result=dict(version='0.74',timestamp_utc=datetime.now(timezone.utc).isoformat(),checks=checks,reviewer_selfchecks=mutations,comparisons=comparisons,
        aggregates=[dict(id=id,model=model,**{k:str(v) for k,v in t.items()}) for (id,model),t in aggregates.items()],numeric_csv=csvpath.name,
        independence='Same-agent independent exact-binary closed exp/log trajectories and source integrals; no production calls. Original MAT reopened/exported by MATLAB.',
        summary=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks)))
    out=folder/f'independent_QA_v74_{stamp}.json';out.write_text(json.dumps(result,indent=2)+'\n');failed=[c for c in checks if not c['passed']]
    log=dict(qa=out.relative_to(ROOT).as_posix(),summary=result['summary'],selfchecks=mutations,comparisons=comparisons,failed=failed[:100]);print(json.dumps({k:v for k,v in log.items() if k!='comparisons'}))
    (folder/f'independent_QA_v74_{stamp}.log').write_text(json.dumps(log,indent=2)+'\n')
    return int(bool(failed) or not all(m['passed'] for m in mutations))
if __name__=='__main__':sys.exit(main())
