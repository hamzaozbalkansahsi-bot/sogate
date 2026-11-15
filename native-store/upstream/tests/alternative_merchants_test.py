import importlib.util,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('am',R/'scripts/verify-alternative-merchants.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class AlternativeMerchantTests(unittest.TestCase):
 def test_manufacturer_evidence_is_bound_to_brand_and_exact_merchant(self):
  seller={'id':981893,'score':9.7,'authorized':False};proof={'981893':{'reviewed':True,'nameAndAddressMatched':True,'issuer':'Filli Boya','merchantId':'981893'}}
  self.assertTrue(m.independent(seller,'Filli Boya',proof))
  self.assertFalse(m.independent(seller,'Bianca',proof))
  self.assertFalse(m.independent({**seller,'id':1},'Filli Boya',proof))
  self.assertFalse(m.independent({**seller,'score':8.8},'Filli Boya',proof))
  self.assertFalse(m.independent(seller,'Filli Boya',{'981893':{**proof['981893'],'nameAndAddressMatched':False}}))
if __name__=='__main__':unittest.main()
