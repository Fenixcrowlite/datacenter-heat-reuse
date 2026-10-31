"""C98 idempotent evidence on existing DataCenter card; no status changes."""
import hashlib,json,sys
from pathlib import Path
D=Path(__file__).resolve().parent
SCC=D.parent.parent
sys.path.insert(0,str(SCC))
import registry
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-c98-ua-boundary-20261030-1954"
FILES=("c98_ua_threshold.py","qa_c98_independent.py","C98_SWEEP.csv",
       "C98_THRESHOLDS.json","C98_INDEPENDENT_QA.json","C98_FINDINGS.md",
       "C98_RUN_LOG.txt","C98_QA_LOG.txt")
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()
def guard():
    for root in (D,D.parent,SCC,Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
        for name in FLAGS:
            if (root/name).exists():raise RuntimeError("STOP_ACTIVE "+str(root/name))
def save(path,obj):
    with path.open("x",encoding="utf-8") as f:
        json.dump(obj,f,indent=2,sort_keys=True,ensure_ascii=False);f.write("\n")
def main():
    guard()
    m=json.loads((D/"C98_THRESHOLDS.json").read_text(encoding="utf-8"))
    q=json.loads((D/"C98_INDEPENDENT_QA.json").read_text(encoding="utf-8"))
    if m["task_id"]!=TASK or m["unique_simulations"]!=127 or m["hour_steps"]!=1112520:
        raise RuntimeError("INVALID_MODEL_METADATA")
    if m["field_validated"] or m["vendor_COP"] or m["source_signoffs_added"]!=0:
        raise RuntimeError("UNSUPPORTED_PHYSICAL_CLAIM")
    if q["status"]!="PASS" or q["independent_assertions"]<800 or q["rows_checked"]!=127 or not q["negative_energy_detected"] or not q["negative_feasibility_detected"]:
        raise RuntimeError("QA_NOT_PASS")
    if sha(D/"C98_SWEEP.csv")!=m["sweep_sha256"] or q["sweep_sha256"]!=m["sweep_sha256"]:
        raise RuntimeError("SHA_MISMATCH")
    with registry._open() as db:
        task=db.execute("SELECT id,status FROM tasks WHERE id=?",(TASK,)).fetchone()
        if not task:raise RuntimeError("EXISTING_TASK_MISSING")
        prior=db.execute("SELECT id FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",(TASK,ACTOR)).fetchone()
    receipt=D/"CANONICAL_RECEIPT_C98.json"
    if prior:
        print(json.dumps({"existing_event":prior["id"],"receipt_exists":receipt.exists()}));return
    if receipt.exists():raise RuntimeError("RECEIPT_WITHOUT_EVENT")
    manifest={"schema":"C98_SHA256_MANIFEST_V1","task_id":TASK,
              "qa":"820 independent assertions; 127 simulations; 7 pass/fail brackets; 2 negative controls",
              "field_validated":False,"source_signoffs_added":0,
              "files":{name:{"sha256":sha(D/name),"bytes":(D/name).stat().st_size} for name in FILES}}
    man=D/"SHA256_MANIFEST_C98.json";save(man,manifest)
    ev={"schema":"C98_EVIDENCE_V1","task_id":TASK,"actor":ACTOR,
        "artifact":str(D/"C98_SWEEP.csv"),"summary":str(D/"C98_THRESHOLDS.json"),
        "manifest":str(man),"manifest_sha256":sha(man),"sweep_sha256":m["sweep_sha256"],
        "qa":manifest["qa"],"field_validated":False,"source_signoffs_added":0,
        "next":"Use measured source/flow and vendor UA/COP curves, couple evaporator loop; include ventilation/dehumidification"}
    evp=D/"EVIDENCE_C98.json";save(evp,ev)
    guard()
    with registry._open() as db:
        prior=db.execute("SELECT id FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",(TASK,ACTOR)).fetchone()
        if prior:eid=prior["id"]
        else:
            registry._event(db,TASK,"evidence",ACTOR,
                {"artifact":ev["artifact"],"summary":ev["summary"],
                 "manifest":ev["manifest"],"evidence":str(evp),
                 "sha256":ev["sweep_sha256"],"qa":ev["qa"],
                 "field_validated":False,"source_signoffs_added":0,"next":ev["next"]})
            eid=db.execute("SELECT last_insert_rowid()").fetchone()[0]
    save(receipt,{"task_id":TASK,"actor":ACTOR,"event_id":eid,
                  "evidence_sha256":sha(evp),"manifest_sha256":sha(man)})
    with registry._open() as db:
        check=db.execute("SELECT id,actor FROM task_events WHERE id=? AND task_id=?",(eid,TASK)).fetchone()
        status=db.execute("SELECT status FROM tasks WHERE id=?",(TASK,)).fetchone()[0]
    if not check or check["actor"]!=ACTOR:raise RuntimeError("READBACK_FAILED")
    print(json.dumps({"event_id":eid,"readback":"VERIFIED_EXISTING","task_status":status,
                      "sweep_sha256":m["sweep_sha256"],"manifest_sha256":sha(man),
                      "receipt_sha256":sha(receipt)},indent=2))
if __name__=="__main__":main()
