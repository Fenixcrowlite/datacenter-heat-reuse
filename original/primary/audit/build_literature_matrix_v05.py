"""Traceability tracker: separate existence, article-level extraction, and numerical verification."""
from pathlib import Path
import re,csv
root=Path(__file__).resolve().parents[1]
text=(root/"sources"/"source_catalog.md").read_text(encoding="utf-8")
cols=["id","reference_and_title","role_from_original_catalog","primary_url_or_doi","source_access",
      "full_text_read_and_equations_transcribed","parameter_attribution_verified","numerical_replication","next_action"]
urls={
1:"https://doi.org/10.1016/j.energy.2017.08.078",
17:"https://doi.org/10.54337/ijsepm.8149",
20:"https://doi.org/10.3390/en19030800",
21:"https://doi.org/10.1016/j.rser.2013.12.007"
}
paper= root/"sources"/"papers"/"17_Jurgens_Frankfurt_2024.extracted.txt"
rows=[]
for line in text.splitlines():
    m=re.match(r"^(\d{1,2})\.\s+(.*)",line.strip())
    if not m:continue
    num=int(m.group(1))
    if not 1<=num<=31:continue
    val=m.group(2)
    ital=re.findall(r"\*\*([^*]+)\*\*",val)
    status="Catalog entry only; primary full text not examined"
    if num==1:status="Publisher metadata and abstract verified; full PDF pending"
    if num==17:status="Publisher abstract verified; full PDF "+("available for equation audit" if paper.exists() else "pending download")
    if num==20:status="Publisher abstract verified; exact methods/equations pending"
    rows.append({"id":num,"reference_and_title":re.sub(r"\*","",val),
         "role_from_original_catalog":ital[-1] if ital else "",
         "primary_url_or_doi":urls.get(num,"Find DOI or official original in cited document"),
         "source_access":status,
         "full_text_read_and_equations_transcribed":"NO",
         "parameter_attribution_verified":"NO",
         "numerical_replication":"NO",
         "next_action":"Read original paper; extract equation numbers, inputs, assumptions, units and reusable model block"})
rows.sort(key=lambda x:x["id"])
if len(rows)!=31:raise ValueError(f"Expected 31 source entries; found {len(rows)}")
out=Path(__file__).with_name("literature_traceability_v05.csv")
with out.open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)
print("CREATED",out,"sources",len(rows))
