"""A63: self-contained offline SCADA energy dashboard from immutable A62 simulation exports."""
from __future__ import annotations
import argparse
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import tempfile

FIELDS = ("time_s", "T_pool_C", "Q_pool_W", "Q_pool_loss_W", "Q_pool_net_W",
          "E_pool_input_cum_J", "E_pool_signed_loss_cum_J",
          "E_pool_stored_cum_J", "state_residual_W")
SOURCE_NAMES = ("OUTPUT_V08_SIGNED", "OUTPUT_V09_SIGNED")
STEP = Decimal("900")
J_PER_MWH = Decimal("3600000000")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decimal(row: dict, key: str) -> Decimal:
    try:
        v = Decimal(row[key])
        if not v.is_finite():
            raise ValueError("NONFINITE:" + key)
        return v
    except (KeyError, InvalidOperation, TypeError) as exc:
        raise ValueError("INVALID_NUMERIC:" + key) from exc


def read_one(folder: Path) -> tuple[dict, dict]:
    meta_path = folder / "summary.json"
    data_path = folder / "analysis_with_signed_losses.csv"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if (meta.get("schema_version") != "a62.1"
            or meta.get("source_kind") != "derived_simulation"
            or meta.get("physical_release") is not False
            or meta.get("calibration_ready") is not False
            or meta.get("records") != 672
            or Decimal(str(meta.get("step_seconds"))) != STEP
            or meta.get("analysis_with_signed_losses_sha256") != sha(data_path)):
        raise ValueError("PROVENANCE_GATE_FAILED:" + folder.name)
    heat_capacity = Decimal(str(meta["pool_heat_capacity_J_per_K"]))
    initial_T = Decimal(str(meta["initial_T_C"]))
    if heat_capacity <= 0:
        raise ValueError("INVALID_HEAT_CAPACITY")
    with data_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, strict=True)
        names = reader.fieldnames or []
        if len(names) != len(set(names)) or not set(FIELDS).issubset(names):
            raise ValueError("INVALID_COLUMNS")
        rows = list(reader)
    if len(rows) != meta["records"]:
        raise ValueError("INVALID_ROW_COUNT")
    ein = eloss = Decimal(0)
    negative_count = 0
    gain_J = Decimal(0)
    max_residual = Decimal(0)
    last_T = initial_T
    plot = []
    for idx, row in enumerate(rows):
        v = {key: decimal(row, key) for key in FIELDS}
        if v["time_s"] != STEP * idx:
            raise ValueError("INVALID_TIMEBASE:" + str(idx))
        ein += v["Q_pool_W"] * STEP
        eloss += v["Q_pool_loss_W"] * STEP
        stored = heat_capacity * (v["T_pool_C"] - initial_T)
        state_residual = heat_capacity * (v["T_pool_C"] - last_T) / STEP - v["Q_pool_net_W"]
        last_T = v["T_pool_C"]
        if (abs(v["Q_pool_net_W"] - v["Q_pool_W"] + v["Q_pool_loss_W"]) > Decimal("0.001")
                or abs(ein - v["E_pool_input_cum_J"]) > Decimal("0.1")
                or abs(eloss - v["E_pool_signed_loss_cum_J"]) > Decimal("0.1")
                or abs(stored - v["E_pool_stored_cum_J"]) > Decimal("0.1")
                or abs(state_residual) > Decimal("0.001")
                or abs(v["state_residual_W"] - state_residual) > Decimal("0.001")):
            raise ValueError("ENERGY_CLOSURE_FAILED:" + str(idx))
        max_residual = max(max_residual, abs(state_residual))
        if v["Q_pool_loss_W"] < 0:
            negative_count += 1
            gain_J -= v["Q_pool_loss_W"] * STEP
        plot.append([float(v[k]) for k in FIELDS])
    if abs(ein - eloss - stored) > Decimal("0.1"):
        raise ValueError("TOTAL_CLOSURE_FAILED")
    metrics = {
        "rows": len(rows), "duration_discrete_h": float(len(rows) * STEP / 3600),
        "timestamp_span_h": float((len(rows) - 1) * STEP / 3600),
        "input_MWh": float(ein / J_PER_MWH),
        "signed_loss_MWh": float(eloss / J_PER_MWH),
        "stored_MWh": float(stored / J_PER_MWH),
        "ambient_gain_MWh": float(gain_J / J_PER_MWH),
        "negative_loss_rows": negative_count,
        "max_residual_W": float(max_residual),
        "final_temperature_C": float(last_T),
        "closure_J": float(ein - eloss - stored),
        "source_schema": meta["source_schema"],
        "source_csv_sha256": sha(data_path),
        "source_meta_sha256": sha(meta_path),
        "source_kind": "derived_simulation", "physical_release": False,
    }
    return metrics, {"columns": FIELDS, "rows": plot}


HTML = r"""<!doctype html>
<html lang="sk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>DataCenter | Offline energetická bilancia A63</title>
<style>
:root{color-scheme:dark;--bg:#0b1020;--panel:#141d32;--edge:#33435d;--fg:#e7f0fa;--muted:#9fb1ca;--blue:#60a5fa;--orange:#f59e0b;--green:#34d399}
*{box-sizing:border-box}body{background:var(--bg);color:var(--fg);font:16px system-ui,Arial,sans-serif;max-width:1250px;margin:0 auto;padding:24px}
h1{font-size:clamp(1.5rem,3vw,2.3rem);margin:0 0 8px}.sub{color:var(--muted);line-height:1.6}
.banner{border:2px solid var(--orange);background:#332311;color:#ffdd9b;padding:13px 16px;border-radius:10px;margin:18px 0;font-weight:700}
.toolbar{display:flex;gap:16px;align-items:center;flex-wrap:wrap;margin:22px 0}select{background:var(--panel);color:var(--fg);padding:10px 14px;border:1px solid var(--edge);border-radius:8px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:12px}
.card,.plot,.info{background:var(--panel);border:1px solid var(--edge);border-radius:12px;padding:16px}
.card strong{display:block;font-size:1.35rem;margin-top:7px}.card small{color:var(--muted)}
.plot{margin-top:18px}h2{font-size:1.1rem;margin:0 0 8px}.plot svg{width:100%;height:230px;display:block}
.legend{color:var(--muted);font-size:.86rem}.info{margin-top:18px;color:var(--muted);overflow-wrap:anywhere}
#hover{min-height:1.5em;color:var(--fg);font-variant-numeric:tabular-nums}a{color:var(--blue)}
@media(max-width:600px){body{padding:12px}.plot svg{height:190px}}
</style></head><body>
<h1>Energetická bilancia bazéna</h1>
<p class="sub">DataCenter Heat Reuse · A63 · samostatná offline analytická stránka. Dáta A62, 672 krokov po 900 s.</p>
<div class="banner">SIMULÁCIA / DERIVED · NIE SÚ TO MERANIA · ŽIADNE POTVRDENIE FYZICKEJ BEZPEČNOSTI</div>
<div class="toolbar"><label for="scenario">Verzia modelu:</label><select id="scenario"><option value="v08">SCADA v08</option><option value="v09">MATLAB v09</option></select><span id="status" class="sub"></span></div>
<section class="cards" id="cards" aria-label="Energetické ukazovatele"></section>
<div class="plot"><h2>Teplota bazéna</h2><div class="legend">T_pool [°C] · čas [h]</div><svg id="temp" role="img" aria-label="Priebeh teploty bazéna"></svg></div>
<div class="plot"><h2>Tepelné toky</h2><div class="legend">Q_pool (modrá), Q_pool_loss so znamienkom (oranžová), Q_pool_net (zelená) [kW]; záporná strata = zisk z okolia.</div><svg id="flows" role="img" aria-label="Priebeh tepelných tokov"></svg></div>
<div class="plot"><h2>Kumulatívna energia</h2><div class="legend">Vstup (modrá), podpísané straty (oranžová), akumulácia (zelená) [MWh]. Diskrétne aktualizácie 168 h, časové značky pokrývajú 167,75 h.</div><svg id="energy" role="img" aria-label="Priebeh kumulatívnej energie"></svg></div>
<div class="info"><div id="hover">Presuňte kurzor nad graf a zobrazí sa najbližší časový bod.</div><p>Zdroj: výhradne lokálne overené CSV A62. Nevykonávajú sa žiadne sieťové požiadavky, nenačítavajú sa externé knižnice. Číselné hodnoty sú syntetické. Rezíduum je numerická kontrola modelu, nie dôkaz zhody s reálnym zariadením.</p><div id="provenance"></div></div>
<script type="application/json" id="payload">__DATA__</script>
<script>
"use strict";
const DATA=JSON.parse(document.getElementById("payload").textContent);
const NS="http://www.w3.org/2000/svg";
const colors=["#60a5fa","#f59e0b","#34d399"];
function elem(tag,attrs){const e=document.createElementNS(NS,tag);for(const [k,v] of Object.entries(attrs||{}))e.setAttribute(k,String(v));return e;}
function fmt(x,d=3){return Number(x).toLocaleString("sk-SK",{maximumFractionDigits:d,minimumFractionDigits:d});}
function card(label,val,unit){const e=document.createElement("div");e.className="card";const s=document.createElement("small");s.textContent=label;const b=document.createElement("strong");b.textContent=fmt(val)+" "+unit;e.append(s,b);return e;}
function chart(id,rows,indices,scale,labels){
 const svg=document.getElementById(id);svg.replaceChildren();const W=1100,H=225,L=66,R=16,T=16,B=34;
 const values=rows.flatMap(r=>indices.map(i=>r[i]*scale));let lo=Math.min(...values),hi=Math.max(...values);
 if(lo===hi){lo-=1;hi+=1;}const pad=(hi-lo)*.07;lo-=pad;hi+=pad;
 const x=i=>L+(W-L-R)*i/(rows.length-1),y=v=>H-B-(v-lo)/(hi-lo)*(H-T-B);
 svg.setAttribute("viewBox","0 0 "+W+" "+H);
 for(let i=0;i<5;i++){const v=lo+(hi-lo)*i/4;const yy=y(v);
 svg.append(elem("line",{x1:L,y1:yy,x2:W-R,y2:yy,stroke:"#34435a","stroke-width":1}));
 const t=elem("text",{x:5,y:yy+4,fill:"#b6c5d8","font-size":14});t.textContent=fmt(v,1);svg.append(t);}
 for(let i=0;i<=4;i++){const t=elem("text",{x:x((rows.length-1)*i/4),y:H-8,fill:"#b6c5d8","font-size":14,"text-anchor":"middle"});t.textContent=fmt(rows[rows.length-1][0]/3600*i/4,1)+"h";svg.append(t);}
 indices.forEach((idx,j)=>{const pts=rows.map((r,i)=>x(i).toFixed(2)+","+y(r[idx]*scale).toFixed(2)).join(" ");svg.append(elem("polyline",{points:pts,fill:"none",stroke:colors[j],"stroke-width":2.3,"vector-effect":"non-scaling-stroke"}));});
 if(lo<0&&hi>0)svg.append(elem("line",{x1:L,y1:y(0),x2:W-R,y2:y(0),stroke:"#e5e7eb","stroke-dasharray":"6 5",opacity:.7}));
 const cursor=elem("line",{x1:L,y1:T,x2:L,y2:H-B,stroke:"#fff","stroke-dasharray":"3 4",opacity:0});svg.append(cursor);
 svg.addEventListener("pointermove",ev=>{const rect=svg.getBoundingClientRect();const pos=(ev.clientX-rect.left)/rect.width*W;const i=Math.max(0,Math.min(rows.length-1,Math.round((pos-L)/(W-L-R)*(rows.length-1))));cursor.setAttribute("x1",x(i));cursor.setAttribute("x2",x(i));cursor.setAttribute("opacity",1);document.getElementById("hover").textContent="t="+fmt(rows[i][0]/3600,2)+" h | "+labels.map((name,j)=>name+": "+fmt(rows[i][indices[j]]*scale,3)).join(" | ");});
 svg.addEventListener("pointerleave",()=>cursor.setAttribute("opacity",0));
}
function render(){const key=document.getElementById("scenario").value,m=DATA.metrics[key],r=DATA.series[key].rows;
 const cards=document.getElementById("cards");cards.replaceChildren(
 card("Teplo do bazéna",m.input_MWh,"MWh"),card("Podpísané straty",m.signed_loss_MWh,"MWh"),
 card("Akumulovaná energia",m.stored_MWh,"MWh"),card("Zisk z okolia",m.ambient_gain_MWh,"MWh"),
 card("Konečná teplota",m.final_temperature_C,"°C"),card("Max. rezíduum",m.max_residual_W,"W"));
 document.getElementById("status").textContent=m.negative_loss_rows+" intervalov so ziskom z okolia";
 chart("temp",r,[1],1,["T_pool °C"]);chart("flows",r,[2,3,4],.001,["Q_pool kW","Q_loss kW","Q_net kW"]);
 chart("energy",r,[5,6,7],1/3600000000,["Vstup MWh","Straty MWh","Akumulácia MWh"]);
 document.getElementById("provenance").textContent="CSV SHA256: "+m.source_csv_sha256+" | uzáver bilancie: "+fmt(m.closure_J,7)+" J | source_kind=derived_simulation | physical_release=false";
}
document.getElementById("scenario").addEventListener("change",render);render();
</script></body></html>
"""


def build(a62_dir: Path, output: Path) -> dict:
    a62_dir, output = Path(a62_dir), Path(output)
    if output.exists() or output.is_symlink():
        raise ValueError("DESTINATION_EXISTS")
    if not output.parent.is_dir():
        raise ValueError("DESTINATION_PARENT_MISSING")
    metrics, series = {}, {}
    for key, folder_name in (("v08", SOURCE_NAMES[0]), ("v09", SOURCE_NAMES[1])):
        metrics[key], series[key] = read_one(a62_dir / folder_name)
    payload = {"metrics": metrics, "series": series}
    raw_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False).replace("<", "\\u003c")
    html = HTML.replace("__DATA__", raw_json)
    stage = Path(tempfile.mkdtemp(prefix=".a63-stage-", dir=output.parent))
    try:
        (stage / "dashboard.html").write_text(html, encoding="utf-8")
        (stage / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True)+"\n", encoding="utf-8")
        (stage / "sources.json").write_text(json.dumps({"source_kind":"derived_simulation",
          "physical_release":False,"source_folder":str(a62_dir),"a62_scenarios":list(SOURCE_NAMES)},
          indent=2,sort_keys=True)+"\n",encoding="utf-8")
        os.rename(stage, output)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return metrics


def main():
    p = argparse.ArgumentParser()
    p.add_argument("a62_directory", type=Path)
    p.add_argument("new_output_directory", type=Path)
    args = p.parse_args()
    result = build(args.a62_directory, args.new_output_directory)
    print(json.dumps({"rows_per_scenario":result["v08"]["rows"],
        "v08_stored_MWh":result["v08"]["stored_MWh"],
        "v09_stored_MWh":result["v09"]["stored_MWh"],
        "physical_release":False}))


if __name__ == "__main__":
    main()
