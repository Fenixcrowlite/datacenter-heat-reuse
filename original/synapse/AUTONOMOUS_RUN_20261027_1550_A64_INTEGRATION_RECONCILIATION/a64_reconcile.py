"""A64: read-only reconciliation of A60 trapezoid vs A62 discrete integration.
Inputs are DERIVED SIMULATION, not measurements. No upstream writes.
"""
from __future__ import annotations
import csv
from decimal import Decimal, getcontext
import hashlib
import html
import json
from pathlib import Path

getcontext().prec = 45
D = Path(__file__).resolve().parent
R = D.parent
A60 = R / "AUTONOMOUS_RUN_20261027_1250_A60_SCADA_DERIVED_EXPORT"
A62 = R / "AUTONOMOUS_RUN_20261027_1405_A62_SIGNED_LOSS_EXPORT"
FIELDS = ("time_s","T_pool_C","Q_DC_W","Q_reject_W","Q_pool_W","Q_DH_W","P_HP_W","E_TES_J")
POWER = ("Q_DC_W","Q_reject_W","Q_pool_W","Q_DH_W","P_HP_W")
MWH = Decimal("3600000000")

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_csv(path):
    with Path(path).open(encoding="utf-8",newline="") as f:
        rd=csv.DictReader(f)
        if len(rd.fieldnames or []) != len(set(rd.fieldnames or [])):
            raise ValueError("DUPLICATE_COLUMN")
        rows=list(rd)
    if len(rows)<3 or any(None in r or any(v is None for v in r.values()) for r in rows):
        raise ValueError("MALFORMED_ROWS")
    return rows

def dec(row,key):
    try: v=Decimal(row[key])
    except (KeyError,ValueError,ArithmeticError) as exc:
        raise ValueError("INVALID_FIELD_"+key) from exc
    if not v.is_finite(): raise ValueError("NONFINITE_"+key)
    return v

def reconcile(rows60,rows62,dt_expected=Decimal("900")):
    if len(rows60)!=len(rows62): raise ValueError("ROW_COUNT_MISMATCH")
    for a,b in zip(rows60,rows62):
        for key in FIELDS:
            if dec(a,key)!=dec(b,key): raise ValueError("UPSTREAM_COLUMN_MISMATCH_"+key)
    t=[dec(r,"time_s") for r in rows60]
    if t[0]!=0 or any(t[i+1]-t[i]!=dt_expected for i in range(len(t)-1)):
        raise ValueError("NONUNIFORM_OR_INVALID_TIMEBASE")
    n=len(t)
    out={}
    for key in POWER:
        q=[dec(r,key) for r in rows60]
        trapezoid=sum((q[i]+q[i+1])*dt_expected/2 for i in range(n-1))
        discrete=sum(q)*dt_expected
        terminal=q[-1]*dt_expected
        sample_correction=sum((q[i]-q[i+1])*dt_expected/2 for i in range(n-1))
        delta=discrete-trapezoid
        if delta!=terminal+sample_correction: raise ValueError("DECOMPOSITION_FAILED")
        # For constant timestep this telescopes to dt/2 * (first + last).
        if delta!=dt_expected*(q[0]+q[-1])/2: raise ValueError("ENDPOINT_IDENTITY_FAILED")
        out[key]={
            "trapezoid_MWh":str(trapezoid/MWH),
            "discrete_MWh":str(discrete/MWH),
            "discrete_minus_trapezoid_kWh":str(delta/Decimal("3600000")),
            "terminal_rectangle_kWh":str(terminal/Decimal("3600000")),
            "sample_slope_correction_kWh":str(sample_correction/Decimal("3600000")),
            "first_W":str(q[0]),"last_W":str(q[-1])
        }
    stored=dec(rows62[-1],"E_pool_input_cum_J")
    pool_discrete=Decimal(out["Q_pool_W"]["discrete_MWh"])*MWH
    # A62 cumulative field was serialized from binary float; permit sub-joule rounding.
    if abs(stored-pool_discrete)>Decimal("0.01"):
        raise ValueError("A62_CUMULATIVE_ENERGY_MISMATCH")
    return {"samples":n,"time_span_h":str((t[-1]-t[0])/3600),
            "discrete_duration_h":str(n*dt_expected/3600),
            "step_s":str(dt_expected),"channels":out}

def load_verified(version):
    a=A60/f"OUTPUT_{version}_DERIVED"
    b=A62/f"OUTPUT_{version}_SIGNED"
    pa=a/"analysis_timeseries.csv"; pb=b/"analysis_with_signed_losses.csv"
    sa=json.loads((a/"summary.json").read_text(encoding="utf-8"))
    sb=json.loads((b/"summary.json").read_text(encoding="utf-8"))
    if sa.get("source_kind")!="derived_simulation" or sb.get("source_kind")!="derived_simulation":
        raise ValueError("PROVENANCE_MISMATCH")
    if sa.get("physical_release") is not False or sb.get("physical_release") is not False:
        raise ValueError("RELEASE_FLAG_UNEXPECTED")
    if sa["analysis_csv_sha256"]!=sha(pa) or sb["analysis_with_signed_losses_sha256"]!=sha(pb):
        raise ValueError("SOURCE_HASH_MISMATCH")
    if sb["a60_analysis_sha256"]!=sha(pa):
        raise ValueError("CROSS_PROVENANCE_HASH_MISMATCH")
    if sb["a60_summary_sha256"]!=sha(a/"summary.json"):
        raise ValueError("SUMMARY_HASH_MISMATCH")
    result=reconcile(load_csv(pa),load_csv(pb))
    for key,calc in result["channels"].items():
        reported=Decimal(str(sa["metrics"]["integrated_MWh"][key]))
        if abs(reported-Decimal(calc["trapezoid_MWh"]))>Decimal("0.000000001"):
            raise ValueError("A60_SUMMARY_INCONSISTENT_"+key)
    if abs(Decimal(sb["a61_validation"]["E_pool_input_discrete_MWh"])-Decimal(result["channels"]["Q_pool_W"]["discrete_MWh"]))>Decimal("0.000000001"):
        raise ValueError("A62_SUMMARY_INCONSISTENT")
    result.update({"source_kind":"derived_simulation","physical_release":False,
                   "a60_csv_sha256":sha(pa),"a62_csv_sha256":sha(pb),
                   "a60_summary_sha256":sha(a/"summary.json"),
                   "a62_summary_sha256":sha(b/"summary.json")})
    return result

def render(results):
    parts=['<!doctype html><html lang="sk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
      '<title>A64 | Integrácia energie: dve definície</title>',
      '<style>body{font:16px system-ui;background:#101827;color:#edf2fa;max-width:1100px;margin:auto;padding:24px}h1{color:#7fe6da}table{border-collapse:collapse;width:100%;margin:18px 0}td,th{padding:10px;border:1px solid #42516c;text-align:right}th:first-child,td:first-child{text-align:left}small{color:#bac6da}.warn{background:#49331c;padding:14px;border-radius:8px}.bar{background:#67c5e2;height:12px;display:inline-block}</style>',
      '<h1>A64: porovnanie integrácie energie</h1>',
      '<p class="warn">DERIVED SIMULATION. Nie sú to merania ani fyzikálna certifikácia. A60: lichobežníkové pravidlo nad N-1 intervalmi. A62: N diskrétnych krokov.</p>',
      '<p><b>Matematika:</b> E<sub>A60</sub> = Σ(Pᵢ+Pᵢ₊₁)Δt/2; E<sub>A62</sub> = ΣPᵢΔt. Rozdiel = P<sub>last</sub>Δt + Σ(Pᵢ−Pᵢ₊₁)Δt/2 = (P<sub>first</sub>+P<sub>last</sub>)Δt/2 pri konštantnom kroku.</p>']
    for version,r in results.items():
        parts.append(f'<h2>{html.escape(version)}: {r["samples"]} vzoriek, A60 {r["time_span_h"]} h, A62 {r["discrete_duration_h"]} h</h2>')
        parts.append('<table><thead><tr><th>Kanál</th><th>A60 [MWh]</th><th>A62 [MWh]</th><th>A62 − A60 [kWh]</th><th>Posledný krok [kWh]</th><th>Korekcia sklonu [kWh]</th></tr></thead><tbody>')
        for key,v in r["channels"].items():
            parts.append('<tr><td>'+html.escape(key)+'</td>'+''.join('<td>'+format(Decimal(v[k]),".6f")+'</td>' for k in ("trapezoid_MWh","discrete_MWh","discrete_minus_trapezoid_kWh","terminal_rectangle_kWh","sample_slope_correction_kWh"))+'</tr>')
        parts.append('</tbody></table>')
        p=r["channels"]["Q_pool_W"]
        width=min(100,max(0,float(Decimal(p["discrete_minus_trapezoid_kWh"]))*3))
        parts.append(f'<p>Rozdiel tepla bazéna: <span class="bar" style="width:{width:.2f}%"></span> {Decimal(p["discrete_minus_trapezoid_kWh"]):.6f} kWh</p>')
    parts.append('<small>Obe metódy sú správne pre rozdielne časové konvencie. Nezamieňať bez uvedenia horizontu. Vstupy overené SHA256; originálne A60/A62 zostali nezmenené.</small></html>')
    return "\n".join(parts)+"\n"

def main():
    data={v:load_verified(v) for v in ("V08","V09")}
    out=D/"OUTPUT";out.mkdir(exist_ok=True)
    (out/"comparison.json").write_text(json.dumps({"schema":"a64.1","scenarios":data},indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"comparison.html").write_text(render(data),encoding="utf-8")
    print(json.dumps({"qa":"PASS","scenarios":list(data),"pool_delta_kWh":{v:data[v]["channels"]["Q_pool_W"]["discrete_minus_trapezoid_kWh"] for v in data}}))
if __name__=="__main__": main()
