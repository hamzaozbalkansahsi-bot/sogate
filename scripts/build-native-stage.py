#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/build-native-stage.py
# Açıklama   : Birebir kaynak kopyasından veri içermeyen, alt yola taşınabilir PHP yayın paketi hazırlar.
import hashlib,json,re,secrets,shutil,subprocess,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
subprocess.run(['python',str(ROOT/'scripts/verify-native-snapshot.py')],check=True)
local=json.loads((ROOT/'.local/native-store-build.json').read_text('utf8'))
base=Path('D:/sexogate-local-artifacts-20261114/private-installs')/('native-stage-'+secrets.token_hex(8));base.mkdir()
bundle=base/'bundle';bundle.mkdir()
for name in ['public','private']:shutil.copytree(Path(local[name]),bundle/name)
for name,target in [('branding.js','sexogate-branding.js'),('sexogate.css','sexogate.css')]:shutil.copy2(ROOT/'native-store/theme'/name,bundle/'public'/target)
deploy=bundle/'deploy';deploy.mkdir()
for name in ['dispatcher.php','worker.php']:shutil.copy2(ROOT/'native-store/deploy'/name,deploy/name)
token='/__SEXOGATE_MOUNT__'
def brand(text):
 text=re.sub(r'https://(?:www\.)?nodenohome\.com(?:\.tr)?','https://sexogate.com'+token,text)
 text=re.sub(r'(?:www\.)?nodenohome\.com(?:\.tr)?','sexogate.com',text)
 return re.sub(r'\bNODENO\b','SEXOGATE',text)
def urls(text):
 text=re.sub(r'((?:href|src|action|poster)=["\'])/(?!/|__SEXOGATE_MOUNT__)',lambda m:m[1]+token+'/',text,flags=re.I)
 return re.sub(r'(url\(\s*["\']?)/(?!/|__SEXOGATE_MOUNT__)',lambda m:m[1]+token+'/',text,flags=re.I)
changes={}
for folder in ['public','private']:
 for p in (bundle/folder).rglob('*'):
  if not p.is_file():continue
  if p.suffix.lower() in {'.php','.html','.css','.json','.svg','.webmanifest'}:
   raw=p.read_bytes();text=brand(raw.decode('utf8'))
   if p.suffix in {'.html','.css'}:text=urls(text)
   if p.name=='legal.php':
    text=text.replace("'0850 305 84 78'","''").replace('<span>PTYS Technologies L.L.C.</span><a href="mailto:info@ptys.com.tr">info@ptys.com.tr</a>','<a href="mailto:info@sexogate.com">info@sexogate.com</a>')
   if p.name=='site.webmanifest':
    data=json.loads(text);data['start_url']=token+'/';data['scope']=token+'/';data['id']=token+'/';data['icons']=[{**i,'src':token+i['src']} for i in data['icons']];text=json.dumps(data,ensure_ascii=False)
   if p.name=='config.json':
    data=json.loads(text);data.update(website='https://sexogate.com'+token,domain='sexogate.com',checkoutEnabled=False);text=json.dumps(data,ensure_ascii=False)
   if p.name.startswith('site-documents.') and p.suffix=='.json':
    data=json.loads(text)
    for document in data.get('documents',[]):
     for section in document.get('sections',[]):
      if 'heading' in section:section['title']=section.pop('heading')
    text=json.dumps(data,ensure_ascii=False)
   p.write_text(text,encoding='utf8',newline='\n')
   if p.read_bytes()!=raw:changes[p.relative_to(bundle).as_posix()]='brand/domain/mount relocation'
theme_hash=hashlib.sha256()
for path in sorted((ROOT/'native-store/theme').rglob('*')):
 if path.is_file():theme_hash.update(path.read_bytes())
for path in sorted((ROOT/'native-store/storefront').glob('*')):
 if path.is_file():theme_hash.update(path.read_bytes())
for path in [ROOT/'native-store/source-manifest.json',ROOT/'scripts/build-native-stage.py',*sorted((ROOT/'native-store/deploy').glob('*'))]:
 if path.is_file():theme_hash.update(path.read_bytes())
version=theme_hash.hexdigest()[:16]
selection_file=ROOT/'.local/native-catalog-selection.json';catalog_count=0;dataset=None
if selection_file.is_file():
 selection=json.loads(selection_file.read_text('utf8'));prepared=Path(selection['path']).resolve();allowed=Path('D:/sexogate-local-artifacts-20261114/private-installs/native-catalog-20261115').resolve()
 if not prepared.is_relative_to(allowed) or hashlib.sha256((prepared/'catalog-data.json').read_bytes()).hexdigest()!=selection['sha256']:raise RuntimeError('CATALOG_SELECTION_INVALID')
 data=json.loads((prepared/'catalog-data.json').read_text('utf8'));catalog_count=len(data['products']);dataset=data['dataset']
 if data['catalogOrigin']!='sexogate-suppliers-v1' or catalog_count!=2194 or len(set(p['id']for p in data['products']))!=catalog_count or any(p['published']or not p['hidden']or p['stockKnown']or p['stockQuantity']is not None for p in data['products']):raise RuntimeError('CATALOG_PROVENANCE_INVALID')
 catalog_path=bundle/'private/catalog.json';catalog=json.loads(catalog_path.read_text('utf8'));catalog.update(data);catalog_path.write_text(json.dumps(catalog,ensure_ascii=False,separators=(',',':')),encoding='utf8')
 shutil.copytree(prepared/'catalog-workbench',bundle/'private/catalog-workbench');shutil.copy2(prepared/'catalog-sources.json',bundle/'private/catalog-sources.json')
 shutil.copy2(prepared/'catalog-spec-labels.json',bundle/'private/catalog-spec-labels.json')
 theme_hash.update(selection['sha256'].encode())
 for path in sorted((ROOT/'native-store/catalog').glob('*')):
  if path.is_file():theme_hash.update(path.read_bytes())
 version=theme_hash.hexdigest()[:16]
 subprocess.run(['node',str(ROOT/'native-store/catalog/apply.mjs'),str(bundle)],check=True,cwd=ROOT)
subprocess.run(['node',str(ROOT/'native-store/storefront/apply.mjs'),str(bundle)],check=True,cwd=ROOT)
subprocess.run(['node',str(ROOT/'native-store/deploy/apply-store-theme.mjs'),str(bundle),version],check=True,cwd=ROOT)
admin=bundle/'public/admin.html'
if admin.is_file():admin.write_text(admin.read_text('utf8').replace('/sexogate-catalog.js"','/sexogate-catalog.js?v='+version+'"').replace('/sexogate-catalog.css"','/sexogate-catalog.css?v='+version+'"'),encoding='utf8')
subprocess.run(['node',str(ROOT/'native-store/deploy/relocate.mjs'),str(bundle/'public')],check=True,cwd=ROOT)
for p in (bundle/'public').rglob('*.js'):subprocess.run(['node','--check',str(p)],check=True,capture_output=True)
for p in [*(bundle/'private').glob('*.php'),bundle/'public/index.php',deploy/'dispatcher.php']:subprocess.run([str(ROOT/'.local/php-runtime/php.exe'),'-l',str(p)],check=True,capture_output=True)
# Bu paket hiçbir yerel SQLite, müşteri/oturum veya test siparişi içermez.
files={}
for p in bundle.rglob('*'):
 if p.is_file():
  if p.is_symlink() or p.suffix.lower() in {'.sqlite','.db','.log','.pem'} or 'sessions' in p.parts:raise RuntimeError('PRIVATE_STATE_IN_PACKAGE')
  files[p.relative_to(bundle).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
fingerprint=hashlib.sha256(''.join(k+'\0'+v+'\0' for k,v in sorted(files.items())).encode()).hexdigest();release=fingerprint[:24]
manifest={'schema':1,'release':release,'fingerprint':fingerprint,'assetVersion':version,'files':files,'previewOnly':True,'checkoutEnabled':False,'products':catalog_count,'dataset':dataset,'domain':'sexogate.com','mount':'/test','sourceFiles':771,'sourceSnapshotPreserved':True,'relocations':changes}
(bundle/'deployment-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
archive=base/(release+'.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as out:
 for p in bundle.rglob('*'):
  if p.is_file():out.write(p,p.relative_to(bundle).as_posix())
report={'release':release,'archive':str(archive),'bundle':str(bundle),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'bytes':archive.stat().st_size,'files':len(files),'previewOnly':True,'checkoutEnabled':False,'products':catalog_count,'dataset':dataset}
(ROOT/'.local/native-stage-package.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in report.items() if k not in ['archive','bundle']}))
