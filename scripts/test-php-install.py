#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-php-install.py
# Açıklama   : Yayın arşivini ve sabit kurucuyu önce ayrı yerel dosya alanında doğrular.
import argparse,hashlib,json,os,secrets,shutil,subprocess,time,zipfile
from pathlib import Path
root=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser(description='PHP kurucusunu izole yerel dosya alanında sınar.')
parser.add_argument('--sandbox-root',type=Path,default=root/'.local/php-install-tests')
args=parser.parse_args()
package=json.loads((root/'.local/php-package.json').read_text('utf8'))
sandbox=args.sandbox_root.resolve()/secrets.token_hex(10);(sandbox/'app').mkdir(parents=True)
config=json.loads((root/'hosting/php/config.local.json').read_text('utf8'))
(sandbox/'app/config.local.json').write_text(json.dumps(config),encoding='utf8')
token=secrets.token_hex(32);env=os.environ.copy();env['SEXOGATE_DEPLOY_TOKEN']=token

def run(archive,release):
    shutil.copy2(archive,sandbox/f'app/payload-{release}.zip')
    (sandbox/'app/deploy.json').write_text(json.dumps({'release':release,'sha256':hashlib.sha256(Path(archive).read_bytes()).hexdigest(),'token_hash':hashlib.sha256(token.encode()).hexdigest(),'expires':int(time.time())+600}),encoding='utf8')
    return subprocess.run([str(root/'.local/php-runtime/php.exe'),str(root/'hosting/php/deploy/install.php'),str(sandbox)],capture_output=True,env=env)

r=run(package['archive'],package['release']);body=json.loads(r.stdout);assert r.returncode==0 and body['installed'],body
migration_count=body['migrations'];assert migration_count==len(list((root/'migrations/mysql').glob('*.sql')))
assert not (sandbox/'app/deploy.json').exists();assert not (sandbox/f'app/payload-{package["release"]}.zip').exists();assert (sandbox/'app/active.php').exists()
evil=sandbox/'traversal.zip'
with zipfile.ZipFile(evil,'w') as z:z.writestr('src/../../escape.php','<?php echo 1;')
r=run(evil,secrets.token_hex(12));body=json.loads(r.stdout);assert r.returncode!=0 and body['code']=='PACKAGE_PATH_INVALID',body
assert not (sandbox/'escape.php').exists()
(root/'.local/php-install-local.json').write_text(json.dumps({'packageInstall':True,'migrations':migration_count,'activation':True,'oneTimeToken':True,'pathTraversalRejected':True}),encoding='utf8')
print('PHP package install, schema verification, activation, token consumption and ZIP traversal rejection: PASS')
