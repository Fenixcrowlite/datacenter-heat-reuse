"""Independent A69 acceptance: no imports from the implementation under test."""
import csv
import hashlib
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "FIXTURE"
OUTPUT = HERE / "OUTPUT_SYNTHETIC"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    with (SOURCE / "telemetry.csv").open(newline="", encoding="utf-8") as f:
        data = list(csv.DictReader(f))
    assert len(data) == 30
    report = json.loads((OUTPUT / "summary.json").read_text(encoding="utf-8"))
    receipt = json.loads((OUTPUT / "source_receipt.json").read_text(encoding="utf-8"))
    provenance = json.loads((SOURCE / "provenance.json").read_text(encoding="utf-8"))
    for filename in ("telemetry.csv", "metadata.json", "provenance.json"):
        assert receipt["source_hashes"][filename] == sha(SOURCE / filename), filename
    assert provenance["normalized_csv_sha256"] == sha(SOURCE / "telemetry.csv")
    for filename in ("summary.json", "review.html"):
        assert receipt["output_sha256"][filename] == sha(OUTPUT / filename), filename

    result = {}
    for name in ("Q_net_W", "P_cmd_W", "P_actual_W", "Q_residual_W"):
        energy = Decimal(0)
        for a, b in zip(data, data[1:]):
            ta = datetime.fromisoformat(a["timestamp_utc"])
            tb = datetime.fromisoformat(b["timestamp_utc"])
            dt = Decimal(str((tb - ta).total_seconds()))
            energy += (Decimal(a[name]) + Decimal(b[name])) * dt / Decimal(7200000)
        claimed = Decimal(str(report["integrated_energy_kWh"][name]))
        assert abs(claimed - energy) < Decimal("0.000000001"), (name, claimed, energy)
        result[name] = str(energy)

    trips = sum(x["trip_state"] == "TRIPPED" for x in data)
    starts = sum(a["trip_state"] != "TRIPPED" and b["trip_state"] == "TRIPPED"
                 for a, b in zip(data, data[1:]))
    assert (trips, starts) == (report["trip_rows"], report["trip_starts"])
    assert report["observed_hours"] == 29 / 60
    assert report["source_kind"] == "synthetic_test" and report["physical_release"] is False
    page = (OUTPUT / "review.html").read_text(encoding="utf-8")
    assert page.count("<svg") == 2 and page.count("<polyline") == 4
    assert "SYNTETICKÉ TESTOVACIE DÁTA" in page
    assert "@media(max-width:500px)" in page
    assert "<script" not in page.lower() and "http://" not in page and "https://" not in page
    assert "FYZICKÁ VALIDÁCIA NEPOTVRDENÁ" in page
    return {"status": "PASS", "rows": len(data), "observed_intervals": len(data) - 1,
            "energy_kWh_exact_decimal": result, "trip_rows": trips, "trip_starts": starts,
            "source_hashes_checked": 3, "output_hashes_checked": 2,
            "svg_plots": 2, "svg_series": 4,
            "browser": "not_executed", "physical_release": False}


if __name__ == "__main__":
    result = run()
    (HERE / "INDEPENDENT_QA_A69.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
