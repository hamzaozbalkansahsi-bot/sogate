import importlib.util,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
class PrivateMaintenanceRunnerTest(unittest.TestCase):
 def load(self):
  spec=importlib.util.spec_from_file_location('nodeno_private_runner',ROOT/'scripts/run-private-maintenance.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
 def test_command_is_bounded_and_contains_only_nonce(self):
  m=self.load();command=m.build_command('a'*64);self.assertIn('/home/nodenoho/nodeno-maintenance/private-maintenance.php',command);self.assertNotIn('password',command)
  for invalid in ['../outside','a'*63,'a'*64+';whoami']:
   with self.assertRaises(ValueError):m.build_command(invalid)
 def test_removal_targets_only_its_own_current_job(self):
  m=self.load();calls=[];command=m.build_command('b'*64)
  def cron(backend,action,**params):
   calls.append((action,params));return [{'command':'OTHER JOB','count':1},{'command':command,'count':2}]if action=='listcron'else[]
  with patch.object(m,'call_cron',side_effect=cron):m.cleanup_job(object(),command)
  self.assertEqual(calls[-1],('remove_line',{'line':2}));self.assertEqual(len(calls),2)
if __name__=='__main__':unittest.main()
