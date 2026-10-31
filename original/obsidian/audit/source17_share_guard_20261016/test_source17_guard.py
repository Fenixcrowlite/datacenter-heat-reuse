"""Independent arithmetic and source-text regression tests for the Source 17 guard."""
from decimal import Decimal
from pathlib import Path
import re
import unittest
from source17_guard import analyze, SOURCE_TXT


class Source17GuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = analyze()

    def test_source_contains_all_four_percentages(self):
        source = " ".join(SOURCE_TXT.read_text(encoding="utf-8-sig").split())
        for phrase in ("76.5% of the heat generation", "21% is electricity",
                       "97.5% of the heat generated", "remaining 2.5%"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, source)

    def test_heat_mix_closes_to_100_percent(self):
        e = self.evidence
        self.assertEqual(sum(Decimal(e[k]) for k in
            ("waste_heat_share_pct", "hp_electricity_share_pct", "gas_heat_share_pct")),
            Decimal("100"))

    def test_hp_share_is_97_point_5(self):
        e = self.evidence
        self.assertEqual(Decimal(e["waste_heat_share_pct"]) +
                         Decimal(e["hp_electricity_share_pct"]),
                         Decimal(e["hp_output_share_pct"]))

    def test_cop_discrepancy_is_flagged_not_silenced(self):
        e = self.evidence
        implied = Decimal(e["hp_output_share_pct"]) / Decimal(e["hp_electricity_share_pct"])
        self.assertGreater(implied, Decimal(str(e["reported_table_cop_max"])))
        self.assertFalse(e["implied_cop_inside_table_range"])
        self.assertFalse(e["table_narrative_minima_agree"])

    def test_no_false_scientific_signoff(self):
        e = self.evidence
        self.assertFalse(e["full_paper_signoff"])
        self.assertFalse(e["physical_validation"])
        self.assertIn("NOT proof", e["interpretation"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
