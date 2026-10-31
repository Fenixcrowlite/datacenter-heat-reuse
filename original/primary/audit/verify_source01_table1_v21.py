from pathlib import Path
import csv, hashlib, json
r=Path(__file__).resolve().parents[1]
e=r/'audit/evidence_source01_v21'
j=json.loads((e/'table1_checks_v21.json').read_text(encoding='utf-8'))
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert j['passed']==j['total']==18
assert all(j['checks'].values())
assert h(r/'sources/papers/01_Wahlroos_Espoo_2017.pdf')==j['source_pdf_sha256']
assert h(r/'audit/literature_traceability_v21.csv')==j['traceability_sha256']
assert h(e/'table1_prices_v21.csv')==j['price_csv_sha256']
assert h(e/'source01_original_page07_v21.png')==j['render_sha256']
with (e/'table1_prices_v21.csv').open(encoding='utf-8',newline='') as f:
    prices=list(csv.DictReader(f))
assert len(prices)==12 and len(set(x['month'] for x in prices))==12
assert [float(x['price_EUR_per_MWh']) for x in prices]==list(j['monthly_EUR_per_MWh'].values())
with (r/'audit/literature_traceability_v21.csv').open(encoding='utf-8-sig',newline='') as f:
    rows=list(csv.DictReader(f))
assert len(rows)==31 and not any(x['fully_signed_off']=='YES' for x in rows)
assert 'thesis not checked' in rows[0]['blockers']
print('PASS 18/18 article checks; 12 prices; 31 records; 0 signoffs; 4 SHA checks')
