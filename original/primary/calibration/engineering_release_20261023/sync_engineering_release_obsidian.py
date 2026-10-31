# -*- coding: utf-8 -*-
"""Safe SHA-256 Obsidian sync into isolated owner namespace."""
from pathlib import Path
from hashlib import sha256
import json,shutil
root=Path(__file__).resolve().parent
vault=Path(r'C:\Users\Lysda\Documents\Bimba\02_PROJECTS\02_Automation\DataCenter_Heat_Reuse')
if not vault.is_dir():raise FileNotFoundError(str(vault))
out=vault/'calibration'/'engineering_release_20261023'
out.mkdir(parents=True,exist_ok=True)
wanted=[
 'Engineering_Release_SK.md','Engineering_Release_RU.md','Engineering_Release_EN.md',
 'Engineering_Release_SK.pdf','Engineering_Release_RU.pdf','Engineering_Release_EN.pdf',
 'IT_Independent_HeatRejection_20261023_SK.slx','build_IT_emergency_cooling_SK.m',
 'it_independent_cooling_step_SK.m','test_IT_cooling_failure_SK.m',
 'IT_cooling_failsafe_simulink_results.json','independent_cooling_design_scenarios.json',
 'cooling_nplus1_derating.csv','cooling_failover_sensitivity.csv','cooling_fault_second_scale.csv',
 'cooling_fault_second_scale.json','hydraulic_capacity_table.csv',
 'N7_der10_fail30s.csv','N7_der10_fail300s.csv',
 'RFQ_Carrier_EN.md','RFQ_Oilon_EN.md','RFQ_AlfaLaval_EN.md','RFQ_DryCooler_EN.md',
 'vendor_directory_grounded.csv','RFQ_package_status.json',
 'cooling_resilience_calculator.html','FMEA_engineering_gaps.csv',
 'QA_ENGINEERING_RELEASE_20261023.json']
log=[]
for fn in wanted:
 a=root/fn;b=out/fn
 assert a.is_file(),str(a)
 h=sha256(a.read_bytes()).hexdigest()
 if b.exists():
  action='IDENTICAL' if sha256(b.read_bytes()).hexdigest()==h else 'CONFLICT_PRESERVED'
 else:
  shutil.copy2(a,b);action='COPIED'
 log.append({'name':fn,'action':action,'identical':sha256(b.read_bytes()).hexdigest()==h,
             'sha256':h})
hub=out/'00_Engineering_Release_20261023.md'
text=r"""---
date: 2026-10-23
status: SIMULATION_VERIFIED_NOT_REAL_SYSTEM_CERTIFIED
tags: [datacentrum, chladenie, bazen, simulačné-testy, N-plus-1, projekt]
---

# DataCenter Heat Reuse - bezpečnosť a výkon 2026

Dokončená nezávislá vetva návrhu a QA. Neslúži ako technické osvedčenie či dokumentácia na realizáciu.

- [[Engineering_Release_SK]] / [[Engineering_Release_SK.pdf]]
- [[Engineering_Release_RU]] / [[Engineering_Release_RU.pdf]]
- [[Engineering_Release_EN]] / [[Engineering_Release_EN.pdf]]
- [[IT_Independent_HeatRejection_20261023_SK.slx]] - verzovaný Simulink model samostatného IT chladenia
- [[IT_cooling_failsafe_simulink_results.json]] - 6 hodinových poruchových skúšok s krokom 5 sekúnd
- [[independent_cooling_design_scenarios.json]] - 105120 intervalov z predchádzajúceho Simulinku
- [[cooling_resilience_calculator.html]] - samostatný HTML kalkulátor s upraviteľnými parametrami
- [[FMEA_engineering_gaps.csv]] - 18 rizík a otvorených validačných úloh
- [[RFQ_Carrier_EN]], [[RFQ_Oilon_EN]], [[RFQ_AlfaLaval_EN]], [[RFQ_DryCooler_EN]] - pripravené návrhy, NEODOSLANÉ

**Priority P0**: výrobcom vybrané COP/PLR a 10-MW účinné chladenie IT pri návrhovom lete,
UPS pre obehové čerpadlá, nezávislý bypass a bezpečnostné odpojenie, merania tokov,
hydraulika, aktuálne úplné právne normy a schválenie zodpovedného projektanta.

Staršie v85/v86, bazénový paralelný model a ostatné Obsidian poznámky neboli prepísané.
"""
if not hub.exists():hub.write_text(text,encoding='utf-8')
manifest={'date':'2026-10-23','source':str(root),'dest':str(out),
 'total':len(log),'verified_identical':sum(v['identical'] for v in log),
 'created':sum(v['action']=='COPIED' for v in log),
 'conflicts':[v['name'] for v in log if not v['identical']],'files':log}
(root/'OBSIDIAN_Engineering_Release_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('OBSIDIAN_ENGINEERING_RELEASE',json.dumps({k:manifest[k] for k in ['total','verified_identical','created','conflicts']},ensure_ascii=False))
if manifest['conflicts']:raise SystemExit(3)
