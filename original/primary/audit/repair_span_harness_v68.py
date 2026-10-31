from pathlib import Path
from datetime import datetime, timezone
import json, shutil
ROOT=Path(__file__).resolve().parents[1]
development=ROOT/'results/span_repair_v68_20261011T215413_685622Z'
path=ROOT/'matlab/run_span_repair_v68.m'
shutil.copy2(path,development/'initial_run_span_repair_v68.m')
s=path.read_text()
s=s.replace('base=spec.cases(end);',"base=spec.cases(strcmp({spec.cases.id},'delayed_fault_control'));")
start=s.index('% Boundary witnesses are checked')
end=s.index("[prefix,~]=execute(input(1:2,:),rows(1:2,:));",start)
s=s[:start]+(ROOT/'audit/span_repair_harness_extra_v68.txt').read_text()+'\n'+s[end:]
path.write_text(s,encoding='utf-8')
folder=ROOT/'results'/('span_repair_v68_final_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'))
folder.mkdir()
for name in ['spec.json','preservation.json']:
    shutil.copy2(development/name,folder/name)
note='''Development batch: MATLAB 1432 PASS / 3 FAIL, retained without acceptance.
Three harness defects: appended cases changed the inherited fault-base selection;
near-boundary legacy expectation wrongly predicted rejection (ties-to-even makes
the expanded endpoint exactly one); the same wrong expectation affected the host
probe. Repaired harness only; the saved v68 model and production sources are
unchanged. Fresh final suite reruns with original delayed-fault base and explicit
equality-failure / adjacent-success controls. Sandbox startup failure retained.
'''
(development/'recovery_note.txt').write_text(note)
print(folder.relative_to(ROOT).as_posix())
