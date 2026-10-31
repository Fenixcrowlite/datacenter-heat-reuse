"""Annotate work already completed without mislabeling other articles as reviewed."""
from pathlib import Path
import csv
p=Path(__file__).with_name("literature_traceability_v05.csv")
with p.open(encoding="utf-8-sig",newline="") as f:
    reader=csv.DictReader(f);fieldnames=reader.fieldnames;rows=list(reader)
for r in rows:
    k=int(r["id"])
    if k==1:
        r["source_access"]="Full primary PDF retrieved from Aalto University repository; 12 PDF pages"
        r["full_text_read_and_equations_transcribed"]="PARTIAL: sections 2–5, EnergyPRO methodology, ERE Eq 1; no full input dataset"
        r["parameter_attribution_verified"]="Selected table 1–4 values and 2013/2015 distinctions crosschecked"
        r["numerical_replication"]="NO: model EnergyPRO/real 2013/2015 hourly inputs not available"
        r["next_action"]="Check ERE unit/boundary and CHP optimization in formal independent module; source audit in Wahlroos_primary_source_audit_v05_RU.md"
    elif k==17:
        r["source_access"]="Full primary PDF downloaded from original journal; 13 PDF pages"
        r["full_text_read_and_equations_transcribed"]="PARTIAL: sections 2–8, Tables 1–3, storage and COP; visually verify LCoH Eq 1"
        r["parameter_attribution_verified"]="YES for major technical published values; original COP 3.76/3.67 discrepancy noted"
        r["numerical_replication"]="NO: previous v0.4 disagrees with 5 primary-source targets"
        r["next_action"]="Build independent 144 sold / 152 production GWh model; see Frankfurt_primary_source_audit_v05_RU.md"
with p.open("w",encoding="utf-8-sig",newline="") as f:
    writer=csv.DictWriter(f,fieldnames=fieldnames);writer.writeheader();writer.writerows(rows)
print("UPDATED",p,"reviewed_primary",[int(r["id"]) for r in rows if r["full_text_read_and_equations_transcribed"]!="NO"])
