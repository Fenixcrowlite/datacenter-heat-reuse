"""Audit the existing DCHR MATLAB simulation CSV. Never label simulations as meters."""
from __future__ import annotations
import csv, datetime as dt, hashlib, json, sys
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path

FIELDS = ("IT_MW","DC_Total_MW","HP_Source_Used_MW","HP_Electric_MW",
          "HP_Heat_MW","HP_Heat_Used_MW","Curtailed_HP_Heat_MW","HX_Heat_to_HP_MW","Gas_Heat_MW")
TOL = Decimal("0.000001")
ONE_HOUR = dt.timedelta(hours=1)

def decimal_value(raw, field, line):
    try:
        v = Decimal(raw)
    except (InvalidOperation, TypeError):
        raise ValueError(f"row {line}: invalid {field}")
    if not v.is_finite() or v < 0:
        raise ValueError(f"row {line}: nonfinite/negative {field}")
    return v

def audit(path, expected_rows=None):
    path=Path(path)
    totals={key:Decimal(0) for key in FIELDS}
    n=0; first=None; last=None; max_balance=Decimal(0)
    checks={"dc_ge_it":0,"hp_used_energy_balance":0,"hp_produced_equals_used_plus_curtailed":0,"hp_heat_used_le_produced":0,
            "hp_source_le_hx":0}
    with path.open("r",encoding="utf-8-sig",newline="") as stream:
        reader=csv.DictReader(stream)
        if not reader.fieldnames or len(reader.fieldnames)!=len(set(reader.fieldnames)):
            raise ValueError("missing or duplicate headers")
        if "Time" not in reader.fieldnames or any(f not in reader.fieldnames for f in FIELDS):
            raise ValueError("missing required fields")
        for line,row in enumerate(reader,2):
            if None in row or any(row.get(f) in (None,"") for f in ("Time",)+FIELDS):
                raise ValueError(f"row {line}: missing/truncated field")
            try: timestamp=dt.datetime.strptime(row["Time"],"%d-%b-%Y %H:%M:%S")
            except ValueError as exc:raise ValueError(f"row {line}: invalid timestamp") from exc
            if last is not None and timestamp-last != ONE_HOUR:
                raise ValueError(f"row {line}: non-hourly/duplicate/gap at {timestamp}")
            if first is None:first=timestamp
            last=timestamp
            values={f:decimal_value(row[f],f,line) for f in FIELDS}
            if values["DC_Total_MW"]+TOL < values["IT_MW"]:checks["dc_ge_it"]+=1
            residual=abs(values["HP_Heat_Used_MW"]-values["HP_Source_Used_MW"]-values["HP_Electric_MW"])
            curtail_residual=abs(values["HP_Heat_MW"]-values["HP_Heat_Used_MW"]-values["Curtailed_HP_Heat_MW"])
            max_balance=max(max_balance,residual)
            if residual>TOL:checks["hp_used_energy_balance"]+=1
            if curtail_residual>TOL:checks["hp_produced_equals_used_plus_curtailed"]+=1
            if values["HP_Heat_Used_MW"]>values["HP_Heat_MW"]+TOL:checks["hp_heat_used_le_produced"]+=1
            if values["HP_Source_Used_MW"]>values["HX_Heat_to_HP_MW"]+TOL:checks["hp_source_le_hx"]+=1
            for f in FIELDS:totals[f]+=values[f] # MW * 1 hour = MWh
            n+=1
    if n==0:raise ValueError("empty CSV")
    if expected_rows is not None and n!=expected_rows:raise ValueError(f"expected {expected_rows} rows, got {n}")
    if any(checks.values()):raise ValueError(f"physical consistency failures: {checks}; max residual {max_balance}")
    with localcontext() as ctx:
        ctx.prec=35
        pue=totals["DC_Total_MW"]/totals["IT_MW"] if totals["IT_MW"] else None
        ratio=totals["HP_Source_Used_MW"]/totals["DC_Total_MW"] if totals["DC_Total_MW"] else None
    return {
        "data_class":"SIMULATED_MODEL_OUTPUT_NOT_METERED",
        "source_path":str(path),
        "source_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
        "rows":n,"sampling":"hourly left-endpoint constant-power assumption",
        "first_timestamp_naive":first.isoformat(),
        "last_timestamp_naive":last.isoformat(),
        "period_end_assumed_naive":(last+ONE_HOUR).isoformat(),
        "timezone":"NOT_SPECIFIED_IN_SOURCE",
        "integrated_mwh":{f:format(totals[f],"f") for f in FIELDS},
        "PUE_simulated":format(pue,"f") if pue is not None else None,
        "HP_source_to_DC_energy_ratio_PROXY_NOT_ERF":format(ratio,"f") if ratio is not None else None,
        "physical_checks_failed":checks,
        "max_abs_hp_used_energy_balance_mw":format(max_balance,"f"),
        "ERF":None,"REF":None,"WUE":None,
        "limitations":[
          "Simulation CSV, not calibrated field measurements or verified meter telemetry.",
          "No certified E_REUSE boundary; HP source heat is a diagnostic proxy, NOT ERF.",
          "No renewable electricity or water input series; REF and WUE unavailable.",
          "DC_Total_MW boundary may exclude heat-pump electricity; verify physical metering.",
          "Last interval duration inferred as 1 hour; timestamps lack timezone.",
          "No legal compliance or primary-source signoff."
        ],
        "full_primary_signoff":False,"production_modified":False
    }

def main(argv):
    if len(argv)!=3:
        print("usage: python dchr_sim_energy_audit.py source.csv output.json",file=sys.stderr);return 2
    result=audit(argv[1])
    Path(argv[2]).write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"rows":result["rows"],"PUE_simulated":result["PUE_simulated"],
                      "balance_failures":result["physical_checks_failed"]}))
    return 0

if __name__=="__main__":sys.exit(main(sys.argv))
