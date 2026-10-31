"""C34 immutable evidence and idempotent registration in EXISTING DataCenter task."""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import sqlite3
import time
from pathlib import Path

H = Path(__file__).resolve().parent
SCC = H.parent.parent
DCHR = Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")
TASK = "scc-2aab24704c2bd0"
ACTOR = "chatgpt-dchr-c34-v85-capacity-contract-20261028-1655"
NEXT = ("Locate the real 100 MWh baseline model/dataset and inspect its SOC and temperature definition; "
        "then compare C31 and the actual baseline at identical boundaries. Do not conflate the v85 10 MWh test cases.")
FILES = ["audit_v85_contract.py", "independent_qa_c34.py", "C34_V85_CONTRACT.json",
         "C34_ENGINEERING_NOTE_SK.md", "QA_INDEPENDENT_C34.json", "AUDIT_RUN.log", "QA_RUN.log", "finalize_c34.py"]

def sha(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda: f.read(1024*1024), b""):
            h.update(b)
    return h.hexdigest()

def immutable(name, data):
    p = H / name
    raw = (json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False)+"\n").encode("utf-8")
    if p.exists():
        if p.read_bytes() != raw:
            raise RuntimeError("IMMUTABLE_CONFLICT " + name)
    else:
        with p.open("xb") as f:
            f.write(raw)
    return sha(p)

def stop_check():
    for root in (SCC, SCC/"recovery", SCC/"Continuity", DCHR, H):
        for name in ("STOP", "STOP.txt", "STOP.flag", "PAUSE", "PAUSE.flag", ".STOP", ".PAUSE"):
            if (root/name).exists():
                raise RuntimeError("STOP_ACTIVE " + str(root/name))

def main():
    stop_check()
    data = json.loads((H/"C34_V85_CONTRACT.json").read_text(encoding="utf-8"))
    qa = json.loads((H/"QA_INDEPENDENT_C34.json").read_text(encoding="utf-8"))
    assert data["scope"] == "DCHR_C34_V85_ACTUAL_STORAGE_CONTRACT"
    assert data["source_sha256"]["slx"] == "2a9de22c0c55e8c4a87f7b0e0cfe9cd97db08c991f09d98361b009de310adde7"
    assert data["saved_v85_spec_case_count"] == 27 and data["saved_v85_case_capacities_mwh"] == [10.0]
    assert data["same_baseline_proven"] is False and data["no_matlab_run"] is True
    assert qa["status"] == "PASS" and qa["passed"] == 166 and qa["failed"] == 0
    assert all((H/f).is_file() for f in FILES)
    manifest_sha = immutable("SHA256_MANIFEST_C34.json", {"count": len(FILES), "files": {f: sha(H/f) for f in FILES}})
    evidence = {"scope": data["scope"], "artifact_directory": str(H), "manifest_sha256": manifest_sha,
                "source_model_sha256": data["source_sha256"]["slx"], "source_spec_sha256": data["source_sha256"]["spec"],
                "qa": "166/166 independent checks PASS (Decimal, model ZIP, source SHA, negative controls)",
                "saved_v85_spec_cases": 27, "saved_v85_test_capacity_mwh": 10.0,
                "previous_c33_assumed_capacity_mwh": 100.0, "simulink_100mwh_parity_proven": False,
                "no_matlab_run": True, "primary_source_signoffs": 0, "next_step": NEXT}
    evidence_sha = immutable("EVIDENCE_C34.json", evidence)
    payload = dict(evidence, evidence_sha256=evidence_sha)
    stop_check()
    with sqlite3.connect(SCC/"tasks.sqlite3", timeout=10) as db:
        db.execute("PRAGMA busy_timeout=10000")
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT project,status,worker_pid FROM tasks WHERE id=?", (TASK,)).fetchone()
        if not row or row[0] != "DataCenter Heat Reuse" or row[1] in ("done", "cancelled") or row[2] is not None:
            raise RuntimeError("TASK_NOT_ELIGIBLE " + str(row))
        prior = db.execute("SELECT id,data_json FROM task_events WHERE task_id=? AND actor=? AND kind='evidence'", (TASK,ACTOR)).fetchall()
        if prior:
            if len(prior)!=1 or json.loads(prior[0][1]) != payload:
                raise RuntimeError("EVENT_CONFLICT")
            event_id, state = prior[0][0], "ALREADY_RECORDED"
        else:
            event_id = db.execute("INSERT INTO task_events(task_id,at,kind,actor,data_json) VALUES(?,?,?,?,?)",
                (TASK,time.time(),"evidence",ACTOR,json.dumps(payload,sort_keys=True,ensure_ascii=False))).lastrowid
            state = "RECORDED"
        db.commit()
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    handoff = H/"FINAL_HANDOFF.md"
    if not handoff.exists():
        text = "\n".join([
            "# DCHR C34 saved v85 storage contract | " + dt.datetime.now().astimezone().isoformat(timespec="seconds"), "",
            "VERIFIED: actual saved v85 model hash " + data["source_sha256"]["slx"] + ".",
            "The 27 archived v85 cases all specify C=0.2 MWh/K, Tmin=20C, Tmax=70C, so Emax=10 MWh.",
            "Source electrical_policy_v85.m and earliest_dispatch_kernel_v75.m implement Emax=C*(Tmax-Tmin).",
            "CRITICAL CORRECTION: prior C33 synthetic 100 MWh baseline is NOT equivalent to these v85 10 MWh test cases.",
            "No assertion about all possible v85 configurations or actual real-world tank volume.",
            "Independent QA 166/166 PASS; model ZIP integrity, Decimal cases, source SHA, negative controls.",
            "No MATLAB execution; no changes to OneDrive, Simulink model, shared GUI, OAuth, VRS or other branches.",
            "Existing Synapse task " + TASK + " evidence event #" + str(event_id) + "; task remains queued, no worker.",
            "Card: https://desktop-m9l3i4m.taila1c6bd.ts.net/?synapse_task=" + TASK,
            "Artifact: " + str(H),
            "SHA256 manifest: " + manifest_sha, "SHA256 evidence: " + evidence_sha,
            "Primary source signoffs: 0/31. Dynamic model parity: NOT VERIFIED.",
            "NEXT: " + NEXT, ""
        ])
        with handoff.open("x",encoding="utf-8") as f:
            f.write(text)
    immutable("REGISTRY_RESULT_C34.json", {"task_id":TASK,"event_id":event_id,
        "manifest_sha256":manifest_sha,"evidence_sha256":evidence_sha,"handoff_sha256":sha(handoff)})
    print(json.dumps({"state":state,"event_id":event_id,"task_id":TASK,
                      "manifest_sha256":manifest_sha,"evidence_sha256":evidence_sha,
                      "handoff_sha256":sha(handoff)},ensure_ascii=False))

if __name__ == "__main__":
    main()
