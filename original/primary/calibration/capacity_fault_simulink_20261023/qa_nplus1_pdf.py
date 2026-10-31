from pathlib import Path
import json,fitz
p=Path(__file__).resolve().parent
data=json.loads((p/'capacity_fault_simulink_2025.json').read_text(encoding='utf-8'))
assert len(data)==7 and all(r['steps']==105120 for r in data)
results=[]
for lang in ['SK','RU','EN']:
 f=p/f'Nplus1_Carrier_Selection_{lang}.pdf'
 doc=fitz.open(f)
 clips=[]
 for page in doc:
  for w in page.get_text('words'):
   if w[0]<0 or w[1]<0 or w[2]>page.rect.width+1 or w[3]>page.rect.height+1:clips.append(w[4])
 assert len(doc)>=1 and not clips
 doc[0].get_pixmap(matrix=fitz.Matrix(1.25,1.25)).save(str(p/f'nplus1_preview_{lang}.png'))
 results.append({'lang':lang,'pages':len(doc),'bytes':f.stat().st_size,'clipped':0})
(p/'nplus1_pdf_qa.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print('SIMULINK_AND_PDF_QA_PASS',results)
