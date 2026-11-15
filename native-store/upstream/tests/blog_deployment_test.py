from pathlib import Path
import importlib.util,unittest,copy,json,hashlib
R=Path(__file__).resolve().parents[1]
def module(name,file):
 s=importlib.util.spec_from_file_location(name,R/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=module('blog_publish_test','scripts/publish-blog.py');timer=module('blog_timer_test','scripts/install-blog-timer.py')
class BlogPublicationTests(unittest.TestCase):
 def test_existing_combined_server_timer_is_reused_and_wrong_schedule_is_rejected(self):
  row={'command':'/usr/local/bin/php -d display_errors=0 -d log_errors=0 -d zend.exception_ignore_args=1 /home/test/nodeno-search/search-notifications-runner.php > /dev/null 2>&1',**dict.fromkeys(['minute','hour','day','month','weekday'],'*')};self.assertIs(timer.integrated_timer([row],'/home/test'),row)
  with self.assertRaisesRegex(RuntimeError,'duplicate'):timer.integrated_timer([row,row],'/home/test')
  row['hour']='2'
  with self.assertRaisesRegex(RuntimeError,'schedule_changed'):timer.integrated_timer([row],'/home/test')
 def test_stale_live_release_stops_before_any_mutation(self):
  class Backend:
   def public_health(self):return {'releaseHash':'newer-live','mediaReady':True}
   def upload(self,*args):raise AssertionError('a stale release wrote to hosting')
  with self.assertRaisesRegex(RuntimeError,'live_base_changed'):m.assert_current(Backend(),{'baseReleaseHash':'old'})
 def test_content_gate_rejects_catalogue_changes_even_when_hidden_in_proof(self):
  old={'manifest':{'releaseHash':'a'},'all_bytes':{'private/catalog.json':b'original'}}
  after={'manifest':{'releaseHash':'b'},'all_bytes':{'private/catalog.json':b'changed','private/release.json':b'{}'}}
  proof={'baseReleaseHash':'a','releaseHash':'b','changedFiles':['private/catalog.json']}
  with self.assertRaisesRegex(RuntimeError,'catalogue_commerce_or_media_changed'):m.verify_scope(old,after,proof,{'private/catalog.json':b'changed'})
 def test_unrelated_cron_signature_catches_schedule_changes_but_ignores_line_renumbering(self):
  rows=[{'command':'other-task','minute':'*','hour':'*','count':1},{'command':'blog','minute':'*/5','count':2}]
  a=timer.cron_signature(rows,'blog');b=copy.deepcopy(rows);b[0]['count']=9;self.assertEqual(a,timer.cron_signature(b,'blog'));b[0]['minute']='*/2';self.assertNotEqual(a,timer.cron_signature(b,'blog'))
if __name__=='__main__':unittest.main()
