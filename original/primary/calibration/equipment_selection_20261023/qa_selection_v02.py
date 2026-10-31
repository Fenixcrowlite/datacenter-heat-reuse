from pathlib import Path
import fitz,json,subprocess
d=Path(__file__).resolve().parent
out=[]
for lang in ("SK","RU","EN"):
 path=d/f"Equipment_Selection_{lang}_v02.pdf"
 assert path.exists() and path.stat().st_size>18000
 doc=fitz.open(path)
 text="".join(p.get_text() for p in doc)
 assert len(text)>1700 and ("10" in text) and ("2" in text)
 bad=[]
 for i,p in enumerate(doc):
  for w in p.get_text("words"):
   if w[0]<-1 or w[1]<-1 or w[2]>p.rect.width+1 or w[3]>p.rect.height+1:
    bad.append((i,w[4]))
 assert not bad
 out.append({"lang":lang,"pages":len(doc),"characters":len(text),
             "clipped_words":0,"bytes":path.stat().st_size})
extra=d/"Module_capacity_tradeoff_SK.pdf"
assert extra.exists() and extra.stat().st_size>10000
html=(d/"equipment_configurator.html").read_text(encoding="utf-8")
assert "<script>" in html and "</script>" in html
js=html.split("<script>",1)[1].split("</script>",1)[0]
s=d/"equipment_browser_syntax.js";s.write_text(js,encoding="utf-8")
subprocess.run(["node","--check",str(s)],check=True)
(d/"equipment_v02_qa.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print("EQUIPMENT_V02_3PDF_AND_HTML_PASS",json.dumps(out,ensure_ascii=False))
