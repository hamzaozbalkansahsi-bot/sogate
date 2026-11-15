import importlib.util,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('region',R/'lib/media_review_region.py')
class ReviewRegionTests(unittest.TestCase):
 def test_only_exact_previously_reviewed_target_can_reuse_a_false_positive(self):
  m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
  self.assertTrue(m.same_review_target([492,261,502,266],[492,261,502,266]))
  self.assertFalse(m.same_review_target([492,261,502,266],[480,253,490,258]))
  self.assertFalse(m.same_review_target([492,261,502,266],[490,260,501,265]))
if __name__=='__main__':unittest.main()
