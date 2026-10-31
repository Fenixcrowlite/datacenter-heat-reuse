"""Source 17 Frankfurt paper: bounded numerical claim guard, not a physical validation."""
from __future__ import annotations
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[2]
SOURCE_TXT = ROOT / "sources" / "papers" / "17_Jurgens_Frankfurt_2024.extracted.txt"
SOURCE_PDF = ROOT / "sources" / "papers" / "17_Jurgens_Frankfurt_2024.pdf"
EXPECTED_PDF_SHA256 = "acd250b7e5033156c85e7aa1a4ab0adad9e087d69361511b116cc8dd065583af"


def analyze():
    txt = " ".join(SOURCE_TXT.read_text(encoding="utf-8-sig").split())
    # This is the paper's reported energy mix, not a validated energy balance.
    mix = re.search(
        r"76\.5% of the heat generation is waste heat and\s+21% is electricity"
        r".{0,140}?97\.5% of the heat generated.{0,90}?remaining 2\.5%",
        txt, re.I,
    )
    if not mix:
        raise AssertionError("Source 17 page 65 energy-share passage changed/missing")
    if not re.search(r"COP\s+3\.76 to 3\.9", txt, re.I):
        raise AssertionError("Source 17 Table 3 COP range missing")
    if not re.search(r"COP varies linearly between 3\.9\s+and 3\.67", txt, re.I):
        raise AssertionError("Source 17 narrative COP lower bound missing")
    pdf_hash = sha256(SOURCE_PDF.read_bytes()).hexdigest()
    if pdf_hash != EXPECTED_PDF_SHA256:
        raise AssertionError("Primary PDF SHA256 changed; manual re-review required")
    waste, electricity, gas = Decimal("76.5"), Decimal("21"), Decimal("2.5")
    hp = waste + electricity
    implied = hp / electricity
    return {
        "source": "Jurgens et al. 2024, DOI 10.54337/ijsepm.8149, printed p. 65",
        "source_pdf_sha256": pdf_hash,
        "waste_heat_share_pct": str(waste),
        "hp_electricity_share_pct": str(electricity),
        "gas_heat_share_pct": str(gas),
        "hp_output_share_pct": str(hp),
        "sum_share_pct": str(hp + gas),
        "implied_cop_if_same_annual_energy_denominator": round(float(implied), 6),
        "reported_table_cop_min": 3.76,
        "reported_table_cop_max": 3.9,
        "reported_narrative_cop_min": 3.67,
        "implied_cop_inside_table_range": Decimal("3.76") <= implied <= Decimal("3.9"),
        "table_narrative_minima_agree": Decimal("3.76") == Decimal("3.67"),
        "interpretation": "A boundary/denominator reconciliation is required; this is NOT proof the article is wrong.",
        "full_paper_signoff": False,
        "physical_validation": False,
    }


if __name__ == "__main__":
    target = Path(__file__).with_name("evidence.json")
    if target.exists():
        raise FileExistsError(target)
    target.write_text(json.dumps(analyze(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("EVIDENCE", target)
