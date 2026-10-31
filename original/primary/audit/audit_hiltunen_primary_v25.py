"""Source04 primary-paper partial numerical audit. No physical validation claim."""
from pathlib import Path
import csv
import hashlib
import json
import re
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "sources/papers/04_Hiltunen_Espoo_2020.pdf"
TRACE_IN = ROOT / "audit/literature_traceability_v23.csv"
TRACE_OUT = ROOT / "audit/literature_traceability_v25.csv"
EVIDENCE = ROOT / "audit/evidence_source04_v25/source04_primary_checks_v25.json"
STATUS = ROOT / "STATUS_v25.json"
BOARD = ROOT / "MASTER_STAGEBOARD_v25.md"
NOTES = ROOT / "audit/run_notes_v25.md"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
checks = []
def ck(label, got, expected, pdf_page):
    passed = got == expected
    checks.append({"name": label, "passed": passed, "observed": got,
                   "expected": expected, "pdf_page": pdf_page})
    return passed
def nums_between(text, start, end):
    block = text.split(start, 1)[1].split(end, 1)[0]
    return [float(x.replace("−", "-")) for x in
            re.findall(r"[−-]?\d+(?:\.\d+)?", block)]
def emit_new(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="") as f:
        f.write(content)

with pymupdf.open(PDF) as doc:
    pages = [p.get_text() for p in doc]
ck("publisher reprint has 22 PDF pages", len(pages), 22, 1)
ck("DOI publisher cover", "10.3390/en13143551" in pages[0], True, 1)
ck("title publisher cover", "Highly Renewable District Heat for Espoo Utilizing Waste Heat Sources" in pages[0], True, 1)
p7, p8, p9 = pages[6], pages[7], pages[8]
temps = nums_between(p8, "Outdoor Temperature", "Supply (€/MWh)")
supply = nums_between(p8, "Supply (€/MWh)", "Return (€/MWh)")
ret = nums_between(p8, "Return (€/MWh)", "An energy company")
expected_t = [-20,-16,-12,-10,-8,-6,-4,-2,0,2,4,6,8,10,12,16,20]
expected_s = [50,50,50,50,50,45,45,40,30,30,30,25,20,20,20,20,15]
expected_r = [35,35,35,35,35,32,32,28,21,21,21,18,14,10,10,10,8]
for i, (t, s, r) in enumerate(zip(temps, supply, ret)):
    ck(f"Table2 temperature row {i+1}", t, expected_t[i], 8)
    ck(f"Table2 supply price row {i+1}", s, expected_s[i], 8)
    ck(f"Table2 return price row {i+1}", r, expected_r[i], 8)
    ck(f"Table2 supply >= return row {i+1}", s >= r, True, 8)
ck("Table2 exactly 17 rows in each column", [len(temps),len(supply),len(ret)], [17,17,17], 8)
ck("Table2 supply nonincreasing vs outdoor temp", all(a>=b for a,b in zip(supply,supply[1:])), True, 8)
ck("Table2 return nonincreasing vs outdoor temp", all(a>=b for a,b in zip(ret,ret[1:])), True, 8)
ck("Figure3 condenser 10 MW", bool(re.search(r"DH\s*10 MW", p7)), True, 7)
ck("Figure3 source 7.2 MW", "Heat 7.2 MW" in p7, True, 7)
ck("Figure3 electricity 2.8 MW", "Electricity 2.8 MW" in p7, True, 7)
ck("Figure3 heat balance", abs(10-7.2-2.8)<1e-12, True, 7)
ck("Figure3 implied COP", round(10/2.8, 8), round(25/7, 8), 7)
ck("WWHP design COP 3.7", "Design\n3.7" in p8, True, 8)
ck("hourly EnergyPRO time step", "step was one hour" in pages[4], True, 5)
ck("TES 20000 m3", "20,000 m3 hot water thermal storage" in p9, True, 9)
ck("TES 857.5 MWh", "857.5 MWh" in p9, True, 9)
ck("TES and network losses neglected",
   "Heat losses for the storage or the network were not considered." in p9, True, 9)
for scenario, price in (("A", "29.36"), ("B", "54"), ("C", "77")):
    ck(f"Table3 scenario {scenario} €/MWh",
       bool(re.search(r"Scenario "+scenario+r" \[\d+\]\s*"+price+r"(?!\d)", p9)), True, 9)
with TRACE_IN.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    columns = reader.fieldnames
    rows = list(reader)
ck("exactly 31 distinct source IDs", len(rows)==31 and
   {int(r["id"]) for r in rows}==set(range(1,32)), True, None)
source04 = next(r for r in rows if r["id"]=="4")
ck("trace DOI agrees with primary", source04["candidate_doi"], "10.3390/en13143551", 1)
ck("zero full source signoffs", sum(r["fully_signed_off"]=="YES" for r in rows), 0, None)
failed = [x for x in checks if not x["passed"]]
if failed:
    print(json.dumps({"passed":len(checks)-len(failed),"failed":failed},ensure_ascii=False,indent=2))
    raise SystemExit("Primary check failed; no signoff files written")
source04["review_level"] = "PARTIAL_PRIMARY_NUMERIC_AUDIT_NOT_SIGNED_OFF"
source04["equations_transcribed"] = "PARTIAL"
source04["blockers"] += (" | v25: PDF p7 Figure3 10=7.2+2.8 MW;"
    " p8 Table2 all 17 temperature/supply/return price rows checked;"
    " p9 Table3 three average electricity prices and 20000 m3/857.5 MWh TES checked;"
    " original paper assumes zero TES/network standing loss;"
    " upstream [6],[15],[25],[29]-[34] and EnergyPRO reproduction unverified")
TRACE_OUT.parent.mkdir(parents=True, exist_ok=True)
with TRACE_OUT.open("x", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)
report = {
    "version": "v25", "source_id": 4,
    "paper": "Hiltunen & Syri (2020), Energies 13(14), 3551",
    "doi": "10.3390/en13143551", "pdf_sha256": sha(PDF),
    "pdf_page_to_printed": {"5":4,"7":6,"8":7,"9":8},
    "kind": "partial agreement with accessible original, NOT paper replication",
    "test_pass": len(checks), "test_fail": 0,
    "checks": checks,
    "table2": [{"ambient_C":t,"supply_EUR_per_MWh":s,
                "return_EUR_per_MWh":r} for t,s,r in zip(temps,supply,ret)],
    "figure3": {"Q_condenser_MW":10.0,"Q_evaporator_MW":7.2,
                "W_electric_MW":2.8,"implied_COP":10/2.8},
    "storage": {"volume_m3":20000,"energy_MWh":857.5,
                "standing_and_network_losses_in_paper":"excluded"},
    "caveat": "Source04 does not validate nonzero TES standing loss in v16; upstream [6] and EnergyPRO remain unverified",
    "full_source_signoffs": 0, "independent_physical_validation": "NOT_TESTED",
    "traceability_sha256": sha(TRACE_OUT), "test_script_sha256": sha(Path(__file__))
}
emit_new(EVIDENCE, json.dumps(report,ensure_ascii=False,indent=2)+"\n")
note = """# v25: Hiltunen & Syri (2020), original numerical audit (PARTIAL)
Original: sources/papers/04_Hiltunen_Espoo_2020.pdf, DOI 10.3390/en13143551.
Figure 3, PDF p7 (printed p6): 10 MW DH = 7.2 MW recovered + 2.8 MW electric, COP=3.57142857; not the Table1 WWHP design COP 3.7.
Table 2, PDF p8 (printed p7): 17 temperatures, 17 supply and 17 return prices in EUR/MWh checked against transcription.
Table 3, PDF p9 (printed p8): electricity scenarios A=29.36, B=54, C=77 EUR/MWh.
TES, PDF p9: 20,000 m3 and 857.5 MWh; paper explicitly neglects storage and network losses. Our v16 nonzero loss is a separate assumption, NOT validated by this paper.
No upstream Fortum tariff [6], HP source [15],[29], electricity scenarios [30]-[34], hourly data or EnergyPRO dispatch independently replicated. Full signoffs 0/31, no independent physical validation.
Reproduction: run audit/audit_hiltunen_primary_v25.py on a fresh project copy without v25 outputs; script refuses overwrite.
"""
emit_new(NOTES, note)
board = f"""# v25 Research checkpoint: source04 numerical original audit
{len(checks)}/{len(checks)} checks PASS: Table2 17 temperatures and 34 tariff prices; Figure3 10=7.2+2.8 MW; Table3 three scenarios; TES 20,000 m3 / 857.5 MWh; zero storage/network losses.
Source04 remains PARTIAL. Full primary signoffs 0/31. Source agreement does not prove physical validation.
Evidence: audit/evidence_source04_v25/source04_primary_checks_v25.json; audit/literature_traceability_v25.csv; audit/audit_hiltunen_primary_v25.py.
Next: independent verification, then original tariff [6]. v22/v24 Stateflow remains separate.
"""
emit_new(BOARD, board)
status = {"version":"0.25","research_inherits":"STATUS_v23.json",
          "checkpoint":"source04 Hiltunen 2020 partial original numerical audit",
          "source04_checks_passed":len(checks),"source04_checks_failed":0,
          "source04_review":"PARTIAL_NOT_SIGNED_OFF",
          "full_primary_signoffs":0,"total_sources":31,
          "independent_physical_validation":"NOT_TESTED",
          "primary_paper_replication":False}
status['pdf_sha256'] = sha(PDF)
status['evidence_sha256'] = sha(EVIDENCE)
status['traceability_sha256'] = sha(TRACE_OUT)
status['next'] = 'independent v25 verification, then original tariff [6]'
emit_new(STATUS,json.dumps(status,ensure_ascii=False,indent=2)+'\n')
print('SOURCE04_V25_PASS',len(checks), 'SHA256', sha(EVIDENCE))
