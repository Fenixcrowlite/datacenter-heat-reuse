import sqlite3,json
db=sqlite3.connect(r"C:\Users\Lysda\Desktop\SynapseControlCenter\tasks.sqlite3")
for tid in ("scc-3d9d172beb6e1b","scc-d941595119d699","scc-6b29ef30f68013"):
 rows=db.execute("select id,kind,actor,at from task_events where task_id=? order by id desc limit 4",(tid,)).fetchall()
 print(tid,rows)
print("EVENT1253",db.execute("select count(*) from task_events where id=1253").fetchone()[0])
