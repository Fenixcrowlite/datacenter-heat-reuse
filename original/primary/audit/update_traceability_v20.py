import csv
from pathlib import Path
r=Path(__file__).resolve().parent
src=r/'literature_traceability_v10.csv'
dst=r/'literature_traceability_v20.csv'
if dst.exists(): raise FileExistsError(dst)
with src.open(encoding='utf-8-sig',newline='') as f:
    rows=list(csv.DictReader(f)); fields=list(rows[0])
assert len(rows)==31
assert rows[0]['id']=='1'
rows[0]['review_level']='PARTIAL_PRIMARY_VISUAL_REVIEW_NOT_SIGNED_OFF'
rows[0]['blockers'] += ' | v20 Eq1, Table2 and Table4 visually checked; full source and EnergyPRO reproduction pending'
with dst.open('x',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
print('PASS: 31 rows, source01 partial, 0 fully signed off')
