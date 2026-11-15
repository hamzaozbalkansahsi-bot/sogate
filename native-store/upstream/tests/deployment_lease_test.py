import importlib.util,json,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('deploy_lease',R/'scripts/deploy-cpanel.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
class Backend:
 def __init__(self,store):self.store=store
 def api2(self,fn,**kw):
  if fn=='mkdir':
   path=kw['path']+'/'+kw['name']
   if path in self.store:raise d.DeployError('directory_exists')
   self.store[path]={}
  elif kw['op']=='rename':
   source=d.HOME+'/'+kw['sourcefiles'];target=d.HOME+'/'+kw['destfiles'];self.store[target]=self.store.pop(source)
 def upload(self,path,files):self.store[path].update(files)
 def read(self,mod,fn,**kw):return {'status':1,'data':{'content':self.store[kw['dir']][kw['file']].decode()}}
class DeploymentLeaseTests(unittest.TestCase):
 def test_check_to_write_and_rollback_windows_exclude_second_deployer(self):
  store={};a=Backend(store);b=Backend(store)
  with d.deployment_lease(a):
   for window in ['after_backup_check_before_switch','after_failed_health_check_before_rollback']:
    with self.subTest(window=window):
     with self.assertRaises(d.DeployError):
      with d.deployment_lease(b):self.fail('second pointer writer entered')
   d.require_deployment_lease(a)
  with d.deployment_lease(b):d.require_deployment_lease(b)
 def test_unowned_pointer_write_is_rejected(self):
  with self.assertRaisesRegex(d.DeployError,'lease'):d.require_deployment_lease(Backend({}))
 def test_changed_owner_is_not_released_over_another_writer(self):
  store={};a=Backend(store)
  with self.assertRaisesRegex(d.DeployError,'lease'):
   with d.deployment_lease(a):store[d.HOME+'/nodeno-deploy-lock']['owner.json']=b'changed'
  self.assertIn(d.HOME+'/nodeno-deploy-lock',store)
if __name__=='__main__':unittest.main()
