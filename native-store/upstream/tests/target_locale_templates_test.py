import unittest
from lib.target_locale_templates import protected_template,terminology_key
class TemplateTests(unittest.TestCase):
 def test_terminology_lookup_matches_dotted_and_dotless_regex_variants(self):
  for value in ['NİL','Nıl','NIL','nil']:
   self.assertEqual(terminology_key(value),'nil')
 def test_ordinary_hyphenated_phrases_and_email_label_remain_translatable(self):
  for text in ['US-registered company','E-mail','VAT-inclusive prices']:
   value,bindings=protected_template(text,(),True);self.assertEqual(value,text);self.assertEqual(bindings,{})
  for text,material,description in [('PVC-coated panel','PVC','-coated panel'),('MDF-based product','MDF','-based product')]:
   value,bindings=protected_template(text,(),True);self.assertIn(material,bindings.values());self.assertIn(description,value)
 def test_codes_numbers_dimensions_and_brand_identity_survive(self):
  source='NODENO ND-001: 5 sets, 207 cm, 10 × 20 mm';value,bindings=protected_template(source,(),True)
  self.assertNotIn('NODENO',value);self.assertIn('ND-001',bindings.values());self.assertIn('207 cm',bindings.values());self.assertIn('10 × 20 mm',bindings.values())
 def test_ui_words_are_not_mistaken_for_models(self):
  value,bindings=protected_template('Good design. Easy living.',('Easy',),True);self.assertEqual(bindings,{});self.assertIn('Easy',value)
  value,bindings=protected_template('Easy 5-shelf bookcase',('Easy',),False);self.assertIn('Easy',bindings.values())
 def test_registered_legal_entity_is_preserved_in_full(self):
  value,bindings=protected_template('The seller is PTYS Technologies L.L.C.',(),True)
  self.assertIn('PTYS Technologies L.L.C.',bindings.values());self.assertNotIn('Technologies',value)
 def test_currency_codes_and_units_are_facts_inside_a_sentence(self):
  value,bindings=protected_template('The price is USD 50 per m², width (mm).',(),True)
  self.assertIn('USD',bindings.values());self.assertIn('m²',bindings.values());self.assertIn('mm',bindings.values())
 def test_factory_model_and_finish_designations_are_not_translated(self):
  value,bindings=protected_template('ND 001 TİP 2 MDF PVC RAL 9003',(),True)
  for code in ['ND 001','TİP','MDF','PVC','RAL']:self.assertIn(code,bindings.values())
 def test_embedded_alphanumeric_model_codes_remain_whole(self):
  _,bindings=protected_template('Elegant ND683 Interior Door Set',('Elegant',),False)
  self.assertIn('ND683',bindings.values())
 def test_certificate_identifier_is_preserved_without_freezing_english_prose(self):
  value,bindings=protected_template('E1-certified materials',(),True)
  self.assertEqual(list(bindings.values()),['E1']);self.assertIn('-certified',value)
if __name__=='__main__':unittest.main()
