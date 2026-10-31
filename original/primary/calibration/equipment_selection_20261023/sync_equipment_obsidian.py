# -*- coding: utf-8 -*-
"""Owner scoped safe Obsidian sync with per-file SHA256 verification."""
from pathlib import Path
from hashlib import sha256
import json,shutil
root=Path(__file__).resolve().parent
vault=Path(r"C:\Users\Lysda\Documents\Bimba\02_PROJECTS\02_Automation\DataCenter_Heat_Reuse")
assert vault.is_dir(),"Obsidian vault unavailable"
dest=vault/"calibration"/"equipment_selection_20261023"
dest.mkdir(parents=True,exist_ok=True)
files=[
 "Equipment_Selection_SK.md","Equipment_Selection_RU.md","Equipment_Selection_EN.md",
 "Equipment_Selection_SK_v02.pdf","Equipment_Selection_RU_v02.pdf","Equipment_Selection_EN_v02.pdf",
 "Module_capacity_tradeoff_SK.md","Module_capacity_tradeoff_SK.pdf",
 "equipment_configurator.html",
 "equipment_selection_default.json",
 "HX_low_grade_heat_default.csv","CAPEX_pool_cases_default.csv",
 "screen_equipment_options.py","optimize_module_capacity.py",
 "network_module_2MW_Nplus1_screen.csv","network_module_2MW_Nplus1_screen.json",
 "equipment_v02_qa.json"]
records=[]
for fn in files:
 a=root/fn;b=dest/fn
 assert a.is_file(),f"Missing source {fn}"
 expected=sha256(a.read_bytes()).hexdigest()
 if b.exists():
  status="ALREADY_IDENTICAL" if sha256(b.read_bytes()).hexdigest()==expected else "CONFLICT_NO_OVERWRITE"
 else:
  shutil.copy2(a,b);status="COPIED"
 same=b.is_file() and sha256(b.read_bytes()).hexdigest()==expected
 records.append({"file":fn,"status":status,"verified_identical":same,"sha256":expected})
hub=dest/"00_Vyber_zariadeni_20261023.md"
txt=r"""---
date: 2026-10-23
tags: [datacentrum, bazen, teplovodna-siet, vyber-zariadeni, financie]
status: VERIFIED_SCREENING_NOT_PRODUCT_APPROVED
---
# DataCenter → bazén: výber zariadení

Aktualizované správy 23.10.2026 (v02 po kapacitnej optimalizácii):

- [[Equipment_Selection_SK]] a [[Equipment_Selection_SK_v02.pdf]]
- [[Equipment_Selection_RU]] a [[Equipment_Selection_RU_v02.pdf]]
- [[Equipment_Selection_EN]] a [[Equipment_Selection_EN_v02.pdf]]
- [[Module_capacity_tradeoff_SK]] a [[Module_capacity_tradeoff_SK.pdf]]
- [[equipment_configurator.html]] - interaktívny kalkulátor tepla, plochy, COP a NPV
- [[equipment_selection_default.json]] - výpočty materiálov a plôch
- [[HX_low_grade_heat_default.csv]] - plochy HX pri 25-45 C
- [[CAPEX_pool_cases_default.csv]] - scenáre investície
- [[network_module_2MW_Nplus1_screen.csv]] - kapacitná optimalizácia
- `screen_equipment_options.py` a `optimize_module_capacity.py` - reprodukovateľné skripty

**Rozhodnutie:** 35 C priamy bazénový výmenník, pokiaľ výrobca certifikuje 150 kW pri 35/32 a 27.5/29.5 C. TČ pre sieť pri simulovanom profile predbežne 5x2 MW pracovné + 1x2 MW záložné, vyžaduje konkrétny výber COP a výkonov výrobcom.

**UPOZORNENIE:** 200 kW Pahlén sa uvádza pri cca 60 K rozdiele, nie pri 35 C. Tu potrebujeme individualny nizkoteplotný návrh UA 37.63 kW/K. CAPEX je rozpočtový scenár, nie cenová ponuka. Pôvodný Simulink a modely iného chatu neboli zmenené.
"""
if not hub.exists():hub.write_text(txt,encoding="utf-8");hubstatus="CREATED"
else:hubstatus="UNCHANGED_EXISTING"
manifest={"as_of":"2026-10-23","vault":str(dest),"created":sum(x["status"]=="COPIED" for x in records),
"verified":sum(x["verified_identical"] for x in records),"hub":hubstatus,
"conflicts":[x["file"] for x in records if not x["verified_identical"]],"files":records}
mp=root/"obsidian_equipment_sync_manifest.json"
if mp.exists():raise FileExistsError(str(mp))
mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
print("OBSIDIAN_EQUIPMENT_SYNC_VERIFIED",json.dumps({x:manifest[x] for x in ["created","verified","hub","conflicts","vault"]},ensure_ascii=False))
if manifest["conflicts"]:raise SystemExit(2)
