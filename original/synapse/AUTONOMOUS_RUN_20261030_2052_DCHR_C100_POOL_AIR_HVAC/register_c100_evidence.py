"""Idempotent evidence for existing DataCenter task; no task status mutation."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
D=Path(__file__).resolve().parent
SCC=D.parent.parent
sys.path.insert(0,str(SCC))
import registry
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-c100-air-hvac-20261030-2052"
FILES=("c100_air_hvac.py","qa_c100_independent.py","C100_AIR_HOURLY.csv.gz",
       "C100_AIR_SUMMARY.csv","C100_METADATA.json","C100_INDEPENDENT_QA.json",
       "C100_FINDINGS.md","C100_RUN_LOG.txt","C100_QA_LOG.txt",
       "C100_QA_INITIAL_FAILURE.txt","C100_QA_SECOND_FAILURE.txt")
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
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
    m=json.loads((D/"C100_METADATA.json").read_text(encoding="utf-8"))
    q=json.loads((D/"C100_INDEPENDENT_QA.json").read_text(encoding="utf-8"))
    if m["task_id"]!=TASK or m["hourly_rows"]!=78840 or m["scenarios"]!=9:
        raise RuntimeError("INVALID_METADATA")
    if m["field_validated"] or m["measured_weather"] or m["manufacturer_dehumidifier"] or m["source_signoffs_added"]!=0:
        raise RuntimeError("FALSE_PHYSICAL_CLAIM")
    if q["status"]!="PASS" or q["assertions"]<1000000 or q["rows_checked"]!=78840 or not q["negative_dehum_detected"] or not q["negative_rh_detected"]:
        raise RuntimeError("QA_NOT_ACCEPTED")
    if sha(D/"C100_AIR_HOURLY.csv.gz")!=m["hourly_sha256"] or sha(D/"C100_AIR_SUMMARY.csv")!=m["summary_sha256"]:
        raise RuntimeError("DATA_SHA_MISMATCH")
    if q["hourly_sha256"]!=m["hourly_sha256"] or q["summary_sha256"]!=m["summary_sha256"]:
        raise RuntimeError("QA_SHA_MISMATCH")
    if any(not (D/f).is_file() for f in FILES):raise RuntimeError("MISSING_FILE")
    with registry._open() as db:
        task=db.execute("SELECT id,status FROM tasks WHERE id=?",(TASK,)).fetchone()
        if not task:raise RuntimeError("TASK_NOT_FOUND")
        old=db.execute("SELECT id FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",(TASK,ACTOR)).fetchone()
    receipt=D/"CANONICAL_RECEIPT_C100.json"
    if old:
        print(json.dumps({"existing_event":old["id"],"receipt_exists":receipt.exists()}));return
    if receipt.exists():raise RuntimeError("RECEIPT_WITHOUT_EVENT")
    man={"schema":"C100_SHA256_MANIFEST_V1","task_id":TASK,
         "qa":"13/13 selftests; 1419217 independent assertions; 78840 hourly rows; 2 negative controls",
         "synthetic":True,"source_signoffs_added":0,
         "files":{f:{"sha256":sha(D/f),"bytes":(D/f).stat().st_size} for f in FILES}}
    mp=D/"SHA256_MANIFEST_C100.json";save(mp,man)
    ev={"schema":"C100_EVIDENCE_V1","task_id":TASK,"actor":ACTOR,
        "artifact":str(D/"C100_AIR_HOURLY.csv.gz"),
        "summary":str(D/"C100_AIR_SUMMARY.csv"),
        "metadata":str(D/"C100_METADATA.json"),
        "findings":str(D/"C100_FINDINGS.md"),
        "manifest":str(mp),"manifest_sha256":sha(mp),
        "hourly_sha256":m["hourly_sha256"],"qa":man["qa"],
        "field_validated":False,"source_signoffs_added":0,
        "next":"Measure T/RH/airflow; obtain dehumidifier and HRV curves; include fan/humidifier/cooling energy; couple to C96 with no double count."}
    ep=D/"EVIDENCE_C100.json";save(ep,ev)
    guard()
    with registry._open() as db:
        old=db.execute("SELECT id FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",(TASK,ACTOR)).fetchone()
        if old:eid=old["id"]
        else:
            registry._event(db,TASK,"evidence",ACTOR,
                {"artifact":ev["artifact"],"summary":ev["summary"],
                 "metadata":ev["metadata"],"findings":ev["findings"],
                 "manifest":ev["manifest"],"evidence":str(ep),
                 "sha256":ev["hourly_sha256"],"qa":ev["qa"],
                 "field_validated":False,"source_signoffs_added":0,
                 "next":ev["next"]})
            eid=db.execute("SELECT last_insert_rowid()").fetchone()[0]
    save(receipt,{"task_id":TASK,"actor":ACTOR,"event_id":eid,
                  "evidence_sha256":sha(ep),"manifest_sha256":sha(mp)})
    with registry._open() as db:
        check=db.execute("SELECT id,actor FROM task_events WHERE id=? AND task_id=?",(eid,TASK)).fetchone()
        status=db.execute("SELECT status FROM tasks WHERE id=?",(TASK,)).fetchone()[0]
    if not check or check["actor"]!=ACTOR:raise RuntimeError("READBACK_FAILED")
    print(json.dumps({"event_id":eid,"readback":"VERIFIED","task_status":status,
                      "hourly_sha256":m["hourly_sha256"],"manifest_sha256":sha(mp),
                      "receipt_sha256":sha(receipt)},indent=2))
if __name__=="__main__":main()
