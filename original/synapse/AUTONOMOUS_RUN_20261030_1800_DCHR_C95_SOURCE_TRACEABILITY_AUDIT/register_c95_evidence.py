"""Register C95 read-only traceability evidence on the existing DataCenter task."""
import hashlib,json,sys
from pathlib import Path
D=Path(__file__).resolve().parent
SCC=D.parent.parent
sys.path.insert(0,str(SCC))
import registry
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-c95-source-traceability-20261030-1800"
FILES=("c95_source_traceability.py","qa_c95_independent.py",
       "C95_DRIFT_MATRIX.csv","C95_AUDIT.json","C95_FINDINGS.md",
       "C95_INDEPENDENT_QA.json","C95_RUN_LOG.txt","C95_QA_LOG.txt")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj):
    with p.open("x",encoding="utf-8") as f:
        json.dump(obj,f,indent=2,sort_keys=True,ensure_ascii=False);f.write("\n")
def guard():
    for root in (D,D.parent,SCC,Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
        for name in ("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE"):
            if (root/name).exists():raise RuntimeError("STOP_ACTIVE "+str(root/name))
def main():
    guard()
    qa=json.loads((D/"C95_INDEPENDENT_QA.json").read_text(encoding="utf-8"))
    audit=json.loads((D/"C95_AUDIT.json").read_text(encoding="utf-8"))
    if qa["status"]!="PASS" or qa["checks"]!=16 or audit["catalog_entries_verified"]!=31:
        raise RuntimeError("QA_NOT_PASS")
    if audit["matrix_sha256"]!=sha(D/"C95_DRIFT_MATRIX.csv") or audit["primary_source_signoffs_added"]!=0:
        raise RuntimeError("EVIDENCE_INVALID")
    with registry._open() as db:
        task=db.execute("SELECT id,status FROM tasks WHERE id=?",(TASK,)).fetchone()
        if not task:raise RuntimeError("TASK_NOT_FOUND")
        prior=db.execute("SELECT id FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",
                         (TASK,ACTOR)).fetchone()
    receipt=D/"CANONICAL_RECEIPT_C95.json"
    if prior:
        print(json.dumps({"existing_event":prior["id"],"receipt_exists":receipt.exists()}));return
    if receipt.exists():raise RuntimeError("RECEIPT_WITHOUT_EVENT")
    manifest={"schema":"C95_SHA256_MANIFEST_V1","task_id":TASK,
              "qa":"9 explicit generator assertions, 16/16 independent PASS",
              "catalog_sources":31,"new_signoffs":0,
              "files":{n:{"sha256":sha(D/n),"bytes":(D/n).stat().st_size} for n in FILES}}
    man=D/"SHA256_MANIFEST_C95.json";save(man,manifest)
    ev={"schema":"C95_SOURCE_TRACEABILITY_EVIDENCE_V1","task_id":TASK,"actor":ACTOR,
        "scope":"Cross-check C94 against existing 31-source catalog and canonical parameter registry",
        "catalog_entries":31,"source_signoffs_added":0,"physical_validation":False,
        "production_changed":False,"qa":manifest["qa"],
        "matrix_sha256":sha(D/"C95_DRIFT_MATRIX.csv"),
        "audit_sha256":sha(D/"C95_AUDIT.json"),
        "independent_qa_sha256":sha(D/"C95_INDEPENDENT_QA.json"),
        "manifest_sha256":sha(man),"next":"Use measured source inlet/outlet temperatures and flow, vendor COP map, then reviewed parameter update"}
    evp=D/"EVIDENCE_C95.json";save(evp,ev)
    guard()
    with registry._open() as db:
        prior=db.execute("SELECT id FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",
                         (TASK,ACTOR)).fetchone()
        if prior:event_id=prior["id"]
        else:
            registry._event(db,TASK,"evidence",ACTOR,
                {"artifact":str(D/"C95_DRIFT_MATRIX.csv"),"audit":str(D/"C95_AUDIT.json"),
                 "manifest":str(man),"evidence":str(evp),"sha256":ev["matrix_sha256"],
                 "qa":ev["qa"],"source_signoffs_added":0,"physical_validation":False,
                 "next":ev["next"]})
            event_id=db.execute("SELECT last_insert_rowid()").fetchone()[0]
    save(receipt,{"task_id":TASK,"actor":ACTOR,"event_id":event_id,
                  "evidence_sha256":sha(evp),"manifest_sha256":sha(man)})
    with registry._open() as db:
        check=db.execute("SELECT id,actor FROM task_events WHERE id=? AND task_id=?",(event_id,TASK)).fetchone()
        status=db.execute("SELECT status FROM tasks WHERE id=?",(TASK,)).fetchone()[0]
    if not check or check["actor"]!=ACTOR:raise RuntimeError("READBACK_FAILED")
    print(json.dumps({"event_id":event_id,"readback":"VERIFIED_EXISTING",
        "task_status":status,"matrix_sha256":ev["matrix_sha256"],
        "manifest_sha256":ev["manifest_sha256"],"receipt_sha256":sha(receipt)},indent=2))
if __name__=="__main__":main()
