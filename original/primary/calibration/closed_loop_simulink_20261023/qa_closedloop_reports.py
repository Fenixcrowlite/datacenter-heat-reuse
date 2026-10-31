# -*- coding: utf-8 -*-
from pathlib import Path
import json,fitz
root=Path(__file__).resolve().parent
report=[]
for lang in ("SK","RU","EN"):
 f=root/f"ClosedLoop_Report_{lang}.pdf"
 assert f.exists() and f.stat().st_size>20000
 doc=fitz.open(f)
 alltext="";overs=[]
 for j,page in enumerate(doc):
  alltext+=page.get_text()
  for w in page.get_text("words"):
   if w[0]<-2 or w[1]<-2 or w[2]>page.rect.width+2 or w[3]>page.rect.height+2:
    overs.append({"page":j+1,"text":w[4]})
  if j==0:
   page.get_pixmap(matrix=fitz.Matrix(1.3,1.3),alpha=False).save(str(root/f"preview_closedloop_{lang}.png"))
 assert not overs,overs[:3]
 assert "2025" in alltext and ("250" in alltext) and len(alltext)>1300
 report.append({"language":lang,"size_bytes":f.stat().st_size,
                "pages":len(doc),"chars":len(alltext),"clipped_words":0,
                "preview":f"preview_closedloop_{lang}.png"})
(root/"closedloop_pdf_qa.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print("TRILINGUAL_PDF_QA_PASS",json.dumps(report,ensure_ascii=False))
