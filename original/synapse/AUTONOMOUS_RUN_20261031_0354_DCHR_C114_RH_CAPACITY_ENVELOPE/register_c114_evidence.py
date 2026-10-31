"""Fail-closed C114 evidence, only in the existing DataCenter Synapse task."""
from pathlib import Path
import hashlib,json,sys
D=Path(__file__).resolve().parent
SCC=D.parent.parent
sys.path.insert(0,str(SCC))
import registry
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-c114-rh-capacity-20261031-0354"
FILES=("c114_capacity_search.py","c114_asymmetric.py","qa_c114_independent.py",
       "C114_CAPACITY_ENVELOPE.csv","C114_METADATA.json",
       "C114_ASYMMETRIC_CAPACITY.csv","C114_ASYMMETRIC_METADATA.json",
       "C114_INDEPENDENT_QA.json","C114_FINDINGS.md","register_c114_evidence.py")
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
 p=D/name
 payload=json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
 if p.exists():
  if p.read_text(encoding="utf-8")!=payload:raise RuntimeError("EXISTING_FILE_DRIFT_"+name)
 else:
  with p.open("x",encoding="utf-8") as f:f.write(payload)
def run():
 guard()
 meta=json.loads((D/"C114_METADATA.json").read_text(encoding="utf-8"))
 asym=json.loads((D/"C114_ASYMMETRIC_METADATA.json").read_text(encoding="utf-8"))
 qa=json.loads((D/"C114_INDEPENDENT_QA.json").read_text(encoding="utf-8"))
 assert meta["task_id"]==TASK and asym["task_id"]==TASK
 assert meta["synthetic"] and asym["synthetic"] and not meta["field_validated"]
 assert qa["status"]=="PASS" and qa["annual_reference_hours"]==140160 and qa["negative_controls"]==3
 assert len(meta["results"])==2 and len(asym["rows"])==2
 assert sha(D/"C114_CAPACITY_ENVELOPE.csv")==meta["envelope_sha256"]
 assert sha(D/"C114_ASYMMETRIC_CAPACITY.csv")==asym["data_sha256"]
 for row in asym["rows"]:
  assert row["joint_below_45_h"]==row["joint_above_65_h"]==0
  assert 0<row["dehum_upper_passing_kg_h"]-row["dehum_lower_failing_kg_h"]<=.01
  assert 0<row["humid_upper_passing_kg_h"]-row["humid_lower_failing_kg_h"]<=.01
 for name in FILES:assert (D/name).is_file(),name
 manifest={"schema":"C114_SHA256_MANIFEST_V1","task_id":TASK,"qa_status":"PASS",
           "synthetic":True,"field_validated":False,"source_signoffs_added":0,
           "files":{f:{"sha256":sha(D/f),"bytes":(D/f).stat().st_size} for f in FILES}}
 save_once("SHA256_MANIFEST_C114.json",manifest)
 evidence={"schema":"C114_EVIDENCE_V1","task_id":TASK,"actor":ACTOR,
           "artifact":str(D/"C114_ASYMMETRIC_CAPACITY.csv"),
           "symmetric":str(D/"C114_CAPACITY_ENVELOPE.csv"),
           "qa":str(D/"C114_INDEPENDENT_QA.json"),
           "findings":str(D/"C114_FINDINGS.md"),
           "manifest":str(D/"SHA256_MANIFEST_C114.json"),
           "manifest_sha256":sha(D/"SHA256_MANIFEST_C114.json"),
           "artifact_sha256":asym["data_sha256"],
           "synthetic":True,"field_validated":False,"source_signoffs_added":0,
           "next":"Two-way RH->evaporation->latent heat->pool temperature coupling, conservation QA, then real equipment curves."}
 save_once("EVIDENCE_C114.json",evidence)
 guard()
 with registry._open() as db:
  task=db.execute("select id,status from tasks where id=?",(TASK,)).fetchone()
  assert task and task["status"]=="queued"
  old=db.execute("select id from task_events where task_id=? and kind='evidence' and actor=?",(TASK,ACTOR)).fetchone()
  if old:eid=old["id"]
  else:
   registry._event(db,TASK,"evidence",ACTOR,{
    "artifact":evidence["artifact"],"symmetric":evidence["symmetric"],
    "qa":evidence["qa"],"findings":evidence["findings"],
    "manifest":evidence["manifest"],"evidence":str(D/"EVIDENCE_C114.json"),
    "sha256":evidence["artifact_sha256"],
    "qa_result":"140160 independent hourly reference steps, 94 numeric checks, 3 negative controls PASS",
    "synthetic":True,"field_validated":False,"source_signoffs_added":0,
    "next":evidence["next"]})
   eid=db.execute("select last_insert_rowid()").fetchone()[0]
 save_once("CANONICAL_RECEIPT_C114.json",{"task_id":TASK,"event_id":eid,"actor":ACTOR,
            "evidence_sha256":sha(D/"EVIDENCE_C114.json"),
            "manifest_sha256":sha(D/"SHA256_MANIFEST_C114.json")})
 with registry._open() as db:
  got=db.execute("select id,actor from task_events where id=? and task_id=?",(eid,TASK)).fetchone()
  state=db.execute("select status from tasks where id=?",(TASK,)).fetchone()[0]
 assert got and got["actor"]==ACTOR
 print(json.dumps({"event_id":eid,"readback":"VERIFIED","status":state,
       "artifact_sha256":asym["data_sha256"],
       "manifest_sha256":sha(D/"SHA256_MANIFEST_C114.json"),
       "receipt_sha256":sha(D/"CANONICAL_RECEIPT_C114.json")},indent=2))
if __name__=="__main__":run()
