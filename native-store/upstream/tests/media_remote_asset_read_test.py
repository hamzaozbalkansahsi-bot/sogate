import importlib.util,types,unittest
from pathlib import Path
from unittest.mock import patch
R=Path(__file__).resolve().parents[1]
class RawAdminReadTests(unittest.TestCase):
 def module(self):
  s=importlib.util.spec_from_file_location('raw_admin_read',R/'lib/media_remote_asset_read.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 def test_literal_html_inside_javascript_is_read_as_binary_without_editor_transformation(self):
  m=self.module();original=b'const html="<html><head></head></html>";';seen=[]
  class Response:
   status=200
   def read(self,n):return original
   def getheader(self,n,default=None):return str(len(original))if n=='Content-Length'else default
  class Connection:
   def __init__(self,*a,**kw):pass
   def request(self,method,path,headers):seen.append((method,path))
   def getresponse(self):return Response()
   def close(self):pass
  d=types.SimpleNamespace(PUBLIC='/home/store/public_html',HOME='/home/store',HOST='example.invalid',PORT=2083,remote_path=lambda *a,**kw:None);backend=types.SimpleNamespace(probe=types.SimpleNamespace(credentials=lambda:('isolated','dummy')))
  with patch.object(m.http.client,'HTTPSConnection',Connection):actual=m.read_admin_bytes(backend,d,d.PUBLIC,'admin.js')
  self.assertEqual(actual,original);self.assertEqual(seen,[('GET','/download?file=%2Fhome%2Fstore%2Fpublic_html%2Fadmin.js')])
 def test_other_files_and_unrelated_directories_are_refused_before_credentials(self):
  m=self.module();d=types.SimpleNamespace(PUBLIC='/home/store/public_html',HOME='/home/store');backend=types.SimpleNamespace(probe=types.SimpleNamespace(credentials=lambda:self.fail('out of scope credentials read')))
  for folder,name in [('/home/store/data','admin.js'),('/home/store/public_html','accounts.sqlite')]:
   with self.assertRaises(ValueError):m.read_admin_bytes(backend,d,folder,name)
if __name__=='__main__':unittest.main()
