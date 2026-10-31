"""A66: standalone, mobile-friendly A63+A64 reviewer with strict cross-source gate."""
from __future__ import annotations
from pathlib import Path
import hashlib, json
from decimal import Decimal

HERE=Path(__file__).resolve().parent
RECOVERY=HERE.parent
A63=RECOVERY/"AUTONOMOUS_RUN_20261027_1450_A63_OFFLINE_SCADA_BALANCE_VIEW"/"OUTPUT"/"dashboard.html"
A64=RECOVERY/"AUTONOMOUS_RUN_20261027_1550_A64_INTEGRATION_RECONCILIATION"/"OUTPUT"/"comparison.json"
OUT=HERE/"unified_review.html"
CHANNELS=("Q_DC_W","Q_pool_W","Q_DH_W","P_HP_W","Q_reject_W")
LABELS={"Q_DC_W":"Teplo z dátového centra","Q_pool_W":"Teplo do bazéna","Q_DH_W":"Teplo do centrálnej sústavy","P_HP_W":"Elektrina tepelného čerpadla","Q_reject_W":"Odvedené teplo REJECT"}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load():
    html=A63.read_text(encoding="utf-8")
    start='<script type="application/json" id="payload">'
    end="</script>"
    assert html.count(start)==1
    payload=json.loads(html.split(start,1)[1].split(end,1)[0])
    cmp=json.loads(A64.read_text(encoding="utf-8"))
    if cmp.get("schema")!="a64.1" or set(cmp["scenarios"])!={"V08","V09"}:
        raise ValueError("INVALID_A64_SCHEMA")
    if set(payload["metrics"])!={"v08","v09"}:
        raise ValueError("INVALID_A63_SCHEMA")
    for key in ("v08","v09"):
        a=cmp["scenarios"][key.upper()]
        m=payload["metrics"][key]
        if (a["source_kind"]!="derived_simulation" or a["physical_release"] is not False
            or m["source_kind"]!="derived_simulation" or m["physical_release"] is not False):
            raise ValueError("PHYSICAL_PROVENANCE_GATE")
        if a["a62_csv_sha256"]!=m["source_csv_sha256"] or a["a62_summary_sha256"]!=m["source_meta_sha256"]:
            raise ValueError("SOURCE_HASH_MISMATCH")
        if a["samples"]!=m["rows"] or len(payload["series"][key]["rows"])!=672:
            raise ValueError("ROW_MISMATCH")
        if Decimal(str(m["input_MWh"]))-Decimal(a["channels"]["Q_pool_W"]["discrete_MWh"])>Decimal("0.000000001") or abs(Decimal(str(m["input_MWh"]))-Decimal(a["channels"]["Q_pool_W"]["discrete_MWh"]))>Decimal("0.000000001"):
            raise ValueError("POOL_ENERGY_MISMATCH")
        if Decimal(a["discrete_duration_h"])!=168 or Decimal(a["time_span_h"])!=Decimal("167.75"):
            raise ValueError("TIMEBASE_MISMATCH")
        if set(a["channels"])!=set(CHANNELS):
            raise ValueError("CHANNEL_SET_MISMATCH")
        for name in CHANNELS:
            c=a["channels"][name]
            d=Decimal(c["discrete_MWh"])*1000-Decimal(c["trapezoid_MWh"])*1000
            correction=Decimal(c["terminal_rectangle_kWh"])+Decimal(c["sample_slope_correction_kWh"])
            if abs(d-Decimal(c["discrete_minus_trapezoid_kWh"]))>Decimal("0.000000001") or abs(d-correction)>Decimal("0.000000001"):
                raise ValueError("INTEGRATION_IDENTITY_FAILED:"+name)
    return html,cmp

CSS="""
<style id="a66-style">
.a66-panel{margin-top:18px;background:#141d32;border:1px solid #33435d;border-radius:12px;padding:16px;min-width:0}
.a66-panel p{line-height:1.55;color:#c1cee0}
.a66-table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
.a66-table th,.a66-table td{padding:10px 8px;text-align:right;border-bottom:1px solid #33435d}
.a66-table th:first-child,.a66-table td:first-child{text-align:left}
.a66-table th{color:#dbeafe}
.a66-note{overflow-wrap:anywhere}
@media(max-width:650px){
 .a66-table thead{display:none}
 .a66-table,.a66-table tbody,.a66-table tr,.a66-table td{display:block;width:100%}
 .a66-table tr{border:1px solid #33435d;border-radius:9px;margin:10px 0;padding:6px;max-width:100%;overflow:hidden}
 .a66-table td{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:8px;text-align:right;border:0;overflow-wrap:anywhere}
 .a66-table td::before{content:attr(data-label);text-align:left;color:#c1cee0}
 .a66-table td:first-child{font-weight:700}
}
</style>
"""
SECTION="""
<section class="a66-panel" id="integration-panel" aria-label="Porovnanie metód integrácie">
<h2>Porovnanie integrácie A60 / A62</h2>
<p>Rovnaké syntetické vzorky, odlišný časový interval: A60 používa 671 lichobežníkov (167,75 h), A62 používa 672 diskrétnych krokov (168 h). Rozdiel nie je chyba energetickej bilancie.</p>
<table class="a66-table"><thead><tr><th scope="col">Kanál</th><th scope="col">A60 [MWh]</th><th scope="col">A62 [MWh]</th><th scope="col">Rozdiel [kWh]</th><th scope="col">Posledný krok [kWh]</th><th scope="col">Korekcia sklonu [kWh]</th></tr></thead><tbody id="integration-rows"></tbody></table>
<p id="integration-identity" class="a66-note" aria-live="polite"></p>
<p class="a66-note">DERIVED SIMULATION · bez kalibrovaných meraní, bez potvrdenia fyzickej bezpečnosti. Hodnoty pochádzajú z A64 a sú prepojené s grafmi A63 kontrolou SHA256 vstupov.</p>
</section>
"""
JS="""
<script id="a66-script">
"use strict";
const INTEGRATION=JSON.parse(document.getElementById("a66-payload").textContent);
const integrationNames={"Q_DC_W":"Teplo z dátového centra","Q_pool_W":"Teplo do bazéna","Q_DH_W":"Teplo do centrálnej sústavy","P_HP_W":"Elektrina tepelného čerpadla","Q_reject_W":"Odvedené teplo REJECT"};
const integrationOrder=["Q_DC_W","Q_pool_W","Q_DH_W","P_HP_W","Q_reject_W"];
const integrationColumns=[["Kanál",null],["A60 [MWh]","trapezoid_MWh"],["A62 [MWh]","discrete_MWh"],["Rozdiel [kWh]","discrete_minus_trapezoid_kWh"],["Posledný krok [kWh]","terminal_rectangle_kWh"],["Korekcia sklonu [kWh]","sample_slope_correction_kWh"]];
function renderIntegration(){
 const scenario=document.getElementById("scenario").value.toUpperCase();
 const a=INTEGRATION.scenarios[scenario],tbody=document.getElementById("integration-rows");
 tbody.replaceChildren();
 for(const channel of integrationOrder){
  const row=document.createElement("tr");
  for(const [label,key] of integrationColumns){
   const cell=document.createElement("td");
   cell.setAttribute("data-label",label);
   cell.textContent=key===null?integrationNames[channel]:Number(a.channels[channel][key]).toLocaleString("sk-SK",{minimumFractionDigits:3,maximumFractionDigits:6});
   row.append(cell);
  }
  tbody.append(row);
 }
 document.getElementById("integration-identity").textContent="Kontrola: rozdiel = posledný krok + korekcia sklonu. Časová os "+a.time_span_h+" h, diskrétna simulácia "+a.discrete_duration_h+" h. Zdroj: A64 / "+scenario+".";
}
document.getElementById("scenario").addEventListener("change",renderIntegration);
renderIntegration();
</script>
"""
def build():
    html,comparison=load()
    if OUT.exists():
        raise FileExistsError("OUTPUT_IMMUTABLE")
    assert html.count("</head>")==1 and html.count('<div class="info">')==1 and html.count("</body>")==1
    data=json.dumps(comparison,ensure_ascii=False,separators=(",",":"),allow_nan=False).replace("<","\\u003c")
    html=html.replace("</head>",CSS+"</head>")
    html=html.replace('<div class="info">',SECTION+'<div class="info">',1)
    html=html.replace("</body>",'<script type="application/json" id="a66-payload">'+data+'</script>'+JS+"</body>")
    OUT.write_text(html,encoding="utf-8")
    return {"html":str(OUT),"bytes":OUT.stat().st_size,"a63_sha256":sha(A63),"a64_sha256":sha(A64),"output_sha256":sha(OUT),"source_kind":"derived_simulation","physical_release":False}
if __name__=="__main__":
    print(json.dumps(build(),ensure_ascii=False))
