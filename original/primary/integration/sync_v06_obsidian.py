"""Copy verified DataCenter study artifacts to Obsidian without overwriting divergent files."""
from pathlib import Path
import hashlib,shutil,json
from datetime import datetime,timezone
one=Path(__file__).resolve().parents[1]
obs=Path(r"C:\Users\Lysda\Documents\Bimba\02_PROJECTS\02_Automation\DataCenter_Heat_Reuse")
allow=[
"MASTER_STAGEBOARD_v06.md","STATUS_v06.json",
"audit/Ebrahimi_source_audit_v06_RU.md",
"audit/Hiltunen_Espoo_2020_primary_source_audit_v06_RU.md",
"audit/Sintong_2023_primary_source_audit_v06_RU.md",
"audit/analytical_preflight_v06.py","audit/analytical_preflight_v06.json",
"audit/sintong_consistency_v06.py","audit/sintong_consistency_v06.json",
"audit/literature_traceability_v06.csv","audit/literature_traceability_v06.json",
"audit/metadata_crossref_v06.csv","audit/metadata_crossref_v06.json",
"audit/source_acquisition_v06.json","audit/openalex_acquisition_v06.json",
"audit/stockholm_theses_fetch_v06.json",
"sources/original/Datacentra_teplo_vedecke_prace.pdf",
"sources/papers/04_Hiltunen_Espoo_2020.pdf",
"sources/papers/08_Tofani_Stockholm_2022.pdf",
"sources/papers/09_Sintong_Stockholm_2023.pdf",
"sources/papers/21_Ebrahimi_2014.pdf"
]
def hashfile(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):h.update(chunk)
    return h.hexdigest()
report={"updated":datetime.now(timezone.utc).isoformat(),"source":str(one),"destination":str(obs),"files":[]}
for f in allow:
    src=one/f;dst=obs/f; row={"path":f}
    if not src.exists():
        row["status"]="SOURCE_MISSING"
    else:
        src_hash=hashfile(src)
        if dst.exists():
            row["status"]="ALREADY_IDENTICAL" if hashfile(dst)==src_hash else "CONFLICT_SKIPPED"
        else:
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,dst)
            row["status"]="COPIED" if hashfile(dst)==src_hash else "CHECKSUM_MISMATCH"
        row["sha256"]=src_hash;row["bytes"]=src.stat().st_size
    report["files"].append(row)
    print(f, row["status"], flush=True)
report["summary"]={s:sum(x["status"]==s for x in report["files"]) for s in ("COPIED","ALREADY_IDENTICAL","CONFLICT_SKIPPED","CHECKSUM_MISMATCH","SOURCE_MISSING")}
out=one/"integration/obsidian_v06_copy_manifest.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print("SUMMARY",json.dumps(report["summary"],ensure_ascii=False),flush=True)
