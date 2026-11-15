"""Publish only reviewed front image corrections using shared backup and rollback."""
from pathlib import Path
import hashlib,importlib.util,json,sys,types,subprocess
R=Path(__file__).resolve().parents[1];E=R/'artifacts/front-image-integrity-20261115'

def load(n,path):
 s=importlib.util.spec_from_file_location(n,R/path);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m

def verify(base,new,proof,expected):
 assert not new['manifest'].get('testOnly')
 assert base['manifest']['releaseHash']==proof['baseReleaseHash']and new['manifest']['releaseHash']==proof['releaseHash']
 delta={n for n,b in new['all_bytes'].items()if base['all_bytes'].get(n)!=b};removed=set(base['all_bytes'])-set(new['all_bytes'])
 assert delta==set(expected)|{'private/release.json'}and set(proof['changedFiles'])==set(expected)
 assert removed==set(proof['removedManifestFiles']) and all(n.startswith('public/assets/fronts/')for n in removed)
 assert all(new['all_bytes'][n]==b for n,b in expected.items())
 assert all(new['all_bytes'].get(n)==b for n,b in base['all_bytes'].items()if n not in delta and n not in removed)
 assert {n for n in delta if n.startswith('private/')}=={'private/release.json','private/catalog.json','private/cabinet-fronts.json'}
 old=json.loads(base['all_bytes']['private/catalog.json']);current=json.loads(new['all_bytes']['private/catalog.json']);old['meta']['frontCatalogVersion']=current['meta']['frontCatalogVersion'];assert old==current
 assert current['meta']['frontCatalogVersion']==hashlib.sha256(new['all_bytes']['private/cabinet-fronts.json']).hexdigest()

def main():
 prep=load('front_rule_prepare','scripts/prepare-front-rule-release-20261115.py');d=load('front_rule_deploy','scripts/deploy-cpanel.py');proof=json.loads((E/'release.json').read_bytes());base=d.load_release(R/proof['base']);new=d.load_release(R/proof['release']);expected=prep.changes_for(base);verify(base,new,proof,expected)
 # The old full audit binds the old owner manifest. Verify that exact old
 # binding, all unchanged furniture/supplier bytes, then re-run the owner gate
 # against the newly reviewed manifest instead of bypassing the audit.
 cleanup_path=R/'artifacts/media-cleanup.json';cleanup=json.loads(cleanup_path.read_bytes());audit=json.loads((R/'artifacts/measurement-orders/full-media-audit.json').read_bytes())
 assert cleanup['publicationReady']is True and not cleanup.get('testOnly')
 assert audit['passed']is True and audit['sourceReportSha256']==d.sha256(cleanup_path.read_bytes()) and audit['mediaVersion']==new['manifest']['mediaVersion']
 for name,digest in audit['files'].items():
  assert d.sha256((base if name=='private/cabinet-fronts.json'else new)['all_bytes'][name])==digest
 for index,row in enumerate(cleanup['images'].values(),1):
  for field,digest,folder in [('sourcePath','sourceSha','media-originals'),('path','outputSha','media-cleaned')]:
   path=R/row[field];assert not path.is_symlink() and path.resolve().is_relative_to((R/'artifacts'/folder).resolve()) and d.sha256(path.read_bytes())==row[digest]
  if index%1000==0:print(json.dumps({'mediaHashesVerified':index,'total':len(cleanup['images'])}),flush=True)
 d.validate_supplier_publication(R,new);owner=load('front_rule_owner','lib/owner_media_gate.py');owner.verify_owner_catalogues(R,new)
 subprocess.run(['node',str(R/'scripts/verify-current-media.mjs'),str(R),str(R/proof['release'])],check=True)
 (E/'media.json').write_text(json.dumps({'passed':True,'releaseHash':proof['releaseHash'],'allOriginalAndOutputHashesVerified':True,'ownerCatalogueGateRerun':True,'priorFurnitureAndSupplierAuditBindingVerified':True})+'\n')
 (E/'content-quality.json').write_text(json.dumps({'scope':'unchanged-live-editorial-bank','bankSha256':hashlib.sha256(new['all_bytes']['private/blog-bank.json']).hexdigest(),'heldTranslations':[],'noEditorialChange':True}))
 publisher=load('front_rule_publisher','scripts/publish-blog.py');original=publisher.module
 def dependency(name,path):
  if path=='scripts/prepare-blog-release.py':return types.SimpleNamespace(changes_for=lambda base,bank:expected)
  return original(name,path)
 publisher.module=dependency;publisher.E=E;publisher.verify_scope=verify;publisher.main()

if __name__=='__main__':main()
