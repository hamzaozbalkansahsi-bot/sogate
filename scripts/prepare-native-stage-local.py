#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/prepare-native-stage-local.py
# Açıklama   : Sunucu paketiyle aynı özel alan ve test alt yolu için ayrı yerel kabul alanı kurar.
import json,secrets,shutil,subprocess,sys,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;package=json.loads((ROOT/'.local/native-stage-package.json').read_text('utf8'))
previous=json.loads((ROOT/'.local/native-stage-local.json').read_text('utf8'))if'--reuse-state'in sys.argv else None
base=Path('D:/sexogate-local-artifacts-20261114/private-installs')/('native-mount-local-'+secrets.token_hex(8));home=base/'private-home/.sexogate-native-test';release=home/'releases'/package['release'];release.parent.mkdir(parents=True);shutil.copytree(package['bundle'],release);state=home/'state';state.mkdir();public=release/'public';private=release/'private'
if previous:
 prior=Path(previous['home']).resolve()/'state';allowed=Path('D:/sexogate-local-artifacts-20261114/private-installs').resolve();assert prior.is_relative_to(allowed)and prior.parent.name=='.sexogate-native-test'and prior.parent.parent.parent.name.startswith('native-mount-local-')and not prior.is_symlink()
 for file in prior.iterdir():
  assert not file.is_symlink()
  if file.suffix=='.sqlite':
   with sqlite3.connect(file)as source_db,sqlite3.connect(state/file.name)as target_db:source_db.backup(target_db)
  elif file.suffix=='.bin':shutil.copy2(file,state/file.name)
runtime={'privateRoot':private.as_posix(),'storageRoot':state.as_posix(),'mediaRoot':(home/'media').as_posix()}
php_literal=lambda value: "'"+str(value).replace('\\','/').replace("'","\\'")+"'"
(release/'nodeno-runtime.php').write_text('<?php return ['+','.join(php_literal(k)+'=>'+php_literal(v) for k,v in runtime.items())+'];',encoding='utf8')
(home/'active.json').write_text(json.dumps({'release':package['release']}),encoding='utf8');shutil.copy2(release/'deploy/worker.php',home/'worker.php');(private/'cache').mkdir(exist_ok=True);(home/'media').mkdir()
selection=ROOT/('.local/native-marketplace-selection.json'if(ROOT/'.local/native-marketplace-selection.json').is_file()else'.local/native-catalog-selection.json')
if package.get('products')and selection.is_file():
 import os
 media_selection=json.loads(selection.read_text('utf8'));allowed_base=Path('D:/sexogate-local-artifacts-20261114/private-installs').resolve()
 roots=[media_selection['mediaRoot']]+([media_selection['legacyMediaRoot']]if media_selection.get('legacyMediaRoot')else[])
 for media_path in roots:
  source=Path(media_path).resolve();assert source in [(allowed_base/'native-catalog-20261115/media'),(allowed_base/'marketplace-catalog-20261116/media')]
  for file in source.iterdir():
   if file.is_file()and not file.is_symlink()and not(home/'media'/file.name).exists():os.link(file,home/'media'/file.name)
web=base/'web';(web/'test').mkdir(parents=True)
entry="<?php define('SEXOGATE_NATIVE_MOUNT','/test');define('SEXOGATE_NATIVE_RELEASE',"+php_literal(package['release'])+");require "+php_literal(release/'deploy/dispatcher.php')+';'
(web/'test/index.php').write_text(entry,encoding='utf8')
preview='/test/native-preview-0123456789abcdef';preview_file=web/preview.lstrip('/')/'index.php';preview_file.parent.mkdir();preview_file.write_text(entry.replace("'/test'",php_literal(preview)),encoding='utf8')
router="<?php $path=parse_url($_SERVER['REQUEST_URI'],PHP_URL_PATH);require str_starts_with($path,"+php_literal(preview)+")?"+php_literal(preview_file)+":"+php_literal(web/'test/index.php')+';'
(base/'router.php').write_text(router,encoding='utf8')
seed=state/'local-owner-seed.json';access=json.loads((ROOT/'.local/php-access.json').read_text('utf8'));seed.write_text(json.dumps({k:access[k] for k in ['email','password','totpSecret']}),encoding='utf8')
code="require $argv[1].'/control-auth.php';$root=$argv[2];$s=json_decode(file_get_contents($root.'/local-owner-seed.json'),true);$db=nodenoControlDatabase($root);if(!$db->query(\"SELECT COUNT(*) FROM control_users WHERE role='owner'\")->fetchColumn()){$id=nodenoControlId('owner_');$db->prepare('INSERT INTO control_users(id,email,display_name,role,password_hash,totp_secret,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)')->execute([$id,$s['email'],'Yerel yönetici','owner',password_hash($s['password'],PASSWORD_BCRYPT),nodenoControlEncrypt($root,$s['totpSecret'],$id),time(),time()]);}"
try:r=subprocess.run([str(ROOT/'.local/php-runtime/php.exe'),'-d','extension=pdo_sqlite','-d','extension=sqlite3','-r',code,str(private),str(state)],capture_output=True);assert r.returncode==0,'ISOLATED_OWNER_SETUP_FAILED'
finally:seed.unlink(missing_ok=True)
worker=subprocess.run([str(ROOT/'.local/php-runtime/php.exe'),'-d','extension=pdo_sqlite','-d','extension=sqlite3',str(home/'worker.php')],capture_output=True)
assert worker.returncode==0,'LOCAL_NATIVE_WORKER_FAILED'
report={'base':str(base),'home':str(home),'web':str(web),'router':str(base/'router.php'),'release':package['release'],'url':'https://127.0.0.1:3188/test','previewUrl':'https://127.0.0.1:3188'+preview}
(ROOT/'.local/native-stage-local.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({'prepared':True,'release':package['release'],'url':report['url']}))
