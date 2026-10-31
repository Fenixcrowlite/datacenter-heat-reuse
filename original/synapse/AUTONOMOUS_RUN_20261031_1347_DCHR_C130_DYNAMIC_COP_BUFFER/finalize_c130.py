"""Fail-closed C130 receipt and evidence writer for existing Synapse task."""
from pathlib import Path
import datetime,hashlib,json,sys
D=Path(__file__).resolve().parent
ROOT=D.parent.parent
sys.path.insert(0,str(ROOT))
import registry
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-c130-dynamic-cop-buffer-20261031-1347"
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda:f.read(1048576),b""):h.update(block)
    return h.hexdigest()
def guard():
    for root in (D,D.parent,ROOT,Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
        for flag in FLAGS:
            if (root/flag).exists():raise RuntimeError("STOP_ACTIVE "+str(root/flag))
def once(name,text):
    p=D/name
    if p.exists():
        if p.read_text(encoding="utf-8")!=text:raise RuntimeError("DRIFT "+name)
    else:p.write_text(text,encoding="utf-8")
def jonce(name,obj):
    once(name,json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
def main():
    guard()
    meta=json.loads((D/"C130_METADATA.json").read_text(encoding="utf-8"))
    qa=json.loads((D/"C130_INDEPENDENT_QA.json").read_text(encoding="utf-8"))
    summary=json.loads((D/"C130_SUMMARY.json").read_text(encoding="utf-8"))
    assert meta["task_id"]==TASK and meta["synthetic"] and not meta["field_validated"]
    assert meta["rows"]==qa["rows"]==4032 and meta["scenarios"]==qa["scenarios"]==6
    assert meta["selftests"]==8 and qa["negative_controls"]==9 and qa["independent"]
    assert qa["status"]=="PASS" and len(summary)==6
    assert meta["data_sha256"]==qa["data_sha256"]==sha(D/"C130_DYNAMIC_COP_BUFFER.csv.gz")
    assert meta["summary_sha256"]==qa["summary_sha256"]==sha(D/"C130_SUMMARY.json")
    names=("c130_dynamic_cop_buffer.py","qa_c130_independent.py","finalize_c130.py",
           "C130_DYNAMIC_COP_BUFFER.csv.gz","C130_SUMMARY.json","C130_METADATA.json",
           "C130_INDEPENDENT_QA.json","C130_FINDINGS.md")
    manifest={"schema":"C130_SHA256_MANIFEST_V1","task_id":TASK,
              "files":{name:sha(D/name) for name in names}}
    jonce("SHA256_MANIFEST_C130.json",manifest)
    next_step=("Obtain manufacturer COP maps and measured DC waste heat, then implement "
               "buffer losses/charge limits and repeat independent balances; no runtime edits.")
    ev={"task_id":TASK,"actor":ACTOR,"artifact":str(D/"C130_DYNAMIC_COP_BUFFER.csv.gz"),
        "sha256":meta["data_sha256"],"manifest":str(D/"SHA256_MANIFEST_C130.json"),
        "manifest_sha256":sha(D/"SHA256_MANIFEST_C130.json"),
        "qa":str(D/"C130_INDEPENDENT_QA.json"),"findings":str(D/"C130_FINDINGS.md"),
        "scenarios":6,"rows":4032,"selftests":8,"negative_controls":9,
        "synthetic":True,"field_validated":False,"source_signoffs_added":0,
        "next":next_step}
    jonce("EVIDENCE_C130.json",ev)
    guard()
    with registry._open() as db:
        row=db.execute("SELECT status FROM tasks WHERE id=?",(TASK,)).fetchone()
        if not row or row["status"]!="queued":raise RuntimeError("TASK_STATUS_DRIFT")
        prior=db.execute("SELECT id FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",
                         (TASK,ACTOR)).fetchone()
        if prior:eid=prior["id"]
        else:
            registry._event(db,TASK,"evidence",ACTOR,
                {"artifact":ev["artifact"],"sha256":ev["sha256"],
                 "qa":ev["qa"],"findings":ev["findings"],"manifest":ev["manifest"],
                 "evidence":str(D/"EVIDENCE_C130.json"),
                 "qa_result":"4032 independent rows, 9 negative controls PASS; 8 selftests PASS",
                 "synthetic":True,"not_field_validated":True,"next":ev["next"]})
            eid=db.execute("SELECT last_insert_rowid()").fetchone()[0]
    with registry._open() as db:
        back=db.execute("SELECT actor,data_json FROM task_events WHERE id=? AND task_id=?",(eid,TASK)).fetchone()
        status=db.execute("SELECT status FROM tasks WHERE id=?",(TASK,)).fetchone()["status"]
    if not back or back["actor"]!=ACTOR or ev["sha256"] not in back["data_json"]:
        raise AssertionError("EVENT_READBACK")
    jonce("CANONICAL_RECEIPT_C130.json",
          {"task_id":TASK,"event_id":eid,"actor":ACTOR,
           "evidence_sha256":sha(D/"EVIDENCE_C130.json"),
           "manifest_sha256":ev["manifest_sha256"]})
    now=datetime.datetime.now().astimezone().isoformat()
    handoff=f"""# C130 FINAL_HANDOFF | {now}

## Live preflight
Read NIGHT_HANDOFF_20261021.md, AGENTS.md, agent_knowledge/INDEX.md,
personal-assistant-kernel.md v1.2, workstream-isolation, task-lifecycle,
SynapseMCP concurrency. SynapseMCP Web ping OK at 13:47 CET,
control_enabled=true. At 13:50 CET free RAM 3894 MiB, VRAM 1223/8188 MiB,
GPU 0%; STOP/PAUSE absent in checked roots. Existing processes and Git
worktrees inspected; EduMotion Preview PID 18244 and 35824 still share
LISTENING port 8769; no changes to either. Desktop Commander monthly
quota exhausted, but primary SynapseMCP Web works.

## Engineering
New task-local C130 temperature COP + finite source heat and 0/30 kWh
buffer. Six 7-day scenarios, 4032 quarter-hour transitions. Source
and buffer balance checked independently for every row.
8 embedded tests, 4032 independent row checks, 9 negative controls PASS.
First run found a down-ramp surplus thermal dispatch, corrected within
C130 scope; independent QA test-row selection also corrected.
Data SHA256 {ev['sha256']}
Manifest SHA256 {ev['manifest_sha256']}
No physical or vendor validation, source signoffs still 0/31.

## Synapse
Existing task {TASK}; evidence event {eid} read back, status {status}.
No duplicate card, worker, Codex session or GPU job created.
No VRS, OAuth, shared GUI, MATLAB, SCADA or peer worktree edits.

## Exact next executable step
{next_step}
"""
    once("FINAL_HANDOFF.md",handoff)
    print(json.dumps({"status":"PASS","event_id":eid,"readback":"VERIFIED",
                      "task_status":status,"data_sha256":ev["sha256"],
                      "manifest_sha256":ev["manifest_sha256"],
                      "handoff_sha256":sha(D/"FINAL_HANDOFF.md"),
                      "manifest_files":len(names)},indent=2))
if __name__=="__main__":main()
