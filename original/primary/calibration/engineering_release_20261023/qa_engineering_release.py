# -*- coding: utf-8 -*-
from pathlib import Path
import csv,json,re,subprocess,fitz
p=Path(__file__).resolve().parent
release={}
pdf=[]
for lang in ('SK','RU','EN'):
 f=p/f'Engineering_Release_{lang}.pdf'
 assert f.is_file() and f.stat().st_size>30000
 doc=fitz.open(f)
 clipped=[]
 extracted=''
 for j,page in enumerate(doc):
  extracted+=page.get_text()
  for w in page.get_text('words'):
   if w[0]<-1 or w[1]<-1 or w[2]>page.rect.width+1 or w[3]>page.rect.height+1:
    clipped.append((j,w[4]))
  if j==0:page.get_pixmap(matrix=fitz.Matrix(1.2,1.2)).save(str(p/f'report_preview_{lang}.png'))
 assert not clipped,clipped[:4]
 assert len(extracted)>1600 and '2025' in extracted
 pdf.append({'lang':lang,'pages':len(doc),'bytes':f.stat().st_size,'chars':len(extracted),'clipped':0})
src=p/'cooling_resilience_calculator.html'
ht=src.read_text(encoding='utf-8')
js=ht.split('<script>',1)[1].split('</script>',1)[0]
(p/'ui_syntax_check.js').write_text(js,encoding='utf-8')
subprocess.run(['node','--check',str(p/'ui_syntax_check.js')],check=True)
stress=json.loads((p/'IT_cooling_failsafe_simulink_results.json').read_text(encoding='utf-8'))
assert len(stress)==6 and sum(not x['safeSimulation'] for x in stress)==4
j=json.loads((p/'independent_cooling_design_scenarios.json').read_text(encoding='utf-8'))
assert j['profile']['rows']==105120
assert abs(j['profile']['E_IT_heat_MWh']-j['profile']['E_reused_source_MWh']-j['profile']['E_rejected_MWh'])<.002
with (p/'FMEA_engineering_gaps.csv').open(encoding='utf-8-sig') as f:
 rows=list(csv.DictReader(f))
assert len(rows)>=18
for name in ('Carrier','Oilon','AlfaLaval','DryCooler'):
 assert (p/f'RFQ_{name}_EN.md').stat().st_size>800
release={'pdf':pdf,'HTML_JS':'VALIDATED_NODE_CHECK','Simulink_failure_cases':len(stress),
         'unsafe_conditions_detected':sum(not x['safeSimulation'] for x in stress),
         'annual_source_rows':105120,'FMEA_rows':len(rows),'RFQ_drafts':4,
         'physical_vendor_duty_point_verified':False,
         'operating_safety_certified':False}
f=p/'QA_ENGINEERING_RELEASE_20261023.json'
if f.exists():raise FileExistsError(str(f))
f.write_text(json.dumps(release,indent=2,ensure_ascii=False),encoding='utf-8')
print('ENGINEERING_RELEASE_QA_PASS',json.dumps(release,ensure_ascii=False))
