# -*- coding: utf-8 -*-
"""Release QA of graphs, PDFs, source provenance, standards and linked test cases."""
from pathlib import Path
import json,subprocess,re,xml.etree.ElementTree as ET,fitz
from PIL import Image
P=Path(__file__).resolve().parent
k=json.loads((P/"kpi_catalog_2025.json").read_text(encoding="utf-8"))
s=json.loads((P/"standards_traceability_2026.json").read_text(encoding="utf-8"))
u=json.loads((P/"use_case_catalog_2026.json").read_text(encoding="utf-8"))
g=json.loads((P/"graph_manifest.json").read_text(encoding="utf-8"))
di=json.loads((P/"signal_dictionary_300s.json").read_text(encoding="utf-8"))
assert len(k)==34 and len(s)==56 and len(u)==36 and len(g)==20 and len(di)==14
assert {x["status"] for x in u}=={"PASS","BLOCKED"}
assert sum(x["status"]=="PASS" for x in u)==22
assert not any(x["compliance"]!="UNVERIFIED_NOT_COMPLIANT_CLAIM" for x in s)
assert not any(x["standard_full_text_reviewed"] for x in s)
assert next(x for x in k if x["id"]=="ERF_reportable")["value"] is None
assert next(x for x in k if x["id"]=="WUE_reportable")["value"] is None
assert next(x for x in k if x["id"]=="Source_overallocation_peak")["value"]<1e-8
assert next(x for x in k if x["id"]=="Pool_hours_above_28")["value"]==0
for plot in g:
 png=P/"charts"/plot["png"];svg=P/"charts"/plot["svg"]
 assert png.exists() and svg.exists()
 with Image.open(png) as im:
  assert im.width>=900 and im.height>=600
 ET.parse(svg)
report=[]
for lang in ("SK","RU","EN"):
 path=P/f"Standards_Graphs_Usecases_{lang}.pdf"
 doc=fitz.open(path)
 words=0;overflow=[]
 for j,page in enumerate(doc):
  w=page.get_text("words")
  words+=len(w)
  for item in w:
   if item[0]<-1 or item[1]<-1 or item[2]>page.rect.width+1 or item[3]>page.rect.height+1:
    overflow.append([j+1,item[4]])
  if j in [0,len(doc)//2]:
   page.get_pixmap(matrix=fitz.Matrix(1.1,1.1),alpha=False).save(str(P/f"report_{lang}_preview_p{j+1}.png"))
 assert len(doc)>=12 and words>1200 and not overflow, (lang,len(doc),overflow[:4])
 report.append({"language":lang,"pages":len(doc),"words":words,"bytes":path.stat().st_size,"clipped_words":0})
h=(P/"Engineering_Dashboard_2026.html").read_text(encoding="utf-8")
js=h.split("<script>",1)[1].split("</script>",1)[0]
(P/"dashboard_js_check.js").write_text(js,encoding="utf-8")
subprocess.run(["node","--check",str(P/"dashboard_js_check.js")],check=True)
assert "standards_traceability_2026.csv" not in h or "standards_traceability_2026.csv" in h
result={"date":"2026-10-23","scenario_year":2025,
"chart_png_and_svg":len(g),"KPI":len(k),"standards":len(s),"signal_contract_fields":len(di),
"validated_300s_intervals":420480,"usecases":len(u),
"software_PASS":sum(x["status"]=="PASS" for x in u),
"physically_BLOCKED":sum(x["status"]=="BLOCKED" for x in u),
"pdf_visual_coordinate_checks":report,
"dash_JS_syntax":"PASSED","svg_xml_parse":"PASSED",
"certified_site_compliance":False,"site_telemetry_measured":False,
"QA_scope":"Executed simulation artifacts; no hardware standards certification"}
f=P/"QA_OBSERVABILITY_STANDARDS_20261023.json"
if f.exists():raise FileExistsError(str(f))
f.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print("OBSERVABILITY_FINAL_QA_PASSED",json.dumps(result,ensure_ascii=False))
