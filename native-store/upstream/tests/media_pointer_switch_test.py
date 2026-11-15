from pathlib import Path
from types import SimpleNamespace
from unittest import mock
import importlib.util,unittest
R=Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('media_switch',R/'lib/media_pointer_switch.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class PointerSwitchTest(unittest.TestCase):
 def run_switch(self,b,old,new,plan,write,health):return m.switch_pointer(old,new,plan,read=lambda:b.pointer,write=lambda body:write(b,body),health=health)
 def fixture(self):
  plan={'releaseHash':'new','baseReleaseHash':'old','mediaVersion':'clean'};b=SimpleNamespace(pointer=b'old',public_health=lambda:{'status':'ok','releaseHash':'new','mediaVersion':'clean','checkoutEnabled':False,'mediaReady':True});return plan,b
 def test_lost_write_ack_is_accepted_only_after_actual_new_pointer_and_health(self):
  plan,b=self.fixture()
  def write(backend,body):backend.pointer=body;raise ConnectionError('lost ack')
  self.assertEqual(self.run_switch(b,b'old',b'new',plan,write,b.public_health)['releaseHash'],'new')
 def test_bad_new_health_restores_and_verifies_previous_pointer(self):
  plan,b=self.fixture();b.public_health=lambda:{'releaseHash':'old'}if b.pointer==b'old'else{'status':'failed'}
  with self.assertRaisesRegex(RuntimeError,'media_new_health_failed'):self.run_switch(b,b'old',b'new',plan,lambda backend,body:setattr(backend,'pointer',body),b.public_health)
  self.assertEqual(b.pointer,b'old')
 def test_concurrent_different_pointer_is_preserved(self):
  plan,b=self.fixture()
  def health():b.pointer=b'external';return{'status':'failed'}
  b.public_health=health
  with self.assertRaisesRegex(RuntimeError,'concurrent'):self.run_switch(b,b'old',b'new',plan,lambda backend,body:setattr(backend,'pointer',body),b.public_health)
  self.assertEqual(b.pointer,b'external')
if __name__=='__main__':unittest.main()
