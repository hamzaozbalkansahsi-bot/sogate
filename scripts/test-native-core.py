#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-core.py
# Açıklama   : NODENO regresyonlarını ayrı yerel alanda, yalnız kayıtlı sahte anahtar istisnasıyla çalıştırır.
import hashlib,json,os,secrets,shutil,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent;source=ROOT/'native-store/upstream';manifest=json.loads((ROOT/'native-store/source-manifest.json').read_text('utf8'))
base=Path('D:/sexogate-local-artifacts-20261114/private-installs');sandbox=base/('native-regression-'+secrets.token_hex(8));sandbox.mkdir()
for name,sha in manifest['files'].items():
 p=source/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==sha
 target=sandbox/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
# Yalnız özgün testlerin sabit 667 kimlikli referansı; uygulama paketine/Git'e girmez.
fixture=ROOT.parent/'Nodeno/data/catalog-source.json';before=hashlib.sha256(fixture.read_bytes()).hexdigest();shutil.copy2(fixture,sandbox/'data/catalog-source.json')
(sandbox/'AGENTS.md').write_text('Isolated original-source regression fixture; not application instructions.\n',encoding='utf8')
shutil.copytree(ROOT.parent/'Nodeno/data/legal',sandbox/'data/legal')
runtime=sandbox/'artifacts/runtime-php';runtime.parent.mkdir();target=(ROOT/'.local/php-runtime').resolve()
assert runtime.resolve().is_relative_to(base.resolve()) and target.is_relative_to(ROOT.resolve())
quote=lambda value:"'"+str(value).replace("'","''")+"'"
shell=shutil.which('pwsh') or 'C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'
subprocess.run([shell,'-NoProfile','-Command','New-Item -ItemType Junction -Path '+quote(runtime)+' -Target '+quote(target)+' | Out-Null'],check=True,capture_output=True)
scan=sandbox/'php-scan';scan.mkdir();(scan/'local.ini').write_text('extension=pdo_sqlite\nextension=sqlite3\n',encoding='ascii');temp=base/('native-regression-temp-'+secrets.token_hex(8));temp.mkdir()
env=os.environ.copy();env.update(PHP_BINARY=str(target/'php.exe'),PHP_INI_SCAN_DIR=str(scan),TEMP=str(temp),TMP=str(temp))
names='account-runtime collections-runtime control-auth control-catalog control-operations control-marketing control-analytics admin-editor admin-campaign-view admin-password-visibility shopping-experience guest-checkout locale-runtime market-preferences visitor-market date-time product-presentation product-specs catalog-pagination storefront-filters payments-core payments-store payments-refunds payments-stripe-form payments-sandbox-keys payments-ui payments-admin payment-activation payment-documents-maintenance private-maintenance payments-http privacy-preferences blog-tools blog-runtime'.split()
log=ROOT/'.local/native-core-tests-final.log'
with log.open('w',encoding='utf8') as out:result=subprocess.run(['node','--test',*[str('tests/'+name+'.test.mjs') for name in names]],cwd=sandbox,env=env,stdout=out,stderr=subprocess.STDOUT)
assert hashlib.sha256(fixture.read_bytes()).hexdigest()==before,'REFERENCE_SOURCE_CHANGED'
print(json.dumps({'exitCode':result.returncode,'testFiles':len(names),'testAssertionsUnchanged':True,'syntheticFixtureExceptions':len(manifest.get('fixtureSanitizations',{})),'isolatedTestArea':True,'originalCatalogFixtureOnly':True,'applicationCatalogImported':False}))
raise SystemExit(result.returncode)
