"""Isolated EU data-centre metric prototype (NOT a compliance certification).
References: Directive (EU) 2023/1791 Arts 12, 26; Delegated Reg (EU) 2024/1364 Annex III.
Synthetic inputs must never be described as measured site data.
"""
from __future__ import annotations
import json,sys
from decimal import Decimal,InvalidOperation,localcontext
from pathlib import Path

FIELDS=("edc_kwh","eit_kwh","ereuse_kwh","eres_total_kwh","win_m3")
def number(v,label):
    if isinstance(v,bool) or not isinstance(v,(int,str,Decimal)):
        raise ValueError(f"{label}: supply decimal string/integer; floats forbidden")
    try:d=Decimal(str(v))
    except (InvalidOperation,ValueError):raise ValueError(f"{label}: invalid number")
    if not d.is_finite() or d<0:raise ValueError(f"{label}: nonfinite/negative")
    return d
def metrics(row):
    if not isinstance(row,dict):raise ValueError("record must be an object")
    missing=[k for k in FIELDS if k not in row]
    if missing:raise ValueError("missing: "+",".join(missing))
    d={k:number(row[k],k) for k in FIELDS}
    edc,eit,reuse,res,water=(d[k] for k in FIELDS)
    if edc==0 or eit==0:raise ValueError("zero energy denominator")
    if eit>edc:raise ValueError("E_IT exceeds E_DC: incompatible meter boundary")
    if reuse>edc:raise ValueError("E_REUSE exceeds E_DC: check reuse boundary, not heat-pump output")
    if res>edc:raise ValueError("E_RES-TOT exceeds E_DC: check reporting boundary")
    with localcontext() as ctx:
        ctx.prec=30
        out={"PUE":edc/eit,"ERF":reuse/edc,"REF":res/edc,
             "WUE_m3_per_MWh_IT":water/(eit/Decimal(1000))}
    return {k:format(v,"f") for k,v in out.items()}
def applicability(installed_it_kw,total_rated_energy_input_kw):
    it=number(installed_it_kw,"installed_it_kw")
    total=number(total_rated_energy_input_kw,"total_rated_energy_input_kw")
    return {"article12_reporting_500kW_or_more":it>=500,
            "article26_heat_reuse_over_1MW":total>1000,
            "note":"Threshold indicators only, NOT legal determination; national law, exceptions and feasibility require review."}
def integrate_hourly(rows):
    if not isinstance(rows,list) or not rows:raise ValueError("nonempty intervals required")
    accum={k:Decimal(0) for k in FIELDS}
    for i,r in enumerate(rows):
        if not isinstance(r,dict):raise ValueError(f"interval {i}: not object")
        hours=number(r.get("duration_h"),f"interval {i} duration_h")
        if hours==0:raise ValueError(f"interval {i}: zero duration")
        for k,kw in (("edc_kwh","edc_kw"),("eit_kwh","eit_kw"),
                     ("ereuse_kwh","ereuse_kw"),("eres_total_kwh","eres_total_kw")):
            accum[k]+=number(r.get(kw),f"interval {i} {kw}")*hours
        accum["win_m3"]+=number(r.get("water_m3_per_h"),f"interval {i} water_m3_per_h")*hours
    result={k:format(v,"f") for k,v in accum.items()}
    return {"integrated":result,"indicators":metrics(result),
            "warning":"Synthetic/assumed unless independently metered; pool heat output is not automatically E_REUSE."}
def main(argv):
    if len(argv)!=3 or argv[1]!="sample":
        print("usage: python eu_dc_metrics.py sample output.json",file=sys.stderr);return 2
    sample={"edc_kwh":"1200000","eit_kwh":"1000000","ereuse_kwh":"300000",
            "eres_total_kwh":"600000","win_m3":"2000"}
    result={"data_class":"SYNTHETIC_FIXTURE_NOT_MEASURED",
      "inputs":sample,"metrics":metrics(sample),
      "threshold_example":applicability("500","1000"),
      "source_refs":[
        "https://eur-lex.europa.eu/eli/dir/2023/1791/oj/eng",
        "https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj/eng"],
      "full_primary_signoff":False,"site_compliance_verified":False}
    Path(argv[2]).write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":"SYNTHETIC_SAMPLE","PUE":result["metrics"]["PUE"],
                      "ERF":result["metrics"]["ERF"]},ensure_ascii=False))
    return 0
if __name__=="__main__":sys.exit(main(sys.argv))
