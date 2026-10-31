# -*- coding: utf-8 -*-
"""Non-destructive Obsidian sync: own namespace, sha256 verified."""
from pathlib import Path
import hashlib,json,shutil
src=Path(__file__).resolve().parent
vault=Path(r"C:\Users\Lysda\Documents\Bimba\02_PROJECTS\02_Automation\DataCenter_Heat_Reuse")
if not vault.exists():raise FileNotFoundError(str(vault))
dest=vault/"calibration"/"closed_loop_simulink_20261023"
dest.mkdir(parents=True,exist_ok=True)
files=[
 "DC_Pool_Coupled_ClosedLoop_20261023_SK.slx",
 "DC_Pool_Coupled_Simulink_diagram.png",
 "dc_pool_coupled_step_SK.m",
 "build_closed_loop_simulink_SK.m",
 "run_closed_loop_cases_SK.m",
 "run_nopool25_baseline_SK.m",
 "manufacturer_cop_reference_SK.m",
 "run_manufacturer_cop_comparison_SK.m",
 "ClosedLoop_Simulink_Matematika_SK.md",
 "simulink_closed_loop_summary_168h.json",
 "simulink_closed_loop_summary_8760h.json",
 "simulink_nopool25_baseline_8760h.json",
 "closed_loop_independent_QA_2025.json",
 "closed_loop_incremental_opex_2025.json",
 "manufacturer_certified_points_carrier.csv",
 "carrier_cop_certified_vs_scenario.csv",
 "carrier_cop_certified_comparison_SK.png"
]
out=[]
for file in files:
 origin=src/file;target=dest/file
 assert origin.is_file(),str(origin)
 sha=hashlib.sha256(origin.read_bytes()).hexdigest()
 if target.exists():
  action="ALREADY_IDENTICAL" if hashlib.sha256(target.read_bytes()).hexdigest()==sha else "CONFLICT_UNCHANGED"
 else:
  shutil.copy2(origin,target)
  action="COPIED"
 ok=target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest()==sha
 out.append({"name":file,"action":action,"sha256":sha,"identical":ok})
hub=dest/"00_ClosedLoop_DataCenter_Bazen_SK.md"
hubtext=r"""---
tags: [datacentrum, bazen, simulink, closed-loop, kalibracia]
status: VERIFIED_SIMULATION_NOT_CERTIFIED
date: 2026-10-23
---
# DataCenter ↔ bazén ↔ teplovodná sieť

Nový oddelený model MATLAB/Simulink so skutočnou 5-minútovou tepelnou spätnou väzbou.

- [[ClosedLoop_Simulink_Matematika_SK]] - kompletné rovnice, výsledky a metodika
- [[DC_Pool_Coupled_ClosedLoop_20261023_SK.slx]] - nový Simulink model, bez zásahu do pôvodného bazénového projektu
- ![[DC_Pool_Coupled_Simulink_diagram.png]]
- ![[carrier_cop_certified_comparison_SK.png]]
- [[manufacturer_certified_points_carrier.csv]] - overené skúšobné body Eurovent pri W10-7
- [[simulink_closed_loop_summary_8760h.json]] - 8760h výsledky
- [[closed_loop_independent_QA_2025.json]] - nezávislé kontroly
- [[closed_loop_incremental_opex_2025.json]] - OPEX citlivosť

Veľké vstupné/výstupné CSV (4 × 105120 riadkov) zostávajú v:
`C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\calibration\closed_loop_simulink_20261023\`

UPOZORNENIE: reálna prevádzka, normová zhoda a COP pre 25–35°C / 70°C ešte nie sú overené.
"""
if not hub.exists():hub.write_text(hubtext,encoding="utf-8")
else:out.append({"name":hub.name,"action":"HUB_ALREADY_EXISTS","identical":False})
manifest={"created":"2026-10-23","target":str(dest),"copied":sum(x["action"]=="COPIED" for x in out),
 "identical":sum(x["identical"] for x in out),
 "conflicts":[x for x in out if x["action"]=="CONFLICT_UNCHANGED"],"files":out}
target_manifest=src/"obsidian_sync_closed_loop_manifest.json"
if target_manifest.exists():raise FileExistsError("No-clobber manifest already exists")
target_manifest.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
print("OBSIDIAN_SYNC_CLOSED_LOOP",json.dumps({"copied":manifest["copied"],"identical":manifest["identical"],
 "conflicts":len(manifest["conflicts"]),"folder":str(dest)},ensure_ascii=False))
if manifest["conflicts"]:raise SystemExit(2)
