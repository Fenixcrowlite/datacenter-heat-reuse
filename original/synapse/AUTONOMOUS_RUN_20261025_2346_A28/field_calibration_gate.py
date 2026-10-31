"""DataCenter A28: fail-closed, read-only calibration-residual covariance gate.

This is NOT a calibration service or a release approval. Operational readings
alone cannot identify sensor-error covariance: matched traceable reference
readings are mandatory. Sample covariance describes residual variability;
systematic mean biases are reported separately, never averaged away.
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

FIELDS = (
    "flow_time_utc", "hot_time_utc", "cold_time_utc",
    "flow_read_m3h", "flow_ref_m3h",
    "hot_read_C", "hot_ref_C", "cold_read_C", "cold_ref_C",
)
SENSORS = ("flow", "hot", "cold")
MIN_SAMPLES = 12
SHA_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("timestamp must include timezone")
    return dt.astimezone(timezone.utc)


def finite(value: str) -> float:
    x = float(value)
    if not math.isfinite(x):
        raise ValueError("nonfinite numeric reading")
    return x


def check_metadata(meta: dict, last_time: datetime, data_dir: Path) -> dict:
    if meta.get("source_class") not in ("SYNTHETIC_TEST", "FIELD_CALIBRATION"):
        raise ValueError("invalid source_class")
    if meta.get("units") != {"flow": "m3/h", "hot": "degC", "cold": "degC"}:
        raise ValueError("unit schema mismatch")
    if not all(isinstance(meta.get(k), (int, float))
               and not isinstance(meta.get(k), bool)
               and math.isfinite(meta[k]) and meta[k] > 0
               for k in ("sample_period_s", "max_skew_s")):
        raise ValueError("invalid sample period or skew limit")
    if meta["max_skew_s"] >= meta["sample_period_s"] / 2:
        raise ValueError("skew limit too loose")
    trace = {}
    if meta["source_class"] == "FIELD_CALIBRATION":
        certs = meta.get("certificates")
        if not isinstance(certs, dict) or set(certs) != set(SENSORS):
            raise ValueError("missing instrument certificates")
        for sensor in SENSORS:
            c = certs[sensor]
            if not isinstance(c, dict) or not all(c.get(k) for k in
                ("instrument_id", "reference_id", "file", "sha256", "expires_utc")):
                raise ValueError("incomplete certificate metadata")
            if not SHA_PATTERN.fullmatch(c["sha256"]):
                raise ValueError("invalid certificate SHA256")
            path = (data_dir / c["file"]).resolve()
            if not path.is_relative_to(data_dir.resolve()):
                raise ValueError("certificate escapes data directory")
            if not path.is_file() or sha256(path).lower() != c["sha256"].lower():
                raise ValueError("certificate missing or SHA mismatch")
            if utc(c["expires_utc"]) < last_time:
                raise ValueError("certificate expired during sample period")
            trace[sensor] = {"instrument_id": c["instrument_id"],
                             "reference_id": c["reference_id"],
                             "sha256": sha256(path)}
    return trace


def covariance(residuals: list[tuple[float, float, float]]) -> tuple[list[float], list[list[float]]]:
    cols = [list(x) for x in zip(*residuals)]
    bias = [statistics.mean(x) for x in cols]
    n = len(residuals)
    cov = [[sum((cols[i][k] - bias[i]) * (cols[j][k] - bias[j])
                for k in range(n)) / (n - 1)
            for j in range(3)] for i in range(3)]
    if any(cov[i][i] <= 0 for i in range(3)):
        raise ValueError("zero residual variance: cannot estimate covariance")
    # Symmetric by construction; check PSD without tolerance in physical units.
    r = [[cov[i][j] / math.sqrt(cov[i][i] * cov[j][j])
          for j in range(3)] for i in range(3)]
    for i in range(3):
        for j in range(i + 1, 3):
            if abs(r[i][j]) > 1 + 1e-10:
                raise ValueError("invalid correlation")
    det = 1 + 2*r[0][1]*r[0][2]*r[1][2] - r[0][1]**2 - r[0][2]**2 - r[1][2]**2
    if det < -1e-10:
        raise ValueError("invalid covariance PSD")
    return bias, cov


def lag1_effective_n(values: list[float]) -> dict:
    n = len(values)
    mu = statistics.mean(values)
    centered = [x - mu for x in values]
    denom = sum(x*x for x in centered)
    if denom <= 0:
        raise ValueError("zero variance")
    rho = sum(centered[i]*centered[i-1] for i in range(1,n)) / denom
    # AR(1) heuristic only; negative correlation is conservatively not credited.
    n_eff = max(1.0, min(float(n), n*(1-rho)/(1+rho))) if 0 < rho < 1 else float(n)
    return {"lag1_sample_autocorrelation": rho, "ar1_heuristic_n_eff": n_eff}


def analyze(csv_path: Path, metadata_path: Path) -> dict:
    if not csv_path.is_file() or not metadata_path.is_file():
        raise FileNotFoundError("CSV or metadata missing")
    meta = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or tuple(reader.fieldnames) != FIELDS:
            raise ValueError("CSV columns or order do not match schema")
        rows = list(reader)
    if len(rows) < MIN_SAMPLES:
        raise ValueError("too few paired calibration samples")
    if len(rows) > 1_000_000:
        raise ValueError("sample limit exceeded")
    period = meta.get("sample_period_s")
    skew_limit = meta.get("max_skew_s")
    if not isinstance(period, (float,int)) or not isinstance(skew_limit, (float,int)):
        raise ValueError("invalid timing metadata")
    residuals, times, max_skew = [], [], 0.0
    for row in rows:
        if None in row or any(row[k] is None or not row[k].strip() for k in FIELDS):
            raise ValueError("missing CSV value")
        timestamps = [utc(row[k]) for k in FIELDS[:3]]
        seconds = [(t - timestamps[0]).total_seconds() for t in timestamps]
        skew = max(seconds) - min(seconds)
        if skew > skew_limit:
            raise ValueError("unsynchronized sensor triplet")
        max_skew = max(max_skew, skew)
        t = timestamps[0]
        if times:
            step = (t-times[-1]).total_seconds()
            if not 0 < step <= 1.5*period or step < 0.5*period:
                raise ValueError("nonmonotonic, duplicated or missing time step")
        times.append(t)
        vals = [finite(row[k]) for k in FIELDS[3:]]
        if vals[0] <= 0 or vals[1] <= 0:
            raise ValueError("nonpositive flow or reference")
        residuals.append((vals[0]-vals[1], vals[2]-vals[3], vals[4]-vals[5]))
    trace = check_metadata(meta, times[-1], metadata_path.parent)
    biases, cov = covariance(residuals)
    cols = list(zip(*residuals))
    correlation = [[cov[i][j]/math.sqrt(cov[i][i]*cov[j][j])
                    for j in range(3)] for i in range(3)]
    ar = {s: lag1_effective_n(list(cols[i])) for i,s in enumerate(SENSORS)}
    return {
        "status": "SYNTHETIC_ONLY_NOT_FIELD_VERIFIED" if meta["source_class"] == "SYNTHETIC_TEST"
                  else "FIELD_CANDIDATE_REQUIRES_INDEPENDENT_CERTIFICATE_REVIEW",
        "source_class": meta["source_class"],
        "release_allowed": False,
        "csv_sha256": sha256(csv_path),
        "metadata_sha256": sha256(metadata_path),
        "sample_count": len(rows),
        "time_start_utc": times[0].isoformat(),
        "time_end_utc": times[-1].isoformat(),
        "max_sensor_skew_s": max_skew,
        "residual_bias": dict(zip(SENSORS, biases)),
        "residual_sample_covariance": cov,
        "residual_sample_correlation": correlation,
        "residual_standard_deviation": dict(zip(SENSORS, [math.sqrt(cov[i][i]) for i in range(3)])),
        "autocorrelation_diagnostic": ar,
        "certificate_hashes": trace,
        "limits": [
            "Residuals are measured minus matched references, not process-value covariance.",
            "Mean residual bias is systematic and must not be divided by sqrt(n).",
            "Lag-1 effective sample size is an AR(1) heuristic, not a confidence interval.",
            "Certificate file hashes do not authenticate issuer, traceability or accuracy.",
            "Field candidate requires independent review and holdout heat-meter validation.",
            "No SCADA/MATLAB production files or controls changed."
        ]
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--metadata", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise FileExistsError(a.output)
    report = analyze(a.csv, a.metadata)
    a.output.write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(report["status"], "samples=", report["sample_count"])


if __name__ == "__main__":
    main()
