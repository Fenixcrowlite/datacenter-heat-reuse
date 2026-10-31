# -*- coding: utf-8 -*-
"""Data provenance gate: separate measured A, research B, manufacturer C, synthetic D."""
import argparse,csv,json,math,re,hashlib
from datetime import datetime,timezone
from pathlib import Path
FIELDS=['timestamp_utc','Q_DC_available_W','T_DC_C','Q_DH_request_W',
'T_air_C','RH','T_pool_sensor1_C','T_pool_sensor2_C','pool_flow_m3h',
'P_IT_W','Q_REJECT_measured_W','main_reject_ok','backup_reject_ok']
NUMERIC=FIELDS[1:]
def parse_iso(s):
 if not re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:Z|[+-]\d\d:\d\d)',s):
  raise ValueError('ISO8601 offset or Z is required')
 x=datetime.fromisoformat(s.replace('Z','+00:00'))
 if x.utcoffset().total_seconds()!=0:
  raise ValueError('Timestamp must be UTC normalized')
 return x
def audit(inp,meta_path,out):
 inp=Path(inp);meta_path=Path(meta_path);out=Path(out)
 meta=json.loads(meta_path.read_text(encoding='utf-8'))
 for key in ('dataset_id','provenance','source_uri','measurement_method','units','expected_step_seconds'):
  if not meta.get(key):raise ValueError('Missing metadata '+key)
 if meta['provenance'] not in ('A','B','C','D'):raise ValueError('Invalid provenance')
 if meta['expected_step_seconds']!=900:raise ValueError('v07 expected 900 s')
 if meta['provenance']=='A':
  if not meta.get('instrument_ids') or not meta.get('calibration_document'):
   raise ValueError('Field measurements class A require instrument IDs and calibration document')
  if meta['source_uri'].startswith('synthetic:'):
   raise ValueError('Synthetic measurements cannot be class A')
 if meta['provenance']=='D' and not meta['source_uri'].startswith('synthetic:'):
  raise ValueError('Class D must explicitly have a synthetic provenance URI')
 assert len(set(FIELDS))==len(FIELDS)
 with inp.open(encoding='utf-8-sig',newline='') as f:
  rd=csv.DictReader(f)
  if rd.fieldnames!=FIELDS:raise ValueError(f'Expected exact schema {FIELDS}')
  data=[]
  for lineno,row in enumerate(rd,start=2):
   t=parse_iso(row['timestamp_utc'])
   x={}
   for k in NUMERIC:
    try:n=float(row[k])
    except (ValueError,TypeError):raise ValueError(f'{k} is invalid on line {lineno}')
    if not math.isfinite(n):raise ValueError(f'{k} is not finite on line {lineno}')
    x[k]=n
   if x['RH']<0 or x['RH']>1:raise ValueError('RH outside 0..1')
   if not 0<=x['T_DC_C']<=90:raise ValueError('Source temperature outside engineering envelope')
   if not -40<=x['T_air_C']<=65:raise ValueError('Air temperature outside envelope')
   for k in ('Q_DC_available_W','Q_DH_request_W','pool_flow_m3h','P_IT_W','Q_REJECT_measured_W'):
    if x[k]<0:raise ValueError(k+' negative')
   if not 0<=x['main_reject_ok']<=1 or not 0<=x['backup_reject_ok']<=1:
    raise ValueError('Availability outside 0..1')
   if data:
    step=(t-data[-1][0]).total_seconds()
    if step!=900:raise ValueError(f'Duplicate, missing or irregular step at {lineno}: {step}s')
   data.append((t,x))
 if len(data)<2:raise ValueError('At least two time points required')
 digest=hashlib.sha256(inp.read_bytes()).hexdigest()
 info={'status':'ACCEPTED_AS_INGEST_NOT_AS_MODEL_VALIDATION',
  'dataset_id':meta['dataset_id'],'provenance':meta['provenance'],
  'raw_SHA256':digest,'records':len(data),
  'time_start_utc':data[0][0].isoformat(),
  'time_end_utc':data[-1][0].isoformat(),
  'step_s':900,'source_uri':meta['source_uri'],
  'units':meta['units'],
  'limitations':'These data are staged and independently checked. They are NOT yet inputs to the current virtual-sensor Stateflow v07 closed loop.'}
 if out.exists():raise FileExistsError('Never overwrite previously staged dataset')
 out.mkdir(parents=True)
 (out/'validated_dataset_metadata.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
 with (out/'normalized_measurements_v07.csv').open('w',newline='',encoding='utf-8-sig') as g:
  w=csv.writer(g);w.writerow(FIELDS)
  for t,x in data:w.writerow([t.isoformat().replace('+00:00','Z')]+[f'{x[k]:.8g}' for k in NUMERIC])
 print('ACCEPTED',meta['provenance'],len(data),'records',out)
 return info
if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('--input',required=True);p.add_argument('--metadata',required=True);p.add_argument('--output',required=True)
 args=p.parse_args()
 audit(args.input,args.metadata,args.output)
