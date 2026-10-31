"""Record active hourly research automation in project state and Obsidian."""
from pathlib import Path
import json,hashlib,shutil
from datetime import datetime,timezone
root=Path(__file__).resolve().parents[1]
d=json.loads((root/"STATUS_v08.json").read_text(encoding="utf8"))
d["version"]="0.9"; d["updated_utc"]=datetime.now(timezone.utc).isoformat()
d["automatic_progress_task"]={"state":"ACTIVE","title":"DataCenter Heat Reuse: этапы",
  "schedule":"Hourly condition watch","task_id":"6ac577fb64b081918f271322566b3e24",
  "notes":"Runs are discrete, not continuous live execution; only verified milestones trigger reports"}
(root/"STATUS_v09.json").write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf8")
(root/"MASTER_STAGEBOARD_v09.md").write_text((root/"MASTER_STAGEBOARD_v08.md").read_text(encoding="utf8")+
 "\n\n## Automation v0.9 — ACTIVE\n"
 "- Старый истёкший PC Overnight Run переведён в hourly condition-watch DataCenter Heat Reuse: этапы.\n"
 "- ID 6ac577fb64b081918f271322566b3e24. Прогресс только по воспроизводимым файлам и тестам, без заявлений о непрерывном background runtime.\n"
 "- Источник истины последнего состояния STATUS_v09.json.\n",encoding="utf8")
obs=Path(r"C:\Users\Lysda\Documents\Bimba\02_PROJECTS\02_Automation\DataCenter_Heat_Reuse")
results=[]
for n in ("STATUS_v09.json","MASTER_STAGEBOARD_v09.md"):
 a=root/n;b=obs/n;b.parent.mkdir(parents=True,exist_ok=True)
 ha=hashlib.sha256(a.read_bytes()).hexdigest()
 if b.exists():state="IDENTICAL" if hashlib.sha256(b.read_bytes()).hexdigest()==ha else "CONFLICT"
 else:
  shutil.copy2(a,b);state="COPIED" if hashlib.sha256(b.read_bytes()).hexdigest()==ha else "BAD_HASH"
 results.append((n,state))
print(json.dumps(results))
