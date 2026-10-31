"""Reproducible internal PDF crosscheck; NOT independent source validation."""
import hashlib
import json
from pathlib import Path
import fitz

root = Path(__file__).resolve().parents[1]
pdf = root / "sources" / "papers" / "21_Ebrahimi_2014.pdf"
expected = "4aaffa92f30b0d5aa9c7a7e58e5ff8cad3eb05c9f8969b079d6127aab1600a40"
sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
doc = fitz.open(pdf)
def normalize(text):
    return " ".join(text.replace("–", "-").replace("−", "-").split())
p7, p8, p16 = [normalize(doc[i].get_text()) for i in (6, 7, 15)]
checks = {
    "primary_pdf_sha256": sha == expected,
    "primary_pdf_17_pages": len(doc) == 17,
    "discussion_90_and_48": "90" in p7 and "48" in p7 and "liquid pumped" in p7.lower(),
    "table9_heading": "Table 9" in p8,
    "table10_heading": "Table 10" in p8 and "liquid pump" in p8.lower(),
    "table11_heading": "Table 11" in p8,
    "table9_pump_47_7_to_48": "47.7" in p8 and "48" in p8,
    "table9_compression_90": "90" in p8 and "vapor" in p8.lower(),
    "table10_range_45_90": "45-90" in p8.replace(" ", ""),
    "reference12_marcinichen_2012": "[12] Marcinichen" in p16 and "2012;41:36-51" in p16.replace(" ", ""),
    "separate_pump_and_compressor": "liquid pumped" in p7.lower() and "vapor compression" in p7.lower(),
}
report = {
    "source_id": 21,
    "scope": "Ebrahimi original PDF internal crosscheck; Marcinichen [12] original NOT inspected",
    "evidence_class": {
        "primary_match": "Ebrahimi text only",
        "math_identity": "NOT_TESTED",
        "independent_validation": "NOT_PERFORMED"
    },
    "sha256": sha,
    "page_count": len(doc),
    "checks": checks,
    "passed": sum(checks.values()),
    "failed": sum(not v for v in checks.values()),
    "unresolved": "Table 10 liquid pump 45-90 C conflicts with Table 9 pump about 48 C; compare original Marcinichen 2012 before using."
}
out = root / "audit" / "ebrahimi_marcinichen_crossref_tests_v11.json"
if out.exists():
    prior = json.loads(out.read_text(encoding="utf-8"))
    if prior != report:
        raise AssertionError("Existing v11 evidence differs; do not overwrite")
else:
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print("PASSED", report["passed"], "FAILED", report["failed"])
print("EVIDENCE", out)
if report["failed"]:
    print("FAILED_CHECKS", [k for k, v in checks.items() if not v])
    raise SystemExit(1)
