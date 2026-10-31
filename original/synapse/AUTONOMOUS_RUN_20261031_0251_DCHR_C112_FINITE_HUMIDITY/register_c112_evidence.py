"""Fail-closed, idempotent C112 evidence registration in the existing DataCenter card."""
from pathlib import Path
import hashlib,json,sys
D=Path(__file__).resolve().parent
SCC=D.parent.parent
sys.path.insert(0,str(SCC))
import registry
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-c112-finite-humidity-20261031-0251"
FILES=("c112_finite_humidity.py","qa_c112_independent.py",
       "C112_ROOM_HUMIDITY_HOURLY.csv.gz","C112_SUMMARY.csv",
       "C112_METADATA.json","C112_INDEPENDENT_QA.json",
       "C112_FINDINGS.md","register_c112_evidence.py")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def guard():
 for root in (D,D.parent,SCC,Path("C:/Users/Lysda/OneDrive/Projects/DataCenter_Heat_Reuse")):
  for flag in ("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE"):
   if (root/flag).exists():raise RuntimeError("STOP_ACTIVE "+str(root/flag))
def save_once(name,obj):
 path=D/name
 payload=json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
 if path.exists():
  if path.read_text(encoding="utf-8")!=payload:raise RuntimeError("EXISTING_FILE_DRIFT "+name)
 else:
  with path.open("x",encoding="utf-8") as f:f.write(payload)
def run():
 guard()
 m=json.loads((D/"C112_METADATA.json").read_text(encoding="utf-8"))
 q=json.loads((D/"C112_INDEPENDENT_QA.json").read_text(encoding="utf-8"))
 assert m["task_id"]==TASK and m["synthetic"] and not m["field_validated"] and m["source_signoffs_added"]==0
 assert m["rows"]==70080 and q["status"]=="PASS" and q["rows"]==70080 and q["negative_controls"]==3
 assert sha(D/"C112_ROOM_HUMIDITY_HOURLY.csv.gz")==m["hourly_sha256"]
 assert sha(D/"C112_SUMMARY.csv")==m["summary_sha256"]
 for file in FILES:assert (D/file).is_file(),file
 manifest={"schema":"C112_SHA256_MANIFEST_V1","task_id":TASK,
  "files":{f:{"sha256":sha(D/f),"bytes":(D/f).stat().st_size} for f in FILES},
  "synthetic":True,"field_validated":False,"qa_status":"PASS"}
 save_once("SHA256_MANIFEST_C112.json",manifest)
 evidence={"schema":"C112_EVIDENCE_V1","task_id":TASK,"actor":ACTOR,
  "artifact":str(D/"C112_ROOM_HUMIDITY_HOURLY.csv.gz"),
  "summary":str(D/"C112_SUMMARY.csv"),"qa":str(D/"C112_INDEPENDENT_QA.json"),
  "findings":str(D/"C112_FINDINGS.md"),
  "manifest":str(D/"SHA256_MANIFEST_C112.json"),
  "manifest_sha256":sha(D/"SHA256_MANIFEST_C112.json"),
  "artifact_sha256":m["hourly_sha256"],"synthetic":True,
  "field_validated":False,"source_signoffs_added":0,
  "next":"Capacity search for RH 45-65%, then RH->evaporation and latent-energy coupling; verify real vendor data."}
 save_once("EVIDENCE_C112.json",evidence)
 guard()
 with registry._open() as db:
  task=db.execute("select id,status from tasks where id=?",(TASK,)).fetchone()
  assert task and task["status"]=="queued"
  old=db.execute("select id from task_events where task_id=? and kind='evidence' and actor=?",(TASK,ACTOR)).fetchone()
  if old:eid=old["id"]
  else:
   registry._event(db,TASK,"evidence",ACTOR,{
    "artifact":evidence["artifact"],"summary":evidence["summary"],
    "qa":evidence["qa"],"findings":evidence["findings"],
    "manifest":evidence["manifest"],"evidence":str(D/"EVIDENCE_C112.json"),
    "sha256":evidence["artifact_sha256"],
    "qa_result":"70080 hourly rows; 1121344 independent checks; 3 negative controls PASS",
    "synthetic":True,"field_validated":False,"source_signoffs_added":0,
    "next":evidence["next"]})
   eid=db.execute("select last_insert_rowid()").fetchone()[0]
 save_once("CANONICAL_RECEIPT_C112.json",{"task_id":TASK,"event_id":eid,"actor":ACTOR,
  "evidence_sha256":sha(D/"EVIDENCE_C112.json"),
  "manifest_sha256":sha(D/"SHA256_MANIFEST_C112.json")})
 with registry._open() as db:
  check=db.execute("select id,actor from task_events where id=? and task_id=?",(eid,TASK)).fetchone()
  status=db.execute("select status from tasks where id=?",(TASK,)).fetchone()[0]
 assert check and check["actor"]==ACTOR
 print(json.dumps({"event_id":eid,"readback":"VERIFIED","status":status,
  "manifest_sha256":sha(D/"SHA256_MANIFEST_C112.json"),
  "receipt_sha256":sha(D/"CANONICAL_RECEIPT_C112.json")},indent=2))
if __name__=="__main__":run()
