"""Publish the exact reviewed mobile correction with the shared backup/lease/rollback path."""
from pathlib import Path
import hashlib,importlib.util,json,sys,types
R=Path(__file__).resolve().parents[1];E=R/'artifacts/mobile-layout-20261113'
def load(n,path):
 s=importlib.util.spec_from_file_location(n,R/path);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m

def verify(base,new,proof,expected):
 assert not new['manifest'].get('testOnly');assert base['manifest']['releaseHash']==proof['baseReleaseHash']and new['manifest']['releaseHash']==proof['releaseHash']
 delta={n for n,b in new['all_bytes'].items()if base['all_bytes'].get(n)!=b};assert delta==set(expected)|{'private/release.json'}and set(proof['changedFiles'])==set(expected)
 assert set(expected)=={'private/catalog.json','private/index.html','public/app.js','public/styles.css','public/store-insights.js','public/store-insights.css'}
 assert all(new['all_bytes'][n]==b for n,b in expected.items());assert all(new['all_bytes'].get(n)==b for n,b in base['all_bytes'].items()if n not in delta)
 old=json.loads(base['all_bytes']['private/catalog.json']);after=json.loads(new['all_bytes']['private/catalog.json']);assert old['products']==after['products'];name=next(c for c in after['categories']if c['id']=='ahsap-mobilya-malzemeleri')['name'];assert len(name)==11 and name['tr']=='Ahşap mobilya ve yardımcı ürünler'
 next(c for c in after['categories']if c['id']=='ahsap-mobilya-malzemeleri')['name']=next(c for c in old['categories']if c['id']=='ahsap-mobilya-malzemeleri')['name'];assert old==after
 assert new['all_bytes']['private/blog-bank.json']==base['all_bytes']['private/blog-bank.json']

def main():
 prepare=load('mobile_layout_preparation','scripts/prepare-mobile-layout-release.py');d=load('mobile_layout_backend','scripts/deploy-cpanel.py');proof=json.loads((E/'release.json').read_bytes());base=d.load_release(R/proof['base']);new=d.load_release(R/proof['release']);expected=prepare.changes_for(base);verify(base,new,proof,expected)
 media=load('mobile_layout_media','scripts/publish-social-links-20261112.py');media.E=E;media.O=R/proof['release'];media.verify_unchanged_media(d,new,proof)
 (E/'content-quality.json').write_text(json.dumps({'scope':'unchanged-live-editorial-bank','bankSha256':hashlib.sha256(new['all_bytes']['private/blog-bank.json']).hexdigest(),'heldTranslations':[],'noEditorialChange':True}),encoding='utf-8')
 publisher=load('mobile_layout_shared_publisher','scripts/publish-blog.py');original=publisher.module;publisher.module=lambda name,path:types.SimpleNamespace(changes_for=lambda base,bank:expected)if path=='scripts/prepare-blog-release.py'else original(name,path);publisher.E=E;publisher.verify_scope=verify;publisher.main()
if __name__=='__main__':main()
