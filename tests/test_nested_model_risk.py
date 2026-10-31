import io
from pathlib import Path
import tempfile
import unittest
import zipfile

from tools.nested_model_risk import scan_nested_bytes


class NestedModelRiskTests(unittest.TestCase):
    def test_nested_user_home_detected_in_compressed_member(self):
        sink=io.BytesIO()
        with zipfile.ZipFile(sink,"w",compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("simulink/state.xml",
                       b"<entry>prefix: "+b"C:\\Users\\Example\\State"+b"</entry>")
        self.assertIn("nested_user_home_path",scan_nested_bytes(sink.getvalue()))

    def test_clean_inner_xml(self):
        sink=io.BytesIO()
        with zipfile.ZipFile(sink,"w") as z:
            z.writestr("simulink/model.xml",b"<model>temperature</model>")
        self.assertEqual(set(),scan_nested_bytes(sink.getvalue()))

    def test_author_metadata_is_classified_not_reproduced(self):
        sink=io.BytesIO()
        with zipfile.ZipFile(sink,"w") as z:
            z.writestr("docProps/core.xml",b"<dc:creator>Private Real Name</dc:creator>")
        flags=scan_nested_bytes(sink.getvalue())
        self.assertIn("nested_creator_metadata",flags)
        self.assertNotIn("Private Real Name",str(flags))

    def test_traversal_and_case_alias_are_classified(self):
        sink=io.BytesIO()
        with zipfile.ZipFile(sink,"w") as z:
            z.writestr("simulink/../evil.xml",b"foo")
            z.writestr("simulink/X.xml",b"1")
            z.writestr("simulink/x.XML",b"2")
        flags=scan_nested_bytes(sink.getvalue())
        self.assertIn("nested_unsafe_path",flags)
        self.assertIn("nested_case_alias",flags)


if __name__=="__main__":
    unittest.main()
