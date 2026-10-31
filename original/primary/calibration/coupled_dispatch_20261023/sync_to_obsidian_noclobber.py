# -*- coding: utf-8 -*-
"""Append-only Obsidian handoff. Never overwrite parallel chat work or old vault notes."""
from pathlib import Path
from hashlib import sha256
import json, shutil
root=Path(__file__).resolve().parent
vault=Path(r"C:\Users\Lysda\Documents\Bimba\02_PROJECTS\02_Automation\DataCenter_Heat_Reuse")
if not vault.is_dir():raise FileNotFoundError("Known Obsidian vault missing: "+str(vault))
target=vault/"calibration"/"coupled_dispatch_20261023"
target.mkdir(parents=True,exist_ok=True)
files=["Annual_Coupled_Study_SK.md","Annual_Coupled_Study_RU.md","Annual_Coupled_Study_EN.md",
 "Annual_Coupled_Study_SK.pdf","Annual_Coupled_Study_RU.pdf","Annual_Coupled_Study_EN.pdf",
 "Integracia_matematika_rocna_SK.md","coupled_annual_SK.png",
 "coupled_scenarios_2025.csv","pool_volume_cover_sensitivity_2025.csv","coupled_results_2025.json"]
result=[]
for rel in files:
 src=root/rel;dest=target/rel
 if not src.is_file():raise FileNotFoundError(str(src))
 digest=sha256(src.read_bytes()).hexdigest()
 if dest.exists():
  status="ALREADY_IDENTICAL" if sha256(dest.read_bytes()).hexdigest()==digest else "CONFLICT_UNTOUCHED"
 else:
  shutil.copy2(src,dest);status="COPIED"
 result.append({"name":rel,"status":status,"hash_sha256":digest,"identical":sha256(dest.read_bytes()).hexdigest()==digest})
hub=target/"00_Kalibracia_DC_2025.md"
hubText="""---
tags: [datacentrum, bazen, teplovodna-siet, matlab, kalibracia]
status: VERIFIED_SIMULATION_NOT_REAL_WORLD_CERTIFIED
date: 2026-10-23
---

# DataCenter Heat Reuse - bazen 2025 / integracia

- [[Integracia_matematika_rocna_SK]] - podrobná matematika a jednotkové bilancie
- [[Annual_Coupled_Study_SK]] - slovenská technická správa
- [[Annual_Coupled_Study_RU]] - rusky
- [[Annual_Coupled_Study_EN]] - English
- PDF: [[Annual_Coupled_Study_SK.pdf]], [[Annual_Coupled_Study_RU.pdf]], [[Annual_Coupled_Study_EN.pdf]]
- Datové súbory: [[coupled_scenarios_2025.csv]], [[pool_volume_cover_sensitivity_2025.csv]]
- ![[coupled_annual_SK.png]]

> Modelové vstupy: NASA POWER 2025 reanalysis, Eurostat SK 2025 ceny. DC záťaž, COP a bazénové straty zatiaľ scenárové. Externá certifikácia nebola vykonaná. Bazénový paralelný Simulink projekt zostáva bez zmien.
"""
if not hub.exists():hub.write_text(hubText,encoding="utf-8");hubStatus="COPIED"
else:hubStatus="ALREADY_EXISTED_NOT_OVERWRITTEN"
manifest={"date":"2026-10-23","owner":"calibration_coupled_dispatch",
 "vault_target":str(target),"hub":hubStatus,
 "copied":sum(x["status"]=="COPIED" for x in result),
 "conflicts":[x for x in result if x["status"]=="CONFLICT_UNTOUCHED"],
 "verified_identical":sum(x["identical"] for x in result),"files":result}
manifestFile=root/"obsidian_sync_manifest_20261023.json"
if manifestFile.exists():raise FileExistsError(str(manifestFile))
manifestFile.write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
print(json.dumps({k:manifest[k] for k in ["vault_target","hub","copied","verified_identical","conflicts"]},ensure_ascii=False))
if manifest["conflicts"]:raise SystemExit(3)
