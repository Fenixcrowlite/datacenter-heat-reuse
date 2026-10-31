# -*- coding: utf-8 -*-
"""Independent first-law, delayed sensors, latch and physical failure QA from CSV."""
from pathlib import Path
import csv,json,math,hashlib
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results'/'pool_failure_v06'
report=json.loads((OUT/'vysledky_v06_SK.json').read_text(encoding='utf-8'))
assert len(report['scenarios'])==7
cases=[]; checks=0
def ck(flag,context):
 global checks
 checks+=1
 if not flag:raise AssertionError(context)
for s in report['scenarios']:
 name=s['scenar']
 with (OUT/f'scenar_{name}_SK.csv').open(encoding='utf-8-sig',newline='') as f:
  rows=[{k:float(v) for k,v in rec.items()} for rec in csv.DictReader(f)]
 ck(len(rows)==672,(name,'length'))
 Tprev=16.;ITprev=30.;latchPrev=False; leakSum=0;excessSum=0;stuckUnsafe=0;alarms=0
 for i,r in enumerate(rows):
  t=r['T_pool_C'];TIT=r['T_IT_risk_C'];qpool=r['Q_pool_actual_W']
  qleak=r['Q_stuck_leak_W'];qcmd=qpool-qleak
  dc=r['Q_DC_available_W']; Qrej=r['Q_reject_actual_W']
  QhpSrc=r['Q_HP_source_W']
  Qex=r['Q_reject_unhandled_W']
  direct=r['Q_HX_physical_W']; Qloss=r['Q_pool_loss_W']
  ck(all(math.isfinite(v) for v in r.values()),(name,i,'finite'))
  ck(abs(r['cas_h']-i/4)<1e-9,(name,i,'clock'))
  ck(abs((t-Tprev)*997*500*4182/900-(qpool-Qloss))<1e-5,(name,i,'water'))
  ck(abs(dc-direct-QhpSrc-Qrej-Qex)<1e-5,(name,i,'dc'))
  ck(abs(r['Q_HP_pool_W']+r['Q_HP_DH_W']+r['Q_HP_TES_W']-QhpSrc-r['P_HP_W'])<1e-5,(name,i,'hp'))
  ck(abs(qpool-direct-r['Q_HP_pool_W'])<1e-5,(name,i,'pool'))
  ck(abs(Qrej+Qex+qleak-r['Q_reject_command_W'])<1e-5,(name,i,'reject+leak'))
  expectedIT=max(30.,ITprev+900*(Qex-max(0,2000*(ITprev-30)))/8e6)
  ck(abs(TIT-expectedIT)<1e-7,(name,i,'ITbuffer'))
  ck(abs(r['IT_risk_alarm']-(1 if TIT>=42 else 0))<.1,(name,i,'alarm'))
  ck(0<=qleak<=25000.0001 and Qrej>=0 and Qex>=0,(name,i,'nonnegative flows'))
  ck(10<t<55,(name,i,'pool nonsafety bound'))
  ck(abs(r['Q_balance_DC_W'])<1e-5,(name,i,'dc residual'))
  ck(qcmd>=-1e-6,(name,i,'command nonnegative'))
  measured1=(rows[i-2]['T_pool_C'] if i>=2 else 16.)+r['bias1_K']
  measured2=(rows[i-3]['T_pool_C'] if i>=3 else 16.)+r['bias2_K']
  ck(abs(measured1-r['sensor_1_C'])<1e-6,(name,i,'sensor lag1'))
  ck(abs(measured2-r['sensor_2_C'])<1e-6,(name,i,'sensor lag2'))
  invalid=not(math.isfinite(measured1) and math.isfinite(measured2))
  mismatch=abs(measured1-measured2)>.35
  hot=max(measured1,measured2)>=27.7
  fault=invalid or mismatch or hot or r['flow_ok']<.5 or r['E_STOP']>.5
  expectedLatch=fault or (latchPrev and not(r['manual_reset']>.5 and max(measured1,measured2)<=27.65))
  latch=r['safety_latched']>.5
  ck(latch==expectedLatch,(name,i,'latch state'))
  if latch:
    ck(abs(qcmd)<1e-7,(name,i,'software off'))
  if r['valve_stuck']<.5:
    ck(qleak==0,(name,i,'valve not stuck'))
  if r['reject_availability']>=1:
    ck(Qex<1e-6,(name,i,'reject healthy'))
  leakSum+=qleak*.25/1e6;excessSum+=Qex*.25/1e6
  stuckUnsafe+=int(r['leak_without_command']>.5)
  alarms+=int(r['IT_risk_alarm']>.5)
  Tprev=t;ITprev=TIT;latchPrev=latch
 ck(abs(leakSum-s['leak_stuck_MWh'])<1e-9,(name,'integral leak'))
 ck(abs(excessSum-s['unhandled_cooling_MWh'])<1e-9,(name,'integral IT'))
 ck(stuckUnsafe==s['unsafe_leak_samples'],(name,'unsafe samples'))
 ck(alarms==s['IT_risk_alarm_samples'],(name,'alarms count'))
 cases.append({'case':name,'rows':len(rows),'leak_MWh':leakSum,'unhandled_MWh':excessSum,
               'unsafe_leak_samples':stuckUnsafe,'IT_alarm_samples':alarms})
d={x['case']:x for x in cases}
ck(d['zdravy']['leak_MWh']==0 and d['zdravy']['unhandled_MWh']==0,'healthy')
ck(d['spolocny_bias_nedetekovany']['unsafe_leak_samples']==0,'common bias without leak')
ck(d['zaseknuty_ventil']['unsafe_leak_samples']>0,'stuck valve should reveal exposure')
ck(d['vypadok_REJECT']['IT_alarm_samples']>0,'IT reject loss')
ck(d['kombinovana_porucha']['IT_alarm_samples']>0,'combined IT risk')
h={}
for stem in (
 'matlab/simulink/DCHR_Electrical_Dispatch_Stateflow_v85.slx',
 'matlab/pool_feedback_v04/DC_Bazen_Uzavreta_Regulacia_v04_SK.slx',
 'matlab/pool_safety_v05/DC_Bazen_Bezpecnost_v05_SK.slx',
 'matlab/pool_failure_v06/DC_Bazen_Fyzikalne_Poruchy_v06_SK.slx'):
 p=ROOT/stem;h[stem]=hashlib.sha256(p.read_bytes()).hexdigest()
ck(h['matlab/simulink/DCHR_Electrical_Dispatch_Stateflow_v85.slx']=='2a9de22c0c55e8c4a87f7b0e0cfe9cd97db08c991f09d98361b009de310adde7','original v85 unchanged')
payload={'status':'PASS','test_assertions':checks,'cases':cases,'model_sha256':h,
         'interpretation':'No physical validation. Actual valve leakage and unhandled IT heat are simulated failures; both can remain dangerous even if software latch trips.'}
(OUT/'QA_NEZAVISLA_V06_SK.json').write_text(json.dumps(payload,indent=2,ensure_ascii=False),encoding='utf-8')
print('QA_V06_PASS',checks,'assertions',len(cases),'scenarios')
