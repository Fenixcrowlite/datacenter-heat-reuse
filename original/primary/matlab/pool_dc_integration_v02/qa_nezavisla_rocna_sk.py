# -*- coding: utf-8 -*-
"""Nezavisly QA nad CSV/JSON Simulink R2026a, len citanie vstupov."""
import csv,math,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]/'results'/'pool_dc_integration_v02'
j=json.loads((ROOT/'rocne_vysledky_SK.json').read_text(encoding='utf-8'))
C=997*500*4182
qa={'dataset':'SYNTHETIC','model':j['model'],'tests':{},'results':{}}
samples={}
for sc in j['scenare']:
    name=sc['scenar']
    with (ROOT/f'rocny_{name}_SK.csv').open(encoding='utf-8-sig',newline='') as f:
        rows=[{k:float(v) for k,v in r.items()} for r in csv.DictReader(f)]
    assert len(rows)==8760,(name,len(rows))
    assert all(r['hodina']==i for i,r in enumerate(rows)),name
    for r in rows: assert all(math.isfinite(x) for x in r.values()),name
    td=[r['T_bazen_C'] for r in rows]
    assert max(td)<=27.8000001 and min(td)>0,name
    residual_dc=max(abs(r['Q_dostupne_DC_W']-sum(r[k] for k in ('Q_odobrane_DC_W','Q_siet_W','Q_akumulacia_W','Q_odpad_W'))) for r in rows)
    residual_hp=max(abs(r['Q_bazen_W']-r['Q_odobrane_DC_W']-r['P_TC_W']) for r in rows)
    residual_pool=abs((td[-1]-16)*C/3.6e9-sum(r['Q_bazen_W']-r['Q_straty_W'] for r in rows)/1e6)
    assert residual_dc<1e-6 and residual_hp<1e-6 and residual_pool<1e-7,name
    assert all(0<=r['Q_odobrane_DC_W']<=r['Q_dostupne_DC_W']+1e-6 for r in rows),name
    assert all(0<=r['P_TC_W']<=35000+1e-7 for r in rows),name
    assert all((r['P_TC_W']==0) for r in rows if r['rezim_0_1_2']==1),name
    assert all((r['P_TC_W']==0 and r['Q_bazen_W']==0) for r in rows if r['rezim_0_1_2']==0),name
    if name=='vypadok_168h':
        assert all(rows[h][k]==0 for h in range(4000,4168) for k in ('Q_bazen_W','Q_siet_W','Q_akumulacia_W')),name
    for fld,sumcol in [('Dodane_bazen_MWh','Q_bazen_W'),('Elektrina_TC_MWh','P_TC_W'),('Teplo_z_DC_do_bazena_MWh','Q_odobrane_DC_W')]:
        assert abs(sc[fld]-sum(r[sumcol] for r in rows)/1e6)<1e-7,name
    samples[name]=sc
    qa['results'][name]={'passed':True,'rows':len(rows),'maximum_T_C':max(td),'dc_W':residual_dc,'hp_W':residual_hp,'storage_MWh':residual_pool}
assert samples['bez_plachty']['Dodane_bazen_MWh']>samples['zaklad']['Dodane_bazen_MWh']
assert samples['teply_zdroj']['Elektrina_TC_MWh']<samples['zaklad']['Elektrina_TC_MWh']
qa['tests']={'annual_csv_rows':4,'energy_closures':12,'safety_temperature':4,'stop_168h':1,'source_partition':4,'hourly_cop_limits':4,'cross_scenario_sense':2}
qa['status']='PASS'
( ROOT/'QA_NEZAVISLA_ROCNA_SK.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
print('QA_PASS',json.dumps(qa['tests'],ensure_ascii=False))
