"""Use the existing lease/backup/readback/rollback publisher for an exact social delta."""
from pathlib import Path
import base64,hashlib,http.client,importlib.util,json,ssl,sys,types,urllib.parse
R=Path(__file__).resolve().parents[1];E=R/'artifacts/social-keywords-20261113'

def load(n,path):
 s=importlib.util.spec_from_file_location(n,R/path);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m

def verify(base,new,proof,expected):
 assert not new['manifest'].get('testOnly')
 assert base['manifest']['releaseHash']==proof['baseReleaseHash']and new['manifest']['releaseHash']==proof['releaseHash']
 delta={n for n,b in new['all_bytes'].items()if base['all_bytes'].get(n)!=b}
 assert delta==set(expected)|{'private/release.json'}and set(proof['changedFiles'])==set(expected)
 assert all(new['all_bytes'][n]==b for n,b in expected.items())
 assert all(new['all_bytes'].get(n)==b for n,b in base['all_bytes'].items()if n not in delta)
 assert all(not n.startswith(('public/assets/suppliers/','public/assets/doors/','public/assets/fronts/'))for n in delta)

def binary_backup_read(d,b,directory,name,expected):
 # Fileman's UTF-8 content reader cannot round-trip PNG/JPEG. Download only the
 # exact prepared asset from a protected deployment backup, with TLS intact.
 assert directory.startswith(d.HOME+'/nodeno-backups/')and '/public/assets/brand'in directory
 assert name in ['social-logo.png','social-logo-white.png','share-cover.jpg']
 d.remote_path(directory,private=True);d.component(name)
 user,password=b.probe.credentials();auth=base64.b64encode((user+':'+password).encode()).decode('ascii')
 conn=http.client.HTTPSConnection(d.HOST,d.PORT,timeout=60,context=ssl.create_default_context())
 try:
  conn.request('GET','/download?'+urllib.parse.urlencode({'file':directory+'/'+name}),headers={'Authorization':'Basic '+auth,'Accept-Encoding':'identity'})
  response=conn.getresponse();assert response.status==200 and response.getheader('Content-Encoding','identity')=='identity'
  body=response.read(len(expected)+1);assert body==expected;return body
 finally:conn.close()

def main():
 prepare=load('social_keyword_prepare','scripts/prepare-social-keywords-20261113.py');d=load('social_keyword_deploy','scripts/deploy-cpanel.py');proof=json.loads((E/'release.json').read_bytes());base=d.load_release(R/proof['base']);new=d.load_release(R/proof['release']);expected=prepare.changes_for(base);verify(base,new,proof,expected)
 media=load('social_keyword_media','scripts/publish-social-links-20261112.py');media.E=E;media.O=R/proof['release'];media.verify_unchanged_media(d,new,proof)
 (E/'content-quality.json').write_text(json.dumps({'scope':'unchanged-live-editorial-bank','bankSha256':hashlib.sha256(new['all_bytes']['private/blog-bank.json']).hexdigest(),'heldTranslations':[],'noEditorialChange':True}))
 publisher=load('social_keyword_publisher','scripts/publish-blog.py');original=publisher.module
 def dependency(name,path):
  if path=='scripts/prepare-blog-release.py':return types.SimpleNamespace(changes_for=lambda base,bank:expected)
  module=original(name,path)
  if path=='scripts/publish-paint-release.py':
   default=module.verified_private_read
   module.verified_private_read=lambda d,b,directory,name,body:binary_backup_read(d,b,directory,name,body)if name.endswith(('.png','.jpg'))else default(d,b,directory,name,body)
  return module
 publisher.module=dependency;publisher.E=E;publisher.verify_scope=verify;publisher.main()

if __name__=='__main__':main()
