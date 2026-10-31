# -*- coding: utf-8 -*-
"""Create *synthetic D* replay data from v07. Validate sensor CSV via prior QA gate.
Sensor signals will enter v08 Stateflow as EXTERNAL FROM WORKSPACE data."""
from pathlib import Path
import csv,json,sys,hashlib
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results'/'pool_measurement_v08'
sys.path.insert(0,str(ROOT/'matlab'/'pool_redundancy_v07'))
from kontrola_vstupnych_merani_v07 import audit,FIELDS
src=ROOT/'results'/'pool_redundancy_v07'
info=json.loads((src/'vysledky_v07_SK.json').read_text(encoding='utf-8'))
start=datetime(2026,10,23,tzinfo=timezone.utc)
names=[]
for case in info['cases']:
 name=case['scenar']
 staged=OUT/'staged_D'/name
 if staged.exists():raise FileExistsError(f'Refuse existing replay case: {staged}')
 folder=OUT/'source_D'/name
 if folder.exists():raise FileExistsError(f'Refuse existing raw D case: {folder}')
 folder.mkdir(parents=True)
 with (src/f'scenar_{name}_SK.csv').open(encoding='utf-8-sig',newline='') as f:
  rows=list(csv.DictReader(f))
 assert len(rows)==672
 sensor=folder/'recorded_measured_schema_D.csv'
 cmds=folder/'source_operational_inputs_D_21.csv'
 with sensor.open('w',encoding='utf-8-sig',newline='') as f, cmds.open('w',encoding='utf-8-sig',newline='') as g:
  w=csv.writer(f);v=csv.writer(g)
  w.writerow(FIELDS)
  v.writerow(['cas_h','Q_DC_source_raw_W','T_DC_C','Q_DH_req_W','T_air_C','RH','activity','cover',
   'IT_ok','pool_ok','TES_ok','HX_ok','bias1_K','bias2_K','flow_ok',
   'E_STOP','manual_RESET','primary_valve_stuck','reject_main_availability',
   'secondary_valve_stuck','reject_backup_availability','IT_shedding_enable'])
  for i,r in enumerate(rows):
   t=(start+timedelta(seconds=900*i)).isoformat().replace('+00:00','Z')
   w.writerow([t,r['Q_DC_source_raw_W'],r['T_DC_C'],r['Q_DH_req_W'],
    r['T_air_C'],r['RH'],r['sensor1_C'],r['sensor2_C'],
    30*float(r['flow_ok']),float(r['Q_DC_source_raw_W'])*1.1,
    r['Q_reject_physical_W'],r['reject_main_availability'],
    r['reject_backup_availability']])
   v.writerow([r[k] for k in v_header()] if False else [r['cas_h']]+[r[k] for k in [
    'Q_DC_source_raw_W','T_DC_C','Q_DH_req_W','T_air_C','RH','activity','cover',
    'IT_ok','pool_ok','TES_ok','HX_ok','bias1_K','bias2_K','flow_ok',
    'E_STOP','manual_RESET','primary_valve_stuck','reject_main_availability',
    'secondary_valve_stuck','reject_backup_availability','IT_shedding_enable']])
 meta={'dataset_id':'synthetic_replay_v07_'+name,'provenance':'D',
  'source_uri':'synthetic:v07_20261023/'+name,
  'measurement_method':'SIMULINK v07 recorded virtual sensors; no real measurements; IT power and flow demonstration placeholders',
  'expected_step_seconds':900,
  'units':{'Q_DC_available_W':'W','T_DC_C':'C','Q_DH_request_W':'W',
   'T_air_C':'C','RH':'1','T_pool_sensor1_C':'C',
   'T_pool_sensor2_C':'C','pool_flow_m3h':'m3/h','P_IT_W':'W',
   'Q_REJECT_measured_W':'W','main_reject_ok':'1','backup_reject_ok':'1'}}
 mp=folder/'source_provenance_D.json'
 mp.write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
 accepted=audit(sensor,mp,staged)
 # Each accepted D CSV is now separate from the 21 raw control demands.
 assert accepted['provenance']=='D' and accepted['records']==672
 names.append({'case':name,'D_sha256':accepted['raw_SHA256'],'staged':str(staged)})
(OUT/'D_REPLAY_INPUT_MANIFEST.json').write_text(
 json.dumps({'classification':'D_SYNTHETIC_NEVER_FIELD_MEASUREMENT',
   'scenario_count':len(names),'cases':names},indent=2),encoding='utf-8')
print('V08_SYNTHETIC_D_SENSOR_INPUT_VALIDATED',len(names),'cases')
