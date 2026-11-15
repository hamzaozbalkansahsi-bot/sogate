import importlib.util,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class PublicSwitchTests(unittest.TestCase):
 def module(self):
  s=importlib.util.spec_from_file_location('public_switch',R/'lib/media_public_switch.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 def test_partial_public_failure_restores_old_assets_and_leaves_unused_new_module(self):
  m=self.module();files={'admin.js':b'old-js','admin.html':b'old-html'};previous={**files,'helper.js':None};proposed={'helper.js':b'new-helper','admin.js':b'new-js','admin.html':b'new-html'}
  def write(name,body):
   if name=='admin.html'and body==b'new-html':raise OSError('transport failed')
   files[name]=body
  with self.assertRaises(OSError):
   with m.public_assets_transaction(previous,proposed,read=files.get,write=write):pass
  self.assertEqual(files['admin.js'],b'old-js');self.assertEqual(files['admin.html'],b'old-html');self.assertEqual(files['helper.js'],b'new-helper')
 def test_lost_upload_ack_is_accepted_only_after_exact_public_readback(self):
  m=self.module();files={'admin.js':b'old'}
  def write(name,body):files[name]=body;raise OSError('lost acknowledgement')
  with m.public_assets_transaction({'admin.js':b'old'},{'admin.js':b'new'},read=files.get,write=write):self.assertEqual(files['admin.js'],b'new')
 def test_unexpected_concurrent_public_bytes_are_preserved(self):
  m=self.module();files={'admin.js':b'old'}
  with self.assertRaisesRegex(RuntimeError,'concurrent'):
   with m.public_assets_transaction({'admin.js':b'old'},{'admin.js':b'new'},read=files.get,write=lambda n,b:files.__setitem__(n,b)):
    files['admin.js']=b'unexpected';raise OSError('health failed')
  self.assertEqual(files['admin.js'],b'unexpected')
 def test_stale_public_preflight_prevents_any_writes(self):
  m=self.module();writes=[]
  with self.assertRaisesRegex(RuntimeError,'concurrent'):
   with m.public_assets_transaction({'admin.js':b'old'},{'admin.js':b'new'},read=lambda n:b'unexpected',write=lambda n,b:writes.append(n)):pass
  self.assertEqual(writes,[])
 def test_complete_health_is_checked_only_after_both_pointer_and_public_bytes_match(self):
  m=self.module();files={'admin.js':b'old'};pointer=[b'old-pointer'];calls=[]
  def health():
   calls.append((pointer[0],files['admin.js']))
   if (pointer[0],files['admin.js'])==(b'new-pointer',b'new'):return {'release':'new'}
   if (pointer[0],files['admin.js'])==(b'old-pointer',b'old'):return {'release':'old'}
   raise RuntimeError('actual bootstrap public fingerprint mismatch')
  result=m.switch_with_public_assets(b'old-pointer',b'new-pointer',{'admin.js':b'old'},{'admin.js':b'new'},read_pointer=lambda:pointer[0],write_pointer=lambda v:pointer.__setitem__(0,v),read_asset=files.get,write_asset=lambda n,v:files.__setitem__(n,v),health=health,is_new=lambda h:h['release']=='new',is_old=lambda h:h['release']=='old')
  self.assertEqual(result,{'release':'new'});self.assertEqual(calls,[(b'new-pointer',b'new')])
 def test_failed_combined_health_restores_both_before_validating_old_release(self):
  m=self.module();files={'admin.js':b'old'};pointer=[b'old-pointer'];checks=[];writes=[]
  def health():
   checks.append((pointer[0],files['admin.js']))
   return {'release':'old'if checks[-1]==(b'old-pointer',b'old')else'failed'}
  def write_pointer(value):writes.append(value);pointer[0]=value
  with self.assertRaisesRegex(RuntimeError,'new release health'):
   m.switch_with_public_assets(b'old-pointer',b'new-pointer',{'admin.js':b'old'},{'admin.js':b'new'},read_pointer=lambda:pointer[0],write_pointer=write_pointer,read_asset=files.get,write_asset=lambda n,v:files.__setitem__(n,v),health=health,is_new=lambda h:h['release']=='new',is_old=lambda h:h['release']=='old')
  self.assertEqual(checks,[(b'new-pointer',b'new'),(b'old-pointer',b'old')]);self.assertEqual(writes,[b'new-pointer',b'old-pointer'])
 def test_failed_old_health_never_reactivates_the_failed_new_release(self):
  m=self.module();files={'a':b'old'};pointer=[b'old-pointer'];writes=[]
  def write_pointer(value):pointer[0]=value;writes.append(value)
  with self.assertRaisesRegex(RuntimeError,'not reactivated'):
   m.switch_with_public_assets(b'old-pointer',b'new-pointer',{'a':b'old'},{'a':b'new'},read_pointer=lambda:pointer[0],write_pointer=write_pointer,read_asset=files.get,write_asset=lambda n,v:files.__setitem__(n,v),health=lambda:{},is_new=lambda h:False,is_old=lambda h:False)
  self.assertEqual(pointer[0],b'old-pointer');self.assertEqual(writes,[b'new-pointer',b'old-pointer']);self.assertEqual(files['a'],b'old')
if __name__=='__main__':unittest.main()
