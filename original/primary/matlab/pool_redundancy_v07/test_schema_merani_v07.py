# -*- coding: utf-8 -*-
"""Regression tests. Example data intentionally SYNTHETIC; never label measured."""
from pathlib import Path
from datetime import datetime,timedelta,timezone
from tempfile import TemporaryDirectory
import csv,json
from kontrola_vstupnych_merani_v07 import audit,FIELDS
with TemporaryDirectory() as t:
 root=Path(t)
 inp=root/'example_D.csv'
 meta=root/'example_D.json'
 with inp.open('w',encoding='utf-8',newline='') as f:
  w=csv.writer(f);w.writerow(FIELDS)
  for k in range(4):
   time=(datetime(2026,10,23,tzinfo=timezone.utc)+timedelta(minutes=15*k)).isoformat().replace('+00:00','Z')
   w.writerow([time,170000,30,90000,29,.6,27.4,27.4,30,180000,45000,1,1])
 m={'dataset_id':'example_D_NOT_MEASURED','provenance':'D',
   'source_uri':'synthetic:unit-test-only',
   'measurement_method':'generated constants, NOT measurements',
   'expected_step_seconds':900,
   'units':{k:('W' if k.endswith('_W') else 'C' if k.endswith('_C') else
        'm3/h' if k.endswith('_m3h') else '1') for k in FIELDS[1:]}}
 meta.write_text(json.dumps(m),encoding='utf-8')
 r=audit(inp,meta,root/'accepted_D')
 assert r['provenance']=='D' and r['records']==4
 bad=dict(m);bad['provenance']='A'
 meta.write_text(json.dumps(bad),encoding='utf-8')
 try:audit(inp,meta,root/'reject_A')
 except ValueError as e:
  assert 'instrument IDs' in str(e)
 else:raise AssertionError('Fabricated A provenance was accepted')
 m['expected_step_seconds']=1200
 meta.write_text(json.dumps(m),encoding='utf-8')
 try:audit(inp,meta,root/'reject_step')
 except ValueError as e:assert '900' in str(e)
 else:raise AssertionError('Unapproved step was accepted')
 print('V07_PROVENANCE_TEST_PASS: D accepted, false A rejected, wrong step rejected')
