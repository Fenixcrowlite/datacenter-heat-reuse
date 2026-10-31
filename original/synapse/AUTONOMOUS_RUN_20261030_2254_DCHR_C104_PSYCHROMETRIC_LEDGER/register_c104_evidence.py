"""Idempotent evidence write to existing DataCenter Synapse task. No new task."""
import hashlib,json,sys
from pathlib import Path
D=Path(__file__).resolve().parent
SCC=D.parent.parent
sys.path.insert(0,str(SCC))
import registry
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-c104-psychrometric-20261030-2254"
FILES=("c104_psychrometric.py","c104_physical_summary.py","qa_c104_independent.py",
       "qa_c104_summary.py","C104_PSYCHROMETRIC_HOURLY.csv.gz",
       "C104_PSYCHROMETRIC_SUMMARY.csv","C104_PHYSICAL_SUMMARY.csv",
       "C104_METADATA.json","C104_INDEPENDENT_QA.json","C104_SUMMARY_QA.json","C104_FINDINGS.md")
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def guard():
 for root in (D,D.parent,SCC,Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
  for flag in FLAGS:
   if (root/flag).exists():raise RuntimeError("STOP_ACTIVE "+str(root/flag))
def save(p,x):
 with p.open("x",encoding="utf-8") as f:json.dump(x,f,indent=2,sort_keys=True,ensure_ascii=False);f.write("\n")
def run():
 guard()
 m=json.loads((D/"C104_METADATA.json").read_text(encoding="utf-8"))
 q=json.loads((D/"C104_INDEPENDENT_QA.json").read_text(encoding="utf-8"))
 z=json.loads((D/"C104_SUMMARY_QA.json").read_text(encoding="utf-8"))
 assert m["task_id"]==TASK and m["synthetic"] and not m["field_validated"] and m["source_signoffs_added"]==0
 assert q["status"]=="PASS" and q["rows_checked"]==78840 and q["assertions"]>=2000000 and q["negative_controls"]==2
 assert z["status"]=="PASS" and z["rows"]==78840 and z["scenarios"]==9 and z["dimensional_schema_check"]
 assert sha(D/"C104_PSYCHROMETRIC_HOURLY.csv.gz")==m["hourly_sha256"]
 assert sha(D/"C104_PHYSICAL_SUMMARY.csv")==z["sha256"]
 assert all((D/f).is_file() for f in FILES)
 with registry._open() as db:
  task=db.execute("SELECT id,status FROM tasks WHERE id=?",(TASK,)).fetchone()
  assert task is not None
  old=db.execute("SELECT id FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",(TASK,ACTOR)).fetchone()
 if old:
  print(json.dumps({"existing_event":old["id"],"task_status":task["status"]}));return
 manifest={"schema":"C104_MANIFEST_V1","task_id":TASK,"synthetic":True,
   "qa":"17/17 selftest; 2207520 independent row checks; 2 negative controls; 81 annual comparisons; dimensional schema gate",
   "files":{f:{"sha256":sha(D/f),"bytes":(D/f).stat().st_size} for f in FILES}}
 mp=D/"SHA256_MANIFEST_C104.json";save(mp,manifest)
 ev={"schema":"C104_EVIDENCE_V1","task_id":TASK,"actor":ACTOR,
   "artifact":str(D/"C104_PSYCHROMETRIC_HOURLY.csv.gz"),
   "physical_summary":str(D/"C104_PHYSICAL_SUMMARY.csv"),
   "qa":str(D/"C104_INDEPENDENT_QA.json"),"qa_summary":str(D/"C104_SUMMARY_QA.json"),
   "findings":str(D/"C104_FINDINGS.md"),"manifest":str(mp),
   "manifest_sha256":sha(mp),"hourly_sha256":m["hourly_sha256"],
   "physical_summary_sha256":z["sha256"],
   "qa_result":manifest["qa"],"synthetic":True,"field_validated":False,"source_signoffs_added":0,
   "next":"Add sensible HRV bypass controls; then couple water and air loads to one constrained heat source after source/vender validation."}
 ep=D/"EVIDENCE_C104.json";save(ep,ev)
 guard()
 with registry._open() as db:
  old=db.execute("SELECT id FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",(TASK,ACTOR)).fetchone()
  if old:eid=old["id"]
  else:
   registry._event(db,TASK,"evidence",ACTOR,{
    "artifact":ev["artifact"],"physical_summary":ev["physical_summary"],
    "qa":ev["qa"],"qa_summary":ev["qa_summary"],"findings":ev["findings"],
    "manifest":ev["manifest"],"evidence":str(ep),"sha256":ev["hourly_sha256"],
    "qa_result":ev["qa_result"],"synthetic":True,"field_validated":False,
    "source_signoffs_added":0,"next":ev["next"]})
   eid=db.execute("SELECT last_insert_rowid()").fetchone()[0]
 save(D/"CANONICAL_RECEIPT_C104.json",{"task_id":TASK,"actor":ACTOR,"event_id":eid,
    "evidence_sha256":sha(ep),"manifest_sha256":sha(mp)})
 with registry._open() as db:
  check=db.execute("SELECT id,actor FROM task_events WHERE id=? AND task_id=?",(eid,TASK)).fetchone()
  status=db.execute("SELECT status FROM tasks WHERE id=?",(TASK,)).fetchone()[0]
 assert check and check["actor"]==ACTOR
 print(json.dumps({"event_id":eid,"readback":"VERIFIED","task_status":status,
    "manifest_sha256":sha(mp),"receipt_sha256":sha(D/"CANONICAL_RECEIPT_C104.json")},indent=2))
if __name__=="__main__":run()
