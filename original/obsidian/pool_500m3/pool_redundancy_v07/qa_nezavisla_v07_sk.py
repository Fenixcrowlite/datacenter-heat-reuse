# -*- coding: utf-8 -*-
"""Independent CSV regression/physics audit, not using MATLAB implementation."""
import csv,json,math,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[2];O=P/'results'/'pool_redundancy_v07'
j=json.loads((O/'vysledky_v07_SK.json').read_text(encoding='utf-8'))
assert len(j['cases'])==8
count=0;rowsum=[]
def ck(ok,*context):
 global count
 count+=1
 if not ok:raise AssertionError(context)
for sc in j['cases']:
 name=sc['scenar']
 with (O/f'scenar_{name}_SK.csv').open(encoding='utf-8-sig',newline='') as f:
  rows=[{k:float(v) for k,v in line.items()} for line in csv.DictReader(f)]
 ck(len(rows)==672,name,'row count')
 Tprev=16.;TIprev=30.;prevLatch=False
 leakE=unhandledE=backupE=mainE=shedE=0
 alarms=0;unsafe=0
 for k,r in enumerate(rows):
  Tw=r['T_pool_C'];Ti=r['T_IT_model_C']
  Qorig=r['Q_DC_source_raw_W'];Qdc=r['Q_DC_eff_W'];shed=r['Q_IT_shed_W']
  direct=r['Q_HX_phys_W'];hpSrc=r['Q_HP_source_W']
  reject=r['Q_reject_physical_W'];main=r['Q_reject_main_W'];backup=r['Q_reject_backup_W']
  unhandled=r['Q_unhandled_W'];leak=r['Q_leak_W']
  command=r['Q_pool_phys_W']-leak
  ck(all(math.isfinite(v) for v in r.values()),name,k,'finite')
  ck(abs(r['cas_h']-k/4)<1e-10,name,k,'clock')
  ck(abs((Tw-Tprev)*997*500*4182/900-(r['Q_pool_phys_W']-r['Q_pool_loss_W']))<1e-5,name,k,'water')
  ck(abs(Qdc-(direct+hpSrc+reject+unhandled))<1e-5,name,k,'DC first law')
  ck(abs(r['Q_HP_pool_W']+r['Q_HP_DH_W']+r['Q_HP_charge_W']-hpSrc-r['P_HP_W'])<1e-5,name,k,'HP first law')
  ck(abs(r['Q_pool_phys_W']-direct-r['Q_HP_pool_W'])<1e-5,name,k,'pool heat')
  ck(abs(reject-main-backup)<1e-5,name,k,'dual reject')
  ck(abs(r['Q_reject_command_W']-leak-reject-unhandled)<1e-5,name,k,'reject leak continuity')
  ck(abs(Qorig-Qdc-shed)<1e-5,name,k,'source load shedding')
  ck(0<=main<=180000+.0001 and 0<=backup<=150000+.0001,name,k,'capacity bounds')
  ck(0<=shed<=Qorig+1e-7 and unhandled>=0 and leak>=0,name,k,'no negative heat')
  ck(abs(r['residual_reject_W'])<1e-5,name,k,'reject residual')
  ck(abs(r['residual_DC_W'])<1e-5,name,k,'dc residual')
  ck(command>=-1e-6,name,k,'software command nonnegative')
  ck(10<Tw<55,name,k,'reasonable synthetic water')
  ck(abs(main-min(max(0,r['Q_reject_command_W']-leak),180000*r['reject_main_availability']))<1e-6,name,k,'main physical valve')
  rest=max(0,r['Q_reject_command_W']-leak-main)
  ck(abs(backup-min(rest,150000*r['reject_backup_availability']))<1e-6,name,k,'backup cooler')
  shouldLeak=(r['primary_valve_stuck']>.5 and r['secondary_valve_stuck']>.5 and command<=1e-7)
  if not shouldLeak:ck(leak==0,name,k,'single valve isolation')
  if r['safety_latch']>.5:ck(abs(command)<1e-6,name,k,'software safety command off')
  # independent delayed sensors, fully observable only in test CSV
  ts1=(rows[k-2]['T_pool_C'] if k>=2 else 16.)+r['bias1_K']
  ts2=(rows[k-3]['T_pool_C'] if k>=3 else 16.)+r['bias2_K']
  ck(abs(ts1-r['sensor1_C'])<1e-6,name,k,'sensor lag 15m')
  ck(abs(ts2-r['sensor2_C'])<1e-6,name,k,'sensor lag 30m')
  fault=(abs(ts1-ts2)>.35 or max(ts1,ts2)>=27.7 or r['flow_ok']<.5 or r['E_STOP']>.5)
  wantedLatch=fault or (prevLatch and not(r['manual_RESET']>.5 and max(ts1,ts2)<=27.65))
  ck((r['safety_latch']>.5)==wantedLatch,name,k,'safety latch state')
  newTi=max(30,TIprev+900*(unhandled-max(0,2000*(TIprev-30)))/8e6)
  ck(abs(Ti-newTi)<1e-7,name,k,'IT buffer state')
  ck((r['IT_model_alarm']>.5)==(Ti>=42),name,k,'IT indicator')
  intendedShedding=(TIprev>=38 and r['reject_main_availability']<.5 and
       r['reject_backup_availability']<.5 and r['IT_shedding_enable']>.5)
  if intendedShedding:
   ck(abs(shed-.7*Qorig)<1e-6,name,k,'70% mitigation')
  else:
   ck(shed==0,name,k,'not authorized to shed')
  leakE+=leak/4e6;unhandledE+=unhandled/4e6
  mainE+=main/4e6;backupE+=backup/4e6;shedE+=shed/4e6
  unsafe+=int(r['leak_at_zero_cmd']>.5);alarms+=int(r['IT_model_alarm']>.5)
  Tprev=Tw;TIprev=Ti;prevLatch=wantedLatch
 for metric,observed in [('leak_MWh',leakE),('unhandled_MWh',unhandledE),
   ('main_rejected_MWh',mainE),('backup_rejected_MWh',backupE),
   ('IT_avoided_source_MWh',shedE)]:
  ck(abs(sc[metric]-observed)<1e-8,name,metric)
 ck(unsafe==sc['unsafe_leak_samples'],name,'unsafe count')
 ck(alarms==sc['IT_alarm_samples'],name,'alarm count')
 rowsum.append({'scenario':name,'rows':672,'leak_MWh':leakE,'unhandled_MWh':unhandledE,
  'rejected_backup_MWh':backupE,'IT_heat_avoided_MWh':shedE,'T_IT_max_C':sc['T_IT_model_max_C']})
R={q['scenario']:q for q in rowsum}
ck(R['primarny_ventil_zaseknuty']['leak_MWh']==0,'primary alone fails closed')
ck(R['oba_ventily_zaseknute']['leak_MWh']>0,'dual valve heat leak reproduced')
ck(R['hlavny_REJECT_off_zalozny_ok']['unhandled_MWh']==0,'backup rejection sufficient')
ck(R['hlavny_REJECT_off_zalozny_ok']['rejected_backup_MWh']>0,'backup used')
ck(R['oba_REJECT_off_bez_shedding']['unhandled_MWh']>
  R['oba_REJECT_off_so_shedding']['unhandled_MWh'],'mitigation improves heat balance')
ck(R['oba_REJECT_off_so_shedding']['IT_heat_avoided_MWh']>0,'mitigation switched on')
hashes={}
for f in ['matlab/simulink/DCHR_Electrical_Dispatch_Stateflow_v85.slx',
 'matlab/pool_feedback_v04/DC_Bazen_Uzavreta_Regulacia_v04_SK.slx',
 'matlab/pool_safety_v05/DC_Bazen_Bezpecnost_v05_SK.slx',
 'matlab/pool_failure_v06/DC_Bazen_Fyzikalne_Poruchy_v06_SK.slx',
 'matlab/pool_redundancy_v07/DC_Bazen_Dvojita_Ochrana_v07_SK.slx']:
 path=P/f
 hashes[f]=hashlib.sha256(path.read_bytes()).hexdigest()
ck(hashes['matlab/simulink/DCHR_Electrical_Dispatch_Stateflow_v85.slx']==
 '2a9de22c0c55e8c4a87f7b0e0cfe9cd97db08c991f09d98361b009de310adde7','v85 modified')
result={'status':'PASS','checks':count,'scenario_count':len(rowsum),'scenarios':rowsum,
 'models_sha256':hashes,'data_provenance':'D synthetic','safety_statement':
 'Physical redundant devices and automatic load reduction are hypothetical. Not a safety certification.'}
(O/'QA_NEZAVISLA_V07_SK.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
print('V07_INDEPENDENT_QA_PASS',count,'assertions',len(rowsum),'scenarios')
