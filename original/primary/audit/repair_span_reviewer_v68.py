"""Preserve initial sealed reviewer; issue corrected review/proof artifacts."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, shutil, sys
ROOT=Path(__file__).resolve().parents[1]
folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
def new(path,text):
    with path.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
proof=(ROOT/'audit/Span_padding_derivation_v68.md').read_text()
proof=proof.replace('(1/5!)/(1-1/6) = 87/32','(1/5!)/(1-1/5) = 87/32')
proof+='\nProof revision: the conservative geometric tail ratio is 1/5, not 1/6.\nThe earlier sealed draft incorrectly equated the sharper 1/6 bound to 87/32.\nThe production numerator and its validity are unchanged.\n'
new(ROOT/'audit/Span_padding_derivation_v68r2.md',proof)
s=(ROOT/'audit/span_tail_review_v68.py').read_text()
s=s.replace('(1/5!)/(1-1/6)', '(1/5!)/(1-1/5)').replace('(1-F(1,6))','(1-F(1,5))')
s=s.replace("'interval_dispatch_kernel_v66' in v['message']", "'DCHR_Event_Brackets_Stateflow_v67r2/Six_Mode_Interval_Dispatch' in v['message']")
s=s.replace("trace[-1][235]==1 and trace[-1][246]==1", "trace[-1][235] in [1,3] and trace[-1][246]==1")
s=s.replace('from pathlib import Path','from pathlib import Path\nimport hashlib, json')
s=s.replace('    # Integral forms:', '''    for rec in json.loads((folder/'reviewer_hashes_v68r2.json').read_text()):
        path=folder.parents[1]/rec['path']
        sealed=folder/'reviewer_snapshot_v68r2'/rec['path']
        check('reviewer_seal',rec['path'],hashlib.sha256(path.read_bytes()).hexdigest()==rec['sha256'] and hashlib.sha256(sealed.read_bytes()).hexdigest()==rec['sha256'])
    # Integral forms:''')
new(ROOT/'audit/span_tail_review_v68r2.py',s)
s=(ROOT/'audit/verify_span_repair_v68.py').read_text().replace('from span_tail_review_v68 import','from span_tail_review_v68r2 import')
s=s.replace('independent_QA_v68_','independent_QA_v68r2_').replace('root_traces_v68_','root_traces_v68r2_')
new(ROOT/'audit/verify_span_repair_v68r2.py',s)
paths=[ROOT/'audit'/n for n in ['Span_padding_derivation_v68r2.md','span_tail_review_v68r2.py','verify_span_repair_v68r2.py','repair_span_reviewer_v68.py']]
manifest=[]
for p in paths:
    dest=folder/'reviewer_snapshot_v68r2'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    manifest.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(folder/'reviewer_hashes_v68r2.json').write_text(json.dumps(manifest,indent=2)+'\n')
(folder/'reviewer_revision_note_v68r2.txt').write_text('''Initial sealed QA draft independently audited before final review:
1. Geometric e bound used ratio 1/6 but claimed equality to the looser 87/32.
   Revised proof uses valid conservative ratio 1/5; production tail is valid.
2. Stateflow runtime stack reports chart/line, not the helper function name.
   Match actual saved chart path and specific failure message.
3. Delayed passive-restart candidate already starts below the threshold; it
   correctly reports status 3 (already reached), not status 1 (interior root).
The first sealed scripts/proof stay preserved. Revised QA and derivation have
a separate immutable source seal. No MATLAB source or saved model changed.
''')
print('SEALED REVISED REVIEWER',len(paths),'files')
