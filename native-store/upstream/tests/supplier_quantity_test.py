"""Exercise PHP quote calculation against tampered quantities and client prices."""
import json,subprocess,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class QuantityTests(unittest.TestCase):
 def quote(self,quantity,parent=False,extra=None):
  p={'id':'alka-test','code':'ND-ALK-TEST','name':{'tr':'Çıta'},'productType':'supplier-item','quantityPolicy':{'minimum':3,'step':3},'saleUnit':'metre','salePriceMinor':2400,'priceTaxPolicy':'unspecified','variationSelectionRequired':parent}
  item={'id':p['id'],'quantity':quantity,**(extra or{})}
  php="require 'hosting/door-commerce.php';$v=json_decode(stream_get_contents(STDIN),true);try{echo json_encode(nodenoCommerceQuote(['products'=>[$v['p']]],[$v['item']],'TR'));}catch(Throwable $e){echo json_encode(['error'=>$e->getMessage()]);}"
  proc=subprocess.run([str(R/'artifacts/runtime-php/php.exe'),'-r',php],input=json.dumps({'p':p,'item':item}).encode(),capture_output=True,cwd=R);self.assertEqual(proc.returncode,0,proc.stderr);return json.loads(proc.stdout)
 def test_unit_price_times_actual_metres(self):
  q=self.quote(6);self.assertEqual(q['subtotalTryMinor'],14400);self.assertEqual(q['lines'][0]['saleUnit'],'metre');self.assertIsNone(q['lines'][0]['taxIncluded']);self.assertFalse(q['checkoutEnabled'])
 def test_tampered_below_minimum_and_wrong_step_rejected(self):
  for qty in [1,4]:self.assertEqual(self.quote(qty)['error'],'commerce_quantity_invalid')
 def test_unselected_parent_and_injected_price_rejected(self):
  self.assertEqual(self.quote(3,True)['error'],'commerce_variant_required');self.assertEqual(self.quote(3,extra={'salePriceMinor':1})['error'],'commerce_item_invalid')
if __name__=='__main__':unittest.main()
