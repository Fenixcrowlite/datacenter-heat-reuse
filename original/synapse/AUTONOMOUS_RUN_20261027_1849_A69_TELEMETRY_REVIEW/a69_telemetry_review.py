"""A69: offline, provenance-checked review of normalized A59 telemetry.

This tool does not connect to SCADA, validate sensor certificates, or authorize hardware.
It writes a new directory only. All measurements retain their declared source kind.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import os
import shutil
import statistics
import tempfile
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

FIELDS = ("timestamp_utc", "asset_id", "calibration_ref", "T_C", "Q_net_W",
          "P_cmd_W", "P_actual_W", "trip_state", "Q_residual_W", "Q_nominal_W")
NUMERIC = ("T_C", "Q_net_W", "P_cmd_W", "P_actual_W", "Q_residual_W", "Q_nominal_W")
POWER = ("Q_net_W", "P_cmd_W", "P_actual_W", "Q_residual_W", "Q_nominal_W")
NONNEGATIVE = ("P_cmd_W", "P_actual_W", "Q_residual_W", "Q_nominal_W")
CHANNELS = ("Q_net_W", "P_cmd_W", "P_actual_W", "Q_residual_W")


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicate_keys)


def utc(text):
    try:
        stamp = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("INVALID_UTC") from exc
    if stamp.tzinfo is None or stamp.utcoffset() != timedelta(0):
        raise ValueError("UTC_REQUIRED")
    return stamp


def load(source: Path):
    source = Path(source)
    if source.is_symlink() or not source.is_dir():
        raise ValueError("INVALID_SOURCE_DIRECTORY")
    csv_path, meta_path, prov_path = (source / n for n in
        ("telemetry.csv", "metadata.json", "provenance.json"))
    for path in (csv_path, meta_path, prov_path):
        if not path.is_file() or path.is_symlink():
            raise ValueError("INVALID_INPUT_FILE:" + path.name)
    meta, prov = read_json(meta_path), read_json(prov_path)
    if prov.get("schema_version") != "a59.1":
        raise ValueError("INVALID_A59_SCHEMA")
    kind = prov.get("source_kind")
    if kind not in ("synthetic_test", "real_telemetry") or meta.get("source_kind") != kind:
        raise ValueError("SOURCE_KIND_CONFLICT")
    if prov.get("physical_release") is not False:
        raise ValueError("PHYSICAL_RELEASE_FORBIDDEN")
    if not isinstance(meta.get("asset_id"), str) or not meta["asset_id"]:
        raise ValueError("INVALID_ASSET_ID")
    if not isinstance(meta.get("sensor_calibration_record"), str) or not meta["sensor_calibration_record"]:
        raise ValueError("INVALID_CALIBRATION_REF")
    if not isinstance(meta.get("provenance_notes"), str):
        raise ValueError("INVALID_PROVENANCE_NOTES")
    csv_sha, meta_sha = digest(csv_path), digest(meta_path)
    if (prov.get("normalized_csv_sha256") != csv_sha or
        prov.get("metadata_sha256") != meta_sha or
        meta.get("original_csv_sha256") != csv_sha):
        raise ValueError("SOURCE_SHA_MISMATCH")
    with csv_path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        if reader.fieldnames != list(FIELDS):
            raise ValueError("INVALID_CSV_COLUMNS")
        rows = []
        previous = None
        for record in reader:
            if None in record or any(v is None for v in record.values()):
                raise ValueError("MALFORMED_ROW")
            if record["asset_id"] != meta["asset_id"] or record["calibration_ref"] != meta["sensor_calibration_record"]:
                raise ValueError("IDENTITY_MISMATCH")
            if record["trip_state"] not in ("RUN", "TRIPPED"):
                raise ValueError("INVALID_TRIP_STATE")
            timestamp = utc(record["timestamp_utc"])
            if previous is not None:
                delta = (timestamp - previous).total_seconds()
                if not 0 < delta <= 3600:
                    raise ValueError("TIMEBASE_INVALID")
            previous = timestamp
            values = {}
            for name in NUMERIC:
                try:
                    value = Decimal(record[name])
                except (InvalidOperation, TypeError) as exc:
                    raise ValueError("NON_NUMERIC:" + name) from exc
                if not value.is_finite():
                    raise ValueError("NONFINITE:" + name)
                if name in NONNEGATIVE and value < 0:
                    raise ValueError("NEGATIVE_POWER:" + name)
                values[name] = value
            rows.append({"timestamp": timestamp, "state": record["trip_state"], **values})
    if len(rows) < 20 or prov.get("rows") != len(rows):
        raise ValueError("ROW_COUNT_CONFLICT")
    return rows, meta, prov, {"telemetry.csv": csv_sha,
                               "metadata.json": meta_sha,
                               "provenance.json": digest(prov_path)}


def energy_kwh(rows, field):
    """Trapezoidal integration across observed timestamps only; no final extrapolation."""
    total = Decimal(0)
    for a, b in zip(rows, rows[1:]):
        dt = Decimal(str((b["timestamp"] - a["timestamp"]).total_seconds()))
        total += (a[field] + b[field]) * dt / Decimal(7200000)
    return total


def summary(rows, meta, prov, hashes):
    steps = [(b["timestamp"] - a["timestamp"]).total_seconds() for a, b in zip(rows, rows[1:])]
    med = statistics.median(steps)
    trips = sum(row["state"] == "TRIPPED" for row in rows)
    starts = sum(a["state"] != "TRIPPED" and b["state"] == "TRIPPED"
                 for a, b in zip(rows, rows[1:]))
    warnings = ["CALIBRATION_AND_TIME_SYNC_NOT_INDEPENDENTLY_VERIFIED"]
    if any(step > med * 1.5 for step in steps):
        warnings.append("IRREGULAR_SAMPLE_GAPS_REVIEW")
    if trips:
        warnings.append("TRIPPED_STATES_PRESENT")
    return {
        "schema": "a69.1", "source_kind": prov["source_kind"],
        "asset_id": meta["asset_id"], "calibration_ref": meta["sensor_calibration_record"],
        "source_hashes": hashes, "rows": len(rows),
        "first_utc": rows[0]["timestamp"].isoformat(),
        "last_utc": rows[-1]["timestamp"].isoformat(),
        "observed_hours": sum(steps) / 3600,
        "median_step_s": med, "trip_rows": trips, "trip_starts": starts,
        "temperature_first_C": float(rows[0]["T_C"]),
        "temperature_last_C": float(rows[-1]["T_C"]),
        "integrated_energy_kWh": {key: float(energy_kwh(rows, key)) for key in CHANNELS},
        "warnings": warnings, "physical_release": False,
        "integration": "trapezoidal_on_observed_intervals_no_final_extrapolation",
        "provenance_notes": meta["provenance_notes"]
    }


def svg_plot(rows, channels, title, unit, scale=1.0):
    width, height = 920, 270
    left, right, top, bottom = 65, 20, 24, 42
    plot_w, plot_h = width - left - right, height - top - bottom
    values = [float(row[name]) / scale for row in rows for name, _ in channels]
    low, high = min(values), max(values)
    if math.isclose(low, high):
        low -= 1
        high += 1
    else:
        padding = (high - low) * 0.08
        low -= padding
        high += padding
    span = (rows[-1]["timestamp"] - rows[0]["timestamp"]).total_seconds()
    colors = ("#6bb8ff", "#ffbd70", "#64dfad", "#e8a3ff")
    pieces = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title, quote=True)}">'
              f'<title>{html.escape(title)}</title>']
    for i in range(5):
        y = top + plot_h * i / 4
        val = high - (high - low) * i / 4
        pieces.append(f'<line x1="{left}" x2="{width-right}" y1="{y:.2f}" y2="{y:.2f}" stroke="#36425d"/>')
        pieces.append(f'<text x="{left-9}" y="{y+4:.2f}" text-anchor="end" fill="#bdcde0" font-size="12">{val:.1f}</text>')
    for i, (name, label) in enumerate(channels):
        points = []
        for row in rows:
            t = (row["timestamp"] - rows[0]["timestamp"]).total_seconds()
            x = left + plot_w * t / span
            y = top + plot_h * (high - float(row[name]) / scale) / (high - low)
            points.append(f"{x:.2f},{y:.2f}")
        pieces.append(f'<polyline fill="none" stroke="{colors[i]}" stroke-width="2.5" points="{" ".join(points)}"/>')
    pieces.append(f'<text x="{left}" y="{height-12}" fill="#bdcde0" font-size="13">0 h</text>')
    pieces.append(f'<text x="{width-right}" y="{height-12}" text-anchor="end" fill="#bdcde0" font-size="13">{span/3600:.2f} h</text>')
    pieces.append('</svg>')
    legend = " · ".join(f'<span style="color:{colors[i]}">{html.escape(label)}</span>' for i, (_, label) in enumerate(channels))
    return f'<section class="plot"><h2>{html.escape(title)} [{html.escape(unit)}]</h2>{"".join(pieces)}<p>{legend}</p></section>'


def html_report(rows, report):
    kind = report["source_kind"]
    banner = ("SYNTETICKÉ TESTOVACIE DÁTA" if kind == "synthetic_test"
              else "DEKLAROVANÁ TELEMETRIA, NEOVERENÝ FYZICKÝ PÔVOD")
    def card(label, value):
        return f'<article class="card"><small>{html.escape(label)}</small><strong>{html.escape(str(value))}</strong></article>'
    energies = report["integrated_energy_kWh"]
    cards = [
        card("Vzorky", report["rows"]),
        card("Pozorovaný interval", f'{report["observed_hours"]:.3f} h'),
        card("Teplota na konci", f'{report["temperature_last_C"]:.3f} °C'),
        card("Prechody do TRIPPED", report["trip_starts"]),
        card("Energia Q_net", f'{energies["Q_net_W"]:.3f} kWh'),
        card("Energia P_actual", f'{energies["P_actual_W"]:.3f} kWh'),
    ]
    plots = [
        svg_plot(rows, (("T_C", "T"),), "Teplota média", "°C"),
        svg_plot(rows, (("P_cmd_W", "P_cmd"), ("P_actual_W", "P_actual"),
                        ("Q_net_W", "Q_net")), "Výkony", "kW", 1000),
    ]
    note = html.escape(report["provenance_notes"])
    sha = html.escape(report["source_hashes"]["telemetry.csv"])
    warning = ", ".join(html.escape(x) for x in report["warnings"])
    return f'''<!doctype html><html lang="sk"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>A69 | Prehľad SCADA telemetrie</title>
<style>
:root{{color-scheme:dark}}*{{box-sizing:border-box}}
body{{background:#0b1223;color:#eef4ff;font:16px system-ui,Arial,sans-serif;max-width:1100px;margin:auto;padding:20px}}
h1{{font-size:clamp(1.4rem,3vw,2.3rem)}}p{{line-height:1.55;color:#c5d3e7}}
.banner{{background:#4b2818;border:2px solid #ffb36b;padding:14px;border-radius:10px;color:#ffe1bb;font-weight:750}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:12px;margin:18px 0}}
.card,.plot,.info{{background:#16223b;border:1px solid #3c4c69;border-radius:12px;padding:14px;min-width:0}}
.card strong{{display:block;font-size:1.4rem;margin-top:7px}}small{{color:#b5c8df}}
.plot{{margin:16px 0}}.plot svg{{display:block;width:100%;height:auto}}
.info{{overflow-wrap:anywhere}}.warning{{color:#ffd19e}}
@media(max-width:500px){{body{{padding:10px}}.cards{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}
</style></head><body><h1>Prehľad SCADA telemetrie · A69</h1>
<div class="banner">{banner} · FYZICKÁ VALIDÁCIA NEPOTVRDENÁ</div>
<p>Samostatný offline prehľad normalizovaného exportu A59. Bez pripojenia na SCADA a bez sieťových požiadaviek.
Integrácia je lichobežníková len medzi pozorovanými časovými značkami; posledný krok sa neodhaduje.</p>
<section class="cards">{"".join(cards)}</section>
{"".join(plots)}
<section class="info"><h2>Proveniencia a obmedzenia</h2>
<p>Asset: <strong>{html.escape(report["asset_id"])}</strong> · kalibrácia (iba deklarovaná): {html.escape(report["calibration_ref"])}</p>
<p>Zdroj: {html.escape(kind)} · {note}</p><p class="warning">Upozornenia: {warning}</p>
<p>SHA256 normalizovaného CSV: <code>{sha}</code></p>
<p>Žiadne meranie ani certifikát nebol nezávisle potvrdený. Výsledok nie je povolením prevádzky.</p></section></body></html>
'''


def review(source: Path, destination: Path):
    source, destination = Path(source), Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ValueError("DESTINATION_EXISTS")
    if not destination.parent.is_dir():
        raise ValueError("DESTINATION_PARENT_MISSING")
    rows, meta, prov, hashes = load(source)
    report = summary(rows, meta, prov, hashes)
    staging = Path(tempfile.mkdtemp(prefix=".a69-staging-", dir=destination.parent))
    try:
        (staging / "summary.json").write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        (staging / "review.html").write_text(html_report(rows, report), encoding="utf-8")
        receipt = {"schema": "a69.receipt.1", "source_hashes": hashes,
                   "output_sha256": {name: digest(staging / name) for name in ("summary.json", "review.html")},
                   "physical_release": False}
        (staging / "source_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.rename(staging, destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("a59_normalized_directory", type=Path)
    parser.add_argument("new_output_directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(review(args.a59_normalized_directory, args.new_output_directory),
                     indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
