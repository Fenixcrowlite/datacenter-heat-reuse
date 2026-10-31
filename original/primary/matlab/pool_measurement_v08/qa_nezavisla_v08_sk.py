# -*- coding: utf-8 -*-
"""Independent raw CSV QA: full signal wiring, no Ttrue->safety sensor shortcut.
Data are SYNTHETIC D from v07. This tests import/replay, NOT real calibration."""
from pathlib import Path
import csv,json,hashlib,math
BASE=Path(__file__).resolve().parents[2]
R=BASE/'results'/'pool_measurement_v08'
j=json.loads((R/'vysledky_v08_SK.json').read_text(encoding='utf-8'))
assert len(j['cases'])==8
checks=0;cases=[]
def verify(condition,*why):
 global checks
 checks+=1
 if not condition:raise AssertionError(why)
for sc in j['cases']:
 name=sc['scenario']
 with (R/f'sim_v08_{name}_SK.csv').open(encoding='utf-8-sig',newline='') as f:
  rows=[{k:float(v) for k,v in line.items()} for line in csv.DictReader(f)]
 with (R/'staged_D'/name/'normalized_measurements_v07.csv').open(encoding='utf-8-sig',newline='') as f:
  ext=[r for r in csv.DictReader(f)]
 meta=json.loads((R/'staged_D'/name/'validated_dataset_metadata.json').read_text(encoding='utf-8'))
 verify(meta['provenance']=='D',name,'not real')
 verify(len(rows)==672 and len(ext)==672,name,'records')
 prevT=16.;prevE=0.45*3.6e9;prevIT=30.;prevLatch=False
 maxTdiff=maxQdiff=0.
 with (BASE/'results'/'pool_redundancy_v07'/f'scenar_{name}_SK.csv').open(encoding='utf-8-sig',newline='') as f:
  gold=[{k:float(v) for k,v in line.items()} for line in csv.DictReader(f)]
 for k,(r,m,g) in enumerate(zip(rows,ext,gold)):
  qdc=r['Q_DC_eff_W'];src=r['Q_HP_source_W'];Qh=r['Q_HX_phys_W']
  qout=r['Q_reject_physical_W'];qu=r['Q_unhandled_W']
  leak=r['Q_leak_W'];phys=r['Q_pool_phys_W'];T=r['T_pool_C']
  Ti=r['T_IT_model_C'];comp=r['P_HP_W'];shed=r['Q_IT_shed_W']
  cmd=phys-leak;z1=float(m['T_pool_sensor1_C']);z2=float(m['T_pool_sensor2_C'])
  verify(all(math.isfinite(v) for v in r.values()),name,k,'finite')
  verify(abs(r['cas_h']-k/4)<1e-10,name,k,'time')
  verify(abs(r['external_T1_C']-z1)<1e-8 and abs(r['external_T2_C']-z2)<1e-8,
   name,k,'actual staged external sensors')
  verify(abs(r['sensor1_C']-z1)<1e-7 and abs(r['sensor2_C']-z2)<1e-7,
   name,k,'Stateflow gate received external sensor inputs')
  verify(abs((T-prevT)*997*500*4182/900-(phys-r['Q_pool_loss_W']))<1e-5,
   name,k,'pool first law')
  verify(abs(qdc-Qh-src-qout-qu)<1e-5,name,k,'DC first law')
  verify(abs(r['Q_HP_pool_W']+r['Q_HP_DH_W']+r['Q_HP_charge_W']-src-comp)<1e-5,
   name,k,'HP first law')
  verify(abs(r['Q_reject_command_W']-leak-qout-qu)<1e-5,name,k,'reject first law')
  verify(abs(r['Q_reject_total_W']-r['Q_reject_main_W']-r['Q_reject_backup_W'])<1e-5,
   name,k,'reject 2 channels')
  verify(abs(r['Q_DC_source_raw_W']-qdc-shed)<1e-5,
   name,k,'IT shed accounting')
  verify(abs(r['residual_DC_W'])<1e-5 and abs(r['residual_reject_W'])<1e-5,
   name,k,'residual')
  verify(10<T<55 and qout>=0 and qu>=0 and leak>=0,name,k,'signs')
  fault=(abs(z1-z2)>.35 or max(z1,z2)>=27.7 or r['flow_ok']<.5 or r['E_STOP']>.5)
  expected=fault or (prevLatch and not(r['manual_RESET']>.5 and max(z1,z2)<=27.65))
  verify((r['safety_latch']>.5)==expected,name,k,'latch based on external measurements only')
  if expected:verify(abs(cmd)<1e-6,name,k,'software heating off on latch')
  if not(r['primary_valve_stuck']>.5 and r['secondary_valve_stuck']>.5):
   verify(leak==0,name,k,'isolation valve hardware fault independent')
  TIT=max(30,prevIT+900*(qu-max(0,2000*(prevIT-30)))/8e6)
  verify(abs(TIT-Ti)<1e-7,name,k,'IT thermal indicator')
  verify(abs(T-g['T_pool_C'])<0.005,name,k,'regression water')
  verify(abs(phys-g['Q_pool_phys_W'])<200,name,k,'regression heat')
  maxTdiff=max(maxTdiff,abs(T-g['T_pool_C']))
  maxQdiff=max(maxQdiff,abs(phys-g['Q_pool_phys_W']))
  prevT=T;prevIT=Ti;prevLatch=expected
 verify(abs(maxTdiff-sc['maximum_temperature_error_vs_v07_C'])<1e-9,name,'diff compare')
 cases.append({'name':name,'rows':672,'source_class':'D_SYNTHETIC',
   'max_temperature_diff_C':maxTdiff,'max_heating_diff_W':maxQdiff})
sha={}
for path in ['matlab/simulink/DCHR_Electrical_Dispatch_Stateflow_v85.slx',
             'matlab/pool_redundancy_v07/DC_Bazen_Dvojita_Ochrana_v07_SK.slx',
             'matlab/pool_measurement_v08/DC_Bazen_Externe_Merania_v08_SK.slx']:
 sha[path]=hashlib.sha256((BASE/path).read_bytes()).hexdigest()
verify(sha['matlab/simulink/DCHR_Electrical_Dispatch_Stateflow_v85.slx']==
 '2a9de22c0c55e8c4a87f7b0e0cfe9cd97db08c991f09d98361b009de310adde7',
 'original v85 unchanged')
p={'status':'PASS','checks':checks,'cases':cases,'source_class':'D_SYNTHETIC_REPLAY',
 'models_sha256':sha,'semantic_warning':'Validated signal wiring, not measured calibration, not field sensor independence'}
(R/'QA_NEZAVISLA_V08_SK.json').write_text(json.dumps(p,indent=2,ensure_ascii=False),encoding='utf-8')
print('INDEPENDENT_V08_QA_PASS',checks,'assertions',len(cases),'cases')
