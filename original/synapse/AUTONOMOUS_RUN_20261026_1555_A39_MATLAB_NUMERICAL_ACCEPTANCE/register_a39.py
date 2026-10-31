"""Idempotent evidence event for verified A39 MATLAB numerical replay; existing card only."""
from pathlib import Path
import hashlib,json,sqlite3,time,datetime
HERE=Path(__file__).resolve().parent
CENTER=HERE.parent.parent
TASK='scc-3d9d172beb6e1b'
ACTOR='chatgpt-a39-dchr-matlab-acceptance-20261026-1555'
FILES=['preflight_a39.py','PREFLIGHT.json','run_a39.m','MATLAB_RESULT.json',
       'MATLAB_STDOUT.txt','MATLAB_STDERR.txt','MATLAB_PID.txt','test_a39.py','TEST_LOG.txt']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save_once(p,content):
 if p.exists():
  if p.read_text(encoding='utf8')!=content:raise RuntimeError('EXISTING_CONFLICT '+str(p))
 else:p.write_text(content,encoding='utf8')
def main():
 for root in (CENTER,CENTER/'recovery',HERE):
  for n in ('STOP','STOP.flag','STOP.txt','.stop','.STOP','PAUSE','PAUSE.flag','STOP_MANAGED_WORKERS.txt'):
   if (root/n).exists():raise RuntimeError('STOP_ACTIVE '+str(root/n))
 r=json.loads((HERE/'MATLAB_RESULT.json').read_text(encoding='utf8'))
 p=json.loads((HERE/'PREFLIGHT.json').read_text(encoding='utf8'))
 tests=(HERE/'TEST_LOG.txt').read_text(encoding='utf-8-sig')
 assert 'Ran 10 tests' in tests and tests.rstrip().endswith('OK'),'QA_NOT_PASS'
 assert r['status']=='MATLAB_NUMERICAL_ACCEPTANCE_PASS'
 assert (r['cases'],r['samples_per_case'],r['comparisons'])==(12,672,80640)
 assert 0<=r['max_error']<1e-6
 assert r['stateflow_executed'] is False and r['physical_release_allowed'] is False
 assert 'A39_MATLAB_NUMERICAL_PASS' in (HERE/'MATLAB_STDOUT.txt').read_text(encoding='utf8')
 assert (HERE/'MATLAB_STDERR.txt').stat().st_size==0
 for name in FILES:
  if not (HERE/name).is_file():raise RuntimeError('MISSING '+name)
 evidence={'scope':'isolated_A39_real_MATLAB_R2026a_12x672_numerical_acceptance',
           'status':'VERIFIED_MATLAB_NUMERICAL_ONLY',
           'matlab_comparisons':80640,'max_abs_difference':r['max_error'],
           'python_regression':'10/10 PASS',
           'source_a38_step_sha256':p['a38_step_sha256'],
           'source_a38_acceptance_sha256':p['a38_acceptance_sha256'],
           'source_v08_sha256':p['source_v08_sha256'],
           'source_a36_sha256':p['source_a36_sha256'],
           'matlab_result_sha256':sha(HERE/'MATLAB_RESULT.json'),
           'stdout_sha256':sha(HERE/'MATLAB_STDOUT.txt'),
           'matlab_pid_from_launch_file':int((HERE/'MATLAB_PID.txt').read_text(encoding='utf8')),
           'result_file_mtime_utc':datetime.datetime.fromtimestamp((HERE/'MATLAB_RESULT.json').stat().st_mtime,datetime.timezone.utc).isoformat(),
           'note':'MATLAB output executed_at string has *** timezone-format placeholder; use file mtime; mathematical results validated independently',
           'stateflow_executed':False,'physical_release_allowed':False,
           'next_step':'Build isolated Stateflow controller with TES SOC, REJECT A/B N-1 and IT shedding, test transition guards and 672-step parity; no hardware release'}
 save_once(HERE/'EVIDENCE.json',json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
 manifest={name:sha(HERE/name) for name in FILES+['EVIDENCE.json']}
 save_once(HERE/'SHA256_MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 payload={'scope':evidence['scope'],'artifact_directory':str(HERE),
          'evidence_sha256':sha(HERE/'EVIDENCE.json'),
          'manifest_sha256':sha(HERE/'SHA256_MANIFEST.json'),
          'matlab_result_sha256':evidence['matlab_result_sha256'],
          'qa':'MATLAB R2026a 80640 comparisons PASS max error 2.91e-11; Python 10/10 PASS',
          'status':'MATLAB_NUMERICAL_ACCEPTED_STATEFLOW_NOT_EXECUTED',
          'release_status':'PHYSICAL_RELEASE_BLOCKED',
          'next_step':evidence['next_step']}
 db=sqlite3.connect(CENTER/'tasks.sqlite3',timeout=8,isolation_level=None)
 db.execute('pragma busy_timeout=8000')
 assert db.execute('pragma quick_check').fetchone()[0]=='ok'
 db.execute('begin immediate')
 try:
  state=db.execute('select status,stage,worker_pid,owner from tasks where id=?',(TASK,)).fetchone()
  assert state==('review','planned',None,'MATLAB/Stateflow QA'),('TASK_CHANGED',state)
  rows=db.execute('select id,data_json from task_events where task_id=? and actor=? and kind=?',(TASK,ACTOR,'evidence')).fetchall()
  if len(rows)>1:raise RuntimeError('DUPLICATE_EVENTS')
  if rows:
   assert json.loads(rows[0][1])==payload,'EVENT_CONFLICT'
   event,action=rows[0][0],'EXISTING_EVENT'
  else:
   event=db.execute('insert into task_events(task_id,at,kind,actor,data_json) values(?,?,?,?,?)',
       (TASK,time.time(),'evidence',ACTOR,json.dumps(payload,ensure_ascii=False))).lastrowid
   action='CREATED_EVENT'
  db.commit()
 except BaseException:
  db.rollback();raise
 finally:db.close()
 result={'action':action,'task_id':TASK,'event_id':event,**payload}
 result_path=HERE/'REGISTRY_RESULT.json'
 if result_path.exists():
  old=json.loads(result_path.read_text(encoding='utf8'))
  assert {k:v for k,v in old.items() if k!='action'}=={k:v for k,v in result.items() if k!='action'},'REGISTRY_RESULT_CONFLICT'
 else:
  save_once(result_path,json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'action':action,'task_id':TASK,'event_id':event,
                   'manifest_sha256':payload['manifest_sha256'],
                   'evidence_sha256':payload['evidence_sha256']},indent=2))
if __name__=='__main__':main()
