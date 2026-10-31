"""Acquire publisher PDF only if it is a genuine PDF; never overwrite."""
from pathlib import Path
import urllib.request,json,time
base=Path(__file__).resolve().parents[1]
target=base/"sources"/"papers"/"20_Verzino_Varna_2026.pdf"
urls=[
"https://www.mdpi.com/1996-1073/19/3/800/pdf-vor",
"https://mdpi-res.com/d_attachment/energies/energies-19-00800/article_deploy/energies-19-00800.pdf",
"https://www.mdpi.com/1996-1073/19/3/800/pdf"]
report={"source":20,"success":False,"attempts":[]}
for url in urls:
 if target.exists() and target.open("rb").read(4)==b"%PDF":
  report["success"]=True;report["existing"]=True;break
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (research literature audit)"})
  with urllib.request.urlopen(req,timeout=10) as r:data=r.read(14_000_000)
  if data[:4]!=b"%PDF" or len(data)<20000:raise ValueError("non-PDF or too small")
  target.parent.mkdir(parents=True,exist_ok=True)
  tmp=target.with_suffix(".tmp")
  tmp.write_bytes(data);tmp.replace(target)
  report["success"]=True;report["bytes"]=len(data);report["url"]=url;break
 except Exception as e:
  report["attempts"].append({"url":url,"error":str(e)[:150]})
output=base/"audit"/"varna_pdf_acquisition_v08.json"
output.write_text(json.dumps(report,indent=2),encoding="utf8")
print(json.dumps(report))
