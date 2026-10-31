"""Independent file-integrity and source04 evidence audit; no production import."""
from pathlib import Path
import hashlib, json, csv
import pymupdf
root = Path(__file__).resolve().parents[1]
audit = root / "audit"
pdf = root / "sources/papers/04_Hiltunen_Espoo_2020.pdf"
evp = audit / "evidence_source04_v25/source04_primary_checks_v25.json"
stp = root / "STATUS_v25.json"
trp = audit / "literature_traceability_v25.csv"
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
ev = json.loads(evp.read_text(encoding="utf-8"))
st = json.loads(stp.read_text(encoding="utf-8"))
with trp.open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
tests = {}
tests["original_pdf_hash"] = digest(pdf)==ev["pdf_sha256"]==st["pdf_sha256"]
tests["evidence_hash"] = digest(evp)==st["evidence_sha256"]
tests["traceability_hash"] = digest(trp)==st["traceability_sha256"]==ev["traceability_sha256"]
tests["all_90_primary_checks_pass"] = len(ev["checks"])==90 and all(x["passed"] for x in ev["checks"])
tests["registry_31_unique"] = len(rows)==31 and {int(x["id"]) for x in rows}==set(range(1,32))
tests["no_full_signoff"] = not any(x["fully_signed_off"]=="YES" for x in rows)
tests["source04_partial"] = next(x for x in rows if x["id"]=="4")["fully_signed_off"]=="NO"
tests["17_table2_rows"] = len(ev["table2"])==17
tests["figure3_energy_closure"] = abs(ev["figure3"]["Q_condenser_MW"]-ev["figure3"]["Q_evaporator_MW"]-ev["figure3"]["W_electric_MW"])<1e-12
tests["storage_losses_excluded"] = ev["storage"]["standing_and_network_losses_in_paper"]=="excluded"
with pymupdf.open(pdf) as doc:
    p8 = doc[7].get_text()
    p9 = doc[8].get_text()
tests["paper_DOI_original"] = "10.3390/en13143551" in pymupdf.open(pdf)[0].get_text()
tests["paper_table2_units"] = "Supply (€/MWh)" in p8 and "Return (€/MWh)" in p8
tests["paper_storage_volume"] = "20,000 m3 hot water thermal storage" in p9
tests["paper_storage_capacity"] = "857.5 MWh" in p9
tests["paper_explicit_zero_losses"] = "Heat losses for the storage or the network were not considered." in p9
assert all(tests.values()), [k for k,v in tests.items() if not v]
out = audit / "evidence_source04_v25/independent_verification_v25.json"
with out.open("x", encoding="utf-8") as f:
    json.dump({"type":"independent_evidence_and_primary_text_QA",
               "passed":sum(tests.values()),"failed":0,
               "checks":tests,"pdf_sha256":digest(pdf),
               "evidence_sha256":digest(evp)},f,indent=2)
print("INDEPENDENT_V25_PASS",sum(tests.values()),"SHA256",digest(out))
