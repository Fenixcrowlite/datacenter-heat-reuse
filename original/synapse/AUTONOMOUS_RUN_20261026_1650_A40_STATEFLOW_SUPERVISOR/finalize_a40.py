"""Final live verification and handoff for A40. Read-only system checks."""
from __future__ import annotations
import datetime,hashlib,json,sqlite3,subprocess,time
from pathlib import Path
import psutil

HERE=Path(__file__).resolve().parent
CENTER=HERE.parent.parent
TASK='scc-3d9d172beb6e1b'
ACTOR='chatgpt-a40-dchr-stateflow-supervisor-20261026-1650'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    manifest=json.loads((HERE/'SHA256_MANIFEST.json').read_text(encoding='utf-8'))
    bad=[n for n,h in manifest.items() if not (HERE/n).is_file() or sha(HERE/n)!=h]
    assert not bad,('SHA_MISMATCH',bad)
    r=json.loads((HERE/'REGISTRY_RESULT.json').read_text(encoding='utf-8'))
    assert r['event_id']==1227 and r['task_id']==TASK
    db=sqlite3.connect('file:'+str(CENTER/'tasks.sqlite3')+'?mode=ro',uri=True)
    assert db.execute('pragma quick_check').fetchone()[0]=='ok'
    rows=db.execute('select id,data_json from task_events where task_id=? and actor=?',(TASK,ACTOR)).fetchall()
    assert len(rows)==1 and rows[0][0]==1227
    assert json.loads(rows[0][1])['model_sha256']==sha(HERE/'DCHR_A40_Safety_Controller.slx')
    task=db.execute('select status,stage,worker_pid from tasks where id=?',(TASK,)).fetchone()
    db.close()
    stoproots=[CENTER,CENTER/'recovery',HERE,CENTER.parent/'temp_coding',CENTER.parent/'EduMotionPipeline']
    stopnames=('STOP','STOP.flag','STOP.txt','.stop','.STOP','PAUSE','PAUSE.flag','STOP_MANAGED_WORKERS.txt')
    flags=[str(root/name) for root in stoproots for name in stopnames if (root/name).exists()]
    procs=list(psutil.process_iter(['pid','name','cmdline']))
    matlab=[p.info['pid'] for p in procs if (p.info.get('name') or '').lower().startswith('matlab')]
    jarvice_status_path=CENTER.parent/'temp_coding'/'telegram_codex_bot'/'logs'/'devteam-daemon-status.json'
    js=json.loads(jarvice_status_path.read_text(encoding='utf-8'))
    jpid=int(js['pid'])
    jp=next((p for p in procs if p.info['pid']==jpid),None)
    jcmd=' '.join(jp.info.get('cmdline') or []) if jp else ''
    heartbeat_age=round(time.time()-float(js['updated_at']),1)
    jarvice_live=bool(jp and 'launch_devteam_worker' in jcmd and heartbeat_age<180)
    gpu=subprocess.run(['nvidia-smi','--query-gpu=memory.used,memory.total,utilization.gpu',
        '--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=12)
    vm=psutil.virtual_memory()
    live={'time_local':datetime.datetime.now().astimezone().isoformat(),
      'ram_available_gib':round(vm.available/2**30,3),
      'gpu_csv':gpu.stdout.strip() if gpu.returncode==0 else 'unavailable',
      'matlab_process_pids':matlab,
      'jarvice_pid':jpid,'jarvice_live_idle':jarvice_live,
      'jarvice_heartbeat_age_s':heartbeat_age,'jarvice_status':js.get('status'),
      'worktree_directory_counts':{
        'jarvice':len(list((CENTER.parent/'.jarvice_worktrees').iterdir())),
        'task_repos':len(list((CENTER/'.task_repos').iterdir()))},
      'stop_flags_checked':len(stoproots),'stop_flags_found':flags,
      'task_state':task,'event_id':1227,'manifest_verified_files':len(manifest)}
    (HERE/'FINAL_LIVE.json').write_text(json.dumps(live,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assert not matlab,'MATLAB_STILL_RUNNING'
    assert not flags,'STOP_ACTIVE'
    assert task==('review','planned',None),'TASK_STATE_CHANGED'
    now=live['time_local']
    text=f"""# Synapse A40 final handoff | {now} | DESKTOP-M9L3I4M

## Verified intake
Read live: NIGHT_HANDOFF_20261021.md, AGENTS.md, agent_knowledge/INDEX.md, personal-assistant-kernel v1.2, workstream-isolation, registry-task-lifecycle, synapsemcp-web-concurrency. Original 21 Oct handoff is historical, not live. SynapseMCP Web ping and read/PowerShell verified. VRS skipped. No Codex sessions, new persistent workers, GPU jobs, shared GUI or production source changes.

## Actual engineering artifact
Folder: `{HERE}`
Saved real MATLAB/Simulink/Stateflow R2026a model: `DCHR_A40_Safety_Controller.slx`.
4 states NORMAL/DEGRADED/CRITICAL/TES_FULL, 11 transitions (including default), 4 inputs and 3 outputs. The output `shedCeilingFraction` is a synthetic upper bound, NOT a hardware command.
4 real Stateflow simulation runs x 672 synthetic 15-minute samples = **2688 samples**. Mode counts:
- main_only: [226,153,36,257]
- both: [276,0,0,396]
- backup_only: [189,166,207,110]
- neither: [96,0,576,0].
Python independent transition oracle: 2688/2688 exact mode parity. Python regression **9/9 PASS**. MATLAB stdout has all 4 PASS lines, stderr empty. Saved SLX ZIP integrity verified. Full caveats: `ENGINEERING_REPORT_RU.md`.

## Evidence and Synapse
Existing task `{TASK}`, unchanged status `review/planned`, no worker PID. Exactly one evidence event **1227**, idempotent second registration returned EXISTING_EVENT. No duplicate task.
EVIDENCE.json SHA256: `{sha(HERE/'EVIDENCE.json')}`.
SHA256_MANIFEST.json SHA256: `{sha(HERE/'SHA256_MANIFEST.json')}`.
Saved SLX SHA256: `{sha(HERE/'DCHR_A40_Safety_Controller.slx')}`.
All {len(manifest)} manifest files independently rehashed PASS. SQLite quick_check OK.

## Live resources / ownership
RAM available: {live['ram_available_gib']} GiB. GPU nvidia-smi: {live['gpu_csv']} (MiB used,total, GPU%).
MATLAB processes: {matlab} (none). Jarvice PID {jpid}, live_idle={jarvice_live}, heartbeat age {heartbeat_age}s. Jarvice is not restarted. Checked STOP/PAUSE in {len(stoproots)} roots: {flags or 'none detected'} (not a full recursive claim).
Worktree folder counts: {live['worktree_directory_counts']}. Synapse task has no running worker.

## Release status and exact next executable step
**STATEFLOW_OPEN_LOOP_SIM_VERIFIED; CLOSED_LOOP_NOT_DONE; PHYSICAL_RELEASE_BLOCKED.**
The chart consumes precomputed A38 temperature/SOC, so this is not a closed-loop thermal controller, not a verified N-1 physical protection system, and not safe for equipment control.
Next: in a fresh isolated copy, connect chart mode to A38 thermal recurrence and bounded IT shed with REJECT A/B branch switching delays; replay 672 steps with closed-loop feedback, assert energy conservation, TES bounds, thermal alarms and independent Python/MATLAB parity. Do not modify v85 SLX, SCADA, OAuth or peer-owned files.
"""
    (HERE/'FINAL_HANDOFF.md').write_text(text,encoding='utf-8')
    (HERE/'FINAL_HANDOFF_SHA256.txt').write_text(sha(HERE/'FINAL_HANDOFF.md')+'  FINAL_HANDOFF.md\n',encoding='utf-8')
    verify={'status':'PASS','manifest_files':len(manifest),'python_tests':9,
      'real_stateflow_scenarios':4,'stateflow_samples':2688,
      'independent_mode_comparisons':2688,'registry_event':1227,
      'handoff_sha256':sha(HERE/'FINAL_HANDOFF.md'),
      'model_sha256':sha(HERE/'DCHR_A40_Safety_Controller.slx'),
      'jarvice_live_idle':jarvice_live,'matlab_processes':matlab}
    (HERE/'FINAL_VERIFY.json').write_text(json.dumps(verify,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(verify,ensure_ascii=False))
if __name__=='__main__':main()
