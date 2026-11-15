import hashlib,importlib.util,json,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('lineage',R/'lib/media_scan_lineage.py')
class ScanLineageTests(unittest.TestCase):
 def test_cached_combination_pins_parent_receipt_report_frames_and_retained_hits(self):
  m=importlib.util.module_from_spec(s);s.loader.exec_module(m);dump=lambda v:json.dumps(v).encode();sha=lambda b:hashlib.sha256(b).hexdigest();path='artifacts/media-object-removal-20261102/web-supplemental/reports/'+'a'*64+'.json';parent={'fileSha256':'a'*64,'passVersion':'old','frames':[{'frame':0,'background':'white','rgbSha256':'b'*64}],'hits':[{'id':'old','box':[1,2,3,4]}]};body=dump(parent);index={'a'*64:{'path':path,'reportSha256':sha(body)}};child={**parent,'passVersion':'new','hits':[{'id':'new','box':[1,2,3,4]}],'scanLineage':{'path':path,'sha256':sha(body),'passVersion':'old'}};m.validate_combined_report(child,index,'old',lambda p:body)
  for changed in [{**child,'hits':[]},{**child,'frames':[{**parent['frames'][0],'rgbSha256':'c'*64}]},{**child,'scanLineage':{**child['scanLineage'],'sha256':'d'*64}}]:
   with self.assertRaisesRegex(ValueError,'lineage'):m.validate_combined_report(changed,index,'old',lambda p:body)
  with self.assertRaisesRegex(ValueError,'lineage'):m.validate_combined_report(child,index,'old',lambda p:b'changed')
if __name__=='__main__':unittest.main()
