"""Idempotent C118 evidence receipt on EXISTING DataCenter task. No new task."""
import hashlib,json,sys
from pathlib import Path
D=Path(__file__).resolve().parent;SCC=D.parent.parent
sys.path.insert(0,str(SCC))
import registry
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-c118-subhour-rh-20261031-0550"
FILES=("c118_subhour_rh.py","qa_c118_independent.py","C118_SUBHOUR_STRESS.csv.gz",
       "C118_SUMMARY.csv","C118_METADATA.json","C118_INDEPENDENT_QA.json",
       "C118_FINDINGS.md","finalize_c118.py")
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda:f.read(1048576),b""):h.update(block)
    return h.hexdigest()
def guard():
    for root in (D,D.parent,SCC,Path("C:/Users/Lysda/OneDrive/Projects/DataCenter_Heat_Reuse")):
        for flag in FLAGS:
            if (root/flag).exists():raise RuntimeError("STOP_ACTIVE "+str(root/flag))
def once(name,obj):
    p=D/name
    s=json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+"\n"
    if p.exists():
        if p.read_text(encoding="utf-8")!=s:raise RuntimeError("OUTPUT_DRIFT_"+name)
    else:p.write_text(s,encoding="utf-8")
def run():
    guard()
    meta=json.loads((D/"C118_METADATA.json").read_text(encoding="utf-8"))
    qa=json.loads((D/"C118_INDEPENDENT_QA.json").read_text(encoding="utf-8"))
    assert meta["task_id"]==TASK and meta["synthetic"] and not meta["field_validated"]
    assert qa["status"]=="PASS" and qa["rows"]==210240
    assert qa["negative_controls"]==4 and qa["numerical_crosscheck"]["cases"]==60
    assert sha(D/"C118_SUBHOUR_STRESS.csv.gz")==meta["hourly_sha256"]
    assert sha(D/"C118_SUMMARY.csv")==meta["summary_sha256"]
    assert all((D/name).is_file() for name in FILES)
    manifest={"schema":"C118_SHA256_MANIFEST_V1","task_id":TASK,
              "synthetic":True,"qa":"PASS",
              "files":{name:{"sha256":sha(D/name),"bytes":(D/name).stat().st_size} for name in FILES}}
    once("SHA256_MANIFEST_C118.json",manifest)
    evidence={"schema":"C118_EVIDENCE_V1","task_id":TASK,"actor":ACTOR,
              "artifact":str(D/"C118_SUBHOUR_STRESS.csv.gz"),
              "artifact_sha256":meta["hourly_sha256"],
              "summary":str(D/"C118_SUMMARY.csv"),
              "qa":str(D/"C118_INDEPENDENT_QA.json"),
              "findings":str(D/"C118_FINDINGS.md"),
              "manifest":str(D/"SHA256_MANIFEST_C118.json"),
              "manifest_sha256":sha(D/"SHA256_MANIFEST_C118.json"),
              "synthetic":True,"field_validated":False,"source_signoffs_added":0,
              "next":"Subhour responsive dehumidifier + dynamic air temperature/enthalpy; calibrate with measured air flow and equipment."}
    once("EVIDENCE_C118.json",evidence)
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
                "manifest":evidence["manifest"],"evidence":str(D/"EVIDENCE_C118.json"),
                "qa_result":"210240 rows, 2733120 independent row checks, 210216 continuity, 60 numerical crosschecks, 4 negative controls PASS",
                "synthetic":True,"field_validated":False,"source_signoffs_added":0,
                "next":evidence["next"]})
            eid=db.execute("select last_insert_rowid()").fetchone()[0]
    once("CANONICAL_RECEIPT_C118.json",{"task_id":TASK,"event_id":eid,
        "actor":ACTOR,"evidence_sha256":sha(D/"EVIDENCE_C118.json"),
        "manifest_sha256":sha(D/"SHA256_MANIFEST_C118.json")})
    with registry._open() as db:
        row=db.execute("select id,actor from task_events where id=? and task_id=?",(eid,TASK)).fetchone()
        state=db.execute("select status from tasks where id=?",(TASK,)).fetchone()[0]
    assert row and row["actor"]==ACTOR and state=="queued"
    print(json.dumps({"event_id":eid,"readback":"VERIFIED","status":state,
        "artifact_sha256":meta["hourly_sha256"],
        "manifest_sha256":sha(D/"SHA256_MANIFEST_C118.json"),
        "receipt_sha256":sha(D/"CANONICAL_RECEIPT_C118.json")},indent=2))
if __name__=="__main__":run()
