from pathlib import Path
from hashlib import sha256
import shutil,json
d=Path(__file__).resolve().parent
vault=Path(r"C:\Users\Lysda\Documents\Bimba\02_PROJECTS\02_Automation\DataCenter_Heat_Reuse\calibration\equipment_selection_20261023")
a=d/"Equipment_Selection_SK.md"
b=vault/"Equipment_Selection_SK_20261023_v02.md"
assert a.is_file() and vault.is_dir()
if b.exists():
 assert sha256(a.read_bytes()).hexdigest()==sha256(b.read_bytes()).hexdigest(), "Version name conflict: did not overwrite"
 status="already identical"
else:
 shutil.copy2(a,b)
 status="copied alternative filename"
assert sha256(a.read_bytes()).hexdigest()==sha256(b.read_bytes()).hexdigest()
hub=vault/"00_Vyber_zariadeni_20261023.md"
h=hub.read_text(encoding="utf-8")
h=h.replace("[[Equipment_Selection_SK]] a [[Equipment_Selection_SK_v02.pdf]]",
 "[[Equipment_Selection_SK_20261023_v02]] a [[Equipment_Selection_SK_v02.pdf]]")
h+="\nPoznamka: sucasny `Equipment_Selection_SK.md` bol upraveny paralelnym pracovnym tokom a **NEBOL PREPISANY**. Aktualna kopia je `Equipment_Selection_SK_20261023_v02.md`.\n"
hub.write_text(h,encoding="utf-8")
out={"verified":True,"status":status,"preserved_parallel_Obsidian_path":str(vault/"Equipment_Selection_SK.md"),"copy":str(b),"sha256":sha256(b.read_bytes()).hexdigest()}
target=d/"obsidian_conflict_resolution_20261023.json"
if target.exists():raise FileExistsError(str(target))
target.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print("OBSIDIAN_OWNERSHIP_CONFLICT_RESOLVED",json.dumps(out,ensure_ascii=False))
