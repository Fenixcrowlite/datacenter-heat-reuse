import sqlite3,json,sys
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
p=r'C:\Users\Lysda\Desktop\SynapseControlCenter\tasks.sqlite3'
c=sqlite3.connect('file:'+p.replace('\\','/')+'?mode=ro',uri=True)
for (name,) in c.execute("SELECT name FROM sqlite_master WHERE type='table'"):
 print('TABLE',name)
 if name=='tasks':
  print('TARGET',c.execute("SELECT id,title,status,owner,updated FROM tasks WHERE id IN ('scc-3d9d172beb6e1b','scc-d941595119d699','scc-71049230e9c567')").fetchall())
 elif name!='sqlite_sequence':
  print('COLUMNS',[row[1] for row in c.execute('PRAGMA table_info('+name+')')])
