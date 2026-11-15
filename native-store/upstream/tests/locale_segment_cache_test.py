import unittest
from lib.target_locale_templates import canonical_segment,rebind_segment
class SegmentCacheTests(unittest.TestCase):
 def test_same_sentence_reuses_translation_without_swapping_source_facts(self):
  a,ma=canonical_segment('Width ZXQ7ZXQ and height ZXQ2ZXQ')
  b,mb=canonical_segment('Width ZXQ1ZXQ and height ZXQ9ZXQ')
  self.assertEqual(a,b)
  target='Height ZXQ1ZXQ; width ZXQ0ZXQ'
  self.assertEqual(rebind_segment(target,ma),'Height ZXQ2ZXQ; width ZXQ7ZXQ')
  self.assertEqual(rebind_segment(target,mb),'Height ZXQ9ZXQ; width ZXQ1ZXQ')
 def test_duplicate_references_and_unknown_facts(self):
  source,mapping=canonical_segment('ZXQ8ZXQ + ZXQ8ZXQ')
  self.assertEqual(source,'ZXQ0ZXQ + ZXQ0ZXQ');self.assertEqual(rebind_segment(source,mapping),'ZXQ8ZXQ + ZXQ8ZXQ')
  with self.assertRaises(ValueError):rebind_segment('ZXQ99ZXQ',mapping)
if __name__=='__main__':unittest.main()
