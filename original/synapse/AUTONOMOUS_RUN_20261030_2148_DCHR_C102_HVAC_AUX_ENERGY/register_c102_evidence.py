"""Register one idempotent C102 evidence event on EXISTING Synapse task."""
import hashlib,json,sys
from pathlib import Path
D=Path(__file__).resolve().parent
SCC=D.parent.parent
sys.path.insert(0,str(SCC))
import registry
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-c102-hvac-aux-20261030-2148"
FILES=("c102_hvac_aux.py","qa_c102_independent.py","C102_AUX_HOURLY.csv.gz",
       "C102_AUX_SUMMARY.csv","C102_METADATA.json","C102_INDEPENDENT_QA.json","C102_FINDINGS.md")
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):h.update(chunk)
    return h.hexdigest()
def guard():
    for root in (D,D.parent,SCC,Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
        for n in FLAGS:
            if (root/n).exists():raise RuntimeError("STOP_ACTIVE "+str(root/n))
def save(p,obj):
    with p.open("x",encoding="utf-8") as f:json.dump(obj,f,indent=2,ensure_ascii=False,sort_keys=True);f.write("\n")
def run():
    guard()
    m=json.loads((D/"C102_METADATA.json").read_text(encoding="utf-8"))
    q=json.loads((D/"C102_INDEPENDENT_QA.json").read_text(encoding="utf-8"))
    if m["task_id"]!=TASK or not m["synthetic"] or m["field_validated"] or m["source_signoffs_added"]!=0:raise RuntimeError("BAD_PROVENANCE")
    if q["status"]!="PASS" or q["rows_checked"]!=78840 or q["assertions"]<1000000 or q["corruption_controls"]!=2 or not q["hot_hour_control"]:raise RuntimeError("QA_GATE")
    if sha(D/"C102_AUX_HOURLY.csv.gz")!=m["hourly_sha256"] or sha(D/"C102_AUX_SUMMARY.csv")!=m["summary_sha256"]:raise RuntimeError("SHA_MISMATCH")
    if any(not (D/f).is_file() for f in FILES):raise RuntimeError("MISSING_FILE")
    with registry._open() as db:
        task=db.execute("SELECT id,status FROM tasks WHERE id=?",(TASK,)).fetchone()
        if not task:raise RuntimeError("TASK_MISSING")
        old=db.execute("SELECT id FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",(TASK,ACTOR)).fetchone()
    if old:
        print(json.dumps({"existing_event":old["id"],"task_status":task["status"]}));return
    man={"schema":"C102_SHA256_MANIFEST_V1","task_id":TASK,
         "synthetic":True,"source_signoffs_added":0,
         "qa":"9/9 selftests; 1025013 independent checks; 78840 rows; 2 corruption controls; hot-hour branch",
         "files":{f:{"sha256":sha(D/f),"bytes":(D/f).stat().st_size} for f in FILES}}
    mp=D/"SHA256_MANIFEST_C102.json";save(mp,man)
    ev={"schema":"C102_EVIDENCE_V1","task_id":TASK,"actor":ACTOR,
        "artifact":str(D/"C102_AUX_HOURLY.csv.gz"),"summary":str(D/"C102_AUX_SUMMARY.csv"),
        "metadata":str(D/"C102_METADATA.json"),"findings":str(D/"C102_FINDINGS.md"),
        "qa":str(D/"C102_INDEPENDENT_QA.json"),"manifest":str(mp),
        "manifest_sha256":sha(mp),"hourly_sha256":m["hourly_sha256"],
        "qa_result":man["qa"],"field_validated":False,"source_signoffs_added":0,
        "next":"Obtain measured weather/flow and vendor curves; full latent cooling psychrometrics; couple air/water constrained heat allocation."}
    ep=D/"EVIDENCE_C102.json";save(ep,ev)
    guard()
    with registry._open() as db:
        old=db.execute("SELECT id FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",(TASK,ACTOR)).fetchone()
        if old:eid=old["id"]
        else:
            registry._event(db,TASK,"evidence",ACTOR,
                {"artifact":ev["artifact"],"summary":ev["summary"],"metadata":ev["metadata"],
                 "findings":ev["findings"],"qa":ev["qa"],"manifest":ev["manifest"],
                 "evidence":str(ep),"sha256":ev["hourly_sha256"],
                 "qa_result":ev["qa_result"],"field_validated":False,
                 "source_signoffs_added":0,"next":ev["next"]})
            eid=db.execute("SELECT last_insert_rowid()").fetchone()[0]
    save(D/"CANONICAL_RECEIPT_C102.json",{"task_id":TASK,"actor":ACTOR,"event_id":eid,
      "evidence_sha256":sha(ep),"manifest_sha256":sha(mp)})
    with registry._open() as db:
        check=db.execute("SELECT id,actor FROM task_events WHERE id=? AND task_id=?",(eid,TASK)).fetchone()
        status=db.execute("SELECT status FROM tasks WHERE id=?",(TASK,)).fetchone()[0]
    if not check or check["actor"]!=ACTOR:raise RuntimeError("REGISTRY_READBACK_FAIL")
    print(json.dumps({"event_id":eid,"readback":"VERIFIED","task_status":status,
      "manifest_sha256":sha(mp),"receipt_sha256":sha(D/"CANONICAL_RECEIPT_C102.json")},indent=2))
if __name__=="__main__":run()
