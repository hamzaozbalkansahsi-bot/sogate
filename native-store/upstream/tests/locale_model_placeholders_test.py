import unittest
from lib.target_locale_templates import model_placeholders,restore_model_placeholders
class ModelPlaceholderTest(unittest.TestCase):
 def test_model_transport_preserves_repeated_roles_and_unicode_body(self):
  source='Width ZXQ8ZXQ and height ZXQ2ZXQ. Repeat ZXQ8ZXQ.'
  transported,mapping=model_placeholders(source)
  self.assertEqual(transported,'Width 870000 and height 870001. Repeat 870000.')
  self.assertEqual(restore_model_placeholders('Breite 870 000, Höhe 870001; 870000.',mapping),'Breite ZXQ8ZXQ, Höhe ZXQ2ZXQ; ZXQ8ZXQ.')
 def test_only_whole_markers_are_restored(self):
  _,mapping=model_placeholders('ZXQ0ZXQ')
  self.assertEqual(restore_model_placeholders('18700001',mapping),'18700001')
if __name__=='__main__':unittest.main()
