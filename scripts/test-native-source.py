#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-source.py
# Açıklama   : NODENO doğrudan kaynak kopyasının bütünlüğünü ve veri sınırını denetler.
import hashlib,json,unittest
from pathlib import Path
from native_fixture_safety import safe_fixture

ROOT=Path(__file__).resolve().parent.parent
class DirectCopyTest(unittest.TestCase):
 def test_source_matches_with_recorded_synthetic_fixture_redactions(self):
  manifest_path=ROOT/'native-store/source-manifest.json';self.assertTrue(manifest_path.is_file(),'Direct NODENO source snapshot is missing')
  manifest=json.loads(manifest_path.read_text('utf8'));self.assertGreater(len(manifest['files']),400)
  for name,sha in manifest['files'].items():
   self.assertEqual(hashlib.sha256((ROOT/'native-store/upstream'/name).read_bytes()).hexdigest(),sha,name)
   original=(ROOT.parent/'Nodeno'/name).read_bytes()
   self.assertEqual(hashlib.sha256(safe_fixture(name,original)).hexdigest(),sha,'Source changed: '+name)
   if name in manifest.get('fixtureSanitizations',{}):self.assertEqual(hashlib.sha256(original).hexdigest(),manifest['fixtureSanitizations'][name]['sourceSha256'],name)
  for name in ['web/app.js','web/admin.js','web/admin-editor.js','web/payments.js','web/shopping-core.js','web/blog-entry.js','hosting/index.php','hosting/payments.php','hosting/control-store.php','hosting/account.php']:
   self.assertIn(name,manifest['files'])
 def test_no_customer_runtime_or_business_catalog_copied(self):
  folder=ROOT/'native-store/upstream';self.assertTrue(folder.is_dir())
  for p in folder.rglob('*'):
   if p.is_file():
    self.assertNotIn(p.suffix.lower(),['.sqlite','.db','.bin','.zip'])
    self.assertFalse(p.name.startswith(('.env','client_secret')) or p.name.endswith('.local'))
    self.assertNotIn('catalog-source.json',p.parts)
  self.assertFalse((folder/'data/brand.json').exists())

if __name__=='__main__':unittest.main()
