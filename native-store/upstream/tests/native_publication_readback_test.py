import base64,hashlib,importlib.util,json,types,unittest
from unittest.mock import patch
from pathlib import Path
spec=importlib.util.spec_from_file_location('native_publication_readback',Path(__file__).resolve().parents[1]/'scripts/publish-native-locales-release.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class ReadbackTests(unittest.TestCase):
 def fixture(self,name,body,served=None,size=None):
  reads=[];root='/home/example/public_html'
  def content(backend,directory,filename):
   reads.append('fileman')
   if len(body)>1048576:raise RuntimeError('fileman_size_limit')
   return body
  def public(relative):reads.append('https');return body if served is None else served
  d=types.SimpleNamespace(PUBLIC=root,CRITICAL=('index.php','.htaccess'),text_content=content,sha256=lambda b:hashlib.sha256(b).hexdigest(),listing=lambda backend,directory:{name.split('/')[-1]:{'type':'file','size':len(body)if size is None else size}})
  return d,types.SimpleNamespace(public_read=public),reads
 def test_large_native_file_uses_exact_https_bytes_when_editor_limit_is_exceeded(self):
  name='locales/fa.catalogue.json';body=b'x'*1048577;d,b,reads=self.fixture(name,body)
  module.verify_public(d,b,{name:body},https=False);self.assertEqual(reads,['https'])
 def test_large_native_file_rejects_wrong_physical_size(self):
  name='locales/kk.catalogue.json';body=b'x'*1048577;d,b,_=self.fixture(name,body,size=7)
  with self.assertRaisesRegex(RuntimeError,'public_file_metadata_mismatch'):module.verify_public(d,b,{name:body})
 def test_large_native_file_rejects_tampered_served_bytes(self):
  name='locales/ky.catalogue.json';body=b'x'*1048577;d,b,_=self.fixture(name,body,served=b'y'*len(body))
  with self.assertRaisesRegex(RuntimeError,'public_https_readback_mismatch'):module.verify_public(d,b,{name:body})
 def test_editor_fallback_is_not_available_for_unrelated_files(self):
  name='other.json';body=b'x'*1048577;d,b,reads=self.fixture(name,body)
  with self.assertRaisesRegex(RuntimeError,'fileman_size_limit'):module.verify_public(d,b,{name:body})
  self.assertEqual(reads,['fileman'])
 def test_small_assets_keep_both_fileman_and_https_readback(self):
  name='app.js';body=b'export const ready=true;';d,b,reads=self.fixture(name,body)
  module.verify_public(d,b,{name:body});self.assertEqual(reads,['fileman','https'])
 def test_large_original_uses_verified_base_bytes_without_editor_read(self):
  name='locales/de.catalogue.json';body=b'x'*1048577;d,b,reads=self.fixture(name,body)
  self.assertEqual(module.public_originals(d,b,{name:b'new'},{'public/'+name:body}),{name:body});self.assertEqual(reads,['https'])
 def test_large_original_rejects_changed_live_bytes(self):
  name='locales/fa.catalogue.json';body=b'x'*1048577;d,b,_=self.fixture(name,body,served=b'y'*len(body))
  with self.assertRaisesRegex(RuntimeError,'public_https_readback_mismatch'):module.public_originals(d,b,{name:b'new'},{'public/'+name:body})
 def backup_fixture(self):
  files={};d=types.SimpleNamespace(sha256=lambda body:hashlib.sha256(body).hexdigest())
  def upload(d,backend,directory,name,body,private=False):
   self.assertTrue(private);files[name]=body
  def read(d,backend,directory,name):
   self.assertLessEqual(len(files[name]),1000000);return files[name]
  return d,files,upload,read
 def test_large_backup_roundtrips_exact_bytes_in_private_ascii_chunks(self):
  d,files,upload,read=self.backup_fixture();name='locales/de.catalogue.json';body='Ürün معلومات 商品'.encode()*150000
  with patch.object(module,'remote_upload',upload),patch.object(module,'remote_read',read):module.backup_public_file(d,None,'/private-backup/public',name,body)
  manifest=json.loads(files[name+'.parts.json']);actual=b''.join(base64.b64decode(files[p['file']],validate=True)for p in manifest['parts'])
  self.assertEqual(actual,body);self.assertEqual(manifest['sha256'],d.sha256(actual));self.assertNotIn(name,files)
  for part in manifest['parts']:
   chunk=base64.b64decode(files[part['file']],validate=True);self.assertEqual(part['sha256'],d.sha256(chunk));self.assertEqual(part['bytes'],len(chunk))
 def test_large_backup_rejects_tampered_chunk(self):
  d,files,upload,read=self.backup_fixture();name='locales/fa.catalogue.json'
  with patch.object(module,'remote_upload',upload),patch.object(module,'remote_read',lambda *args:b'changed'):
   with self.assertRaisesRegex(RuntimeError,'public_backup_chunk_mismatch'):module.backup_public_file(d,None,'/backup',name,b'x'*1048577)
 def test_large_backup_rejects_tampered_manifest(self):
  d,files,upload,read=self.backup_fixture();name='locales/ky.catalogue.json'
  with patch.object(module,'remote_upload',upload),patch.object(module,'remote_read',lambda *args:b'changed'if args[-1].endswith('.parts.json')else read(*args)):
   with self.assertRaisesRegex(RuntimeError,'public_backup_manifest_mismatch'):module.backup_public_file(d,None,'/backup',name,b'x'*1048577)
 def test_small_backup_retains_single_file_and_exact_readback(self):
  d,files,upload,read=self.backup_fixture();name='app.js';body=b'export{}'
  with patch.object(module,'remote_upload',upload),patch.object(module,'remote_read',read):module.backup_public_file(d,None,'/backup',name,body)
  self.assertEqual(files,{name:body})
 def test_large_backup_has_closed_size_bound(self):
  d,files,upload,read=self.backup_fixture()
  with patch.object(module,'remote_upload',upload):
   with self.assertRaisesRegex(RuntimeError,'backup_dictionary_too_large'):module.backup_public_file(d,None,'/backup','locales/fa.catalogue.json',b'x'*16000001)
  self.assertEqual(files,{})
