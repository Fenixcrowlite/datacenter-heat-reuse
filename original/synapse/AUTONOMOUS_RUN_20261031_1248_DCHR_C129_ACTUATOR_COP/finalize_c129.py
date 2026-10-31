"""Fail-closed C129 evidence writer for the existing DataCenter Synapse task."""
from pathlib import Path
import datetime,hashlib,json,sys
D=Path(__file__).resolve().parent
ROOT=D.parent.parent
sys.path.insert(0,str(ROOT))
import registry
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-c129-actuator-cop-20261031-1248"
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()
def guard():
    for root in (D,D.parent,ROOT,Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
        for n in FLAGS:
            if (root/n).exists():raise RuntimeError("STOP_ACTIVE "+str(root/n))
def once(name,body):
    p=D/name
    if p.exists():
        if p.read_text(encoding="utf-8")!=body:raise RuntimeError("EXISTING_DRIFT_"+name)
    else:p.write_text(body,encoding="utf-8")
def jonce(name,obj):
    once(name,json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
def main():
    guard()
    meta=json.loads((D/"C129_METADATA.json").read_text(encoding="utf-8"))
    qa=json.loads((D/"C129_INDEPENDENT_QA.json").read_text(encoding="utf-8"))
    summary=json.loads((D/"C129_SUMMARY.json").read_text(encoding="utf-8"))
    assert meta["task_id"]==TASK and meta["synthetic"] and not meta["field_validated"]
    assert meta["rows"]==qa["rows"]==22848 and meta["scenarios"]==qa["scenarios"]==34
    assert qa["status"]=="PASS" and qa["independent"] and qa["negative_controls"]==11
    assert qa["regression_numeric_fields"]==72576 and qa["regression_max_abs_delta"]<2e-9
    assert qa["ramp_limited_rows"]>0 and meta["selftests"]==8
    assert meta["data_sha256"]==qa["data_sha256"]==sha(D/"C129_ACTUATOR_COP.csv.gz")
    assert meta["summary_sha256"]==sha(D/"C129_SUMMARY.json")
    assert len(summary)==34 and all(v["quarters"]==672 for v in summary.values())
    names=("c129_actuator_cop.py","qa_c129_independent.py","finalize_c129.py",
           "C129_ACTUATOR_COP.csv.gz","C129_SUMMARY.json","C129_METADATA.json",
           "C129_INDEPENDENT_QA.json","C129_FINDINGS.md")
    manifest={"schema":"C129_SHA256_MANIFEST_V1","task_id":TASK,
              "files":{name:sha(D/name) for name in names}}
    jonce("SHA256_MANIFEST_C129.json",manifest)
    ev={"task_id":TASK,"actor":ACTOR,"artifact":str(D/"C129_ACTUATOR_COP.csv.gz"),
        "sha256":meta["data_sha256"],"manifest":str(D/"SHA256_MANIFEST_C129.json"),
        "manifest_sha256":sha(D/"SHA256_MANIFEST_C129.json"),
        "qa":str(D/"C129_INDEPENDENT_QA.json"),"findings":str(D/"C129_FINDINGS.md"),
        "scenarios":34,"rows":22848,"selftests":8,"negative_controls":11,
        "regression_numeric_fields":72576,"synthetic":True,"field_validated":False,
        "source_signoffs_added":0,
        "next":"Validate COP(T_source,T_sink,load) with manufacturer data, add DC waste heat availability and buffer; no shared runtime edits."}
    jonce("EVIDENCE_C129.json",ev)
    guard()
    with registry._open() as db:
        row=db.execute("SELECT status FROM tasks WHERE id=?",(TASK,)).fetchone()
        if not row or row["status"]!="queued":raise RuntimeError("TASK_STATUS_DRIFT")
        prior=db.execute("SELECT id FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",(TASK,ACTOR)).fetchone()
        if prior:eid=prior["id"]
        else:
            registry._event(db,TASK,"evidence",ACTOR,
                {"artifact":ev["artifact"],"sha256":ev["sha256"],
                 "qa":ev["qa"],"findings":ev["findings"],"manifest":ev["manifest"],
                 "evidence":str(D/"EVIDENCE_C129.json"),
                 "qa_result":"22848 independent rows, 11 negative controls, 72576 C128 numeric comparisons PASS",
                 "synthetic":True,"not_field_validated":True,"next":ev["next"]})
            eid=db.execute("SELECT last_insert_rowid()").fetchone()[0]
    with registry._open() as db:
        back=db.execute("SELECT actor FROM task_events WHERE id=? AND task_id=?",(eid,TASK)).fetchone()
        status=db.execute("SELECT status FROM tasks WHERE id=?",(TASK,)).fetchone()["status"]
    if not back or back["actor"]!=ACTOR:raise AssertionError("EVENT_READBACK")
    jonce("CANONICAL_RECEIPT_C129.json",
          {"task_id":TASK,"event_id":eid,"actor":ACTOR,
           "evidence_sha256":sha(D/"EVIDENCE_C129.json"),
           "manifest_sha256":ev["manifest_sha256"]})
    now=datetime.datetime.now().astimezone().isoformat()
    handoff=f"""# C129 FINAL_HANDOFF | {now}

## Live preflight
SynapseMCP Web ping 2026-10-31 12:45:48 CET: ok, control_enabled=true.
Read NIGHT_HANDOFF, AGENTS, INDEX, Kernel v1.2, workstream-isolation,
registry-task-lifecycle and SynapseMCP concurrency skill.
12:46 CET RAM free 4112/16203 MiB, VRAM 1221/8188 MiB, GPU 0%.
STOP/PAUSE absent in checked roots. Existing Synapse/Jarvice tasks,
process owners, Preview 8769 dual listeners and Git worktrees inspected;
none changed. Desktop Commander monthly quota exhausted.
No new Codex, GPU job, worker, GUI, OAuth, VRS, SCADA or MATLAB changes.

## Engineering
34 isolated 7-day synthetic scenarios, 22848 quarter-hour transitions.
8 embedded tests, 22848 independent CSV checks, 11 negative controls PASS.
C128 ideal actuator regression: 12096 rows, 72576 numeric comparisons,
max delta {qa['regression_max_abs_delta']:.4g}. Slew-limited rows {qa['ramp_limited_rows']}.
Data SHA256 {ev['sha256']}.
Manifest SHA256 {ev['manifest_sha256']}.
Model fixed assumed COP and ramp, not manufacturer/field validated; signoffs 0/31.

## Synapse registry
Existing task {TASK}, evidence event {eid} read back; status {status}.
No new card or worker.

## Exact next executable step
Validate heat-pump COP dependence on source/sink temperatures and load,
add finite waste heat availability and buffer storage, and independently
check vendor data. Do not apply synthetic sizing to real hardware.
"""
    once("FINAL_HANDOFF.md",handoff)
    print(json.dumps({"status":"PASS","event_id":eid,"readback":"VERIFIED",
                      "task_status":status,"data_sha256":ev["sha256"],
                      "manifest_sha256":ev["manifest_sha256"],
                      "handoff_sha256":sha(D/"FINAL_HANDOFF.md"),
                      "manifest_files":len(names)},indent=2))
if __name__=="__main__":main()
