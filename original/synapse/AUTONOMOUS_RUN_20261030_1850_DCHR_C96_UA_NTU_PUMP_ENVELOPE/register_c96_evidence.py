"""Idempotent C96 evidence write to EXISTING DataCenter card, never change task status."""
import hashlib,json,sys
from pathlib import Path
D=Path(__file__).resolve().parent
SCC=D.parent.parent
sys.path.insert(0,str(SCC))
import registry
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-c96-ua-ntu-pump-20261030-1850"
FILES=("c96_ua_ntu_pool.py","qa_c96_independent.py","C96_HOURLY.csv.gz",
       "C96_SUMMARY.csv","C96_METADATA.json","C96_FINDINGS.md",
       "C96_RUN_LOG.txt","C96_QA_LOG.txt","C96_INDEPENDENT_QA.json")
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()
def save(p,obj):
    with p.open("x",encoding="utf-8") as f:
        json.dump(obj,f,indent=2,sort_keys=True,ensure_ascii=False);f.write("\n")
def guard():
    for root in (D,D.parent,SCC,Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
        for name in FLAGS:
            if (root/name).exists():raise RuntimeError("STOP_ACTIVE "+str(root/name))
def main():
    guard()
    m=json.loads((D/"C96_METADATA.json").read_text(encoding="utf-8"))
    qa=json.loads((D/"C96_INDEPENDENT_QA.json").read_text(encoding="utf-8"))
    if m["task_id"]!=TASK or m["scenarios"]!=26 or m["hourly_rows"]!=227760:
        raise RuntimeError("METADATA_INVALID")
    if qa["status"]!="PASS" or qa["hourly_rows_verified"]!=227760 or qa["scenario_groups_verified"]!=26 or qa["LMTD_independent_checks"]!=12 or not qa["negative_corruption_detected"]:
        raise RuntimeError("QA_NOT_PASS")
    if sha(D/"C96_HOURLY.csv.gz")!=m["hourly_sha256"] or sha(D/"C96_SUMMARY.csv")!=m["summary_sha256"]:
        raise RuntimeError("DATA_SHA_MISMATCH")
    if m["field_validated"] or m["vendor_COP"] or m["primary_source_signoffs_added"]!=0:
        raise RuntimeError("UNSUPPORTED_PHYSICAL_CLAIM")
    with registry._open() as db:
        task=db.execute("SELECT id,status FROM tasks WHERE id=?",(TASK,)).fetchone()
        if not task:raise RuntimeError("EXISTING_TASK_MISSING")
        prior=db.execute("SELECT id FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",(TASK,ACTOR)).fetchone()
    receipt=D/"CANONICAL_RECEIPT_C96.json"
    if prior:
        print(json.dumps({"existing_event":prior["id"],"receipt_exists":receipt.exists()}));return
    if receipt.exists():raise RuntimeError("RECEIPT_WITHOUT_EVENT")
    manifest={"schema":"C96_SHA256_MANIFEST_V1","task_id":TASK,
       "QA":"16/16 selftests; 227760/227760 independent rows; 26/26 groups; 12/12 LMTD; negative corruption detected",
       "physical_validation":False,"new_source_signoffs":0,
       "files":{name:{"sha256":sha(D/name),"bytes":(D/name).stat().st_size} for name in FILES}}
    man=D/"SHA256_MANIFEST_C96.json";save(man,manifest)
    ev={"schema":"C96_UA_NTU_PUMP_EVIDENCE_V1","task_id":TASK,"actor":ACTOR,
      "artifact":str(D/"C96_HOURLY.csv.gz"),"summary":str(D/"C96_SUMMARY.csv"),
      "manifest":str(man),"manifest_sha256":sha(man),
      "hourly_sha256":m["hourly_sha256"],"summary_sha256":m["summary_sha256"],
      "qa":manifest["QA"],"physical_validation":False,"production_changed":False,
      "source_signoffs_added":0,
      "next":"Narrow UA below 2 kW/K to find failure boundary; obtain real source and vendor COP/pressure curves"}
    evp=D/"EVIDENCE_C96.json";save(evp,ev)
    guard()
    with registry._open() as db:
        prior=db.execute("SELECT id FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",(TASK,ACTOR)).fetchone()
        if prior:eid=prior["id"]
        else:
            registry._event(db,TASK,"evidence",ACTOR,
                {"artifact":ev["artifact"],"summary":ev["summary"],
                 "manifest":ev["manifest"],"evidence":str(evp),
                 "sha256":ev["hourly_sha256"],"qa":ev["qa"],
                 "physical_validation":False,"source_signoffs_added":0,
                 "next":ev["next"]})
            eid=db.execute("SELECT last_insert_rowid()").fetchone()[0]
    save(receipt,{"task_id":TASK,"actor":ACTOR,"event_id":eid,
         "evidence_sha256":sha(evp),"manifest_sha256":sha(man)})
    with registry._open() as db:
        check=db.execute("SELECT id,actor FROM task_events WHERE id=? AND task_id=?",(eid,TASK)).fetchone()
        status=db.execute("SELECT status FROM tasks WHERE id=?",(TASK,)).fetchone()[0]
    if not check or check["actor"]!=ACTOR:raise RuntimeError("READBACK_FAILED")
    print(json.dumps({"event_id":eid,"readback":"VERIFIED_EXISTING","task_status":status,
       "hourly_sha256":m["hourly_sha256"],"manifest_sha256":sha(man),
       "receipt_sha256":sha(receipt)},indent=2))
if __name__=="__main__":main()
