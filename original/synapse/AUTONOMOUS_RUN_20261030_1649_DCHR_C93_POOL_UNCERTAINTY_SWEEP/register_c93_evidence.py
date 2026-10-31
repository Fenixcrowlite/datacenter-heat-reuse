"""Idempotent C93 evidence registration into an EXISTING Synapse task only."""
import hashlib, json, sys
from pathlib import Path
D=Path(__file__).resolve().parent
SCC=D.parent.parent
sys.path.insert(0,str(SCC))
import registry
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-c93-pool-uncertainty-20261030-1649"
FILES=("c93_uncertainty_sweep.py","qa_c93_independent.py","C93_SCENARIO_MATRIX.csv",
       "C93_MATRIX_METADATA.json","C93_INDEPENDENT_QA.json","C93_FINDINGS.md")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write_new(p,obj):
    with p.open("x",encoding="utf-8") as f:
        json.dump(obj,f,ensure_ascii=False,sort_keys=True,indent=2)
        f.write("\n")
def guard():
    for root in (D,D.parent,SCC,Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
        for f in ("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE"):
            if (root/f).exists():raise RuntimeError("STOP_ACTIVE "+str(root/f))
def main():
    guard()
    qa=json.loads((D/"C93_INDEPENDENT_QA.json").read_text(encoding="utf-8"))
    meta=json.loads((D/"C93_MATRIX_METADATA.json").read_text(encoding="utf-8"))
    if qa["status"]!="PASS" or qa["checks"]!=24 or qa["scenario_count"]!=54:
        raise RuntimeError("QA_NOT_ACCEPTED")
    if meta["matrix_sha256"]!=sha(D/"C93_SCENARIO_MATRIX.csv"):
        raise RuntimeError("OUTPUT_DRIFT")
    receipt=D/"CANONICAL_RECEIPT_C93.json"
    with registry._open() as db:
        task=db.execute("SELECT id,status FROM tasks WHERE id=?",(TASK,)).fetchone()
        if task is None:raise RuntimeError("TASK_NOT_FOUND")
        prior=db.execute("SELECT id FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",(TASK,ACTOR)).fetchone()
    if prior is not None:
        print(json.dumps({"existing_event":prior["id"],"receipt_exists":receipt.exists()}))
        return
    if receipt.exists():raise RuntimeError("RECEIPT_EXISTS_WITHOUT_EVENT")
    manifest={"schema":"C93_SHA256_MANIFEST_V1","task_id":TASK,"synthetic":True,
              "source_signoffs_added":0,"qa":"8/8 self + 24/24 independent PASS",
              "files":{name:{"sha256":sha(D/name),"bytes":(D/name).stat().st_size} for name in FILES}}
    manifest_path=D/"SHA256_MANIFEST_C93.json"
    write_new(manifest_path,manifest)
    evidence={"schema":"C93_POOL_UNCERTAINTY_EVIDENCE_V1","task_id":TASK,"actor":ACTOR,
              "scope":"54-case 8760h pool water uncertainty sweep; 473040 steps",
              "synthetic":True,"physical_validation":False,"source_signoffs_added":0,
              "qa":"8/8 self + 24/24 independent PASS",
              "matrix_sha256":sha(D/"C93_SCENARIO_MATRIX.csv"),
              "qa_sha256":sha(D/"C93_INDEPENDENT_QA.json"),
              "script_sha256":sha(D/"c93_uncertainty_sweep.py"),
              "manifest_sha256":sha(manifest_path),
              "findings_sha256":sha(D/"C93_FINDINGS.md"),
              "production_changed":False,
              "next":"Measured HX inlet/outlet temperatures/flows and HP COP vs lift; couple ventilation and dehumidification"}
    evidence_path=D/"EVIDENCE_C93.json"
    write_new(evidence_path,evidence)
    guard()
    with registry._open() as db:
        existing=db.execute("SELECT id FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",(TASK,ACTOR)).fetchone()
        if existing: event_id=existing["id"]
        else:
            registry._event(db,TASK,"evidence",ACTOR,
                {"artifact":str(D/"C93_SCENARIO_MATRIX.csv"),
                 "manifest":str(manifest_path),"evidence":str(evidence_path),
                 "sha256":evidence["matrix_sha256"],"qa":"8/8 self + 24/24 independent PASS",
                 "synthetic":True,"physical_validation":False,"source_signoffs_added":0,
                 "next":evidence["next"]})
            event_id=db.execute("SELECT last_insert_rowid()").fetchone()[0]
    write_new(receipt,{"schema":"SYNAPSE_IDEMPOTENT_EVIDENCE_RECEIPT_V1","task_id":TASK,
                      "actor":ACTOR,"event_id":event_id,"evidence_sha256":sha(evidence_path),
                      "manifest_sha256":sha(manifest_path)})
    with registry._open() as db:
        row=db.execute("SELECT id,actor FROM task_events WHERE id=? AND task_id=?",(event_id,TASK)).fetchone()
        state=db.execute("SELECT status FROM tasks WHERE id=?",(TASK,)).fetchone()[0]
    if not row or row["actor"]!=ACTOR:raise RuntimeError("READBACK_FAILED")
    print(json.dumps({"event_id":event_id,"readback":"VERIFIED_EXISTING","task_status":state,
        "matrix_sha256":evidence["matrix_sha256"],"manifest_sha256":evidence["manifest_sha256"],
        "evidence_sha256":sha(evidence_path),"receipt_sha256":sha(receipt)},indent=2))
if __name__=="__main__":main()
