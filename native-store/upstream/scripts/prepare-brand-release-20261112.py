"""Prepare revised identity over the exact current live application."""
from pathlib import Path
import hashlib,importlib.util,json,os,re,sys
R=Path(__file__).resolve().parents[1];E=R/'artifacts/brand-refresh-20261112';B=R/'artifacts/cpanel-release-social-copy-20261112-r2';O=R/'artifacts/cpanel-release-brand-reference-20261112-r2'
BASE='4ae93a114d896dfe6e9297a355eac9c907123d87e2a7e62b92c4235692ed9bf0';VERSION='brand-20261112-v2'

def cache_urls(body):
    text=body.decode('utf-8')
    for name in ['assets/brand/logo-horizontal.svg','assets/brand/logo-horizontal-white.svg','assets/brand/logo-with-slogan.svg','wordmark.svg','brand.svg','favicon.svg','favicon.ico','apple-touch-icon.png','site.webmanifest']:
        text=re.sub(r'/'+re.escape(name)+r'(?:\?v=[A-Za-z0-9_-]+)?(?=[\'"`])','/'+name+'?v='+VERSION,text)
    return text.encode('utf-8')

def main():
    spec=importlib.util.spec_from_file_location('brand_release_backend',R/'scripts/deploy-cpanel.py');d=importlib.util.module_from_spec(spec);sys.modules[spec.name]=d;spec.loader.exec_module(d)
    base=d.load_release(B);assert base['manifest']['releaseHash']==BASE
    assert d.CpanelBackend(allow_writes=False).public_health()['releaseHash']==BASE
    assets=json.loads((E/'assets.json').read_bytes())['files'];changes={'public/'+n:(R/'web'/n).read_bytes()for n in assets}
    for n in ['public/app.js','public/admin.js','public/admin.html','public/welcome-poster.js','private/index.html','private/legal.php']:
        body=cache_urls(base['all_bytes'][n])
        if n=='public/app.js':body=re.sub(rb'welcome-poster\.js\?v=[A-Za-z0-9_-]+',b'welcome-poster.js?v='+VERSION.encode(),body)
        if n in ['private/index.html','public/admin.html']:
            entry='app.js'if n=='private/index.html'else'admin.js';body=re.sub(rb'/'+entry.encode()+rb'\?v=[A-Za-z0-9_-]+',b'/'+entry.encode()+b'?v='+VERSION.encode(),body)
        assert body!=base['all_bytes'][n],n
        changes[n]=body
        source=R/'hosting/legal.php'if n=='private/legal.php'else R/'web'/('index.html'if n=='private/index.html'else Path(n).name)
        source_before=source.read_bytes();edited=cache_urls(source_before)
        if n=='public/app.js':edited=re.sub(rb'welcome-poster\.js\?v=[A-Za-z0-9_-]+',b'welcome-poster.js?v='+VERSION.encode(),edited)
        if source.name in ['index.html','admin.html']:
            entry='app.js'if source.name=='index.html'else'admin.js';edited=re.sub(rb'/'+entry.encode()+rb'\?v=[A-Za-z0-9_-]+',b'/'+entry.encode()+b'?v='+VERSION.encode(),edited)
        temp=source.with_suffix(source.suffix+'.tmp');temp.write_bytes(edited);temp.replace(source)
        if n=='private/legal.php'and edited!=source_before:
            coverage_path=R/'artifacts/target-locales-20261111/coverage.json';coverage=json.loads(coverage_path.read_bytes())
            assert hashlib.sha256(source_before).hexdigest()==coverage['sourceFiles']['hosting/legal.php']
            assert edited.replace(b'?v='+VERSION.encode(),b'')==source_before,'Translated legal text must remain byte-exact'
            before=E/'translation-source-binding-before.json'
            if not before.exists():before.write_bytes(coverage_path.read_bytes())
            coverage['sourceFiles']['hosting/legal.php']=hashlib.sha256(edited).hexdigest();coverage_path.write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            (E/'translation-source-binding.json').write_text(json.dumps({'passed':True,'file':'hosting/legal.php','urlOnly':True,'translatedTextByteExactAfterRemovingBrandVersion':True})+'\n')
    manifest=json.loads(base['all_bytes']['public/site.webmanifest'])
    for icon in manifest['icons']:icon['src']=icon['src'].split('?')[0]+'?v='+VERSION
    manifest_bytes=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode();changes['public/site.webmanifest']=manifest_bytes;(R/'web/site.webmanifest').write_bytes(manifest_bytes)
    for n in ['social-media.php','social-campaigns.php','social-admin.php']:changes['private/'+n]=(R/'hosting'/n).read_bytes()
    assert set(changes).issubset(base['all_bytes'])
    if not O.exists():
        for n in base['manifest']['files']:
            t=O/n;t.parent.mkdir(parents=True,exist_ok=True)
            if n in changes:t.write_bytes(changes[n])
            else:os.link(B/n,t)
        hashes={n:d.sha256((O/n).read_bytes())for n in sorted(base['manifest']['files'])};fp=hashlib.sha256()
        for n,digest in hashes.items():fp.update((n+'\0'+digest+'\0').encode())
        release={**base['manifest'],'files':hashes,'releaseHash':fp.hexdigest()};(O/'private/release.json').write_text(json.dumps(release,indent=2)+'\n')
    candidate=d.load_release(O);release=candidate['manifest']
    for n in base['all_bytes']:
        if n in changes:assert candidate['all_bytes'][n]==changes[n],n
        elif n!='private/release.json':assert candidate['all_bytes'][n]==base['all_bytes'][n],n
    proof={'prepared':True,'base':B.relative_to(R).as_posix(),'release':O.relative_to(R).as_posix(),'baseReleaseHash':BASE,'releaseHash':release['releaseHash'],'changedFiles':sorted(changes),'brandVersion':'reference-20261112-v2','cataloguePricesCheckoutAndCustomerStoragePreserved':True}
    (E/'release.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))

if __name__=='__main__':main()
