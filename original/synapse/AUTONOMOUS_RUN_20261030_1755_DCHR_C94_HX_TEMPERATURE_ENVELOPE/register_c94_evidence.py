"""Idempotent C94 evidence for existing DataCenter task. Never creates tasks."""
import hashlib,json,sys
from pathlib import Path
D=Path(__file__).resolve().parent
SCC=D.parent.parent
sys.path.insert(0,str(SCC))
import registry
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-c94-hx-envelope-20261030-1755"
FILES=("c94_hx_temperature_envelope.py","qa_c94_independent.py",
       "C94_HOURLY.csv","C94_SUMMARY.csv","C94_METADATA.json",
       "C94_INDEPENDENT_QA.json","C94_FINDINGS.md","C94_RUN_LOG.txt","C94_QA_LOG.txt")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write_new(p,obj):
    with p.open("x",encoding="utf-8") as f:
        json.dump(obj,f,indent=2,sort_keys=True,ensure_ascii=False);f.write("\n")
def guard():
    for root in (D,D.parent,SCC,Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
        for name in ("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE"):
            if (root/name).exists():raise RuntimeError("STOP_ACTIVE "+str(root/name))
def main():
    guard()
    meta=json.loads((D/"C94_METADATA.json").read_text(encoding="utf-8"))
    qa=json.loads((D/"C94_INDEPENDENT_QA.json").read_text(encoding="utf-8"))
    if qa["status"]!="PASS" or qa["hourly_rows_checked"]!=157680 or qa["scenario_groups_checked"]!=18:
        raise RuntimeError("QA_NOT_PASS")
    if meta["hourly_sha256"]!=sha(D/"C94_HOURLY.csv") or meta["summary_sha256"]!=sha(D/"C94_SUMMARY.csv"):
        raise RuntimeError("OUTPUT_DRIFT")
    if meta["primary_source_signoffs_added"]!=0 or meta["measured"] is not False:
        raise RuntimeError("WRONG_VALIDATION_STATUS")
    with registry._open() as db:
        task=db.execute("SELECT id,status FROM tasks WHERE id=?",(TASK,)).fetchone()
        if not task:raise RuntimeError("EXISTING_TASK_MISSING")
        prior=db.execute("SELECT id FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",
                         (TASK,ACTOR)).fetchone()
    receipt=D/"CANONICAL_RECEIPT_C94.json"
    if prior:
        print(json.dumps({"existing_event":prior["id"],"receipt_exists":receipt.exists()}));return
    if receipt.exists():raise RuntimeError("RECEIPT_WITHOUT_EVENT")
    manifest={"schema":"C94_SHA256_MANIFEST_V1","task_id":TASK,"synthetic":True,
              "source_signoffs_added":0,"qa":"12/12 self, 157680/157680 independent hourly, 18/18 groups PASS",
              "files":{name:{"sha256":sha(D/name),"bytes":(D/name).stat().st_size} for name in FILES}}
    manifest_path=D/"SHA256_MANIFEST_C94.json"
    write_new(manifest_path,manifest)
    evidence={"schema":"C94_HX_TEMPERATURE_ENVELOPE_EVIDENCE_V1","task_id":TASK,"actor":ACTOR,
              "scope":"18 synthetic source temperature/flow/backup scenarios x 8760 hours",
              "synthetic":True,"physical_validation":False,"source_signoffs_added":0,
              "qa":manifest["qa"],"hourly_sha256":sha(D/"C94_HOURLY.csv"),
              "summary_sha256":sha(D/"C94_SUMMARY.csv"),
              "independent_qa_sha256":sha(D/"C94_INDEPENDENT_QA.json"),
              "manifest_sha256":sha(manifest_path),"findings_sha256":sha(D/"C94_FINDINGS.md"),
              "production_changed":False,
              "next":"Get measured source temperature/flow and manufacturer COP; implement UA/NTU and air-side ventilation/dehumidification"}
    evpath=D/"EVIDENCE_C94.json"
    write_new(evpath,evidence)
    guard()
    with registry._open() as db:
        prior=db.execute("SELECT id FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",
                         (TASK,ACTOR)).fetchone()
        if prior:event_id=prior["id"]
        else:
            registry._event(db,TASK,"evidence",ACTOR,{
                "artifact":str(D/"C94_SUMMARY.csv"),"hourly":str(D/"C94_HOURLY.csv"),
                "manifest":str(manifest_path),"evidence":str(evpath),
                "sha256":evidence["summary_sha256"],"qa":evidence["qa"],
                "synthetic":True,"physical_validation":False,"source_signoffs_added":0,
                "next":evidence["next"]})
            event_id=db.execute("SELECT last_insert_rowid()").fetchone()[0]
    write_new(receipt,{"schema":"SYNAPSE_IDEMPOTENT_EVIDENCE_RECEIPT_V1",
                       "task_id":TASK,"actor":ACTOR,"event_id":event_id,
                       "evidence_sha256":sha(evpath),"manifest_sha256":sha(manifest_path)})
    with registry._open() as db:
        row=db.execute("SELECT id,actor FROM task_events WHERE id=? AND task_id=?",(event_id,TASK)).fetchone()
        status=db.execute("SELECT status FROM tasks WHERE id=?",(TASK,)).fetchone()[0]
    if not row or row["actor"]!=ACTOR:raise RuntimeError("READBACK_FAILED")
    print(json.dumps({"event_id":event_id,"readback":"VERIFIED_EXISTING","task_status":status,
        "summary_sha256":evidence["summary_sha256"],"hourly_sha256":evidence["hourly_sha256"],
        "manifest_sha256":evidence["manifest_sha256"],"evidence_sha256":sha(evpath),
        "receipt_sha256":sha(receipt)},indent=2))
if __name__=="__main__":main()
