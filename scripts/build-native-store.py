#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/build-native-store.py
# Açıklama   : Doğrudan NODENO motorunu yalnız marka/tema katmanıyla ayrı yerel PHP alanında kurar.
import hashlib,json,re,secrets,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent;SOURCE=ROOT/'native-store/upstream'
manifest=json.loads((ROOT/'native-store/source-manifest.json').read_text('utf8'))
verification=subprocess.run([sys.executable,str(ROOT/'scripts/verify-native-snapshot.py')],capture_output=True)
if verification.returncode:raise RuntimeError('NATIVE_SOURCE_OR_THEME_INTEGRITY_FAILED')
for name,sha in manifest['files'].items():
 if hashlib.sha256((SOURCE/name).read_bytes()).hexdigest()!=sha:raise RuntimeError('SOURCE_SNAPSHOT_CHANGED: '+name)
base=Path('D:/sexogate-local-artifacts-20261114/private-installs');build=base/('native-sexogate-'+secrets.token_hex(8));previous=None
pointer=ROOT/'.local/native-store-build.json'
if pointer.exists():
 previous=json.loads(pointer.read_text('utf8'));storage=Path(previous['storage'])
 if not previous.get('localOnly') or not storage.is_dir() or storage.is_symlink() or not storage.resolve().is_relative_to(base.resolve()) or not re.fullmatch('native-state-[a-f0-9]{16}',storage.name):raise RuntimeError('NATIVE_STATE_PATH_REJECTED')
else:storage=base/('native-state-'+secrets.token_hex(8));storage.mkdir(parents=True,exist_ok=False)
public=build/'public';private=build/'private'
for p in [public,private]:p.mkdir(parents=True,exist_ok=False)
colors={'#172d38':'#5A0A20','#f5f2e9':'#FBF4EF','#d8ec81':'#E7B4BD','#536770':'#716168','#daddd6':'#E6D8DC','#eef3dd':'#F3E6E8','#f7f8f3':'#FBF4EF','#f4f5f3':'#FBF4EF'}
changed=[];js_count=0;php_count=0
for path in (SOURCE/'web').rglob('*'):
 if not path.is_file():continue
 rel=path.relative_to(SOURCE/'web');target=(private/'index.html') if rel.as_posix()=='index.html' else public/rel;target.parent.mkdir(parents=True,exist_ok=True);raw=path.read_bytes()
 if path.suffix=='.css':
  text=raw.decode('utf8');text=re.sub(r'#[a-fA-F0-9]{6}\b',lambda m:colors.get(m[0].lower(),m[0]),text);raw=text.encode('utf8')
 if path.suffix=='.html':
  text=re.sub(r'<meta\s+name="p:domain_verify"[^>]*>','',raw.decode('utf8'));text=re.sub(r'\bNODENO\b','SEXOGATE',text);text=text.replace('</head>','<link rel="stylesheet" href="/sexogate.css"><script defer src="/sexogate-branding.js"></script></head>');text=text.replace('content="#172D38"','content="#5A0A20"');raw=text.encode('utf8')
 target.write_bytes(raw)
 if raw!=path.read_bytes():changed.append('web/'+rel.as_posix())
 if path.suffix=='.js':js_count+=1
for path in (SOURCE/'hosting').iterdir():
 if not path.is_file():continue
 if path.name=='index.php':target=public/path.name
 elif path.name=='.htaccess':target=public/path.name
 elif path.suffix=='.php':target=private/path.name
 else:continue
 shutil.copy2(path,target)
 if path.suffix=='.php':php_count+=1
for name in ['sexogate.css','branding.js']:shutil.copy2(ROOT/'native-store/theme'/name,public/('sexogate-branding.js' if name=='branding.js' else name))
shutil.copy2(SOURCE/'hosting/blog-admin.html',private/'blog-admin.html')
for path in (public/'locales').glob('*.json'):shutil.copy2(path,private/('locale.'+path.name))
fonts=public/'assets/sexogate/fonts';fonts.mkdir(parents=True,exist_ok=True)
for path in (ROOT/'native-store/theme/assets/fonts').iterdir():shutil.copy2(path,fonts/path.name)
brand=ROOT/'native-store/theme/assets/brand';(public/'assets/brand').mkdir(parents=True,exist_ok=True)
for name in ['logo-horizontal.svg','logo-horizontal-dark.svg','logo-horizontal-light.svg']:
 shutil.copy2(brand/'app'/('logo-stacked-light.svg' if 'light' in name else 'logo-stacked.svg'),public/'assets/brand'/name)
for path in (SOURCE/'web').rglob('*.svg'):
 if path.name.startswith('logo') or 'wordmark' in path.name or path.name.startswith('symbol'):
  target=public/path.relative_to(SOURCE/'web');replacement=brand/'favicon.svg' if 'symbol' in path.name else brand/'app'/('logo-stacked-light.svg' if any(t in path.name for t in ['light','white']) else 'logo-stacked.svg');shutil.copy2(replacement,target)
for name in ['favicon.svg','favicon.ico','apple-touch-icon.png']:
 source=brand/('favicon.svg' if name=='favicon.svg' else 'app/'+name);shutil.copy2(source,public/name)
for size in [192,512]:shutil.copy2(brand/'app'/('app-icon-'+str(size)+'.png'),public/('icon-'+str(size)+'.png'))
(public/'site.webmanifest').write_text(json.dumps({'name':'SEXOGATE','short_name':'SEXOGATE','start_url':'/','scope':'/','display':'standalone','theme_color':'#5A0A20','background_color':'#FBF4EF','icons':[{'src':'/icon-'+str(n)+'.png','sizes':str(n)+'x'+str(n),'type':'image/png'} for n in [192,512]]}),encoding='utf8')
for name in ['date-time-regions.json','store-locales.json']:shutil.copy2(SOURCE/'data'/name,private/name)
slogan={'tr':'Tutkunu Keşfet.','en':'Discover your passion.','ru':'Открой свою страсть.','ar':'اكتشف شغفك.','de':'Entdecke deine Leidenschaft.','az':'Ehtirasını kəşf et.','kk':'Құштарлығыңды аш.','tk':'Hyjuwyňy aç.','uz':'Ishtiyoqingni kashf et.','ky':'Кумарыңды ач.','fa':'اشتیاقت را کشف کن.'}
catalog={'brand':{'name':'SEXOGATE','slogan':slogan},'products':[],'categories':[],'collections':[],'meta':{'releaseHash':hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest(),'localOnly':True}}
config={'checkoutEnabled':False,'contactEmail':'info@sexogate.com','contactPhone':None,'contactPhoneUri':None,'domain':'sexogate.com','website':'https://127.0.0.1:3186','socialHandle':'@sexogate','socials':[],'legalName':None,'parentCompany':None,'mode':'catalogue','brand':catalog['brand']}
for path in (public/'locales').glob('*.json'):
 data=json.loads(path.read_text('utf8'));locale=data['locale'];translate=data['translations'];aliases={}
 for name,value in translate.items():
  renamed=re.sub(r'\bNODENO\b','SEXOGATE',name)
  if renamed!=name:aliases[renamed]=re.sub(r'\bNODENO\b','SEXOGATE',value)
 aliases.update({'SEXOGATE':'SEXOGATE','Discover your passion.':slogan[locale]});translate.update(aliases)
 raw=json.dumps(data,ensure_ascii=False).encode('utf8');path.write_bytes(raw);(private/('locale.'+locale+'.json')).write_bytes(raw)
 empty=json.dumps({'schema':1,'locale':locale,'translations':{},'kind':'catalogue','sourceInventorySha256':hashlib.sha256(b'[]').hexdigest()}).encode('utf8')
 (public/'locales'/(locale+'.catalogue.json')).write_bytes(empty);(private/('locale.'+locale+'.catalogue.json')).write_bytes(empty)
for name,value in [('catalog',catalog),('config',config),('media',{})]:(private/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False),encoding='utf8')
meta=subprocess.run([sys.executable,str(ROOT/'scripts/compile-native-meta.py'),'--private',str(private),'--public',str(public)],capture_output=True)
if meta.returncode:raise RuntimeError('NATIVE_BRAND_METADATA_INCOMPLETE')
if previous:
 old_private=Path(previous['private']);old_public=Path(previous['public'])
 for path in [old_private/'blog-bank.json',*old_private.glob('site-documents.*.json')]:
  if path.is_file() and not path.is_symlink():shutil.copy2(path,private/path.name)
 if (old_public/'assets/blog').is_dir():shutil.copytree(old_public/'assets/blog',public/'assets/blog')
(build/'nodeno-runtime.php').write_text("<?php\ndeclare(strict_types=1);\nreturn ['privateRoot'=>"+json.dumps(private.as_posix())+",'storageRoot'=>"+json.dumps(storage.as_posix())+"];\n",encoding='utf8')
# Yalnız SEXOGATE'in yerel test yöneticisi; başka işletmeden kullanıcı/oturum alınmaz.
access=json.loads((ROOT/'.local/php-access.json').read_text('utf8'));seed=storage/'local-owner-seed.json';seed.write_text(json.dumps({k:access[k] for k in ['email','password','totpSecret']}),encoding='utf8')
php=ROOT/'.local/php-runtime/php.exe';code="require $argv[1].'/control-auth.php';$root=$argv[2];$s=json_decode(file_get_contents($root.'/local-owner-seed.json'),true);$db=nodenoControlDatabase($root);if(!(int)$db->query(\"SELECT COUNT(*) FROM control_users WHERE role='owner'\")->fetchColumn()){$id=nodenoControlId('owner_');$db->prepare('INSERT INTO control_users(id,email,display_name,role,password_hash,totp_secret,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)')->execute([$id,$s['email'],'Yerel yönetici','owner',password_hash($s['password'],PASSWORD_BCRYPT),nodenoControlEncrypt($root,$s['totpSecret'],$id),time(),time()]);}"
try:result=subprocess.run([str(php),'-d','extension=pdo_sqlite','-d','extension=sqlite3','-r',code,str(private),str(storage)],capture_output=True)
finally:seed.unlink(missing_ok=True)
if result.returncode:raise RuntimeError('ISOLATED_OWNER_SETUP_FAILED: '+result.stderr.decode('utf8','replace')[:500])
for path in (SOURCE/'hosting').glob('*.php'):
 target=public/path.name if path.name=='index.php' else private/path.name
 if path.read_bytes()!=target.read_bytes():raise RuntimeError('ENGINE_BYTES_CHANGED')
for path in (SOURCE/'web').rglob('*.js'):
 if path.read_bytes()!=(public/path.relative_to(SOURCE/'web')).read_bytes():raise RuntimeError('JS_ENGINE_BYTES_CHANGED')
report={'buildRoot':str(build),'public':str(public),'private':str(private),'storage':str(storage),'url':'https://127.0.0.1:3186','localOnly':True,'sourceFiles':len(manifest['files']),'unchangedPhpModules':php_count,'unchangedJsModules':js_count,'themeChangedFiles':changed,'catalogProducts':0,'donorBusinessDataCopied':False,'checkoutEnabled':False,'builtAt':datetime.now(timezone.utc).isoformat()}
(ROOT/'.local/native-store-build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k not in ['buildRoot','public','private','storage','themeChangedFiles']}))
