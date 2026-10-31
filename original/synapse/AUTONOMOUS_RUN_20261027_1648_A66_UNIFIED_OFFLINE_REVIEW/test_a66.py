"""A66 independent numerical, provenance, and real headless browser regression."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from decimal import Decimal
import a66_unified as m

CHROME=Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
class Integrity(unittest.TestCase):
    def test_sources_and_provenance(self):
        html,comparison=m.load()
        self.assertEqual(comparison["schema"],"a64.1")
        self.assertIn("DERIVED",html)
    def test_output_single_file(self):
        self.assertTrue(m.OUT.exists())
        self.assertIn("id=\"a66-payload\"",m.OUT.read_text(encoding="utf-8"))
    def test_no_external_assets(self):
        text=m.OUT.read_text(encoding="utf-8")
        self.assertNotIn("<script src=",text)
        self.assertNotIn("<link rel=\"stylesheet\"",text)
    def test_five_channels_two_scenarios(self):
        c=m.load()[1]
        for s in c["scenarios"].values():
            self.assertEqual(set(s["channels"]),set(m.CHANNELS))
    def test_exact_delta_identity(self):
        c=m.load()[1]
        for s in c["scenarios"].values():
            for v in s["channels"].values():
                d=Decimal(v["discrete_MWh"])*1000-Decimal(v["trapezoid_MWh"])*1000
                self.assertLess(abs(d-Decimal(v["discrete_minus_trapezoid_kWh"])),Decimal("1e-9"))
    def test_hash_tamper_rejected(self):
        data=m.load()[1]
        data["scenarios"]["V08"]["a62_csv_sha256"]="0"*64
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"comparison.json"
            p.write_text(json.dumps(data),encoding="utf-8")
            with patch.object(m,"A64",p):
                with self.assertRaisesRegex(ValueError,"SOURCE_HASH_MISMATCH"):
                    m.load()
    def test_identity_tamper_rejected(self):
        data=m.load()[1]
        data["scenarios"]["V09"]["channels"]["Q_pool_W"]["terminal_rectangle_kWh"]="99"
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"comparison.json"
            p.write_text(json.dumps(data),encoding="utf-8")
            with patch.object(m,"A64",p):
                with self.assertRaisesRegex(ValueError,"INTEGRATION_IDENTITY_FAILED"):
                    m.load()
    def test_physical_release_tamper_rejected(self):
        data=m.load()[1]
        data["scenarios"]["V08"]["physical_release"]=True
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"comparison.json"
            p.write_text(json.dumps(data),encoding="utf-8")
            with patch.object(m,"A64",p):
                with self.assertRaisesRegex(ValueError,"PHYSICAL_PROVENANCE_GATE"):
                    m.load()
    def test_output_matches_inputs(self):
        text=m.OUT.read_text(encoding="utf-8")
        self.assertIn(m.load()[1]["scenarios"]["V08"]["a62_csv_sha256"],text)
        self.assertIn("renderIntegration",text)

def browser_qa():
    from playwright.sync_api import sync_playwright
    report={"viewports":{},"scenario_checks":0,"errors":[],"external_requests":[]}
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=str(CHROME),headless=True,args=["--disable-gpu","--disable-extensions","--no-first-run"])
        try:
            for width,height in [(320,640),(390,844),(1440,900)]:
                page=browser.new_page(viewport={"width":width,"height":height})
                page.on("pageerror",lambda e:report["errors"].append(str(e)))
                page.on("request",lambda r:report["external_requests"].append(r.url) if r.url.startswith("http") else None)
                page.goto(m.OUT.as_uri(),wait_until="load")
                for scenario in ("v08","v09"):
                    page.select_option("#scenario",scenario)
                    state=page.evaluate("""() => ({
                      width:innerWidth,scroll:document.documentElement.scrollWidth,
                      rows:document.querySelectorAll('#integration-rows tr').length,
                      cells:document.querySelectorAll('#integration-rows td').length,
                      svg:document.querySelectorAll('.plot svg polyline').length,
                      banner:document.body.innerText.includes('NIE SÚ TO MERANIA'),
                      selected:document.querySelector('#scenario').value,
                      identity:document.querySelector('#integration-identity').textContent,
                      pool:document.querySelectorAll('#integration-rows tr')[1].children[3].textContent
                    })""")
                    assert state["scroll"]<=width,(width,scenario,state)
                    assert state["rows"]==5 and state["cells"]==30 and state["svg"]==7,state
                    assert state["banner"] and state["selected"]==scenario,state
                    assert scenario.upper() in state["identity"],state
                    assert state["pool"].startswith("20"),state
                    report["viewports"][f"{width}_{scenario}"]=state
                    report["scenario_checks"]+=1
                page.close()
        finally:browser.close()
    assert not report["errors"] and not report["external_requests"],report
    report["status"]="PASS"
    return report

if __name__=="__main__":
    unittest.main()
