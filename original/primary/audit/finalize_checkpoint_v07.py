"""Freeze v0.7 checkpoint and sync new versioned artifacts into Obsidian (no clobber)."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil

root=Path(__file__).resolve().parents[1]
audit=root/"audit"
p=audit/"Sintong_primary_source_correction_v07_RU.md"
s=p.read_text(encoding="utf8")
old="- Eq. 17 **ещё не сверена визуально**. Не переносить OCR-структуру в код без контроля скобок и степеней."
new="- Eq. 17 визуально сверена на оригинальной печатной стр. 32: eps=1-exp[(1/Cr)*NTU^0.22*(exp(-Cr*NTU^0.78)-1)], Cr=Cmin/Cmax, NTU=UA/Cmin. Eq. 18 для Cr<=0.01: eps=1-exp(-NTU). См. Sintong_p32_eq17_visual_v07.png; это crossflow двух несмешивающихся потоков, а не counterflow."
if old in s:
    p.write_text(s.replace(old,new),encoding="utf8")
elif new not in s:
    raise RuntimeError("unexpected text in correction note; no replacement")

tests=[json.loads((audit/name).read_text(encoding="utf8")) for name in
       ("reference_physics_tests_v07.json","sintong_equations_tests_v07.json")]
assert all(t['status']=="PASS" for t in tests)
base=json.loads((root/"STATUS_v06.json").read_text(encoding="utf8"))
base['version']="0.7"
base['updated_utc']=datetime.now(timezone.utc).isoformat()
base['notes']="M1 source audit ongoing; v0.7 math/reference prototype is not M2/M3 full gate completion."
base['reference_physics_v07']={'state':'PARTIAL_PROTOTYPE_VERIFIED','reference_tests':11,
  'sintong_printed_equation_tests':9, 'random_reference_vectors':1500,
  'random_crossflow_vectors':1000,'synthetic_annual_hours':8760,
  'scope':'first law and energy/temperature bounds; no primary paper numerical replication'}
base['sintong_v07']={'eq17':'visual_verified','eq22':'visual_verified_sign_issue',
  'eq24':'visual_verified_MULTIPLICATION_not_division',
  'scope_note':'Printed Q_DH = Q_DC,cooling + eta_supp*P_comp; not generic efficiency on total Qhot'}
base['next']=[
  "M1 continue 31-source paper-by-paper audit and fill traceability with verified equations",
  "Resolve original author conventions by inspecting Sintong referenced Ham [27], Park [38], original script if accessible",
  "M2 finish independent physical mathematics/spec before promoting MATLAB/Simulink/Stateflow",
  "M3 compare alternative formulations and properties at common boundary datasets; v0.7 is prototype"
]
(root/"STATUS_v07.json").write_text(json.dumps(base,ensure_ascii=False,indent=2),encoding="utf8")
st=root/"MASTER_STAGEBOARD_v06.md"
(root/"MASTER_STAGEBOARD_v07.md").write_text(
 st.read_text(encoding="utf8")+
 "\n\n## Промежуточная точка v0.7, 08.10.2026\n"
 "- Исправлено неверное извлечение Sintong Eq24: коэффициент 0.97 УМНОЖАЕТ Pcomp, не делит. Eq17/22/24 визуально сверены по PDF стр.32–33.\n"
 "- Проверенный независимый reference kernel: audit/reference_physics_v07.py, 11/11 тестов, 1500 random + 8760h synthetic.\n"
 "- Проверка формул Sintong (crossflow, знаки, losses): audit/sintong_equations_v07.py, 9/9 тестов, 1000 random.\n"
 "- audit/Independent_First_Law_v07_RU.md: математическая спецификация для reference.\n"
 "- **Этап M1 НЕ завершен. M2/M3 тоже НЕ завершены целиком; v0.7 является прототипом.**\n",
 encoding="utf8")
files=[
"MASTER_STAGEBOARD_v07.md","STATUS_v07.json",
"audit/Sintong_primary_source_correction_v07_RU.md",
"audit/Sintong_p32_eq17_visual_v07.png",
"audit/Sintong_p32_eq17_20_visual_v07.png",
"audit/Sintong_p33_eq21_22_visual_v07.png",
"audit/Sintong_p33_eq21_25_visual_v07.png",
"audit/reference_physics_v07.py","audit/test_reference_physics_v07.py",
"audit/reference_physics_tests_v07.json",
"audit/sintong_equations_v07.py","audit/sintong_equations_tests_v07.json",
"audit/Independent_First_Law_v07_RU.md"]
obs=Path(r"C:\Users\Lysda\Documents\Bimba\02_PROJECTS\02_Automation\DataCenter_Heat_Reuse")
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for f in files:
    a=root/f;b=obs/f;b.parent.mkdir(parents=True,exist_ok=True)
    if not a.exists():status="SOURCE_MISSING"
    elif b.exists():status="SAME" if sha(a)==sha(b) else "CONFLICT_SKIP"
    else:
        shutil.copy2(a,b)
        status="COPIED" if sha(a)==sha(b) else "CHECKSUM_FAIL"
    rows.append({'path':f,'status':status})
out={'timestamp_utc':datetime.now(timezone.utc).isoformat(),'files':rows}
(root/"integration/obsidian_v07_sync_manifest.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf8")
print(json.dumps({'status':'DONE','test_count':sum(t.get('tests_run',t.get('tests',0)) for t in tests),
  'sync':{k:sum(x['status']==k for x in rows) for k in set(x['status'] for x in rows)},
  'path':str(root)},ensure_ascii=False))
