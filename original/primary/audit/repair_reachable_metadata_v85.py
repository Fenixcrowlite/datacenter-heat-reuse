"""Create corrected execution harness; preserve first candidate and its evidence."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=(R/'matlab/run_electrical_ceiling_v85.m').read_text()
s=s.replace('function run_electrical_ceiling_v85(folder)','function run_electrical_ceiling_v85r2(folder)')
s=s.replace("'saved_model_version','0.83r2'","'saved_model_version','0.85'")
with (R/'matlab/run_electrical_ceiling_v85r2.m').open('x',encoding='utf-8',newline='\n') as f:f.write(s)
s=(R/'audit/run_electrical_ceiling_v85.ps1').read_text().replace('run_electrical_ceiling_v85','run_electrical_ceiling_v85r2')
with (R/'audit/run_electrical_ceiling_v85r2.ps1').open('x',encoding='utf-8',newline='\n') as f:f.write(s)
print('Metadata-only versioned harness correction; model remains v85.')
