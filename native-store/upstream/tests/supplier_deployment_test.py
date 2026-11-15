import importlib.util
import unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('supplier_deploy_helper',R/'scripts/deploy-cpanel.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
class SupplierDeploymentTests(unittest.TestCase):
 def test_backup_reader_preserves_literal_html_inside_javascript(self):
  original='const view=`<header class="topbar"><div>Ürünler</div></header>`;'
  class Cpanel:
   def read(self,module,action,**params):
    content=original if params.get('update_html_document_encoding')==0 else original.replace('<header class="topbar">','<header class="topbar"><meta charset="utf-8">')
    return {'status':1,'data':{'content':content}}
  self.assertEqual(d.text_content(Cpanel(),'/home/nodenoho/nodeno-backups/test','admin.js'),original.encode())
if __name__=='__main__':unittest.main()
