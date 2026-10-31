"""Fail-closed, idempotent registry receipt for verified A48 executable."""
from pathlib import Path
import hashlib,json,sqlite3,subprocess,sys,time
D=Path(__file__).resolve().parent
CENTER=D.parent.parent
TASK='scc-3d9d172beb6e1b'
ACTOR='chatgpt-a48-graphical-executable-acceptance-20261027'
PY=sys.executable
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,s):
 if p.exists():
  if p.read_text(encoding='utf-8-sig')!=s:raise RuntimeError('ARTIFACT_CONFLICT '+str(p))
 else:p.write_text(s,encoding='utf-8')
def main():
 for root in [CENTER,CENTER/'recovery',D,Path(r'C:\Users\Lysda\Desktop\temp_coding'),Path(r'C:\Users\Lysda\Desktop\EduMotionPipeline')]:
  for name in ('STOP','STOP.flag','PAUSE','PAUSE.flag','.STOP','.PAUSE','devteam-daemon.stop'):
   if (root/name).exists():raise RuntimeError('STOP_ACTIVE '+str(root/name))
 test=subprocess.run([PY,'-B',str(D/'verify_a48_executable.py')],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30)
 if test.returncode or 'Ran 10 tests' not in test.stderr or '\nOK' not in test.stderr:raise RuntimeError('QA_FAILED '+test.stderr)
 result=json.loads((D/'SIMULINK_A48_RESULT.json').read_text(encoding='utf-8-sig'))
 if result['status']!='A48_GRAPHICAL_COUPLED_PARITY_PASS' or result['numeric_comparisons']!=51744 or result['samples']!=4704 or result['physical_release']:raise RuntimeError('RESULT_GATE_FAILED')
 if not (D/'DCHR_A48_Graphical_Closed_Loop.slx').exists():raise RuntimeError('MISSING_MODEL')
 evidence={'task_id':TASK,'status':'A48_GRAPHICAL_STATEFLOW_COUPLED_EXECUTABLE_VERIFIED',
  'artifact_dir':str(D),'matlab_version':'R2026a','model_sha256':sha(D/'DCHR_A48_Graphical_Closed_Loop.slx'),
  'matlab_result_sha256':sha(D/'SIMULINK_A48_RESULT.json'),
  'source_builder_sha256':sha(D/'build_a48.m'),
  'matlab_scenarios':7,'intervals_per_scenario':672,'numeric_comparisons':51744,
  'state_parity_exact':True,'independent_python_tests':'10/10 PASS',
  'real_graphical_stateflow_chart':True,'coupled_compressor_plant':True,
  'synthetic_inputs':True,'physical_release':False,
  'limitations':'Synthetic A45 reference; no independent field measurements, 31 primary-source signoffs remain open; not a hardware safety controller.',
  'next_step':'A49: independent fault-injection/property-based validation of transitions, sensor latency and energy balances against a separately derived model; retain physical signoff gate.'}
 put(D/'EVIDENCE_A48_EXEC.json',json.dumps(evidence,indent=2,ensure_ascii=False)+'\n')
 files=['build_a48.m','DCHR_A48_Graphical_Closed_Loop.slx','SIMULINK_A48_RESULT.json','MATLAB_STDOUT.txt','MATLAB_STDERR.txt','verify_a48_executable.py','EVIDENCE_A48_EXEC.json']
 manifest={name:sha(D/name) for name in files}
 put(D/'SHA256_MANIFEST_A48_EXEC.json',json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
 handoff=(f'# A48 executable checkpoint | 2026-10-27 01:53 CET\n'
 f'Task: {TASK}, status review/planned, no worker claim.\n'
 f'Executable model: {D / "DCHR_A48_Graphical_Closed_Loop.slx"}\n'
 f'MATLAB R2026a headless run: 7/7 scenarios, 672 steps each, 51744/51744 comparisons with A45 Python reference.\n'
 f'Independent Python QA: 10/10 PASS; SLX ZIP verified, actual Stateflow graphical chart has ACTIVE/TRIP_PENDING/TRIPPED/RAMPING; 0 FSM mismatches.\n'
 f'Build SHA256: {sha(D/"build_a48.m")}\n'
 f'Model SHA256: {sha(D/"DCHR_A48_Graphical_Closed_Loop.slx")}\n'
 f'Result SHA256: {sha(D/"SIMULINK_A48_RESULT.json")}\n'
 f'Evidence SHA256: {sha(D/"EVIDENCE_A48_EXEC.json")}\n'
 f'Manifest SHA256: {sha(D/"SHA256_MANIFEST_A48_EXEC.json")}\n'
 f'No Codex, new permanent worker, GUI/OAuth/STOP change, physical equipment or VRS. Original A44/A46 SLX hashes verified unchanged.\n'
 f'Physical validation and 31 primary-source signoffs BLOCKED. Next: {evidence["next_step"]}\n')
 put(D/'FINAL_HANDOFF_A48_EXEC.md',handoff)
 payload={'scope':'A48_graphical_coupled_executable_acceptance',
  'artifact_directory':str(D),'model_sha256':evidence['model_sha256'],
  'evidence_sha256':sha(D/'EVIDENCE_A48_EXEC.json'),
  'manifest_sha256':sha(D/'SHA256_MANIFEST_A48_EXEC.json'),
  'handoff_sha256':sha(D/'FINAL_HANDOFF_A48_EXEC.md'),
  'qa':'MATLAB R2026a 7x672, 51744/51744 numerical parity; 10/10 independent Python tests; graphical Stateflow verified',
  'physical_release':False,'next_step':evidence['next_step']}
 db=sqlite3.connect(CENTER/'tasks.sqlite3',timeout=10,isolation_level=None)
 db.execute('PRAGMA busy_timeout=10000')
 if db.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise RuntimeError('DB_INTEGRITY')
 db.execute('BEGIN IMMEDIATE')
 try:
  row=db.execute('SELECT status,stage,worker_pid FROM tasks WHERE id=?',(TASK,)).fetchone()
  if row!=('review','planned',None):raise RuntimeError('OWNERSHIP_CHANGED '+repr(row))
  prior=db.execute('SELECT id,data_json FROM task_events WHERE task_id=? AND actor=? AND kind=?',(TASK,ACTOR,'evidence')).fetchall()
  if len(prior)>1:raise RuntimeError('DUPLICATE_EVENT')
  if prior:
   if json.loads(prior[0][1])!=payload:raise RuntimeError('EVENT_CONFLICT')
   eid=prior[0][0]
  else:
   eid=db.execute('INSERT INTO task_events(task_id,at,kind,actor,data_json) VALUES(?,?,?,?,?)',(TASK,time.time(),'evidence',ACTOR,json.dumps(payload,ensure_ascii=False))).lastrowid
  db.commit()
 except BaseException:db.rollback();raise
 finally:db.close()
 put(D/'REGISTRY_RESULT_A48_EXEC.json',json.dumps({'event_id':eid,'task_id':TASK,**payload},indent=2,ensure_ascii=False)+'\n')
 print(json.dumps({'event_id':eid,'model_sha256':payload['model_sha256'],'evidence_sha256':payload['evidence_sha256'],'handoff_sha256':payload['handoff_sha256'],'tests':'10/10','comparisons':51744},ensure_ascii=False))
if __name__=='__main__':main()
