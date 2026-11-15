import unittest,importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('supplier_seo_content',Path(__file__).resolve().parents[1]/'lib/supplier_seo_content.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class MaterialTests(unittest.TestCase):
 def test_explicit_beech_choice_never_has_pine_or_invoice_in_its_name(self):
  p={'id':'x','modelId':'alka-family-30373','code':'ND-TEST','salePriceMinor':10200,'images':['approved'],'name':dict.fromkeys(m.LOCALES,'Pine')};source={'variantAttributes':[{'name':'Ağaç Cinsi','value':'kayin'}]};detail={'id':'x','description':dict.fromkeys(m.LOCALES,'3 m')};new,body=m.enrich_supplier(p,source,detail)
  self.assertIn('Beech',new['name']['en']);self.assertNotIn('Pine',new['name']['en']);self.assertNotIn('Invoice',new['name']['en']);self.assertEqual((new['code'],new['salePriceMinor'],new['images']),('ND-TEST',10200,['approved']));self.assertEqual(body,detail)
 def test_selected_chestnut_replaces_inherited_lime_fact_without_changing_measurement(self):
  p={'id':'x'};source={'variantAttributes':[{'name':'Ağaç Cinsi','value':'kestane'}]};detail={'id':'x','description':{'tr':'Ağaç cinsi ıhlamur ağacıdır.\n\n3 metre','en':'Lime wood\n\n3 metre','ru':'Липа\n\n3 m','ar':'زيزفون\n\n3 m'}};_,d=m.enrich_supplier(p,source,detail);self.assertEqual(d['description']['en'],'Wood species: Chestnut.\n\n3 metre');self.assertIn('Ihlamur',m.MATERIALS['ihlamur'][0])
if __name__=='__main__':unittest.main()
