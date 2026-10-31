# -*- coding: utf-8 -*-
from pathlib import Path
import fitz,json
D=Path(__file__).resolve().parent
audit=[]
for lang in ("SK","RU","EN"):
 f=D/f"Kalibracia_a_normy_{lang}.pdf"
 assert f.exists() and f.stat().st_size>25000
 doc=fitz.open(f)
 row={"language":lang,"file":str(f),"pages":len(doc),"bytes":f.stat().st_size,"page_checks":[]}
 alltext=""
 for i,p in enumerate(doc):
  s=p.get_text()
  alltext+=s
  blocks=p.get_text("blocks")
  outside=[]
  for bl in blocks:
   if bl[4].strip() and (bl[0] < -2 or bl[1] < -2 or bl[2]>p.rect.width+2 or bl[3]>p.rect.height+2):
    outside.append([round(float(x),1) for x in bl[:4]])
  row["page_checks"].append({"index":i+1,"chars":len(s),"outside_bounds":outside})
  if i==0:p.get_pixmap(matrix=fitz.Matrix(1.4,1.4)).save(str(D/f"pdf_preview_{lang}.png"))
 assert len(doc)>=1 and len(alltext)>=500 and all(not x["outside_bounds"] for x in row["page_checks"])
 assert "2025" in alltext
 if lang=="RU":assert "темпера" in alltext.lower()
 audit.append(row)
(D/"pdf_render_check.json").write_text(json.dumps(audit,indent=2,ensure_ascii=False),encoding="utf-8")
print(json.dumps(audit,ensure_ascii=False,indent=2))
