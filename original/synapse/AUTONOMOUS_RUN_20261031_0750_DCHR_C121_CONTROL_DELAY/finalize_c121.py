"""C121: fail-closed, idempotent evidence on existing DataCenter task."""
import hashlib,json,sys
from pathlib import Path
D=Path(__file__).resolve().parent;S=D.parent.parent
sys.path.insert(0,str(S))
import registry
TASK="scc-2aab24704c2bd0";ACTOR="chatgpt-dchr-c121-control-delay-20261031-0750"
FILES=("c121_delay_sensitivity.py","qa_c121_independent.py","C121_DELAY_HOURLY.csv.gz",
"C121_SUMMARY.csv","C121_METADATA.json","C121_INDEPENDENT_QA.json","C121_FINDINGS.md",
"C121_RUN_LOG.txt","C121_QA_LOG.txt","finalize_c121.py")
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
 p=D/name;data=json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+"\n"
 if p.exists():
  if p.read_text(encoding="utf-8")!=data:raise RuntimeError("DRIFT "+name)
 else:p.write_text(data,encoding="utf-8")
def run():
 guard()
 m=json.loads((D/"C121_METADATA.json").read_text(encoding="utf-8"))
 q=json.loads((D/"C121_INDEPENDENT_QA.json").read_text(encoding="utf-8"))
 assert m["task_id"]==TASK and m["synthetic"] and not m["field_validated"] and m["source_signoffs_added"]==0
 assert q["status"]=="PASS" and q["rows_checked"]==70080 and q["baseline_C120_rows_crosschecked"]==17520 and q["negative_controls"]==5
 assert sha(D/"C121_DELAY_HOURLY.csv.gz")==m["data_sha256"]==q["data_sha256"]
 assert sha(D/"C121_SUMMARY.csv")==m["summary_sha256"]
 assert all((D/n).is_file() for n in FILES)
 manifest={"schema":"C121_SHA256_MANIFEST_V1","task_id":TASK,"qa":"PASS","synthetic":True,
           "files":{n:{"sha256":sha(D/n),"bytes":(D/n).stat().st_size} for n in FILES}}
 once("SHA256_MANIFEST_C121.json",manifest)
 evidence={"schema":"C121_EVIDENCE_V1","task_id":TASK,"actor":ACTOR,
           "artifact":str(D/"C121_DELAY_HOURLY.csv.gz"),"artifact_sha256":m["data_sha256"],
           "qa":str(D/"C121_INDEPENDENT_QA.json"),"findings":str(D/"C121_FINDINGS.md"),
           "manifest":str(D/"SHA256_MANIFEST_C121.json"),
           "manifest_sha256":sha(D/"SHA256_MANIFEST_C121.json"),
           "synthetic":True,"field_validated":False,"source_signoffs_added":0,
           "next":"Add coupled 15-minute air temperature/enthalpy and calibrate actuator power and RH tradeoff."}
 once("EVIDENCE_C121.json",evidence)
 guard()
 with registry._open() as db:
  task=db.execute("select status from tasks where id=?",(TASK,)).fetchone()
  if not task or task["status"]!="queued":raise RuntimeError("TASK_STATE_DRIFT")
  old=db.execute("select id from task_events where task_id=? and kind='evidence' and actor=?",(TASK,ACTOR)).fetchone()
  if old:eid=old["id"]
  else:
   registry._event(db,TASK,"evidence",ACTOR,{"artifact":evidence["artifact"],
    "sha256":evidence["artifact_sha256"],"qa":evidence["qa"],"findings":evidence["findings"],
    "manifest":evidence["manifest"],"evidence":str(D/"EVIDENCE_C121.json"),
    "qa_result":"70080 mass/energy checks, 17520 baseline regressions, 5 negative controls PASS",
    "synthetic":True,"field_validated":False,"source_signoffs_added":0,"next":evidence["next"]})
   eid=db.execute("select last_insert_rowid()").fetchone()[0]
 once("CANONICAL_RECEIPT_C121.json",{"task_id":TASK,"event_id":eid,"actor":ACTOR,
       "evidence_sha256":sha(D/"EVIDENCE_C121.json"),
       "manifest_sha256":sha(D/"SHA256_MANIFEST_C121.json")})
 with registry._open() as db:
  row=db.execute("select actor from task_events where id=? and task_id=?",(eid,TASK)).fetchone()
  status=db.execute("select status from tasks where id=?",(TASK,)).fetchone()[0]
 assert row and row["actor"]==ACTOR and status=="queued"
 print(json.dumps({"event_id":eid,"readback":"VERIFIED","status":status,
  "artifact_sha256":m["data_sha256"],"manifest_sha256":sha(D/"SHA256_MANIFEST_C121.json"),
  "receipt_sha256":sha(D/"CANONICAL_RECEIPT_C121.json")},indent=2))
if __name__=="__main__":run()
