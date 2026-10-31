from pathlib import Path
import calendar, csv, hashlib, json, re
import pymupdf
R=Path(__file__).resolve().parents[1]
pdf=R/'sources/papers/01_Wahlroos_Espoo_2017.pdf'
old=R/'audit/literature_traceability_v20.csv'
new=R/'audit/literature_traceability_v21.csv'
out=R/'audit/evidence_source01_v21'
months=[calendar.month_name[i] for i in range(1,13)]
values=[40.2,40.4,38.6,27.,19.2,16.,13.8,14.6,19.2,24.,32.8,38.]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
assert not new.exists() and not out.exists(), 'v21 already exists; preserve it'
assert sha(pdf)=='f70dc2d65045dc6e23ebc069ebdfcdca566b4134b01f84a08e916b46bc92f651'
doc=pymupdf.open(pdf)
assert len(doc)==12
text=doc[6].get_text()
table=text[text.rfind('Table 1'):]
checks={}
def verify(k,cond):
    checks[k]=bool(cond)
    assert cond,k
verify('table_heading','Pricing of waste heat' in table)
verify('unit_MWh','MWh' in table)
verify('proposed_from_ref20','proposed in Ref. [20]' in text)
verify('ref20_Stenberg_2015','Stenberg' in doc[11].get_text() and '2015' in doc[11].get_text())
for m,v in zip(months,values):
    token=str(int(v)) if v.is_integer() else str(v)
    verify(m,bool(re.search(r'(?m)^'+re.escape(m)+r'\s*\n\s*'+re.escape(token)+r'\s*$',table)))
with old.open(encoding='utf-8-sig',newline='') as f:
    reader=csv.DictReader(f); fields=reader.fieldnames; rows=list(reader)
verify('31_sources',len(rows)==31)
verify('zero_full_signoffs',all(x['fully_signed_off']=='NO' for x in rows))
rows[0]['blockers']+=' | v21 Table1 prices checked against original PDF p7; upstream Stenberg thesis not checked'
out.mkdir(parents=True)
with new.open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
with (out/'table1_prices_v21.csv').open('w',encoding='utf-8',newline='') as f:
    writer=csv.writer(f);writer.writerow(['month','price_EUR_per_MWh','original_locator'])
    writer.writerows((m,v,'Wahlroos 2017 journal p1233 Table1') for m,v in zip(months,values))
page=doc[6]
page.get_pixmap(matrix=pymupdf.Matrix(1.6,1.6),alpha=False).save(str(out/'source01_original_page07_v21.png'))
days=[calendar.monthrange(2015,i)[1] for i in range(1,13)]
report={'version':'v21','scope':'Article Table1 agreement only',
 'source_pdf_sha256':sha(pdf),'article_locator':'PDF p7, journal p1233',
 'monthly_EUR_per_MWh':dict(zip(months,values)),
 'monthly_mean':sum(values)/12,
 'day_weighted_2015_mean':sum(a*b for a,b in zip(values,days))/365,
 'provenance':'Article cites Stenberg 2015 thesis as ref [20]; thesis not verified',
 'checks':checks,'passed':sum(checks.values()),'total':len(checks),
 'primary_full_signoffs':0,'independent_physical_validation':'NOT_TESTED'}
report['traceability_sha256']=sha(new)
report['price_csv_sha256']=sha(out/'table1_prices_v21.csv')
report['render_sha256']=sha(out/'source01_original_page07_v21.png')
(out/'table1_checks_v21.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('PASS',report['passed'],'/',report['total'],'article checks')
print('report_sha256',sha(out/'table1_checks_v21.json'))
print('traceability_sha256',sha(new))
