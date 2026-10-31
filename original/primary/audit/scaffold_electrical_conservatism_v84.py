"""Create a dedicated experiment harness without modifying accepted sources."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = (root/'matlab/run_electrical_ceiling_v83r2.m').read_text()
src = src.replace('function run_electrical_ceiling_v83r2(folder)', 'function run_electrical_conservatism_v84(folder)')
src = src.replace("if ~isfile(path),build_electrical_ceiling_v83r2([a.protocol_ticks a.input],cfg);end", "assert(isfile(path),'Preserved accepted v83r2 model required');")
start = src.index('% Invalid raw operands')
end = src.index('close_system(mdl,0);load_system(path);', start)
src = src[:start] + src[end:]
src = src.replace("'version','0.83'", "'version','0.84'")
src = src.replace('electrical_ceiling_v83.mat', 'electrical_conservatism_v84.mat')
src = src.replace('ELECTRICAL_V83', 'CONSERVATISM_V84')
src = src.replace("'DCHR:v83:AcceptanceFailure'", "'DCHR:v84:AcceptanceFailure'")
target = root/'matlab/run_electrical_conservatism_v84.m'
with target.open('x', encoding='utf-8', newline='\n') as out:
    out.write(src)
runner = (root/'audit/run_electrical_ceiling_v83r2.ps1').read_text().replace('run_electrical_ceiling_v83r2', 'run_electrical_conservatism_v84')
with (root/'audit/run_electrical_conservatism_v84.ps1').open('x', encoding='utf-8', newline='\n') as out:
    out.write(runner)
print('Created versioned MATLAB and batch harnesses; accepted model unchanged.')
