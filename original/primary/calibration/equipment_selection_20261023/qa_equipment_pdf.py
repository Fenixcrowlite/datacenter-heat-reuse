from pathlib import Path
import fitz,json
D=Path(__file__).resolve().parent
records=[]
for lang in ('SK','RU','EN'):
 p=D/f'Equipment_Selection_{lang}.pdf'
 assert p.exists() and p.stat().st_size>20000
 doc=fitz.open(p)
 charcount=0;outside=[]
 for j,page in enumerate(doc):
  charcount+=len(page.get_text())
  for w in page.get_text('words'):
   if w[0]<0 or w[1]<0 or w[2]>page.rect.width+1 or w[3]>page.rect.height+1:
    outside.append((j,w[4]))
  if j==0:
   page.get_pixmap(matrix=fitz.Matrix(1.2,1.2)).save(str(D/f'equipment_preview_{lang}.png'))
 assert len(doc)>=1 and charcount>1000 and not outside
 records.append(dict(lang=lang,pages=len(doc),bytes=p.stat().st_size,chars=charcount,outside=outside))
(D/'equipment_pdf_qa.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
print('EQUIPMENT_PDF_VERIFIED',json.dumps(records,ensure_ascii=False))
