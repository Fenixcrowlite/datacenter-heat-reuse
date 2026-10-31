"""Independent read-only DCHR lineage audit: v07 -> D ingest -> v08 -> SCADA CSV.
No MATLAB execution, no claim of physical validation or provenance beyond checked files.
"""
from __future__ import annotations
import csv, hashlib, json, math
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")
CASES = (
    "zdravy", "primarny_ventil_zaseknuty", "oba_ventily_zaseknute",
    "hlavny_REJECT_off_zalozny_ok", "oba_REJECT_off_bez_shedding",
    "oba_REJECT_off_so_shedding", "spolocny_bias_senzorov",
    "kombinovana_havaria_so_shedding",
)
RAW_FROM_GOLD = {
    "Q_DC_available_W":"Q_DC_source_raw_W", "T_DC_C":"T_DC_C",
    "Q_DH_request_W":"Q_DH_req_W", "T_air_C":"T_air_C",
    "RH":"RH", "T_pool_sensor1_C":"sensor1_C",
    "T_pool_sensor2_C":"sensor2_C",
    "Q_REJECT_measured_W":"Q_reject_physical_W",
    "main_reject_ok":"reject_main_availability",
    "backup_reject_ok":"reject_backup_availability",
}
SIM_FROM_STAGE = {
    "Q_DC_source_raw_W":"Q_DC_available_W", "T_DC_C":"T_DC_C",
    "Q_DH_req_W":"Q_DH_request_W", "T_air_C":"T_air_C", "RH":"RH",
    "reject_main_availability":"main_reject_ok",
    "reject_backup_availability":"backup_reject_ok",
    "external_T1_C":"T_pool_sensor1_C", "external_T2_C":"T_pool_sensor2_C",
    "sensor1_C":"T_pool_sensor1_C", "sensor2_C":"T_pool_sensor2_C",
}

def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or len(set(reader.fieldnames))!=len(reader.fieldnames):
            raise ValueError(f"invalid headers: {path}")
        rows=list(reader)
    if any(None in r or any(v is None or v=="" for v in r.values()) for r in rows):
        raise ValueError(f"malformed rows: {path}")
    return rows

def close(a, b, field: str, case: str, index: int, tolerance=1e-6):
    try:
        x,y=float(a),float(b)
    except (ValueError,TypeError) as exc:
        raise ValueError(f"non-numeric {case} row={index} {field}") from exc
    if not (math.isfinite(x) and math.isfinite(y) and abs(x-y)<=tolerance):
        raise ValueError(f"mismatch {case} row={index} {field}: {x} != {y} tol={tolerance}")

def verify_row(case: str, index: int, gold: dict, raw: dict, op: dict, staged: dict, sim: dict):
    stamp=(datetime(2026,10,23,tzinfo=timezone.utc)+timedelta(seconds=index*900)).isoformat().replace("+00:00","Z")
    if raw["timestamp_utc"]!=stamp or staged["timestamp_utc"]!=stamp:
        raise ValueError(f"timestamp mismatch {case} row={index}")
    close(gold["cas_h"],index/4,"gold time",case,index,1e-9)
    close(sim["cas_h"],index/4,"sim time",case,index,1e-9)
    for col,source in RAW_FROM_GOLD.items():
        close(raw[col],gold[source],f"raw.{col}",case,index,1e-6)
    close(raw["pool_flow_m3h"],30*float(gold["flow_ok"]),"raw.flow",case,index)
    close(raw["P_IT_W"],1.1*float(gold["Q_DC_source_raw_W"]),"raw.IT placeholder",case,index,1e-5)
    for col in raw:
        if col!="timestamp_utc":
            if staged[col]!=format(float(raw[col]),".8g"):
                raise ValueError(f"8-significant-digit ingest mismatch {case} row={index} {col}")
    for col,value in op.items():
        close(value,gold[col],f"operational.{col}",case,index,1e-6)
        if col not in SIM_FROM_STAGE and col!="flow_ok":
            close(sim[col],value,f"sim.operational.{col}",case,index,1e-6)
    for col,source in SIM_FROM_STAGE.items():
        close(sim[col],staged[source],f"sim.external.{col}",case,index,1e-6)
    close(sim["flow_ok"],float(staged["pool_flow_m3h"])>0,f"sim.flow",case,index,1e-6)
    if abs(float(sim["T_pool_C"])-float(gold["T_pool_C"]))>=0.005:
        raise ValueError(f"v07/v08 pool temperature regression {case} {index}")
    if abs(float(sim["Q_pool_phys_W"])-float(gold["Q_pool_phys_W"]))>=200:
        raise ValueError(f"v07/v08 pool heat regression {case} {index}")

def validate(root: Path=ROOT) -> dict:
    out=root/"results"/"pool_measurement_v08"
    v07=root/"results"/"pool_redundancy_v07"
    manifest=json.loads((out/"D_REPLAY_INPUT_MANIFEST.json").read_text(encoding="utf-8-sig"))
    qa=json.loads((out/"QA_NEZAVISLA_V08_SK.json").read_text(encoding="utf-8-sig"))
    results=json.loads((out/"vysledky_v08_SK.json").read_text(encoding="utf-8-sig"))
    if manifest["classification"]!="D_SYNTHETIC_NEVER_FIELD_MEASUREMENT" or manifest["scenario_count"]!=8:
        raise ValueError("D input manifest classification/count changed")
    if qa["source_class"]!="D_SYNTHETIC_REPLAY" or qa["status"]!="PASS" or qa["checks"]!=91565:
        raise ValueError("v08 upstream QA gate changed")
    if results["classification"]!="D_SYNTHETIC_NO_REAL_SENSOR_MEASUREMENT":
        raise ValueError("v08 result classification changed")
    cases={x["case"]:x for x in manifest["cases"]}
    result_cases={x["scenario"]:x for x in results["cases"]}
    qa_cases={x["name"]:x for x in qa["cases"]}
    if any(set(d)!=set(CASES) for d in (cases,result_cases,qa_cases)):
        raise ValueError("case set mismatch")
    model_hashes={}
    for relative,expected in qa["models_sha256"].items():
        p=root/relative
        actual=sha(p)
        if actual.lower()!=expected.lower():
            raise ValueError(f"model SHA mismatch {relative}")
        model_hashes[relative]=actual
    output=[];checks=0
    for name in CASES:
        raw_path=out/"source_D"/name/"recorded_measured_schema_D.csv"
        stage_path=out/"staged_D"/name/"normalized_measurements_v07.csv"
        op_path=out/"source_D"/name/"source_operational_inputs_D_21.csv"
        gold_path=v07/f"scenar_{name}_SK.csv"
        sim_path=out/f"sim_v08_{name}_SK.csv"
        raw_meta=json.loads((out/"source_D"/name/"source_provenance_D.json").read_text(encoding="utf-8"))
        stage_meta=json.loads((out/"staged_D"/name/"validated_dataset_metadata.json").read_text(encoding="utf-8"))
        if (raw_meta["provenance"]!="D" or stage_meta["provenance"]!="D" or
            raw_meta["source_uri"]!=f"synthetic:v07_20261023/{name}" or
            stage_meta["source_uri"]!=raw_meta["source_uri"] or
            stage_meta["status"]!="ACCEPTED_AS_INGEST_NOT_AS_MODEL_VALIDATION" or
            stage_meta["records"]!=672 or stage_meta["step_s"]!=900):
            raise ValueError(f"provenance gate mismatch {name}")
        raw_hash=sha(raw_path)
        if raw_hash.lower()!=cases[name]["D_sha256"].lower() or raw_hash.lower()!=stage_meta["raw_SHA256"].lower():
            raise ValueError(f"D source SHA mismatch {name}")
        gold,raw,op,stage,sim=[read_csv(p) for p in (gold_path,raw_path,op_path,stage_path,sim_path)]
        if any(len(rows)!=672 for rows in (gold,raw,op,stage,sim)):
            raise ValueError(f"row count mismatch {name}")
        if len(sim[0])!=73 or len(op[0])!=22 or len(raw[0])!=13:
            raise ValueError(f"column schema mismatch {name}")
        for i,(g,r,o,s,v) in enumerate(zip(gold,raw,op,stage,sim)):
            verify_row(name,i,g,r,o,s,v)
            checks+=1
        report=result_cases[name]
        if report["source_class"]!="D_SYNTHETIC_REPLAY" or report["records"]!=672:
            raise ValueError(f"result status mismatch {name}")
        energy=sum(float(r["Q_pool_phys_W"]) for r in sim)*.25/1e6
        unhandled=sum(float(r["Q_unhandled_W"]) for r in sim)*.25/1e6
        max_it=max(float(r["T_IT_model_C"]) for r in sim)
        for field,actual in (("pool_MWh",energy),("unhandled_heat_MWh",unhandled),("IT_model_max_C",max_it)):
            close(actual,report[field],f"summary.{field}",name,0,1e-6)
        output.append({"scenario":name,"records":672,"raw_D_sha256":raw_hash,
                       "stage_sha256":sha(stage_path),"v07_sha256":sha(gold_path),
                       "v08_csv_sha256":sha(sim_path),"pool_MWh":energy})
    return {"schema":"dchr.v07_to_scada_v08_lineage.v1","status":"PASS_STATIC_LINEAGE_NO_MATLAB_REEXECUTION",
            "source_class":"D_SYNTHETIC","cases":output,"rows_verified":checks,
            "model_sha256":model_hashes,
            "generating_matlab_script_sha256":sha(root/"matlab"/"pool_measurement_v08"/"spusti_merania_replay_v08_sk.m"),
            "limits":"Static on-disk lineage and numeric checks only. Does not prove MATLAB execution receipt, real measurements, physical accuracy or independent sensors."}

if __name__=="__main__":
    evidence=validate()
    destination=Path(__file__).with_name("DCHR_LINEAGE_EVIDENCE.json")
    destination.write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(evidence["status"],"rows",evidence["rows_verified"],"scenarios",len(evidence["cases"]))
