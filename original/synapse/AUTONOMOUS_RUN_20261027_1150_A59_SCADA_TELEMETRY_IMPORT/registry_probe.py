import sqlite3, json
from pathlib import Path
db = sqlite3.connect("file:C:/Users/Lysda/Desktop/SynapseControlCenter/tasks.sqlite3?mode=ro", uri=True)
db.row_factory = sqlite3.Row
for task_id in ("scc-3d9d172beb6e1b", "scc-d941595119d699"):
    task = db.execute("SELECT id,project,status,stage,worker_pid,title,request_id FROM tasks WHERE id=?", (task_id,)).fetchone()
    print("TASK", dict(task) if task else None)
    for ev in db.execute("SELECT id,kind,actor,substr(data_json,1,180) AS snippet FROM task_events WHERE task_id=? ORDER BY id DESC LIMIT 3", (task_id,)):
        print("EVENT", dict(ev))
print("INTEGRITY", db.execute("PRAGMA quick_check").fetchone()[0])
