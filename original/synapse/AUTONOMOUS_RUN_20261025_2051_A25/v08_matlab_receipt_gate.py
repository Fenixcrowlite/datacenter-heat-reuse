"""Fail-closed MATLAB v08 execution receipt gate. Read-only against project originals.
An existing CSV/QA PASS is not proof of a MATLAB process execution.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")
CASES = (
    "zdravy", "primarny_ventil_zaseknuty", "oba_ventily_zaseknute",
    "hlavny_REJECT_off_zalozny_ok", "oba_REJECT_off_bez_shedding",
    "oba_REJECT_off_so_shedding", "spolocny_bias_senzorov",
    "kombinovana_havaria_so_shedding",
)
MODEL = "matlab/pool_measurement_v08/DC_Bazen_Externe_Merania_v08_SK.slx"
SCRIPT = "matlab/pool_measurement_v08/spusti_merania_replay_v08_sk.m"
BASE = "results/pool_measurement_v08"
MANIFEST = BASE + "/D_REPLAY_INPUT_MANIFEST.json"
QA = BASE + "/QA_NEZAVISLA_V08_SK.json"
RESULTS = BASE + "/vysledky_v08_SK.json"
HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
PASS = re.compile(r"^V08_REPLAY_PASS\s+([a-zA-Z0-9_]+)\s+T_delta=", re.M)
FINAL = re.compile(r"^V08_ALL_REPLAY_CASES_PASS\s+8\s*$", re.M)

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()

def within(base: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("UNSAFE_PATH")
    p = (base / relative).resolve(strict=True)
    if not p.is_relative_to(base.resolve(strict=True)) or not p.is_file():
        raise ValueError("UNSAFE_PATH")
    return p

def read_json(path: Path) -> dict:
    x = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(x, dict):
        raise ValueError("INVALID_JSON_OBJECT")
    return x

def snapshot(root: Path) -> dict:
    qa = read_json(within(root, QA))
    manifest = read_json(within(root, MANIFEST))
    results = read_json(within(root, RESULTS))
    if qa.get("status") != "PASS" or qa.get("source_class") != "D_SYNTHETIC_REPLAY":
        raise ValueError("QA_SOURCE_CLASS")
    if manifest.get("classification") != "D_SYNTHETIC_NEVER_FIELD_MEASUREMENT":
        raise ValueError("MANIFEST_SOURCE_CLASS")
    if results.get("classification") != "D_SYNTHETIC_NO_REAL_SENSOR_MEASUREMENT":
        raise ValueError("RESULTS_SOURCE_CLASS")
    if manifest.get("scenario_count") != 8:
        raise ValueError("MANIFEST_COUNT")
    if sorted(x.get("case") for x in manifest.get("cases", [])) != sorted(CASES):
        raise ValueError("MANIFEST_CASES")
    if sorted(x.get("scenario") for x in results.get("cases", [])) != sorted(CASES):
        raise ValueError("RESULT_CASES")
    if sorted(x.get("name") for x in qa.get("cases", [])) != sorted(CASES):
        raise ValueError("QA_CASES")
    paths = [MODEL, SCRIPT, MANIFEST, QA, RESULTS]
    paths += [f"{BASE}/sim_v08_{case}_SK.csv" for case in CASES]
    files = {rel: digest(within(root, rel)) for rel in paths}
    expected = qa.get("models_sha256", {}).get(MODEL)
    if not expected or files[MODEL] != expected.lower():
        raise ValueError("MODEL_SHA_QA_MISMATCH")
    return {"source_class": "D_SYNTHETIC", "cases": list(CASES), "sha256": files}

def discover(root: Path) -> list[dict]:
    """Bounded filename discovery, no recursive drive walk or process invocation."""
    folders = [root / "matlab" / "pool_measurement_v08",
               root / "results" / "pool_measurement_v08",
               root / "audit", root / "automation"]
    matches = []
    for folder in folders:
        if not folder.is_dir():
            continue
        for child in list(folder.iterdir())[:1200]:
            if not child.is_file():
                continue
            name = child.name.lower()
            if ("v08" in name and child.suffix.lower() in {".log", ".txt", ".json"}
                    and any(x in name for x in ("receipt", "run", "diary", "execution", "matlab"))):
                matches.append({"path": str(child), "sha256": digest(child),
                                "bytes": child.stat().st_size})
    return sorted(matches, key=lambda x: x["path"])

def aware(value: str) -> datetime:
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as e:
        raise ValueError("INVALID_TIME") from e
    if dt.tzinfo is None:
        raise ValueError("NAIVE_TIME")
    return dt.astimezone(timezone.utc)

def validate_receipt(root: Path, receipt_path: Path, current: dict) -> dict:
    receipt = read_json(receipt_path)
    if receipt.get("schema") != "dchr.v08.matlab_execution_receipt.v1":
        raise ValueError("RECEIPT_SCHEMA")
    if receipt.get("source_class") != "D_SYNTHETIC":
        raise ValueError("RECEIPT_PROVENANCE")
    if type(receipt.get("exit_code")) is not int or receipt["exit_code"] != 0:
        raise ValueError("NONZERO_EXIT")
    if not re.fullmatch(r"R20\d{2}[ab]", str(receipt.get("matlab_release", ""))):
        raise ValueError("MATLAB_RELEASE_UNVERIFIED")
    start, end = aware(receipt.get("started_utc")), aware(receipt.get("finished_utc"))
    seconds = (end - start).total_seconds()
    if not 0 < seconds < 86400:
        raise ValueError("INVALID_RUN_DURATION")
    for rel in (MODEL, SCRIPT, MANIFEST, QA, RESULTS):
        if receipt.get("sha256", {}).get(rel) != current["sha256"][rel]:
            raise ValueError("INPUT_SHA_MISMATCH:" + rel)
    outputs = receipt.get("outputs")
    if not isinstance(outputs, dict) or set(outputs) != set(CASES):
        raise ValueError("OUTPUT_CASES")
    for case in CASES:
        rel = f"{BASE}/sim_v08_{case}_SK.csv"
        if outputs[case] != current["sha256"][rel]:
            raise ValueError("OUTPUT_SHA_MISMATCH:" + case)
    log_rel = receipt.get("log_file")
    log = within(receipt_path.parent, log_rel)
    if log.stat().st_size > 8_000_000:
        raise ValueError("LOG_TOO_LARGE")
    if receipt.get("log_sha256") != digest(log):
        raise ValueError("LOG_SHA_MISMATCH")
    data = log.read_text(encoding="utf-8-sig")
    passed = PASS.findall(data)
    if len(passed) != 8 or set(passed) != set(CASES):
        raise ValueError("MATLAB_PASS_MARKERS")
    finals = list(FINAL.finditer(data))
    if len(finals) != 1 or finals[0].start() <= max(m.start() for m in PASS.finditer(data)):
        raise ValueError("MATLAB_FINAL_MARKER")
    return {"status": "VERIFIED_RECEIPT_CONSISTENCY_NOT_INDEPENDENT_MATLAB_RUN",
            "receipt_sha256": digest(receipt_path), "log_sha256": digest(log),
            "matlab_release": receipt["matlab_release"], "duration_seconds": seconds,
            "case_pass_markers": len(passed),
            "limitation": "A valid receipt can still be fabricated; requires trusted MATLAB process capture."}

def audit(root: Path, receipt: Path | None = None) -> dict:
    current = snapshot(root)
    found = discover(root)
    result = {"schema": "dchr.v08.receipt_audit.v1",
              "checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "project": str(root), "source_class": current["source_class"],
              "current_sha256": current["sha256"],
              "discovered_receipt_candidates": found,
              "status": "BLOCKED_MATLAB_EXECUTION_RECEIPT_MISSING",
              "limit": "Static hashes and historical QA do not independently prove a MATLAB execution."}
    if receipt is not None:
        result["receipt_validation"] = validate_receipt(root, receipt, current)
        result["status"] = "VERIFIED_RECEIPT_CONSISTENCY_ONLY"
    return result

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("REFUSE_OVERWRITE")
    result = audit(args.root, args.receipt)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(result["status"], "files", len(result["current_sha256"]),
          "candidates", len(result["discovered_receipt_candidates"]))

if __name__ == "__main__":
    main()
