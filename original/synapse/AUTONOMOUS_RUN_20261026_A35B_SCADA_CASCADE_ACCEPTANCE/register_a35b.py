"""Register A35B headless SCADA QA in existing DataCenter task, idempotently."""
from pathlib import Path
import hashlib,json,sqlite3,time

HERE=Path(__file__).resolve().parent
CENTER=HERE.parent.parent
TASK="scc-3d9d172beb6e1b"
ACTOR="chatgpt-a35b-scada-cascade-acceptance-20261026"
ROOTS=(CENTER,CENTER/"recovery",Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\scada_v09"),HERE)
FLAGS=("STOP","STOP.flag","STOP.txt",".STOP","PAUSE","PAUSE.flag",".PAUSE","STOP_MANAGED_WORKERS.txt")
FILES=["test_scada_cascade_live.py","register_a35b.py","SCADA_ACCEPTANCE.json",
       "SCADA_POOL_OFF_HEADLESS.png","SCADA_CASCADE_ACCEPTANCE_RU.md",
       "QA_RESULT.json","EVIDENCE.json"]
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()
def save_once(p,obj):
    if p.exists():
        if json.loads(p.read_text(encoding="utf8"))!=obj:
            raise RuntimeError("EVIDENCE_CONFLICT "+str(p))
    else:p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def main():
    for root in ROOTS:
        for f in FLAGS:
            if (root/f).exists():raise RuntimeError("STOP_ACTIVE "+str(root/f))
    j=json.loads((HERE/"SCADA_ACCEPTANCE.json").read_text(encoding="utf8"))
    if j["passed"]!=28 or j["total"]!=28 or any(not t["pass"] for t in j["tests"]):
        raise RuntimeError("QA_NOT_PASS")
    if j["server_status_before"]!=j["server_status_after"] or j["release_allowed"]:
        raise RuntimeError("LIVE_STATE_CHANGED")
    if "csrf_token" in (HERE/"SCADA_ACCEPTANCE.json").read_text(encoding="utf8"):
        raise RuntimeError("SECRET_LEAK")
    for name,expected in j["production_source_sha256"].items():
        if sha(Path(name))!=expected:raise RuntimeError("PRODUCTION_SOURCE_CHANGED "+name)
    qa={"tests_passed":28,"tests_total":28,"chrome":"PASS","edge":"PASS",
        "blocked_non_get_requests":0,"server_state_unchanged":True,
        "production_sha_unchanged":True,"simulation_class":"D_SYNTHETIC",
        "release_allowed":False}
    save_once(HERE/"QA_RESULT.json",qa)
    evidence={"scope":"isolated_live_SCADA_v09_headless_cascade_whatif_acceptance",
              "server":"localhost:8091","server_pid":j["server_status_before"]["pid"],
              "source_sha256":j["production_source_sha256"],
              "qa":"28/28 PASS Chrome+Edge; pool/DH OFF; pre-onset baseline; poll stability; GET only; backend unchanged",
              "decision":"SCADA_CASCADE_WHATIF_UI_VERIFIED",
              "limits":"Synthetic scenario overlay, no recalculation of DC/HP/TES/REJECT or physical validation",
              "release_allowed":False,
              "next_step":"Model owner to implement energy-balanced Simulink/Stateflow what-if recalculation if full physics needed; keep production GUI unchanged"}
    save_once(HERE/"EVIDENCE.json",evidence)
    for name in FILES:
        if not (HERE/name).is_file():raise RuntimeError("MISSING_ARTIFACT "+name)
    manifest={name:sha(HERE/name) for name in FILES}
    save_once(HERE/"SHA256_MANIFEST.json",manifest)
    payload={"scope":evidence["scope"],"artifact_directory":str(HERE),
             "evidence_sha256":sha(HERE/"EVIDENCE.json"),
             "manifest_sha256":sha(HERE/"SHA256_MANIFEST.json"),
             "qa":evidence["qa"],"decision":evidence["decision"],
             "limits":evidence["limits"],"next_step":evidence["next_step"]}
    with sqlite3.connect(CENTER/"tasks.sqlite3",timeout=6,isolation_level=None) as db:
        db.execute("pragma busy_timeout=6000")
        if db.execute("pragma quick_check").fetchone()[0]!="ok":raise RuntimeError("SQLITE_INTEGRITY")
        db.execute("begin immediate")
        try:
            row=db.execute("select status,stage,worker_pid,owner from tasks where id=?",(TASK,)).fetchone()
            if row!=("review","planned",None,"MATLAB/Stateflow QA"):
                raise RuntimeError("TASK_OWNERSHIP_CHANGED "+repr(row))
            found=db.execute("select id,data_json from task_events where task_id=? and actor=? and kind='evidence'",(TASK,ACTOR)).fetchall()
            if len(found)>1:raise RuntimeError("DUPLICATE_EVENTS")
            if found:
                if json.loads(found[0][1])!=payload:raise RuntimeError("EVENT_CONFLICT")
                event_id,action=found[0][0],"EXISTING_EVENT"
            else:
                event_id=db.execute("insert into task_events(task_id,at,kind,actor,data_json) values(?,?,?,?,?)",
                    (TASK,time.time(),"evidence",ACTOR,json.dumps(payload,ensure_ascii=False))).lastrowid
                action="CREATED_EVENT"
            db.commit()
        except BaseException:
            db.rollback()
            raise
    save_once(HERE/"REGISTRY_RESULT.json",{"task_id":TASK,"event_id":event_id,**payload})
    print(json.dumps({"event_id":event_id,"action":action,
                      "evidence_sha256":payload["evidence_sha256"],
                      "manifest_sha256":payload["manifest_sha256"]},ensure_ascii=False))
if __name__=="__main__":main()
