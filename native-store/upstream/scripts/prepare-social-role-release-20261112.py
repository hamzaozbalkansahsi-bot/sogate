"""Prepare an immutable social/identity delta from the exact current paint release.

This command never deploys and does not overwrite working source application
files. Every catalogue, paint, payment and customer configuration byte is kept.
Run only after the social module owner has declared the four modules stable.
"""
from pathlib import Path
import hashlib,importlib.util,json,os,re,sys

R=Path(__file__).resolve().parents[1]
E=R/'artifacts/social-role-release-20261112'
B=R/'artifacts/cpanel-release-paints-20261112-r5'
O=R/'artifacts/cpanel-release-social-roles-20261112-r1'
BASE='faa7951843c79715f0580e3878e5df77f7f5670f01911f0059820f1cced97a8c'
VERSION='social-roles-20261112-v5'
SOCIAL=['social-campaigns.php','social-engine.php','social-media.php','social-worker.php']
CACHE_FILES=['private/index.html','private/legal.php','public/app.js','public/admin.js','public/admin.html','public/welcome-poster.js','public/site.webmanifest']

def module():
    s=importlib.util.spec_from_file_location('social_role_release_backend',R/'scripts/deploy-cpanel.py')
    d=importlib.util.module_from_spec(s);sys.modules[s.name]=d;s.loader.exec_module(d);return d

def cache_urls(body):
    text=body.decode('utf-8')
    for name in ['assets/brand/logo-horizontal.svg','assets/brand/logo-horizontal-white.svg','assets/brand/logo-with-slogan.svg','wordmark.svg','brand.svg','favicon.svg','favicon.ico','apple-touch-icon.png','site.webmanifest']:
        text=re.sub(r'/'+re.escape(name)+r'(?:\?v=[A-Za-z0-9_-]+)?(?=[\'"`])','/'+name+'?v='+VERSION,text)
    return text.encode('utf-8')

def cached(name,body):
    if name=='public/site.webmanifest':
        data=json.loads(body)
        for icon in data['icons']:icon['src']=icon['src'].split('?')[0]+'?v='+VERSION
        return (json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    body=cache_urls(body)
    if name=='public/app.js':body=re.sub(rb'welcome-poster\.js\?v=[A-Za-z0-9_-]+',b'welcome-poster.js?v='+VERSION.encode(),body)
    if name in ['private/index.html','public/admin.html']:
        entry='app.js'if name=='private/index.html'else'admin.js'
        body=re.sub(rb'/'+entry.encode()+rb'\?v=[A-Za-z0-9_-]+',b'/'+entry.encode()+b'?v='+VERSION.encode(),body)
    return body

def main():
    E.mkdir(exist_ok=True);d=module();base=d.load_release(B)
    assert base['manifest']['releaseHash']==BASE,'Unexpected live base package'
    live=d.CpanelBackend(allow_writes=False).public_health()
    assert live['releaseHash']==BASE and live['products']==3631 and live['categories']==155 and live['checkoutEnabled']is True and live['mediaReady']is True,'Live paint base changed'
    registry=json.loads((R/'artifacts/social-refresh-20261112/logo-role-assets.json').read_bytes())
    assert registry['version']=='roles-20261112-v3'
    assets=registry['changedWebAssets'];assert len(assets)==10
    source_digests={n:hashlib.sha256((R/'hosting'/n).read_bytes()).hexdigest()for n in SOCIAL}
    changes={'public/'+n:(R/'web'/n).read_bytes()for n in assets}
    changes.update({'private/'+n:(R/'hosting'/n).read_bytes()for n in SOCIAL})
    for n in CACHE_FILES:
        body=cached(n,base['all_bytes'][n])
        if body!=base['all_bytes'][n]:changes[n]=body
    expected_new={'public/assets/brand/social-logo-white.png'}
    assert set(changes)-set(base['all_bytes'])==expected_new,'Unexpected new release file'
    if not O.exists():
        for n in sorted(set(base['manifest']['files'])|set(changes)):
            t=O/n;t.parent.mkdir(parents=True,exist_ok=True)
            if n in changes:t.write_bytes(changes[n])
            else:os.link(B/n,t)
        names=sorted(set(base['manifest']['files'])|set(changes));hashes={n:d.sha256((O/n).read_bytes())for n in names};fp=hashlib.sha256()
        for n,digest in hashes.items():fp.update((n+'\0'+digest+'\0').encode())
        manifest={**base['manifest'],'releaseHash':fp.hexdigest(),'files':hashes}
        (O/'private/release.json').write_text(json.dumps(manifest,indent=2)+'\n')
    new=d.load_release(O)
    for n in set(base['all_bytes'])|set(changes):
        if n=='private/release.json':continue
        assert new['all_bytes'][n]==changes.get(n,base['all_bytes'].get(n)),n+' differs from its approved source'
    assert source_digests=={n:hashlib.sha256((R/'hosting'/n).read_bytes()).hexdigest()for n in SOCIAL},'Social sources changed during sealing'
    delta={n for n,b in new['all_bytes'].items()if base['all_bytes'].get(n)!=b}
    assert delta<=set(changes)|{'private/release.json'}
    for n in ['private/catalog.json','private/config.json','public/index.php','public/styles.css','public/paint-recommendations.js']:
        assert new['all_bytes'][n]==base['all_bytes'][n],n+' must remain byte-exact'
    catalog=json.loads(new['all_bytes']['private/catalog.json'])
    assert len(catalog['products'])==3631 and len(catalog['categories'])==155
    record={'prepared':True,'deployed':False,'base':B.relative_to(R).as_posix(),'release':O.relative_to(R).as_posix(),'baseReleaseHash':BASE,'releaseHash':new['manifest']['releaseHash'],'brandVersion':registry['version'],'assetCacheVersion':VERSION,'changedFiles':sorted(delta-{'private/release.json'}),'newPublicFiles':sorted(expected_new),'socialSourceHashes':source_digests,'products':3631,'categories':155,'checkoutEnabled':True,'paintCataloguePricesCustomerConfigurationAndCheckoutByteExact':True,'workingSourceAppFilesModified':False}
    (E/'release.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record))

if __name__=='__main__':main()
