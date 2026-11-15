from pathlib import Path
import hashlib,importlib.util,json,os,re,sys,urllib.request
R=Path.cwd();E=R/'artifacts/mobile-market-20261111'
spec=importlib.util.spec_from_file_location('market_deploy',R/'scripts/deploy-cpanel.py');d=importlib.util.module_from_spec(spec);sys.modules[spec.name]=d;spec.loader.exec_module(d)
h=json.load(urllib.request.urlopen('https://nodenohome.com/api/health',timeout=40))
c=[p.parent.parent for p in (R/'artifacts').glob('cpanel-release*/private/release.json') if json.loads(p.read_bytes()).get('releaseHash')==h['releaseHash']];assert len(c)==1
B=c[0];base=d.load_release(B);O=R/'artifacts/cpanel-release-mobile-market-20261111-r3';assert not O.exists()
names=['app.js','door-ui.js','cabinet-front-ui.js','welcome-poster.js','welcome-country-map.js','styles.css','shopping-experience.css','market-preferences.js']
changes={'public/'+n:(R/'web'/n).read_bytes() for n in names}
html=base['all_bytes']['private/index.html'].decode();old='</svg></label><div class="account-dropdown">';assert old in html;html=html.replace(old,'</svg></label><div id="header-currency"></div><div class="account-dropdown">')
for name in ['app.js','styles.css','shopping-experience.css']:
 html,n=re.subn('/'+re.escape(name)+r'\?v=[^"\s]+','/'+name+'?v=nodeno-market-20261111-r1',html);assert n==1
changes['private/index.html']=html.encode()
for name in sorted(set(base['manifest']['files'])|set(changes)):
 target=O/name;target.parent.mkdir(parents=True,exist_ok=True)
 if name in changes:target.write_bytes(changes[name])
 else:os.link(B/name,target)
files={p.relative_to(O).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in O.rglob('*') if p.is_file()};fp=hashlib.sha256()
for name,value in sorted(files.items()):fp.update((name+'\0'+value+'\0').encode())
m={**base['manifest'],'releaseHash':fp.hexdigest(),'files':dict(sorted(files.items()))};(O/'private/release.json').write_text(json.dumps(m,indent=2)+'\n');d.load_release(O)
p={'prepared':True,'base':B.relative_to(R).as_posix(),'release':O.relative_to(R).as_posix(),'baseReleaseHash':base['manifest']['releaseHash'],'releaseHash':m['releaseHash'],'changedFiles':sorted(changes),'sourcePackage':'artifacts/cpanel-release-mobile-market-source-20261111-r3','catalogueMediaPricesAndCommerceUnchanged':True,'checkoutEnabledBefore':h['checkoutEnabled']};(E/'release.json').write_text(json.dumps(p,indent=2)+'\n');print(json.dumps(p))
