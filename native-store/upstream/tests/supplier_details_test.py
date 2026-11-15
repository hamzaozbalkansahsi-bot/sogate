import unittest,json,hashlib,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'artifacts/supplier-expansion/publication/detail-test';P.mkdir(exist_ok=True)
class DetailTests(unittest.TestCase):
 def setUp(self):
  self.body=json.dumps({'id':'alka-test','description':{l:'Verified '+l for l in ['tr','en','ru','ar']}},separators=(',',':')).encode();self.sha=hashlib.sha256(self.body).hexdigest();(P/'supplier-details.bin').write_bytes(self.body);(P/'supplier-details.json').write_text(json.dumps({'products':{'alka-test':{'offset':0,'bytes':len(self.body),'sha256':self.sha}}}));self.product={'id':'alka-test','productType':'supplier-item','supplierDetailsHash':self.sha}
 def call(self,id='alka-test'):
  payload={'id':id,'catalog':{'products':[self.product]}};code="require 'hosting/supplier-products.php';$v=json_decode(stream_get_contents(STDIN),true);try{echo json_encode(['value'=>nodenoSupplierDetails('artifacts/supplier-expansion/publication/detail-test',$v['id'],$v['catalog'])]);}catch(Throwable $e){echo json_encode(['error'=>$e->getMessage()]);}"
  r=subprocess.run([str(R/'artifacts/runtime-php/php.exe'),'-r',code],input=json.dumps(payload).encode(),capture_output=True,cwd=R);self.assertEqual(r.returncode,0,r.stderr);return json.loads(r.stdout)
 def test_reads_only_selected_hash_bound_frame(self):self.assertEqual(self.call()['value']['description']['ar'],'Verified ar')
 def test_tampered_bytes_fail_closed(self):
  (P/'supplier-details.bin').write_bytes(self.body.replace(b'Verified',b'Corrupt!'));self.assertIn('hash mismatch',self.call()['error'])
 def test_unknown_hidden_and_path_inputs_are_inaccessible(self):
  for id in ['unknown','../config','alka-test/../../config']:self.assertIsNone(self.call(id)['value'])
  self.product['hidden']=True;self.assertIsNone(self.call()['value'])
if __name__=='__main__':unittest.main()
