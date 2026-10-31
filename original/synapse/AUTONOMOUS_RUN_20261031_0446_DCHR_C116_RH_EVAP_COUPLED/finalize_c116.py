"""Idempotent evidence registration for existing DataCenter Synapse card, C116."""
import hashlib,json,sys
from pathlib import Path
D=Path(__file__).resolve().parent;SCC=D.parent.parent
sys.path.insert(0,str(SCC))
import registry
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-c116-rh-evap-coupled-20261031-0446"
FILES=("c116_two_way_coupling.py","qa_c116_independent.py",
       "C116_TWO_WAY_HOURLY.csv.gz","C116_SUMMARY.csv",
       "C116_METADATA.json","C116_INDEPENDENT_QA.json",
       "C116_FINDINGS.md","finalize_c116.py")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def guard():
 for root in (D,D.parent,SCC,Path("C:/Users/Lysda/OneDrive/Projects/DataCenter_Heat_Reuse")):
  for flag in ("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE"):
   if (root/flag).exists():raise RuntimeError("STOP_ACTIVE "+str(root/flag))
def write_once(name,obj):
 p=D/name;s=json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+"\n"
 if p.exists():
  if p.read_text(encoding="utf-8")!=s:raise RuntimeError("OUTPUT_DRIFT_"+name)
 else:p.write_text(s,encoding="utf-8")
def run():
 guard()
 meta=json.loads((D/"C116_METADATA.json").read_text(encoding="utf-8"))
 qa=json.loads((D/"C116_INDEPENDENT_QA.json").read_text(encoding="utf-8"))
 assert meta["task_id"]==TASK and meta["synthetic"] and not meta["field_validated"]
 assert qa["status"]=="PASS" and qa["rows"]==52560 and qa["negative_controls"]==4
 assert qa["independent_row_checks"]==683280 and qa["ideal_baseline_checks"]==70080
 assert sha(D/"C116_TWO_WAY_HOURLY.csv.gz")==meta["hourly_sha256"]
 assert sha(D/"C116_SUMMARY.csv")==meta["summary_sha256"]
 assert all((D/f).is_file() for f in FILES)
 manifest={"schema":"C116_SHA256_MANIFEST_V1","task_id":TASK,"synthetic":True,
   "qa":"PASS","files":{f:{"sha256":sha(D/f),"bytes":(D/f).stat().st_size} for f in FILES}}
 write_once("SHA256_MANIFEST_C116.json",manifest)
 evidence={"schema":"C116_EVIDENCE_V1","task_id":TASK,"actor":ACTOR,
   "artifact":str(D/"C116_TWO_WAY_HOURLY.csv.gz"),"artifact_sha256":meta["hourly_sha256"],
   "summary":str(D/"C116_SUMMARY.csv"),"qa":str(D/"C116_INDEPENDENT_QA.json"),
   "findings":str(D/"C116_FINDINGS.md"),
   "manifest":str(D/"SHA256_MANIFEST_C116.json"),
   "manifest_sha256":sha(D/"SHA256_MANIFEST_C116.json"),
   "synthetic":True,"field_validated":False,"source_signoffs_added":0,
   "next":"Subhour RH/enthalpy coupling and measured equipment/weather calibration; no physical signoffs."}
 write_once("EVIDENCE_C116.json",evidence)
 guard()
 with registry._open() as db:
  task=db.execute("select id,status from tasks where id=?",(TASK,)).fetchone()
  if not task or task["status"]!="queued":raise RuntimeError("TASK_STATE_DRIFT")
  old=db.execute("select id from task_events where task_id=? and kind='evidence' and actor=?",
                 (TASK,ACTOR)).fetchone()
  if old:eid=old["id"]
  else:
   registry._event(db,TASK,"evidence",ACTOR,{
    "artifact":evidence["artifact"],"sha256":evidence["artifact_sha256"],
    "summary":evidence["summary"],"qa":evidence["qa"],"findings":evidence["findings"],
    "manifest":evidence["manifest"],"evidence":str(D/"EVIDENCE_C116.json"),
    "qa_result":"52560 rows, 683280 independent checks, 105108 continuity, 70080 ideal regression, 4 negative controls PASS",
    "synthetic":True,"field_validated":False,"source_signoffs_added":0,
    "next":evidence["next"]})
   eid=db.execute("select last_insert_rowid()").fetchone()[0]
 write_once("CANONICAL_RECEIPT_C116.json",{"task_id":TASK,"event_id":eid,"actor":ACTOR,
   "evidence_sha256":sha(D/"EVIDENCE_C116.json"),
   "manifest_sha256":sha(D/"SHA256_MANIFEST_C116.json")})
 with registry._open() as db:
  got=db.execute("select id,actor from task_events where id=? and task_id=?",(eid,TASK)).fetchone()
  status=db.execute("select status from tasks where id=?",(TASK,)).fetchone()[0]
 assert got and got["actor"]==ACTOR and status=="queued"
 print(json.dumps({"event_id":eid,"readback":"VERIFIED","status":status,
  "artifact_sha256":meta["hourly_sha256"],
  "manifest_sha256":sha(D/"SHA256_MANIFEST_C116.json"),
  "receipt_sha256":sha(D/"CANONICAL_RECEIPT_C116.json")},indent=2))
if __name__=="__main__":run()
