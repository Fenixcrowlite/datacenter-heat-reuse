import sqlite3,json
db=sqlite3.connect(r"C:\Users\Lysda\Desktop\SynapseControlCenter\tasks.sqlite3")
print("TABLES",db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
for table in ["tasks","events","task_events"]:
 try:
  cols=[x[1] for x in db.execute("PRAGMA table_info("+table+")")]
  print("SCHEMA",table,cols)
  if table=="tasks":
   for row in db.execute("SELECT * FROM tasks WHERE id IN (?,?)",("scc-3d9d172beb6e1b","scc-d941595119d699")):print("TASK",dict(zip(cols,row)))
 except Exception as e: print("ERR",str(e))
