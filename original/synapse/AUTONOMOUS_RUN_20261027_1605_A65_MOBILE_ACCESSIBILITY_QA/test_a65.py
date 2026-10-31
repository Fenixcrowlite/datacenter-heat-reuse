"""A65 static regression tests for mobile report and source preservation."""
import unittest
from pathlib import Path
import a65_mobile_reflow as m
class TestA65(unittest.TestCase):
    def test_expected_rows(self):
        out=m.transform(m.SRC.read_text(encoding="utf-8"))
        self.assertEqual(out.count('data-label='),60)
    def test_no_mutation_source(self):
        self.assertEqual(m.sha(m.SRC),"5f8cd1410e4f598fe3e31b0254ae3a6e203e0734d0b674e37c01987f09b6c309")
    def test_reject_missing_table(self):
        with self.assertRaisesRegex(ValueError,"LAYOUT"):m.transform("<html></html>")
    def test_reject_wrong_cell_count(self):
        src=m.SRC.read_text(encoding="utf-8")
        bad=src.replace("<tr><td>Q_DC_W</td>","<tr><td>Q_DC_W</td><td>EXTRA</td>",1)
        with self.assertRaisesRegex(ValueError,"CELL_COUNT"):m.transform(bad)
    def test_same_numeric_content(self):
        import re
        original=m.SRC.read_text(encoding="utf-8")
        fixed=m.OUT.read_text(encoding="utf-8")
        self.assertEqual(re.findall(r'<td>([^<]+)</td>',original),
                         re.findall(r'<td data-label="[^"]+">([^<]+)</td>',fixed))
    def test_original_probe_proves_defect(self):
        import json
        d=json.loads((m.D/"ORIGINAL_A64_BROWSER_PROBE.json").read_text(encoding="utf-8"))
        self.assertGreater(d["mobile"]["scrollWidth"],d["mobile"]["viewport"])
    def test_mobile_browser_regression(self):
        import json
        d=json.loads((m.D/"BROWSER_QA_A65.json").read_text(encoding="utf-8"))
        for r in d["screens"].values():
            self.assertLessEqual(r["scrollWidth"],r["width"])
            self.assertEqual(r["cells"],60)
    def test_no_remote_assets(self):
        h=m.OUT.read_text(encoding="utf-8")
        self.assertNotIn("https://",h)
        self.assertNotIn("<script",h)
if __name__=="__main__":unittest.main()
