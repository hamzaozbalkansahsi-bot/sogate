import unittest
from lib.target_locale_templates import translation_quality_errors
class TranslationQualityTest(unittest.TestCase):
 def test_added_numbers_and_runaway_generation_are_rejected(self):
  self.assertIn('new_numeric_fact',translation_quality_errors('Previous price','Vorheriger Preis 10,95 €','de'))
  self.assertIn('repetition',translation_quality_errors('Seller contact','The'*30,'de'))
 def test_protected_facts_and_reviewed_loanwords_remain_valid(self):
  self.assertEqual(translation_quality_errors('ZXQ0ZXQ Cabinet','ZXQ0ZXQ Schrank','de'),[])
  self.assertEqual(translation_quality_errors('Material','Material','de',reviewed=True),[])
  self.assertEqual(translation_quality_errors('en','en','fa'),[])
  self.assertIn('fact_changed',translation_quality_errors('ZXQ0ZXQ Cabinet','Schrank','de'))
 def test_english_prose_is_not_accepted_as_a_cyrillic_translation(self):
  self.assertIn('foreign_prose',translation_quality_errors('A cabinet for your home','Шкаф. A cabinet for your home with a beautiful wooden finish.','kk'))
 def test_a_literal_postal_address_does_not_hide_untranslated_body_prose(self):
  source='Address: ZXQ0ZXQ N Gould St Ste N, Sheridan, WY ZXQ1ZXQ, United States.'
  target='Дарек: ZXQ0ZXQ N Gould St Ste N, Sheridan, WY ZXQ1ZXQ, United States.'
  self.assertEqual(translation_quality_errors(source,target,'ky'),[])
  self.assertIn('foreign_prose',translation_quality_errors(source,target+' This entire explanatory paragraph was incorrectly left in English.','ky'))
if __name__=='__main__':unittest.main()
