"""Regression tests for A38 synthetic integration; no shared-runtime writes."""
import csv
import json
import math
import tempfile
import unittest
from pathlib import Path
import integrated_a38 as m

class IntegratedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw, cls.dispatch, cls.tes, cls.source, cls.cases = m.calculate()

    def test_provenance_pinned(self):
        m.check_manifest(m.A37, "thermal_n1.py")
        m.check_manifest(m.A37B, "tes_soc.py")

    def test_provenance_tamper_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            (p / "payload.py").write_text("bad", encoding="utf8")
            (p / "SHA256_MANIFEST.json").write_text('{"payload.py":"0"}', encoding="utf8")
            with self.assertRaisesRegex(RuntimeError, "UPSTREAM_SHA_MISMATCH"):
                m.check_manifest(p, "payload.py")

    def test_all_672_and_12(self):
        self.assertEqual(len(self.raw), 672)
        self.assertEqual(len(self.cases), 12)
        self.assertTrue(all(len(x) == 672 for x in self.cases.values()))

    def test_tes_clip_is_six(self):
        self.assertEqual(sum(x["Q_charge_curtailed_W"] > 1e-6 for x in self.tes), 6)

    def test_tes_bounds_and_trace(self):
        for rows in self.cases.values():
            for row, t in zip(rows, self.tes):
                self.assertGreaterEqual(row["TES_SOC_next"], 0)
                self.assertLessEqual(row["TES_SOC_next"], 1 + 1e-10)
                self.assertAlmostEqual(row["E_TES_next_J"], t["E_TES_next_J"], places=5)

    def test_dc_hp_tes_closure(self):
        for rows in self.cases.values():
            for r in rows:
                self.assertLess(abs(r["DC_residual_W"]), 1e-5)
                self.assertLess(abs(r["HP_residual_W"]), 1e-5)
                self.assertLess(abs(r["TES_residual_J"]), 1e-4)

    def test_fault_gating_pre_24(self):
        for rows in self.cases.values():
            for r in rows[:96]:
                self.assertEqual(r["capacity_W"], 330000)
                self.assertEqual(r["Q_IT_shed_W"], 0)

    def test_reject_caps_post_fault(self):
        for key, rows in self.cases.items():
            label = key.split("/")[0]
            for r in rows[96:]:
                self.assertLessEqual(r["Q_reject_actual_W"],
                                     m.thermal_n1.CAPACITIES[label] + 1e-7)

    def test_full_dc_energy_accounting(self):
        for rows in self.cases.values():
            for r in rows:
                lhs = r["Q_DC_eff_W"] - r["Q_IT_shed_W"]
                rhs = r["Q_HX_W"] + r["Q_HP_source_W"] + r["Q_leak_W"] + r["Q_reject_actual_W"] + r["Q_unhandled_W"]
                self.assertAlmostEqual(lhs, rhs, delta=1e-5)

    def test_preclip_legacy_thermal_equivalence(self):
        for key, rows in self.cases.items():
            name = "trace_" + key.replace("/", "_") + ".csv"
            with (m.A37 / name).open(encoding="utf8", newline="") as f:
                old = list(csv.DictReader(f))
            for r, prior in zip(rows, old):
                if r["cas_h"] >= 69:
                    break
                self.assertAlmostEqual(r["T_IT_next_C"], float(prior["T_IT_next_C"]), delta=1e-7)
                self.assertAlmostEqual(r["Q_IT_shed_W"], float(prior["shed_W"]), delta=1e-7)

    def test_corrected_reject_delta(self):
        legacy = self.cases["neither/no_shed"]
        old = json.loads((m.A37 / "RESULTS_A37.json").read_text(encoding="utf8"))
        previous = old["cases"]["neither/no_shed"]["unhandled_kWh"]
        new = m.summarize({"neither/no_shed": legacy})["neither/no_shed"]["unhandled_kWh"]
        self.assertAlmostEqual(new - previous, 61.346160974, delta=0.00001)

    def test_both_reject_no_overflow(self):
        for key, rows in self.cases.items():
            if key.startswith("both/"):
                self.assertTrue(all(r["Q_unhandled_W"] <= 1e-7 for r in rows))

    def test_shedding_sensitivity(self):
        self.assertGreater(m.summarize(self.cases)["backup_only/no_shed"]["max_T_IT_C"],
                           m.summarize(self.cases)["backup_only/ramp15k_40pct"]["max_T_IT_C"])
        self.assertGreater(m.summarize(self.cases)["neither/ideal_40pct"]["max_T_IT_C"], 42)

    def test_invalid_negative(self):
        bad = [dict(r) for r in self.tes]
        bad[0]["Q_reject_corrected_W"] = -100.0
        with self.assertRaises((AssertionError, ValueError)):
            m.replay_case(self.raw, self.dispatch, bad, 0, m.thermal_n1.POLICIES["no_shed"])

    def test_invalid_nonfinite(self):
        bad = [dict(r) for r in self.raw]
        bad[0]["Q_DC_eff_W"] = "nan"
        with self.assertRaises(ValueError):
            m.replay_case(bad, self.dispatch, self.tes, 0, m.thermal_n1.POLICIES["no_shed"])

    def test_release_flags(self):
        self.assertFalse(m.LIMITS["physical_release_allowed"])
        self.assertFalse(m.LIMITS["matlab_stateflow_executed"])
        self.assertFalse(m.LIMITS["hardware_control"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
