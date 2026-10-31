from pathlib import Path
from hashlib import sha256
import json,shutil
src=Path(__file__).resolve().parent
dest=Path(r"C:\Users\Lysda\Documents\Bimba\02_PROJECTS\02_Automation\DataCenter_Heat_Reuse\calibration\closed_loop_simulink_20261023")
assert dest.is_dir(),"Obsidian destination missing"
files=["ClosedLoop_Report_SK.pdf","ClosedLoop_Report_RU.pdf","ClosedLoop_Report_EN.pdf",
 "ClosedLoop_Report_SK.md","ClosedLoop_Report_RU.md","ClosedLoop_Report_EN.md",
 "closedloop_pdf_qa.json","STATUS_CLOSED_LOOP_20261023.json"]
result=[]
for f in files:
 a=src/f;b=dest/f
 assert a.is_file()
 h=sha256(a.read_bytes()).hexdigest()
 if b.exists():
  if sha256(b.read_bytes()).hexdigest()!=h:raise FileExistsError("CONFLICT: "+str(b))
  action="ALREADY_IDENTICAL"
 else:
  shutil.copy2(a,b);action="COPIED"
 assert sha256(b.read_bytes()).hexdigest()==h
 result.append({"filename":f,"action":action,"sha256":h})
hub=dest/"00_ClosedLoop_DataCenter_Bazen_SK.md"
h=hub.read_text(encoding="utf-8")
tag="## Aktualizované technické správy PDF (SK / RU / EN)"
if tag not in h:
 hub.write_text(h+"\n"+tag+"\n\n- [[ClosedLoop_Report_SK.pdf]]\n- [[ClosedLoop_Report_RU.pdf]]\n- [[ClosedLoop_Report_EN.pdf]]\n- [[STATUS_CLOSED_LOOP_20261023.json]]\n",encoding="utf-8")
out=src/"obsidian_pdf_sync_manifest.json"
if out.exists():raise FileExistsError(str(out))
out.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
print("OBSIDIAN_PDF_SYNC_VERIFIED",len(result),sum(x["action"]=="COPIED" for x in result))
