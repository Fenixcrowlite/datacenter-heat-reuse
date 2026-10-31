from pathlib import Path
import hashlib
p=Path(__file__).resolve().parent.parent/'sources/papers/01_Wahlroos_Espoo_2017.pdf'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='f70dc2d65045dc6e23ebc069ebdfcdca566b4134b01f84a08e916b46bc92f651'
print('PASS source01 PDF SHA256')
import csv,json,re
r=p.parent.parent.parent
base=r/'audit'
text=(p.parent/'01_Wahlroos_Espoo_2017.extracted.txt').read_text(encoding='utf-8',errors='replace')
prices=list(csv.DictReader((base/'evidence_source01_v21/table1_prices_v21.csv').open(encoding='utf-8-sig')))
rows=list(csv.DictReader((base/'literature_traceability_v21.csv').open(encoding='utf-8-sig')))
checks={'reference_present':bool(re.search('Stenberg',text,re.I)),'twelve_months':len(prices)==12,'31_registry_entries':len(rows)==31,'zero_full_signoffs':all(x['fully_signed_off']=='NO' for x in rows),'upstream_pdf_not_local':not any(p.parent.glob('*Stenberg*'))}
assert all(checks.values()),checks
print('PASS',len(checks)+1,'/',len(checks)+1)
d=base/'evidence_source01_v22';d.mkdir(exist_ok=True)
evidence={'version':'v22','checks':checks,'passed':6,'total':6,'upstream_thesis_pdf':'NOT_DOWNLOADED','thesis_prices':'NOT_VERIFIED','physical_validation':'NOT_TESTED','full_signoffs':0}
e=d/'stenberg_boundary_checks_v22.json'
if not e.exists():e.write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
assert json.loads(e.read_text(encoding='utf-8'))==evidence
trace=base/'literature_traceability_v23.csv'
if not trace.exists():
 rows[0]['blockers']+=' | v23: Stenberg thesis indexed cover identified; upstream prices NOT VERIFIED'
 with trace.open('x',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
assert len(list(csv.DictReader(trace.open(encoding='utf-8-sig'))))==31
status=r/'STATUS_v23.json'
obj={'version':'0.23','inherits':'STATUS_v22.json','checkpoint':'Stenberg bibliography identified; price provenance still blocked','local_integrity_tests':'6/6 PASS','upstream_original':'NOT_OBTAINED','primary_source_signoffs':0,'total_sources':31,'independent_physical_validation':'NOT_TESTED','sha256':{'evidence':hashlib.sha256(e.read_bytes()).hexdigest(),'traceability':hashlib.sha256(trace.read_bytes()).hexdigest()},'next':'Acquire Stenberg 2015 original PDF and inspect prices'}
if not status.exists():status.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')
assert json.loads(status.read_text(encoding='utf-8'))==obj
print('PASS v22 evidence and status hashes')
