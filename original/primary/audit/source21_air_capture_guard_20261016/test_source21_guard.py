import unittest
from source21_guard import analyze
class QA(unittest.TestCase):
 def test_pdf(self): self.assertEqual(analyze()['printed_page'],626)
 def test_lift(self): self.assertEqual(list(analyze()['minimum_temperature_lift_from_reported_max_C'].values()),[25,30,52])
 def test_scope(self): self.assertFalse(analyze()['physical_model_validation'])
if __name__=='__main__': unittest.main()
