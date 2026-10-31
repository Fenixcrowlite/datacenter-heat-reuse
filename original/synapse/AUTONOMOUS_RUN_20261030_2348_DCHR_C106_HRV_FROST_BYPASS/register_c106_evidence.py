"""Register one evidence event in the EXISTING DataCenter card; idempotent actor."""
import hashlib,json,sys
from pathlib import Path
D=Path(__file__).resolve().parent
SCC=D.parent.parent
sys.path.insert(0,str(SCC))
import registry
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-c106-frost-bypass-20261030-2348"
FILES=("c106_bypass.py","qa_c106_independent.py","C106_BYPASS_HOURLY.csv.gz",
       "C106_SUMMARY.csv","C106_METADATA.json","C106_INDEPENDENT_QA.json",
       "C106_FINDINGS.md","register_c106_evidence.py")
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for x in iter(lambda:f.read(1<<20),b""):h.update(x)
 return h.hexdigest()
def guard():
 for root in (D,D.parent,SCC,Path("C:/Users/Lysda/OneDrive/Projects/DataCenter_Heat_Reuse")):
  for flag in FLAGS:
   if (root/flag).exists():raise RuntimeError("STOP_ACTIVE "+str(root/flag))
def save(p,v):
 with p.open("x",encoding="utf-8") as f:json.dump(v,f,indent=2,sort_keys=True,ensure_ascii=False);f.write("\n")
def run():
 guard()
 m=json.loads((D/"C106_METADATA.json").read_text(encoding="utf-8"))
 q=json.loads((D/"C106_INDEPENDENT_QA.json").read_text(encoding="utf-8"))
 assert m["task_id"]==TASK and m["synthetic"] and not m["field_validated"] and m["source_signoffs_added"]==0
 assert q["status"]=="PASS" and q["rows"]==78840 and q["independent_assertions"]>=1900000 and q["negative_controls"]==2
 assert sha(D/"C106_BYPASS_HOURLY.csv.gz")==m["hourly_sha256"]
 assert sha(D/"C106_SUMMARY.csv")==m["summary_sha256"]
 assert all((D/f).is_file() for f in FILES)
 with registry._open() as db:
  task=db.execute("SELECT id,status FROM tasks WHERE id=?",(TASK,)).fetchone()
  assert task is not None
  old=db.execute("SELECT id FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",(TASK,ACTOR)).fetchone()
 if old:
  print(json.dumps({"existing_event":old["id"],"task_status":task["status"]}));return
 manifest={"schema":"C106_MANIFEST_V1","task_id":TASK,"synthetic":True,
   "qa":"8/8 selftests; 1971000 independent hourly assertions; 117 annual comparisons; 2/2 negative controls",
   "files":{f:{"sha256":sha(D/f),"bytes":(D/f).stat().st_size} for f in FILES}}
 mp=D/"SHA256_MANIFEST_C106.json";save(mp,manifest)
 ev={"schema":"C106_EVIDENCE_V1","task_id":TASK,"actor":ACTOR,
   "artifact":str(D/"C106_BYPASS_HOURLY.csv.gz"),
   "summary":str(D/"C106_SUMMARY.csv"),"qa":str(D/"C106_INDEPENDENT_QA.json"),
   "findings":str(D/"C106_FINDINGS.md"),"manifest":str(mp),
   "manifest_sha256":sha(mp),"hourly_sha256":m["hourly_sha256"],
   "qa_result":manifest["qa"],"synthetic":True,"field_validated":False,
   "source_signoffs_added":0,
   "next":"Obtain HRV manufacturer frost/defrost curves and real weather; compare bypass vs defrost, then couple air/water loads under a shared DC heat cap."}
 ep=D/"EVIDENCE_C106.json";save(ep,ev)
 guard()
 with registry._open() as db:
  old=db.execute("SELECT id FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",(TASK,ACTOR)).fetchone()
  if old:eid=old["id"]
  else:
   registry._event(db,TASK,"evidence",ACTOR,{
    "artifact":ev["artifact"],"summary":ev["summary"],"qa":ev["qa"],
    "findings":ev["findings"],"manifest":ev["manifest"],"evidence":str(ep),
    "sha256":ev["hourly_sha256"],"qa_result":ev["qa_result"],
    "synthetic":True,"field_validated":False,"source_signoffs_added":0,"next":ev["next"]})
   eid=db.execute("SELECT last_insert_rowid()").fetchone()[0]
 save(D/"CANONICAL_RECEIPT_C106.json",{"task_id":TASK,"actor":ACTOR,"event_id":eid,
   "evidence_sha256":sha(ep),"manifest_sha256":sha(mp)})
 with registry._open() as db:
  check=db.execute("SELECT id,actor FROM task_events WHERE id=? AND task_id=?",(eid,TASK)).fetchone()
  status=db.execute("SELECT status FROM tasks WHERE id=?",(TASK,)).fetchone()[0]
 assert check and check["actor"]==ACTOR
 print(json.dumps({"event_id":eid,"readback":"VERIFIED","task_status":status,
  "manifest_sha256":sha(mp),"receipt_sha256":sha(D/"CANONICAL_RECEIPT_C106.json")},indent=2))
if __name__=="__main__":run()
