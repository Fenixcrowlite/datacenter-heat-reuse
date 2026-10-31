from pathlib import Path
import hashlib,json,sqlite3
root=Path(r'C:\Users\Lysda\Desktop\SynapseControlCenter')
a=root/'recovery'/'AUTONOMOUS_RUN_20261027_0554_A53_GRAPHICAL_CROSSPRODUCT'
b=root/'recovery'/'AUTONOMOUS_RUN_20261027_0600_A53B_JARVICE_WORKTREE_FORENSICS'
for d,filename in [(a,'SHA256_MANIFEST_A53.json'),(b,'SHA256_MANIFEST_A53B.json')]:
 m=json.loads((d/filename).read_text(encoding='utf-8-sig'))
 mismatches=[k for k,v in m.items() if hashlib.sha256((d/k).read_bytes()).hexdigest()!=v]
 print('MANIFEST',d.name,len(m),'PASS' if not mismatches else mismatches)
 assert not mismatches
 db=sqlite3.connect(root/'tasks.sqlite3')
for id,actor in [('scc-3d9d172beb6e1b','chatgpt-a53-graphical-crossproduct-20261027-0554'),('scc-d941595119d699','chatgpt-a53b-jarvice-worktree-attribution-20261027-0600')]:
 rows=db.execute("select id from task_events where task_id=? and actor=? and kind='evidence'",(id,actor)).fetchall()
 print('EVENT',id,rows)
 assert len(rows)==1
print('DB',db.execute('pragma quick_check').fetchone()[0])
