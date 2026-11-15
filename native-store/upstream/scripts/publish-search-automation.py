"""Use the existing shared-lease, readback and rollback publisher for a scoped search release."""
from pathlib import Path
import hashlib,importlib.util,json,sys,types
R=Path(__file__).resolve().parents[1];E=R/'artifacts/search-automation-20261112'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,R/path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def verify(base,new,proof,expected):
 assert not new['manifest'].get('testOnly')
 assert base['manifest']['releaseHash']==proof['baseReleaseHash'] and new['manifest']['releaseHash']==proof['releaseHash']
 changed={n for n,b in new['all_bytes'].items()if base['all_bytes'].get(n)!=b};assert changed==set(proof['changedFiles'])|{'private/release.json'}
 allowed={'private/'+n for n in ['search-notifications.php','control-indexnow.php','seo.php','config.json','index.html','blog-admin.html','blog-admin.php','blog-bank.json','blog-http.php','blog-i18n.php','blog-images.bin','blog-images.json','blog-store.php','blog-worker.php','blog.php','date-time.php']}|{'public/'+n for n in ['.htaccess','index.php','blog-admin.js','blog-entry.js','blog-tools.js','blog.css','seo-core.js','seo-ui.js','app.js']}
 assert set(expected)<=allowed and set(expected)==set(proof['changedFiles']);assert all(new['all_bytes'][n]==b for n,b in expected.items());assert all(new['all_bytes'].get(n)==b for n,b in base['all_bytes'].items()if n not in changed)
 before=json.loads(base['all_bytes']['private/config.json']);after=json.loads(new['all_bytes']['private/config.json']);after.pop('socials',None);before.pop('socials',None);assert before==after
 for n in proof['changedFiles']:
  if n.startswith('private/')and n.endswith('.php')and n!='private/seo.php':assert new['all_bytes'][n]==(R/'hosting'/n[8:]).read_bytes(),'reviewed_php_changed'
  if n.startswith('public/')and n[7:]in['blog-admin.js','blog-entry.js','blog-tools.js','blog.css']:assert new['all_bytes'][n]==(R/'web'/n[7:]).read_bytes(),'reviewed_ui_changed'
 bank=json.loads(new['all_bytes']['private/blog-bank.json']);assert bank.get('publicationReady')is True and bank.get('publicationScope')in ['reviewed-four-language-subset','reviewed-four-language-bank'];assert len(bank['articles'])==proof['editorial']['approvedArticles'];index=json.loads(new['all_bytes']['private/blog-images.json'])['files'];blob=new['all_bytes']['private/blog-images.bin'];compiler=load('search_final_editorial','scripts/compile-blog.py')
 for article in bank['articles']:
  assert set(article.get('locales',{}))>={'en','ru','ar'}
  for lang in ['en','ru','ar']:assert compiler.translation_approved(json.loads((R/'data/blog-translations'/lang/(article['id']+'.json')).read_bytes()),compiler.translation_hash(article)),'translation_review_changed'
  for image in [article['image'],*[x['image']for x in article['locales'].values()]]:
   v=index[image['url']];assert v['offset']>=0 and v['length']>0 and v['offset']+v['length']<=len(blob);assert hashlib.sha256(blob[v['offset']:v['offset']+v['length']]).hexdigest()==image['sha256']==v['sha256'];assert not image.get('testOnly')
def main():
 proof=json.loads((E/'release.json').read_bytes());d=load('search_scoped_deploy','scripts/deploy-cpanel.py');base=d.load_release(R/proof['base']);new=d.load_release(R/proof['release']);expected={n:new['all_bytes'][n]for n in proof['changedFiles']};verify(base,new,proof,expected)
 media=load('search_media_gate','scripts/publish-social-links-20261112.py');media.E=E;media.O=R/proof['release'];media.verify_unchanged_media(d,new,proof)
 quality={'scope':'reviewed-four-language-subset','articles':proof['editorial']['approvedArticles'],'heldArticlesOutsidePublication':proof['editorial']['heldArticles'],'heldTranslations':[],'bankSha256':hashlib.sha256(new['all_bytes']['private/blog-bank.json']).hexdigest()};(E/'content-quality.json').write_text(json.dumps(quality,indent=2)+'\n')
 publisher=load('search_lease_publisher','scripts/publish-blog.py');original=publisher.module
 publisher.module=lambda name,path:types.SimpleNamespace(changes_for=lambda base,bank:expected)if path=='scripts/prepare-blog-release.py'else original(name,path)
 publisher.E=E;publisher.verify_scope=verify;publisher.main()
if __name__=='__main__':main()
