# -*- coding: utf-8 -*-
"""Download only authoritative public NASA POWER and Eurostat evidence, no edits to pool lane.
NASA POWER is gridded reanalysis: not an in-situ sensor measurement.
"""
from __future__ import annotations
import csv, datetime as dt, json, math, statistics, urllib.parse, urllib.request
from pathlib import Path

HERE=Path(__file__).resolve().parent
OUT=HERE/"official_datasets"
OUT.mkdir(parents=True,exist_ok=True)
UA={"User-Agent":"Academic-Research-DC-Heat-Reuse/1.0 (open official data)"}
def download_json(url,output,timeout=80):
    if output.exists():
        return json.loads(output.read_text(encoding="utf-8"))
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=timeout) as resp:
        payload=resp.read(15000000)
        if resp.status!=200:raise ValueError(f"HTTP {resp.status}")
    obj=json.loads(payload.decode("utf-8-sig"))
    output.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")
    print("SAVED_RAW",output,len(payload),flush=True)
    return obj

def weather():
    params={"parameters":"T2M,RH2M,WS2M","community":"SB","longitude":"17.2127",
            "latitude":"48.1702","start":"20250101","end":"20251231","format":"JSON","time-standard":"UTC"}
    url="https://power.larc.nasa.gov/api/temporal/hourly/point?"+urllib.parse.urlencode(params)
    p=OUT/"NASA_POWER_Bratislava_2025_hourly_raw.json"
    o=download_json(url,p,timeout=120)
    if o.get("messages"):print("NASA_MESSAGES",o["messages"],flush=True)
    pars=o.get("properties",{}).get("parameter",{})
    if "T2M" not in pars:raise ValueError("NASA POWER response lacks T2M parameter")
    records=[]
    for stamp,temperature in sorted(pars["T2M"].items()):
        if len(stamp)!=10:continue
        timestamp=dt.datetime.strptime(stamp,"%Y%m%d%H").replace(tzinfo=dt.timezone.utc)
        rh=pars.get("RH2M",{}).get(stamp)
        ws=pars.get("WS2M",{}).get(stamp)
        values=[temperature,rh,ws]
        values=[None if v is None or not math.isfinite(float(v)) or float(v)<-900 else float(v) for v in values]
        records.append((timestamp.isoformat().replace("+00:00","Z"),*values))
    if len(records)!=8760:raise ValueError(f"Expected 8760 hourly rows, got {len(records)}")
    if records[0][0][:10]!="2025-01-01" or records[-1][0][:10]!="2025-12-31":
        raise ValueError("NASA hourly requested year invalid")
    csv_path=OUT/"weather_2025_BRATISLAVA_NASA_POWER_hourly_UTC.csv"
    with csv_path.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f);w.writerow(["datetime_UTC","T2M_C","RH2M_percent","WS2M_m_s"]);w.writerows(records)
    valid=[r[1] for r in records if r[1] is not None]
    if len(valid)<8000:raise ValueError(f"Unexpectedly missing NASA temperature values: {len(valid)} valid")
    bymonth={}
    for m in range(1,13):
        vs=[r[1] for r in records if int(r[0][5:7])==m and r[1] is not None]
        bymonth[f"{m:02d}"]={"n":len(vs),"mean_C":round(statistics.mean(vs),3),"minimum_C":min(vs),"maximum_C":max(vs)}
    # original MATLAB heating demand law with a reference 20 MW peak plus network loss
    def heat(t):
        lf=max(0,min(1.15,(16-t)/28))
        return (2+18*lf)/.94
    out={
        "provider":"NASA POWER","type":"gridded meteorological reanalysis (NOT on-site measurements)",
        "dataset_year":2025,"start":records[0][0],"end":records[-1][0],
        "coordinates":[48.1702,17.2127],"time_basis":"UTC (hourly)",
        "URL":url,"raw_source":str(p),"parsed_CSV":str(csv_path),
        "rows":len(records),"valid_air_temp_rows":len(valid),"coverage":round(len(valid)/len(records),6),
        "air_temp_annual_mean_C":round(statistics.mean(valid),4),
        "min_C":min(valid),"max_C":max(valid),
        "monthly":bymonth,
        "model_heat_demand_annual_MWh_from_source_weather":round(sum(heat(t) for t in valid),2),
        "model_heat_demand_thermal_peak_MW_from_source_weather":round(max(heat(t) for t in valid),4)
    }
    (OUT/"NASA_2025_weather_summary.json").write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding="utf-8")
    print("NASA_OK",json.dumps({k:out[k] for k in ["rows","coverage","air_temp_annual_mean_C","min_C","max_C","model_heat_demand_annual_MWh_from_source_weather"]}),flush=True)
    return out

def decode_eurostat(obj):
    dimensions=obj.get("id",[])
    sizes=obj.get("size",[])
    if not dimensions or len(dimensions)!=len(sizes):raise ValueError("Eurostat JSON-stat invalid dimensions")
    axes=[]
    for dim in dimensions:
        ix=obj["dimension"][dim]["category"]["index"]
        # index is code->pos; reconstruct true position order
        if isinstance(ix,list):raise ValueError("Unexpected Eurostat category list")
        axes.append([k for k,v in sorted(ix.items(),key=lambda item:item[1])])
    n=math.prod(sizes)
    rows=[]
    for flat_str,v in obj.get("value",{}).items():
        pos=int(flat_str)
        if pos>=n:raise ValueError("Eurostat out-of-range flat index")
        coords={}
        for dim,sz,labels in reversed(list(zip(dimensions,sizes,axes))):
            coords[dim]=labels[pos%sz]
            pos//=sz
        coords["value"]=v
        coords["flag"]=obj.get("status",{}).get(flat_str)
        rows.append(coords)
    return rows

def prices(dataset):
    q={"geo":"SK","sinceTimePeriod":"2025-S1","currency":"EUR","unit":"KWH"}
    url=f"https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{dataset}?"+urllib.parse.urlencode(q)
    raw=OUT/(dataset+"_SK_2025_2026_raw.json")
    obj=download_json(url,raw,timeout=80)
    rows=decode_eurostat(obj)
    periods=["2025-S1","2025-S2","2026-S1"]
    accepted=[r for r in rows if r.get("time") in periods]
    columns=sorted({key for r in accepted for key in r.keys()})
    out=OUT/(dataset+"_SK_2025_2026_series.csv")
    with out.open("w",newline="",encoding="utf-8-sig") as f:
        writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader();writer.writerows(accepted)
    # report only selected band and tax type, no ungrounded quote.
    bands=sorted({r.get("nrg_cons") or r.get("NRG_CONS") for r in accepted if r.get("nrg_cons") or r.get("NRG_CONS")})
    flags=sorted({str(r.get("flag")) for r in accepted if r.get("flag")})
    cols=[k for k in accepted[0].keys()] if accepted else columns
    summary={"dataset":dataset,"url":url,"raw":str(raw),"csv":str(out),"rows":len(accepted),
             "dimension_keys":cols,"consumption_bands":bands,"status_flags":flags,
             "latest_timestamp":obj.get("updated"),
             "selected_2026_sample":[r for r in accepted if r.get("time")=="2026-S1"][:6]}
    (OUT/(dataset+"_SK_summary.json")).write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8")
    print("EUROSTAT_OK",dataset,"rows",len(accepted),"bands",bands,"updated",obj.get("updated"),flush=True)
    return summary

if __name__=="__main__":
    failed=[]
    for name,fn in [("NASA",weather),("ELECTRICITY",lambda:prices("nrg_pc_205")),("GAS",lambda:prices("nrg_pc_203"))]:
        try:fn()
        except Exception as exc:
            failed.append({"name":name,"error":repr(exc)})
            print("FAILED",name,repr(exc),flush=True)
    if failed:
        (OUT/"fetch_failures.json").write_text(json.dumps(failed,indent=2),encoding="utf-8")
        raise SystemExit(len(failed))
