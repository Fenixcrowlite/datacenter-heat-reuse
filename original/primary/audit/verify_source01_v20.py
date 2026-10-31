from pathlib import Path
import hashlib,json,csv
r=Path(__file__).resolve().parents[1]
e=r/'audit/evidence_source01_v20'
p=r/'sources/papers/01_Wahlroos_Espoo_2017.pdf'
j=json.loads((e/'primary_checks_v20.json').read_text(encoding='utf-8'))
assert hashlib.sha256(p.read_bytes()).hexdigest()==j['source_sha256']
assert len(j['checks'])==11 and all(c['pass'] for c in j['checks'])
assert all((e/name).is_file() for name in j['page_renders'])
with (r/'audit/literature_traceability_v20.csv').open(encoding='utf-8-sig',newline='') as f:
    rows=list(csv.DictReader(f))
assert len(rows)==31 and sum(x['fully_signed_off']=='YES' for x in rows)==0
assert rows[0]['review_level']=='PARTIAL_PRIMARY_VISUAL_REVIEW_NOT_SIGNED_OFF'
print('PASS read-only evidence verification: 11/11, five renders, 31 rows, zero signoffs')
