"""Copy new v12 evidence to Obsidian without overwriting conflicts."""
from pathlib import Path
from hashlib import sha256
import json, shutil
root=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")
vault=Path(r"C:\Users\Lysda\Documents\Bimba\02_PROJECTS\02_Automation\DataCenter_Heat_Reuse")
files=["STATUS_v12.json","MASTER_STAGEBOARD_v12.md",
       "audit/test_component_contract_v12.py","audit/component_contract_reference_tests_v12.json",
       "audit/Component_contract_audit_v12_RU.md","matlab/run_component_contract_v12.m"]
assert root.is_dir() and vault.is_dir()
manifest=[]
for rel in files:
    source=root/rel
    target=vault/rel
    assert source.is_file(), str(source)
    h=sha256(source.read_bytes()).hexdigest()
    if target.exists():
        action="already_identical" if sha256(target.read_bytes()).hexdigest()==h else "CONFLICT_NOT_OVERWRITTEN"
    else:
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target)
        action="copied"
    same=target.is_file() and sha256(target.read_bytes()).hexdigest()==h
    manifest.append({"file":rel,"action":action,"sha256":h,"verified_identical":same})
out=root/"integration/obsidian_v12_copy_manifest.json"
if out.exists(): raise FileExistsError(str(out))
out.write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
print(json.dumps({"copied":sum(x["action"]=="copied" for x in manifest),
 "identical":sum(x["verified_identical"] for x in manifest),
 "conflicts":[x["file"] for x in manifest if not x["verified_identical"]]},ensure_ascii=False))
