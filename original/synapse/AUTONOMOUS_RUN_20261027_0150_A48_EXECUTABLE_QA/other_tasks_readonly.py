import sqlite3,json,datetime
c=sqlite3.connect('file:C:/Users/Lysda/Desktop/SynapseControlCenter/tasks.sqlite3?mode=ro',uri=True)
for task in ('scc-d941595119d699','scc-71049230e9c567'):
 print('TASK',c.execute('SELECT id,status,stage,owner,worker_pid FROM tasks WHERE id=?',(task,)).fetchone())
 for eid,at,kind,actor in c.execute('SELECT id,at,kind,actor FROM task_events WHERE task_id=? ORDER BY id DESC LIMIT 5',(task,)):
  print(eid,datetime.datetime.fromtimestamp(at).isoformat(),kind,actor)
