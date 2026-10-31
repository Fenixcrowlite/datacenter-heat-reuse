import copy, json, unittest
from pathlib import Path
import scada_api_link as link

class ScadaLinkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lineage=json.loads(Path(__file__).with_name("DCHR_LINEAGE_EVIDENCE.json").read_text(encoding="utf-8"))
        cls.meta={"metadata":{"source_class":"D_SYNTHETIC","hardware_enabled":False},
                  "scenarios":[{"id":x["scenario"],"sha256":x["v08_csv_sha256"],
                                "rows":672,"quality":"D"} for x in cls.lineage["cases"]]}

    def test_good(self):
        self.assertEqual(link.check(self.meta,self.lineage)["scenario_count"],8)
    def test_sha_mutation(self):
        x=copy.deepcopy(self.meta);x["scenarios"][0]["sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"SHA mismatch"):link.check(x,self.lineage)
    def test_wrong_provenance(self):
        x=copy.deepcopy(self.meta);x["metadata"]["source_class"]="A"
        with self.assertRaisesRegex(ValueError,"provenance"):link.check(x,self.lineage)
    def test_hardware_enabled(self):
        x=copy.deepcopy(self.meta);x["metadata"]["hardware_enabled"]=True
        with self.assertRaisesRegex(ValueError,"provenance"):link.check(x,self.lineage)
    def test_missing_case(self):
        x=copy.deepcopy(self.meta);x["scenarios"].pop()
        with self.assertRaisesRegex(ValueError,"case set"):link.check(x,self.lineage)
    def test_bad_rows(self):
        x=copy.deepcopy(self.meta);x["scenarios"][0]["rows"]=671
        with self.assertRaisesRegex(ValueError,"sample count"):link.check(x,self.lineage)
    def test_bad_quality(self):
        x=copy.deepcopy(self.meta);x["scenarios"][0]["quality"]="A"
        with self.assertRaisesRegex(ValueError,"quality"):link.check(x,self.lineage)

if __name__=="__main__":unittest.main()
