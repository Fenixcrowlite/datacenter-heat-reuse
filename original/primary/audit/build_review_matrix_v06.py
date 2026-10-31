"""Produce a conservative 31/31 evidence-based review register.
Metadata match does not imply article equations checked.
"""
import csv, json, hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1]
prev=root/"audit/literature_traceability_v05.csv"
cross=root/"audit/metadata_crossref_v06.json"
out_csv=root/"audit/literature_traceability_v06.csv"
out_json=root/"audit/literature_traceability_v06.json"
with prev.open(encoding="utf-8-sig",newline="") as f:
    rows=list(csv.DictReader(f))
assert len(rows)==31, f"Expected 31 source entries, found {len(rows)}"
numbers=[int(r["id"]) for r in rows]
assert numbers==list(range(1,32)), f"Incorrect catalogue keys: {numbers}"
meta={int(x["nr"]):x for x in json.loads(cross.read_text(encoding="utf-8"))["papers"]}
assert len(meta)==24, f"Expected 24 Crossref-paper metadata rows; got {len(meta)}"
papers=root/"sources/papers"
result=[]
for r in rows:
    nr=int(r["id"])
    m=meta.get(nr,{})
    best=(m.get("candidates") or [{}])[0]
    pdfs=sorted(p.name for p in papers.glob(f"{nr:02d}_*.pdf") if p.stat().st_size > 4096 and p.open("rb").read(4)==b"%PDF")
    level=("CORE_PRIMARY_REVIEW_PENDING_FULL_SIGNOFF" if nr in (1,17) else
           "PARTIAL_PRIMARY" if nr in (4,9,21) else "CATALOG_ONLY")
    blockers=[]
    if nr==4: blockers.append("raw 2016 Helsinki hourly series/control curve incomplete")
    if nr==17: blockers.append("SigLinDe/Meteonorm inputs and manufacturer COP map missing; article COP endpoint discrepancy")
    if nr==20: blockers.append("MDPI PDF 403 from remote device; available abstract only")
    if nr in (1,17): blockers.append("full equation-by-equation verification still pending")
    if nr not in meta: blockers.append("reports/policy records may lack Crossref DOI")
    if not pdfs: blockers.append("primary local PDF not obtained")
    if m.get("status")=="NETWORK_ERROR": blockers.append("Crossref lookup failed")
    if m.get("status")=="AMBIGUOUS_REVIEW_REQUIRED": blockers.append("candidate title/DOI needs manual confirmation")
    result.append({
        "id":nr,"title":r["reference_and_title"],"role":r["role_from_original_catalog"],
        "review_level":level,"fully_signed_off":"NO","local_original_pdfs":";".join(pdfs),
        "primary_url_known":r["primary_url_or_doi"],"crossref_status":m.get("status","NOT_APPLICABLE"),
        "candidate_doi":best.get("doi",""),"candidate_title_similarity":best.get("similarity",""),
        "equations_transcribed":"PARTIAL" if nr in (1,17,4,9,21) else "NO",
        "paper_replicated":"NO","blockers":" | ".join(blockers),
    })
fields=list(result[0])
with out_csv.open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(result)
counts={"total":len(result),"fully_signed_off":0,
        "core_primary_review":sum(r["review_level"].startswith("CORE") for r in result),
        "partial_primary_review":sum(r["review_level"]=="PARTIAL_PRIMARY" for r in result),
        "catalog_only":sum(r["review_level"]=="CATALOG_ONLY" for r in result),
        "local_pdf_count":sum(bool(r["local_original_pdfs"]) for r in result)}
with out_json.open("w",encoding="utf-8") as f:
    json.dump({"counts":counts,"sources":result},f,ensure_ascii=False,indent=2)
print(json.dumps(counts,ensure_ascii=False),flush=True)
print("OUTPUTS:",out_csv,out_json,flush=True)
