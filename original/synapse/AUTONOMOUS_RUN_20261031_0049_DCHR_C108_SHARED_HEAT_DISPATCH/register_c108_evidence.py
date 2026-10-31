"""Idempotent C108 evidence event in existing DataCenter Synapse task."""
import hashlib,json,sys
from pathlib import Path
D=Path(__file__).resolve().parent
SCC=D.parent.parent
sys.path.insert(0,str(SCC))
import registry
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-c108-shared-source-20261031-0049"
FILES=("c108_shared_dispatch.py","qa_c108_independent.py","qa_c108_provenance.py",
 "C108_SHARED_HOURLY.csv.gz","C108_SUMMARY.csv","C108_METADATA.json",
 "C108_INDEPENDENT_QA.json","C108_PROVENANCE_QA.json","C108_FINDINGS.md",
 "register_c108_evidence.py")
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for chunk in iter(lambda:f.read(1048576),b""):h.update(chunk)
 return h.hexdigest()
def guard():
 for root in (D,D.parent,SCC,Path("C:/Users/Lysda/OneDrive/Projects/DataCenter_Heat_Reuse")):
  for flag in FLAGS:
   if (root/flag).exists():raise RuntimeError("STOP_ACTIVE "+str(root/flag))
def write_new(p,obj):
 with p.open("x",encoding="utf-8") as f:
  json.dump(obj,f,indent=2,sort_keys=True,ensure_ascii=False);f.write("\n")
def run():
 guard()
 m=json.loads((D/"C108_METADATA.json").read_text(encoding="utf-8"))
 q=json.loads((D/"C108_INDEPENDENT_QA.json").read_text(encoding="utf-8"))
 p=json.loads((D/"C108_PROVENANCE_QA.json").read_text(encoding="utf-8"))
 assert m["task_id"]==TASK and m["synthetic"] and not m["field_validated"]
 assert m["source_signoffs_added"]==0 and m["rows"]==105120 and m["scenarios"]==12
 assert q["status"]=="PASS" and q["independent_assertions"]>=2200000 and q["negative_controls"]==2
 assert p["status"]=="PASS" and p["checks"]==19
 assert sha(D/"C108_SHARED_HOURLY.csv.gz")==m["hourly_sha256"]
 assert sha(D/"C108_SUMMARY.csv")==m["summary_sha256"]
 assert all((D/f).is_file() for f in FILES)
 with registry._open() as db:
  task=db.execute("SELECT id,status FROM tasks WHERE id=?",(TASK,)).fetchone()
  assert task is not None
  old=db.execute("SELECT id FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",
                 (TASK,ACTOR)).fetchone()
 if old:
  print(json.dumps({"existing_event":old["id"],"status":task["status"]}));return
 manifest={"schema":"C108_SHA256_MANIFEST_V1","task_id":TASK,
  "qa":"12 selftests; 2207664 independent assertions; 12 annual summaries; 2 negative controls; 19 provenance checks",
  "synthetic":True,"field_validated":False,
  "files":{f:{"sha256":sha(D/f),"bytes":(D/f).stat().st_size} for f in FILES}}
 mp=D/"SHA256_MANIFEST_C108.json";write_new(mp,manifest)
 ev={"schema":"C108_EVIDENCE_V1","task_id":TASK,"actor":ACTOR,
  "artifact":str(D/"C108_SHARED_HOURLY.csv.gz"),
  "summary":str(D/"C108_SUMMARY.csv"),
  "qa":str(D/"C108_INDEPENDENT_QA.json"),
  "provenance":str(D/"C108_PROVENANCE_QA.json"),
  "findings":str(D/"C108_FINDINGS.md"),
  "manifest":str(mp),"manifest_sha256":sha(mp),
  "hourly_sha256":m["hourly_sha256"],
  "qa_result":manifest["qa"],"synthetic":True,"field_validated":False,
  "source_signoffs_added":0,
  "next":"Iteratively couple pool evaporation, humidity/air HVAC and heat dispatch; enforce two-loop return temperatures, then replace assumed COP/UA/weather with measured vendor data."}
 ep=D/"EVIDENCE_C108.json";write_new(ep,ev)
 guard()
 with registry._open() as db:
  old=db.execute("SELECT id FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",
   (TASK,ACTOR)).fetchone()
  if old:eid=old["id"]
  else:
   registry._event(db,TASK,"evidence",ACTOR,{
    "artifact":ev["artifact"],"summary":ev["summary"],"qa":ev["qa"],
    "provenance":ev["provenance"],"findings":ev["findings"],
    "manifest":ev["manifest"],"evidence":str(ep),
    "sha256":ev["hourly_sha256"],"qa_result":ev["qa_result"],
    "synthetic":True,"field_validated":False,"source_signoffs_added":0,
    "next":ev["next"]})
   eid=db.execute("SELECT last_insert_rowid()").fetchone()[0]
 write_new(D/"CANONICAL_RECEIPT_C108.json",{"task_id":TASK,"actor":ACTOR,
  "event_id":eid,"evidence_sha256":sha(ep),"manifest_sha256":sha(mp)})
 with registry._open() as db:
  check=db.execute("SELECT id,actor FROM task_events WHERE id=? AND task_id=?",(eid,TASK)).fetchone()
  status=db.execute("SELECT status FROM tasks WHERE id=?",(TASK,)).fetchone()[0]
 assert check and check["actor"]==ACTOR
 print(json.dumps({"event_id":eid,"readback":"VERIFIED","task_status":status,
  "manifest_sha256":sha(mp),"receipt_sha256":sha(D/"CANONICAL_RECEIPT_C108.json")},indent=2))
if __name__=="__main__":run()
