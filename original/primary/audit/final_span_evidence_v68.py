from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, shutil
ROOT=Path(__file__).resolve().parents[1]
development=ROOT/'results/span_repair_v68_final_20261011T215609_349756Z'
path=ROOT/'matlab/run_span_repair_v68.m'
shutil.copy2(path,development/'initial_run_span_repair_v68.m')
s=path.read_text()
old='isequal(prefix,runs{end}.trace(1:2,:))'
assert old in s
s=s.replace(old,"isequal(prefix,runs{find(cellfun(@(r)strcmp(r.id,base.id),runs))}.trace(1:2,:))")
path.write_text(s,encoding='utf-8')
folder=ROOT/'results'/('span_repair_v68_release_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'))
folder.mkdir()
for name in ['spec.json','preservation.json']:
    shutil.copy2(development/name,folder/name)
(development/'recovery_note.txt').write_text('''MATLAB 1434 PASS / 1 FAIL retained.
Independent numerical/artifact QA 36981 PASS / 2 FAIL; the two failures are
the MATLAB failed assertion and its nonzero observed batch receipt.
All six separate reviewer mutations were detected. The remaining harness bug
compared the delayed-fault prefix with runs{end}, now an appended span witness.
Corrected selection by explicit delayed_fault_control ID; new sealed execution
is required. Controller source and saved model stay unchanged.
''')
paths=[ROOT/'audit'/n for n in ['Span_padding_derivation_v68r2.md','span_tail_review_v68r2.py','verify_span_repair_v68r2.py','repair_span_reviewer_v68.py','final_span_evidence_v68.py']]
manifest=[]
for p in paths:
    dst=folder/'reviewer_snapshot_v68r2'/p.relative_to(ROOT);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
    manifest.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(folder/'reviewer_hashes_v68r2.json').write_text(json.dumps(manifest,indent=2)+'\n')
shutil.copy2(development/'reviewer_revision_note_v68r2.txt',folder/'reviewer_revision_note_v68r2.txt')
print(folder.relative_to(ROOT).as_posix())
