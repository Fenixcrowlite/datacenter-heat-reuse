"""Source 21: bounded air-cooled capture-temperature QA, not model calibration."""
from hashlib import sha256
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
SOURCE_PDF = ROOT / "sources" / "papers" / "21_Ebrahimi_2014.pdf"
EXPECTED_SHA256 = "4aaffa92f30b0d5aa9c7a7e58e5ff8cad3eb05c9f8969b079d6127aab1600a40"
DOI = "10.1016/j.rser.2013.12.007"
# Ebrahimi et al. (2014), printed p. 626, PDF page 5, section 2.3.1.
# Approximate legacy air-cooled capture temperatures, not current-site measurements.
CAPTURE_C = {
    "rack_exhaust_before_mixing": (35, 45),
    "crac_return_air": (30, 40),
    "chiller_return_water": (16, 18),
}

def analyze(sink_c=70.0, pdf_path=SOURCE_PDF):
    if not isinstance(sink_c, (float, int)) or not 0 < sink_c < 200:
        raise ValueError("Expected plausible positive sink temperature in Celsius")
    data = Path(pdf_path).read_bytes()
    if not data.startswith(b"%PDF-"):
        raise AssertionError("Local primary source is not a PDF")
    digest = sha256(data).hexdigest()
    if digest != EXPECTED_SHA256:
        raise AssertionError("Local PDF SHA256 changed; re-review required")
    mid = {k: (lo + hi) / 2 for k, (lo, hi) in CAPTURE_C.items()}
    lift = {k: round(max(0.0, float(sink_c) - hi), 2)
            for k, (lo, hi) in CAPTURE_C.items()}
    return {
        "doi": DOI, "printed_page": 626, "pdf_page_one_based": 5,
        "pdf_sha256": digest,
        "source_temperature_ranges_C": {k: list(v) for k, v in CAPTURE_C.items()},
        "source_temperature_midpoints_C": mid,
        "hypothetical_dh_sink_C": float(sink_c),
        "minimum_temperature_lift_from_reported_max_C": lift,
        "all_three_need_uplift_at_hypothetical_sink": all(v > 0 for v in lift.values()),
        "not_a_measured_current_facility": True,
        "not_a_cop_or_energy_efficiency_estimate": True,
        "full_primary_source_signoff": False,
        "physical_model_validation": False,
    }

if __name__ == "__main__":
    dest = Path(__file__).with_name("evidence.json")
    if dest.exists():
        raise FileExistsError(dest)
    dest.write_text(json.dumps(analyze(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("EVIDENCE", dest)
