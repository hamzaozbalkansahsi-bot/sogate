import hashlib,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];spec=importlib.util.spec_from_file_location('release_safety',R/'lib/media_release_safety.py')
class SafetyTests(unittest.TestCase):
 def module(self):m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 def test_approval_is_for_exact_release_media_pdf_policy_and_bytes(self):
  m=self.module();expected={'releaseHash':'new','mediaVersion':'clean','pdfSha256':'pdf','cleanupSha256':'manifest','objectPolicySha256':'policy','releaseFilesSha256':{'private/catalog.json':'c'}};review={'approved':True,**expected};m.validate_independent_review(review,expected)
  for k in expected:
   bad={**expected,k:'changed'}
   with self.subTest(key=k),self.assertRaisesRegex(ValueError,'review'):m.validate_independent_review(review,bad)
 def test_browser_count_cannot_replace_required_views_or_actual_render_response(self):
  m=self.module();manifest={'references':{'7:0':'k'},'images':{'k':{'outputSha':'bytes','width':10,'height':10}}};plan={'releaseHash':'release','mediaVersion':'version'};views=[{'device':d,'product':'7','galleryIndex':0,'imageSha256':'bytes','width':10,'height':10,'actualImageResponse':True,'visualReview':True,'screenshotPath':d,'screenshotSha256':m.sha(d.encode())}for d in ['desktop','mobile']];r={'phase':'live','origin':'https://nodenohome.com','releaseHash':'release','mediaVersion':'version','allBrowserImageBytesExact':True,'views':views};m.validate_live_browser(r,plan,manifest,lambda p:p.encode(),products=['7'])
  for bad in [{**r,'views':[views[0],views[0]]},{**r,'mediaVersion':'old'},{**r,'views':[{**v,'actualImageResponse':False}for v in views]}]:
   with self.assertRaisesRegex(ValueError,'browser'):m.validate_live_browser(bad,plan,manifest,lambda p:p.encode(),products=['7'])
 def test_interrupted_multi_file_promotion_is_idempotently_recovered(self):
  m=self.module()
  with tempfile.TemporaryDirectory()as td:
   p=Path(td);rows=[]
   for i in range(4):
    a=p/f'target{i}';b=p/f'staged{i}';c=p/f'previous{i}';a.write_bytes(b'old');b.write_bytes(b'new');c.write_bytes(b'old');rows.append({'target':str(a),'staged':str(b),'previous':str(c),'oldSha256':m.sha(b'old'),'newSha256':m.sha(b'new')})
   def crash(i):
    if i==1:raise KeyboardInterrupt('simulated process interruption')
   with self.assertRaises(KeyboardInterrupt):m.promote_transaction(rows,p/'journal.json',after_replace=crash)
   self.assertEqual((p/'target0').read_bytes(),b'new');self.assertEqual((p/'target3').read_bytes(),b'old');m.promote_transaction(rows,p/'journal.json');m.promote_transaction(rows,p/'journal.json');self.assertTrue(all(Path(r['target']).read_bytes()==b'new'for r in rows))
   (p/'target0').write_bytes(b'concurrent edit')
   with self.assertRaisesRegex(ValueError,'concurrent'):m.promote_transaction(rows,p/'journal.json')
 def test_https_receipt_requires_every_alias_old_and_fresh_version_url(self):
  m=self.module();plan={'releaseHash':'release','mediaVersion':'new','baseMediaVersion':'old'};manifest={'references':{'7:0':'key'},'images':{'key':{'outputSha':'body'}}};aliases=['nodenohome.com','www.nodenohome.com','nodenohome.com.tr','www.nodenohome.com.tr'];rows=[{'alias':h,'key':'key','reference':'7:0','mode':mode,'urlVersion':'old'if mode=='previous'else'new','bodySha256':'body','status':200}for h in aliases for mode in ['previous','fresh']];r={'releaseHash':'release','mediaVersion':'new','aliases':aliases,'records':rows,'health':{h:{'releaseHash':'release','mediaVersion':'new','mediaReady':True}for h in aliases}}
  m.validate_https_media(r,plan,manifest,['key'])
  for bad in [{**r,'records':rows[:4]},{**r,'records':rows[:-1]+[rows[0]]},{**r,'mediaVersion':'old'},{**r,'records':[{**v,'urlVersion':'old'}for v in rows]}]:
   with self.assertRaisesRegex(ValueError,'HTTPS'):m.validate_https_media(bad,plan,manifest,['key'])
 def test_optimized_python_refuses_safety_operations(self):
  self.module();code=f"import importlib.util;s=importlib.util.spec_from_file_location('safety',{str(R/'lib/media_release_safety.py')!r});m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.require_safe_runtime()";r=subprocess.run([sys.executable,'-O','-c',code],capture_output=True);self.assertNotEqual(r.returncode,0);self.assertIn(b'optimized',r.stderr)
if __name__=='__main__':unittest.main()
