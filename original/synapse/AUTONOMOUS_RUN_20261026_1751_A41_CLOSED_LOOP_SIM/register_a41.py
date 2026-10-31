"""Idempotent evidence append to existing DataCenter Synapse task. No worker launch."""
from __future__ import annotations
import hashlib,json,sqlite3,time,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
CENTER=HERE.parent.parent
TASK="scc-3d9d172beb6e1b"
ACTOR="chatgpt-a41-dchr-closed-loop-20261026-1751"
BASE=["closed_loop_a41.py","build_a41.m","verify_a41.py","delay_sweep_a41.py",
"INPUTS_A41.csv","PYTHON_RESULT.json","PYTHON_STDOUT.txt","PYTHON_STDERR.txt",
"MATLAB_RESULT.json","MATLAB_STDOUT.txt","MATLAB_STDERR.txt","MATLAB_ATTEMPT1_STDERR.txt",
"DCHR_A41_Closed_Loop.slx","DELAY_SWEEP.json","DELAY_SWEEP_STDOUT.txt",
"DELAY_SWEEP_STDERR.txt","QA_STDERR.txt","QA_STDOUT.txt","ENGINEERING_REPORT_RU.md"]
FILES=BASE+["TRACE_A41_"+s+".csv" for s in ("both","main_only","backup_only","neither")]+[
"MATLAB_TRACE_"+s+".csv" for s in ("both","main_only","backup_only","neither")]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save_once(p,data):
    if p.exists():assert p.read_text(encoding="utf8")==data,("EXISTING_CONFLICT",p)
    else:p.write_text(data,encoding="utf8")
def main():
    for root in (CENTER,CENTER/"recovery",HERE):
        for name in ("STOP","STOP.flag","PAUSE","PAUSE.flag",".STOP","STOP_MANAGED_WORKERS.txt"):
            assert not (root/name).exists(),("STOP_ACTIVE",root,name)
    for n in FILES+["register_a41.py"]:
        assert (HERE/n).is_file(),("MISSING",n)
    assert (HERE/"MATLAB_STDERR.txt").stat().st_size==0
    assert (HERE/"PYTHON_STDERR.txt").stat().st_size==0
    assert (HERE/"DELAY_SWEEP_STDERR.txt").stat().st_size==0
    qa=(HERE/"QA_STDERR.txt").read_text(encoding="utf-16")
    assert "Ran 15 tests" in qa and qa.rstrip().endswith("OK"),"QA_FAILED"
    matlab=(HERE/"MATLAB_STDOUT.txt").read_text(encoding="utf-8-sig")
    assert "A41_ALL_SCENARIOS_PASS" in matlab
    for s in ("both","main_only","backup_only","neither"):
        assert "A41_CLOSED_LOOP_PASS "+s in matlab
    result=json.loads((HERE/"MATLAB_RESULT.json").read_text(encoding="utf8"))
    assert result["status"]=="STATEFLOW_CLOSED_LOOP_SIM_PASS"
    assert result["physical_release"] is False
    assert len(result["scenarios"])==4
    assert all(x["samples"]==672 and x["parity"]=="PASS" for x in result["scenarios"].values())
    with zipfile.ZipFile(HERE/"DCHR_A41_Closed_Loop.slx") as z:
        assert z.testzip() is None
        xml=z.read("simulink/systems/system_root.xml")
        assert b"TemperatureMemory" in xml and b"TESMemory" in xml
    sweep=json.loads((HERE/"DELAY_SWEEP.json").read_text(encoding="utf8"))["delay_steps"]
    assert sweep["0"]["max_temperature_C"]<42<sweep["1"]["max_temperature_C"]
    evidence=dict(scope="A41_isolated_synthetic_Simulink_Stateflow_TES_IT_feedback",
      status="STATEFLOW_CLOSED_LOOP_SYNTHETIC_VERIFIED",
      physical_release_allowed=False,matlab="R2026a",scenario_count=4,
      samples_per_scenario=672,matlab_python_numeric_comparisons=26880,
      independent_python_tests="15/15 PASS",delay_sensitivity_cases=5,
      model_sha256=sha(HERE/"DCHR_A41_Closed_Loop.slx"),
      matlab_result_sha256=sha(HERE/"MATLAB_RESULT.json"),
      report_sha256=sha(HERE/"ENGINEERING_REPORT_RU.md"),
      source_a38_sha256=sha(HERE.parent/"AUTONOMOUS_RUN_20261026_1054_A38_TES_N1_INTEGRATION"/"integrated_a38.py"),
      source_a40_sha256=sha(HERE.parent/"AUTONOMOUS_RUN_20261026_1650_A40_STATEFLOW_SUPERVISOR"/"DCHR_A40_Safety_Controller.slx"),
      caveat="Closed loop for TES energy, IT temperature and shed memory only; other A36/HP/IT branches remain synthetic feedforward; no physical certification",
      next_step="A42 isolate fully coupled IT/HP/TES plant, fail-safe IT shutdown under REJECT total loss, sensor delay and heat capacity sweep, then physical parameter validation")
    save_once(HERE/"EVIDENCE.json",json.dumps(evidence,ensure_ascii=False,indent=2)+"\n")
    manifest={n:sha(HERE/n) for n in FILES+["register_a41.py","EVIDENCE.json"]}
    save_once(HERE/"SHA256_MANIFEST.json",json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    payload=dict(scope=evidence["scope"],artifact_directory=str(HERE),
      evidence_sha256=sha(HERE/"EVIDENCE.json"),manifest_sha256=sha(HERE/"SHA256_MANIFEST.json"),
      model_sha256=evidence["model_sha256"],qa="MATLAB/Stateflow 4x672 PASS; Python 15/15 PASS; 26880 numeric comparisons; 5 delay sensitivities",
      status=evidence["status"],release_status="PHYSICAL_RELEASE_BLOCKED",
      next_step=evidence["next_step"])
    db=sqlite3.connect(CENTER/"tasks.sqlite3",timeout=8,isolation_level=None)
    db.execute("pragma busy_timeout=8000")
    assert db.execute("pragma quick_check").fetchone()[0]=="ok"
    db.execute("begin immediate")
    try:
        state=db.execute("select status,stage,worker_pid,owner from tasks where id=?",(TASK,)).fetchone()
        assert state==("review","planned",None,"MATLAB/Stateflow QA"),("TASK_OWNERSHIP_CHANGED",state)
        rows=db.execute("select id,data_json from task_events where task_id=? and actor=? and kind=?",
            (TASK,ACTOR,"evidence")).fetchall()
        assert len(rows)<=1
        if rows:
            assert json.loads(rows[0][1])==payload,"EVENT_CONFLICT"
            eid,action=rows[0][0],"EXISTING_EVENT"
        else:
            eid=db.execute("insert into task_events(task_id,at,kind,actor,data_json) values(?,?,?,?,?)",
                (TASK,time.time(),"evidence",ACTOR,json.dumps(payload,ensure_ascii=False))).lastrowid
            action="CREATED_EVENT"
        db.commit()
    except BaseException:
        db.rollback();raise
    finally:db.close()
    receipt=dict(action=action,event_id=eid,task_id=TASK,**payload)
    path=HERE/"REGISTRY_RESULT.json"
    if path.exists():
        old=json.loads(path.read_text(encoding="utf8"))
        assert {k:v for k,v in old.items() if k!="action"}=={k:v for k,v in receipt.items() if k!="action"}
    else:
        save_once(path,json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(dict(action=action,event_id=eid,task_id=TASK,
        evidence_sha256=payload["evidence_sha256"],model_sha256=payload["model_sha256"])))
if __name__=="__main__":main()
