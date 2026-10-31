from pathlib import Path
import hashlib,json,shutil
src=Path(__file__).resolve().parent
dst=Path(r'C:\Users\Lysda\Documents\Bimba\02_PROJECTS\02_Automation\DataCenter_Heat_Reuse\calibration\capacity_fault_simulink_20261023')
dst.mkdir(parents=True,exist_ok=True)
files=['DC_Pool_Capacity_Fault_20261023_SK.slx','dc_pool_coupled_step_capacity_SK.m',
'build_capacity_fault_simulink_SK.m','run_capacity_fault_annual_SK.m',
'capacity_fault_simulink_2025.csv','capacity_fault_simulink_2025.json',
'Carrier_2025_nominal_vs_Nplus1_options.csv','Carrier_2025_rated_vs_simulated_economics.json',
'Nplus1_Carrier_Selection_SK.md','Nplus1_Carrier_Selection_RU.md','Nplus1_Carrier_Selection_EN.md',
'Nplus1_Carrier_Selection_SK.pdf','Nplus1_Carrier_Selection_RU.pdf','Nplus1_Carrier_Selection_EN.pdf',
'nplus1_pdf_qa.json']
summary=[]
for f in files:
 a=src/f;b=dst/f
 assert a.is_file(),str(a)
 digest=hashlib.sha256(a.read_bytes()).hexdigest()
 status='EXISTING'
 if not b.exists():shutil.copy2(a,b);status='COPIED'
 elif hashlib.sha256(b.read_bytes()).hexdigest()!=digest:status='CONFLICT_UNCHANGED'
 summary.append({'file':f,'status':status,'identical':hashlib.sha256(b.read_bytes()).hexdigest()==digest})
(src/'obsidian_nplus1_sync.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print('OBSIDIAN_NPLUS1_SYNC',json.dumps({'identical':sum(r['identical'] for r in summary),'total':len(files),'conflicts':[r['file'] for r in summary if not r['identical']]},ensure_ascii=False))
