"""Idempotent C120 evidence on existing task; fail closed."""
import hashlib,json,sys
from pathlib import Path
D=Path(__file__).resolve().parent;S=D.parent.parent
sys.path.insert(0,str(S))
import registry
TASK="scc-2aab24704c2bd0";ACTOR="chatgpt-dchr-c120-quarter-control-20261031-0653"
FILES=("c120_quarter_control.py","qa_c120_independent.py","C120_QUARTER_CONTROL.csv.gz",
       "C120_SUMMARY.csv","C120_METADATA.json","C120_INDEPENDENT_QA.json","C120_FINDINGS.md","finalize_c120.py")
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def guard():
 for root in (D,D.parent,S,Path("C:/Users/Lysda/OneDrive/Projects/DataCenter_Heat_Reuse")):
  for flag in FLAGS:
   if (root/flag).exists():raise RuntimeError("STOP_ACTIVE "+str(root/flag))
def once(name,obj):
 p=D/name;s=json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+"\n"
 if p.exists():
  if p.read_text(encoding="utf-8")!=s:raise RuntimeError("DRIFT "+name)
 else:p.write_text(s,encoding="utf-8")
def run():
 guard()
 m=json.loads((D/"C120_METADATA.json").read_text(encoding="utf-8"))
 q=json.loads((D/"C120_INDEPENDENT_QA.json").read_text(encoding="utf-8"))
 assert m["task_id"]==TASK and m["synthetic"] and not m["field_validated"]
 assert q["status"]=="PASS" and q["rows"]==140160 and q["legacy_C118_rows_crosschecked"]==35040 and q["negative_controls"]==5
 assert sha(D/"C120_QUARTER_CONTROL.csv.gz")==m["hourly_sha256"]
 assert sha(D/"C120_SUMMARY.csv")==m["summary_sha256"]
 assert all((D/n).is_file() for n in FILES)
 manifest={"schema":"C120_SHA256_MANIFEST_V1","task_id":TASK,"synthetic":True,"qa":"PASS",
           "files":{n:{"sha256":sha(D/n),"bytes":(D/n).stat().st_size} for n in FILES}}
 once("SHA256_MANIFEST_C120.json",manifest)
 evidence={"schema":"C120_EVIDENCE_V1","task_id":TASK,"actor":ACTOR,
           "artifact":str(D/"C120_QUARTER_CONTROL.csv.gz"),"artifact_sha256":m["hourly_sha256"],
           "qa":str(D/"C120_INDEPENDENT_QA.json"),"findings":str(D/"C120_FINDINGS.md"),
           "manifest":str(D/"SHA256_MANIFEST_C120.json"),
           "manifest_sha256":sha(D/"SHA256_MANIFEST_C120.json"),
           "synthetic":True,"field_validated":False,"source_signoffs_added":0,
           "next":"Model 15-min air enthalpy/temperature, sensor/actuator lag, multiobjective controller QA."}
 once("EVIDENCE_C120.json",evidence)
 guard()
 with registry._open() as db:
  task=db.execute("select status from tasks where id=?",(TASK,)).fetchone()
  if not task or task["status"]!="queued":raise RuntimeError("TASK_STATE_DRIFT")
  old=db.execute("select id from task_events where task_id=? and kind='evidence' and actor=?",(TASK,ACTOR)).fetchone()
  if old:eid=old["id"]
  else:
   registry._event(db,TASK,"evidence",ACTOR,{"artifact":evidence["artifact"],
    "sha256":evidence["artifact_sha256"],"qa":evidence["qa"],"findings":evidence["findings"],
    "manifest":evidence["manifest"],"evidence":str(D/"EVIDENCE_C120.json"),
    "qa_result":"140160 rows, 35040 C118 legacy regressions, 5 negative controls PASS",
    "synthetic":True,"field_validated":False,"source_signoffs_added":0,"next":evidence["next"]})
   eid=db.execute("select last_insert_rowid()").fetchone()[0]
 once("CANONICAL_RECEIPT_C120.json",{"task_id":TASK,"event_id":eid,"actor":ACTOR,
      "evidence_sha256":sha(D/"EVIDENCE_C120.json"),
      "manifest_sha256":sha(D/"SHA256_MANIFEST_C120.json")})
 with registry._open() as db:
  row=db.execute("select actor from task_events where id=? and task_id=?",(eid,TASK)).fetchone()
  status=db.execute("select status from tasks where id=?",(TASK,)).fetchone()[0]
 assert row and row["actor"]==ACTOR and status=="queued"
 print(json.dumps({"event_id":eid,"readback":"VERIFIED","status":status,
   "artifact_sha256":m["hourly_sha256"],"manifest_sha256":sha(D/"SHA256_MANIFEST_C120.json"),
   "receipt_sha256":sha(D/"CANONICAL_RECEIPT_C120.json")},indent=2))
if __name__=="__main__":run()
