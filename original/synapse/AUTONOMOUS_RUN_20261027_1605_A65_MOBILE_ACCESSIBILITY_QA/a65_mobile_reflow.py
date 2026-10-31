"""A65: non-destructive mobile reflow of the verified A64 offline report."""
import hashlib
import json
from pathlib import Path
import re
D=Path(__file__).resolve().parent
SRC=D.parent/"AUTONOMOUS_RUN_20261027_1550_A64_INTEGRATION_RECONCILIATION"/"OUTPUT"/"comparison.html"
OUT=D/"mobile_comparison.html"
LABELS=("Kanál","A60 [MWh]","A62 [MWh]","A62 − A60 [kWh]","Posledný krok [kWh]","Korekcia sklonu [kWh]")
STYLE="""<style>
@media (max-width:700px) {
 body {padding:12px;max-width:100%;overflow-wrap:anywhere}
 h1 {font-size:1.6rem}
 table,thead,tbody,tr,td {display:block;width:auto}
 thead {position:absolute;clip:rect(0,0,0,0);height:1px;overflow:hidden}
 table {border:0;margin:12px 0}
 tbody tr {background:#1b2940;border:1px solid #60718c;border-radius:10px;padding:8px;margin-bottom:14px}
 tbody td {border:0;border-bottom:1px solid #42516c;text-align:left;padding:8px 10px;overflow-wrap:anywhere}
 tbody td:last-child {border-bottom:0}
 tbody td::before {content:attr(data-label);display:block;color:#7fe6da;font-size:.82rem;font-weight:bold;margin-bottom:3px}
 .bar {max-width:55%}
}
</style>"""
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def transform(source):
    if source.count("<table>")!=2 or source.count("<tbody>")!=2:
        raise ValueError("UNEXPECTED_TABLE_LAYOUT")
    count=[0]
    def row_replace(m):
        cells=re.findall(r"<td>(.*?)</td>",m.group(0),re.DOTALL)
        if len(cells)!=len(LABELS):raise ValueError("UNEXPECTED_CELL_COUNT")
        count[0]+=1
        return "<tr>"+ "".join(f'<td data-label="{label}">{value}</td>' for label,value in zip(LABELS,cells))+"</tr>"
    out=re.sub(r"<tr><td>.*?</tr>",row_replace,source)
    if count[0]!=10:raise ValueError("UNEXPECTED_ROW_COUNT")
    if "</style>" not in out:raise ValueError("MISSING_STYLESHEET")
    out=out.replace("</style>","</style>\n"+STYLE,1)
    return out
def main():
    source=SRC.read_text(encoding="utf-8")
    html=transform(source)
    if OUT.exists() and OUT.read_text(encoding="utf-8")!=html:raise RuntimeError("IMMUTABLE_CONFLICT")
    OUT.write_text(html,encoding="utf-8")
    info={"original_sha256":sha(SRC),"mobile_sha256":sha(OUT),
          "source_kind":"derived_simulation","physical_release":False,"rows":10}
    (D/"A65_TRANSFORM_REPORT.json").write_text(json.dumps(info,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(info))
if __name__=="__main__":main()
