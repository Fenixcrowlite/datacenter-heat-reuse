# -*- coding: utf-8 -*-
"""Nezavisle kontrolne vypocty zo skutocneho v85 replay a v03 CSV."""
import json,csv,math,hashlib,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/'results'/'pool_v85_bridge_v03'
report=json.loads((OUT/'most_v85_bazen_v03_SK.json').read_text(encoding='utf-8'))
old=ROOT/'matlab'/'simulink'/'DCHR_Electrical_Dispatch_Stateflow_v85.slx'
digest=hashlib.sha256(old.read_bytes()).hexdigest()
assert digest=='2a9de22c0c55e8c4a87f7b0e0cfe9cd97db08c991f09d98361b009de310adde7',digest
assert len(report['cases'])>=6,'Malo scenarov na QA'
C=997*500*4182
summary={'schema':'V03_INDEPENDENT_QA','old_v85_sha256':digest,'test_count':0,'cases':[]}
byname={}
for case in report['cases']:
    name=case['id']
    with (OUT/('sim_'+name+'.csv')).open(encoding='utf-8-sig',newline='') as f:
        data=[{k:float(v) for k,v in line.items()} for line in csv.DictReader(f)]
    n=case['pocet_intervalov']
    assert len(data)==n
    before=sum(r['Q_v85_povodna_sluzba_W'] for r in data)*.25/1e6
    pool=sum(r['Q_bazen_W'] for r in data)*.25/1e6
    rest=sum(r['Q_DH_povodne_W'] for r in data)*.25/1e6
    losses=sum(r['Q_straty_W'] for r in data)*.25/1e6
    initial=27.70 if 'tepla_voda' in name else 16
    tfin=data[-1]['T_bazen_C']
    assert abs(pool+rest-before)<1e-10
    assert abs(C*(tfin-initial)/3.6e9-(pool-losses))<1e-10
    assert max(r['T_bazen_C'] for r in data)<=27.750000001
    assert all(0<=r['Q_bazen_W']<=150000.00001 for r in data)
    assert all(abs(r['Q_bazen_W']+r['Q_DH_povodne_W']-r['Q_v85_povodna_sluzba_W'])<=1e-6 for r in data)
    if 'stop_bazen' in name:assert all(r['Q_bazen_W']==0 for r in data)
    if 'charge_' in name:assert pool<1e-12,'TES charging must not become pool heat'
    assert abs(before-case['v85_hp_direct_service_MWh'])<1e-8
    lo,hi=case['v85_hull_direct_HP_MWh']
    assert lo-1e-8<=before<=hi+1e-8
    byname[name]=dict(pool=pool,before=before,rem=rest)
    summary['cases'].append({'id':name,'checked':True,'pool_MWh':pool,'other_service_MWh':rest,'source_service_MWh':before})
    summary['test_count']+=10
for case in report['cases']:
    k=case['id']
    if 'stop_bazen' in k:
        companion=k.replace('stop_bazen','studena_voda')
        assert abs(byname[k]['before']-byname[companion]['before'])<1e-12
    summary['test_count']+=1
summary['status']='VERIFIED'
(OUT/'QA_NEZAVISLA_V85_BRIDGE_SK.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print('QA_V85_BRIDGE_PASS',len(summary['cases']),'cases',summary['test_count'],'checks')
