# -*- coding: utf-8 -*-
"""CSV-level independent audit of Stateflow v04 (not using MATLAB helpers)."""
import csv,hashlib,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[2]; O=R/'results'/'pool_feedback_v04'
D=json.loads((O/'vysledky_dispecer_v04_SK.json').read_text(encoding='utf-8'))
hash85=hashlib.sha256((R/'matlab'/'simulink'/'DCHR_Electrical_Dispatch_Stateflow_v85.slx').read_bytes()).hexdigest()
assert hash85=='2a9de22c0c55e8c4a87f7b0e0cfe9cd97db08c991f09d98361b009de310adde7'
total=0;cases=[]
def check(value,identifier):
 global total
 total+=1
 assert value,identifier
for s in D['scenarios']:
 name=s['scenar']
 with (O/f'scenar_{name}_SK.csv').open(encoding='utf-8-sig',newline='') as f:
  rows=[{k:float(v) for k,v in line.items()} for line in csv.DictReader(f)]
 check(len(rows)==672,(name,'rows'));T0=16.;E0=.45*3.6e9
 seen=set()
 for i,r in enumerate(rows):
  T=r['T_bazen_C'];E=r['E_TES_J'];seen.add(round(r['rezim_Stateflow']))
  qpool=r['Q_pool_W']; qdc=r['Qdc_in_W']; qcharge=r['Q_HP_TES_charge_W']; qdis=r['Q_TES_dis_W']
  qdh=r['Q_DH_delivered_W'];qdirect=r['Q_direct_W'];qhpsrc=r['Q_HP_source_W']
  check(all(math.isfinite(x) for x in r.values()),(name,i,'finite'))
  check(abs((T-T0)*997*500*4182/900-(qpool-r['Q_pool_loss_W']))<1e-5,(name,i,'water'))
  check(abs((E-E0)/900-(0.93*qcharge-qdis/0.91-r['Q_TES_standing_loss_W']))<1e-5,(name,i,'TES'))
  check(abs(qdc-(qdirect+qhpsrc+r['Q_reject_W']))<1e-5,(name,i,'source'))
  check(abs(r['Q_HP_pool_W']+r['Q_HP_DH_W']+qcharge-qhpsrc-r['P_HP_comp_W'])<1e-5,(name,i,'HP'))
  check(abs(qpool-qdirect-r['Q_HP_pool_W'])<1e-5,(name,i,'pool'))
  check(abs(qdh-r['Q_HP_DH_W']-qdis)<1e-5,(name,i,'DH'))
  check(10<T<=27.750001 and 0<=E<=.9*3.6e9+1e-5,(name,i,'safe'))
  check(0<=qpool<=150000.1 and 0<=r['P_HP_comp_W']<=55000.1,(name,i,'limits'))
  check(not(qcharge>1e-6 and qdis>1e-6),(name,i,'no simultaneous TES'))
  check(qdh<=r['Qdh_demand_W']+1e-6,(name,i,'DH max'))
  if r['IT_ok']<.5:
   check(qpool==0 and qhpsrc==0 and r['P_HP_comp_W']==0,(name,i,'IT STOP'))
  if r['BAZEN_ok']<.5:check(qpool==0,(name,i,'pool STOP'))
  if r['TES_ok']==0:check(qcharge==0 and qdis==0,(name,i,'TES off'))
  if r['IT_ok']<.5: expected=4
  elif qdc<1e-6:expected=3 if E0>1e5 and r['TES_ok']>.5 and r['Qdh_demand_W']>0 else 0
  elif r['HX_ok']>.5 and r['BAZEN_ok']>.5 and r['Q_pool_req_W']>0 and r['Tdc_C']>T0+5:expected=1
  else:expected=2
  check(round(r['rezim_Stateflow'])==expected,(name,i,'mode',expected))
  T0,E0=T,E
 check(abs(sum(r['Q_pool_W'] for r in rows)*900/3.6e9-s['Bazen_delivered_MWh'])<1e-8,(name,'JSON'))
 cases.append({'case':name,'modes':sorted(seen),'rows':len(rows),'Tmax_C':max(r['T_bazen_C'] for r in rows)})
S={x['scenar']:x for x in D['scenarios']}
check(S['bez_plachty']['Bazen_delivered_MWh']>S['zaklad']['Bazen_delivered_MWh'],'no cover')
check(S['teplejsi_zdroj']['HP_compressor_MWh']<S['zaklad']['HP_compressor_MWh'],'warmer source')
check(S['vypnuty_bazen']['Bazen_delivered_MWh']<S['zaklad']['Bazen_delivered_MWh'],'pool feedback')
check(S['TES_vypnute']['DH_unmet_MWh']>S['zaklad']['DH_unmet_MWh'],'TES influence')
check(S['vysoky_dopyt_DH']['DH_unmet_MWh']>S['zaklad']['DH_unmet_MWh'],'DH demand')
q={'status':'PASS','checks':total,'cases':cases,'source':'RAW_SIMULINK_CSV','old_v85_sha256':hash85}
(O/'QA_NEZAVISLA_V04_SK.json').write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8')
print('QA_V04_PASS',total,'CHECKS',len(cases),'CASES')
