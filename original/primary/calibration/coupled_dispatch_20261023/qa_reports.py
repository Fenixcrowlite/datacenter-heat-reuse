# -*- coding: utf-8 -*-
"""Render and check all report PDFs for visible text and off-page clipping."""
from pathlib import Path
import json
import fitz
root=Path(__file__).resolve().parent
summary=[]
for lang in ["SK","RU","EN"]:
 p=root/f"Annual_Coupled_Study_{lang}.pdf"
 doc=fitz.open(p)
 count=0
 for n,page in enumerate(doc):
  words=page.get_text("words")
  bad=[(w[0],w[1],w[2],w[3]) for w in words
       if w[0]<0 or w[1]<0 or w[2]>page.rect.width+1 or w[3]>page.rect.height+1]
  if bad:raise AssertionError(f"{lang} page {n+1} clipped: {bad[:3]}")
  count+=len(words)
  if n==0:page.get_pixmap(matrix=fitz.Matrix(1.4,1.4),alpha=False).save(str(root/f"preview_report_{lang}.png"))
 text=" ".join(page.get_text() for page in doc)
 assert len(doc)>=2 and count>250
 assert "2025" in text
 assert "250.1" in text or "250,1" in text
 summary.append({"lang":lang,"pages":len(doc),"words":count,"size_bytes":p.stat().st_size,
                 "first_page_rendered":True,"clipped_words":0})
report=root/"pdf_qa.json"
report.write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8")
print("PDF_QA_OK",json.dumps(summary,ensure_ascii=False))
