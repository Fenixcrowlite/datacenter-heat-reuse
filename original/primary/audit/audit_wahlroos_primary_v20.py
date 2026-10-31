from pathlib import Path
import hashlib
import pymupdf
root = Path(__file__).resolve().parents[1]
pdf = root / 'sources/papers/01_Wahlroos_Espoo_2017.pdf'
doc = pymupdf.open(pdf)
print(len(doc))
import json
out = root / 'audit/evidence_source01_v20'
if out.exists():
    raise FileExistsError('Evidence exists. Use new version.')
out.mkdir(parents=True)
def sha(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()
expected='f70dc2d65045dc6e23ebc069ebdfcdca566b4134b01f84a08e916b46bc92f651'
checks=[]
def check(label,condition,location):
    checks.append({'test':label,'pass':bool(condition),'location':location})
    if not condition: raise AssertionError(label)
page={i:' '.join(doc[i].get_text().lower().split()) for i in (0,3,5,6,7,8)}
check('source_sha256',sha(pdf)==expected,'source file')
check('page_count',len(doc)==12,'PDF page count')
check('doi','10.1016/j.energy.2017.08.078' in page[0],'PDF p1')
check('ere_terms',all(t in page[3] for t in ('ere','preuse','pit')),'PDF p4 Eq1')
check('hourly_energypro','energypro' in page[5] and 'hourly' in page[5],'PDF p6 section4.1')
check('direct_feed_assumption','without priming the heat' in page[5],'PDF p6 section4.1')
check('storage_excluded','storage was not considered' in page[6],'PDF p7 section4.2')
check('fixed_DH_temperatures','49' in page[6] and '87' in page[6],'PDF p7 section4.2')
check('table2_capacities',all(t in page[7] for t in ('23.4','58.5','18.7','46.8')),'PDF p8 Table2')
check('table4_savings',all(t in page[8] for t in ('0.6%','6.3%','3.2%','7.3%')),'PDF p9 Table4')
check('table4_costs',all(t in page[8] for t in ('5.5%','12.2%','4.0%','9.9%')),'PDF p9 Table4')
for i in (3,5,6,7,8):
    doc[i].get_pixmap(matrix=pymupdf.Matrix(1.4,1.4),alpha=False).save(str(out/('source01_pdf_p%02d.png'%(i+1))))
record={'version':'v20','source_id':1,'source_sha256':sha(pdf),'doi_from_pdf':'10.1016/j.energy.2017.08.078','scope':'PARTIAL primary PDF text verification, NOT full paper signoff or independent physical validation','checks':checks,'page_renders':[f'source01_pdf_p{i:02d}.png' for i in (4,6,7,8,9)]}
report=out/'primary_checks_v20.json'
report.write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('PASS',sum(x['pass'] for x in checks),'/',len(checks))
print('SOURCE_SHA256',sha(pdf))
print('REPORT_SHA256',sha(report))
