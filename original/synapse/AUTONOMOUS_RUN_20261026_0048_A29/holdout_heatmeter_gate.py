"""A29 independent heat-meter holdout gate for DataCenter A28 residual calibration.
Read-only input analysis; NEVER a production safety/release approval.
Synthetic data cannot be promoted to field evidence by naming or good fit.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path

COLS = ("time_utc", "flow_read_m3h", "hot_read_C", "cold_read_C", "meter_kw")
SENSORS = ("flow", "hot", "cold")
HASH = re.compile(r"^[0-9a-fA-F]{64}$")
UNITS = {"flow": "m3/h", "hot": "degC", "cold": "degC", "meter": "kW"}
MIN_N = 12

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024*1024), b""):
            h.update(b)
    return h.hexdigest()

def stamp(x: str) -> datetime:
    dt = datetime.fromisoformat(x.replace("Z", "+00:00"))
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("timezone required")
    return dt.astimezone(timezone.utc)

def number(x) -> float:
    if isinstance(x, bool):
        raise ValueError("boolean is not a numeric measurement")
    y = float(x)
    if not math.isfinite(y):
        raise ValueError("nonfinite numeric value")
    return y

def positive(x) -> float:
    y = number(x)
    if y <= 0:
        raise ValueError("expected positive value")
    return y

def validated_covariance(c):
    if not isinstance(c, list) or len(c) != 3 or any(not isinstance(row, list) or len(row) != 3 for row in c):
        raise ValueError("covariance must be 3x3")
    m = [[number(x) for x in row] for row in c]
    if any(m[i][i] <= 0 for i in range(3)):
        raise ValueError("nonpositive residual variance")
    if any(abs(m[i][j]-m[j][i])/math.sqrt(m[i][i]*m[j][j]) > 1e-10
           for i in range(3) for j in range(i+1,3)):
        raise ValueError("asymmetric covariance")
    r = [[m[i][j]/math.sqrt(m[i][i]*m[j][j]) for j in range(3)] for i in range(3)]
    if any(abs(r[i][j]) > 1+1e-10 for i in range(3) for j in range(3)):
        raise ValueError("correlation outside [-1,1]")
    determinant = 1 + 2*r[0][1]*r[0][2]*r[1][2]-r[0][1]**2-r[0][2]**2-r[1][2]**2
    if determinant < -1e-10:
        raise ValueError("covariance is not PSD")
    return m

def verify_a28_sources(cal: dict, csv_path: Path, metadata_path: Path) -> dict:
    """Independent recomputation of A28 residual statistics from immutable source bytes."""
    if not csv_path.is_file() or not metadata_path.is_file():
        raise FileNotFoundError("original A28 calibration sources required")
    csv_hash, meta_hash = digest(csv_path), digest(metadata_path)
    if csv_hash.lower() != str(cal.get("csv_sha256", "")).lower() or meta_hash.lower() != str(cal.get("metadata_sha256", "")).lower():
        raise ValueError("A28 raw input hashes disagree with report")
    meta = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
    if meta.get("source_class") != cal.get("source_class"):
        raise ValueError("A28 raw metadata provenance differs")
    fields = ("flow_time_utc", "hot_time_utc", "cold_time_utc",
              "flow_read_m3h", "flow_ref_m3h", "hot_read_C", "hot_ref_C",
              "cold_read_C", "cold_ref_C")
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if tuple(reader.fieldnames or ()) != fields:
            raise ValueError("A28 raw calibration schema differs")
        rows = list(reader)
    if len(rows) < MIN_N or len(rows) != cal.get("sample_count"):
        raise ValueError("A28 sample count mismatch")
    if stamp(rows[0]["flow_time_utc"]) != stamp(cal["time_start_utc"]) or stamp(rows[-1]["flow_time_utc"]) != stamp(cal["time_end_utc"]):
        raise ValueError("A28 source time interval mismatch")
    residuals = [[number(row[a])-number(row[b]) for a,b in
                  (("flow_read_m3h","flow_ref_m3h"),("hot_read_C","hot_ref_C"),("cold_read_C","cold_ref_C"))]
                 for row in rows]
    biases = [statistics.mean(x[i] for x in residuals) for i in range(3)]
    cov = [[sum((r[i]-biases[i])*(r[j]-biases[j]) for r in residuals)/(len(rows)-1)
            for j in range(3)] for i in range(3)]
    reported = validated_covariance(cal.get("residual_sample_covariance"))
    for i,k in enumerate(SENSORS):
        if not math.isclose(biases[i],number(cal["residual_bias"][k]),rel_tol=1e-8,abs_tol=1e-11):
            raise ValueError("A28 reported bias differs from source recomputation")
        for j in range(3):
            if not math.isclose(cov[i][j],reported[i][j],rel_tol=1e-8,abs_tol=1e-11):
                raise ValueError("A28 reported covariance differs from source recomputation")
    return {"calibration_csv_sha256": csv_hash, "calibration_metadata_sha256": meta_hash}

def analyze(calibration_path: Path, holdout_path: Path, metadata_path: Path, calibration_csv_path: Path, calibration_metadata_path: Path) -> dict:
    for p in (calibration_path, holdout_path, metadata_path):
        if not p.is_file():
            raise FileNotFoundError(p)
    cal = json.loads(calibration_path.read_text(encoding="utf-8-sig"))
    meta = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
    if meta.get("source_class") not in ("SYNTHETIC_TEST", "FIELD_CALIBRATION"):
        raise ValueError("unknown source class")
    if meta.get("source_class") != cal.get("source_class"):
        raise ValueError("calibration and holdout source classes differ")
    if meta.get("units") != UNITS:
        raise ValueError("holdout unit mismatch")
    if meta.get("meter_independent") is not True:
        raise ValueError("meter must be independent of model channels")
    period = positive(meta.get("sample_period_s"))
    rho = positive(meta.get("density_kg_m3"))
    cp = positive(meta.get("specific_heat_kj_kg_K"))
    meter_u = positive(meta.get("meter_std_uncertainty_kw"))
    if not (900 <= rho <= 1100 and 3.5 <= cp <= 4.5):
        raise ValueError("liquid water properties outside declared envelope")
    if not HASH.fullmatch(str(cal.get("csv_sha256", ""))) or not HASH.fullmatch(str(cal.get("metadata_sha256", ""))):
        raise ValueError("invalid A28 provenance hashes")
    if cal.get("release_allowed") is not False or int(cal.get("sample_count", 0)) < MIN_N:
        raise ValueError("invalid A28 report or release claim")
    if meta["source_class"] == "SYNTHETIC_TEST" and cal.get("status") != "SYNTHETIC_ONLY_NOT_FIELD_VERIFIED":
        raise ValueError("synthetic provenance status mismatch")
    if meta["source_class"] == "FIELD_CALIBRATION" and cal.get("status") != "FIELD_CANDIDATE_REQUIRES_INDEPENDENT_CERTIFICATE_REVIEW":
        raise ValueError("field provenance status mismatch")
    if digest(holdout_path).lower() == cal["csv_sha256"].lower():
        raise ValueError("holdout reuses calibration CSV")
    verified_sources = verify_a28_sources(cal, calibration_csv_path, calibration_metadata_path)
    cov = validated_covariance(cal.get("residual_sample_covariance"))
    biases = cal.get("residual_bias")
    if not isinstance(biases, dict) or set(biases) != set(SENSORS):
        raise ValueError("missing A28 biases")
    bias = [number(biases[k]) for k in SENSORS]
    cal_end = stamp(cal["time_end_utc"])
    if stamp(cal["time_start_utc"]) >= cal_end:
        raise ValueError("invalid calibration interval")
    with holdout_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if tuple(reader.fieldnames or ()) != COLS:
            raise ValueError("invalid holdout CSV columns")
        rows = list(reader)
    if not MIN_N <= len(rows) <= 1000000:
        raise ValueError("invalid holdout sample count")
    t, pred, observed, point_u = [], [], [], []
    for row in rows:
        if None in row or any(row.get(k) is None or not row[k].strip() for k in COLS):
            raise ValueError("missing holdout value")
        now = stamp(row["time_utc"])
        if now <= cal_end:
            raise ValueError("holdout overlaps calibration period")
        if t:
            delta = (now-t[-1]).total_seconds()
            if not (0.5*period <= delta <= 1.5*period):
                raise ValueError("holdout timing gap, duplicate or reversed sample")
        t.append(now)
        flow, hot, cold, meter = [number(row[k]) for k in COLS[1:]]
        flow -= bias[0]
        hot -= bias[1]
        cold -= bias[2]
        if flow <= 0 or hot <= cold or meter <= 0:
            raise ValueError("invalid positive heat transfer")
        factor = rho*cp/3600.0
        q = factor*flow*(hot-cold)
        jac = (factor*(hot-cold), factor*flow, -factor*flow)
        variance = sum(jac[i]*cov[i][j]*jac[j] for i in range(3) for j in range(3))
        if variance < -1e-8:
            raise ValueError("negative propagated variance")
        point_u.append(math.sqrt(max(0.0, variance)+meter_u**2))
        pred.append(q)
        observed.append(meter)
    certificate_hash = None
    if meta["source_class"] == "FIELD_CALIBRATION":
        cert = meta.get("meter_certificate")
        if not isinstance(cert, dict) or not all(cert.get(k) for k in ("file","sha256","instrument_id","issuer","expires_utc")):
            raise ValueError("missing independent meter certificate")
        if not HASH.fullmatch(str(cert["sha256"])):
            raise ValueError("invalid meter certificate hash")
        cpath = (metadata_path.parent / cert["file"]).resolve()
        if not cpath.is_relative_to(metadata_path.parent.resolve()) or not cpath.is_file():
            raise ValueError("meter certificate path invalid")
        certificate_hash = digest(cpath)
        if certificate_hash.lower() != cert["sha256"].lower() or stamp(cert["expires_utc"]) < t[-1]:
            raise ValueError("meter certificate hash/expiry mismatch")
    residual = [p-m for p,m in zip(pred,observed)]
    z = [e/u for e,u in zip(residual,point_u)]
    pred_energy = sum(pred[i]*(t[i+1]-t[i]).total_seconds()/3600 for i in range(len(t)-1))
    meter_energy = sum(observed[i]*(t[i+1]-t[i]).total_seconds()/3600 for i in range(len(t)-1))
    return {
        "status": "SYNTHETIC_ONLY_NOT_FIELD_VERIFIED" if meta["source_class"] == "SYNTHETIC_TEST"
                  else "FIELD_HOLDOUT_CANDIDATE_REQUIRES_INDEPENDENT_REVIEW",
        "release_allowed": False,
        "sample_count": len(rows),
        "source_class": meta["source_class"],
        "calibration_report_sha256": digest(calibration_path),
        "verified_a28_source_hashes": verified_sources,
        "holdout_csv_sha256": digest(holdout_path),
        "holdout_metadata_sha256": digest(metadata_path),
        "meter_certificate_sha256": certificate_hash,
        "holdout_start_utc": t[0].isoformat(),
        "holdout_end_utc": t[-1].isoformat(),
        "mean_bias_kw": statistics.mean(residual),
        "mae_kw": statistics.mean(abs(e) for e in residual),
        "rmse_kw": math.sqrt(statistics.mean(e*e for e in residual)),
        "mean_relative_abs_error_pct": 100*statistics.mean(abs(e)/m for e,m in zip(residual,observed)),
        "max_abs_normalized_residual": max(abs(x) for x in z),
        "fraction_abs_normalized_residual_le_2": sum(abs(x)<=2 for x in z)/len(z),
        "pointwise_combined_standard_uncertainty_kw": {
            "min": min(point_u), "max": max(point_u), "mean": statistics.mean(point_u)
        },
        "model_energy_kwh_left_rectangle": pred_energy,
        "meter_energy_kwh_left_rectangle": meter_energy,
        "energy_difference_kwh": pred_energy-meter_energy,
        "limits": [
            "Independent meter identity and calibration issuer are not authenticated by file hash.",
            "A28 residual covariance and biases are estimates; their estimation uncertainty is omitted.",
            "Pointwise uncertainty includes sensor residual covariance and declared meter standard uncertainty only.",
            "Normalized residuals are diagnostic, not confidence intervals or release criteria.",
            "Time integration uses left rectangles, not a certified revenue-grade energy meter.",
            "Synthetic inputs are never field validation. No production SCADA or MATLAB changes."
        ]
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--calibration", type=Path, required=True)
    ap.add_argument("--holdout", type=Path, required=True)
    ap.add_argument("--calibration-csv", type=Path, required=True)
    ap.add_argument("--calibration-metadata", type=Path, required=True)
    ap.add_argument("--metadata", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    if a.output.exists():
        raise FileExistsError(a.output)
    result = analyze(a.calibration,a.holdout,a.metadata,a.calibration_csv,a.calibration_metadata)
    a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(result["status"], result["sample_count"])

if __name__ == "__main__":
    main()
