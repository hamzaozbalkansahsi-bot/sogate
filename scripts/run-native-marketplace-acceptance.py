#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/run-native-marketplace-acceptance.py
# Açıklama   : Aynı paketin kabul gruplarını en fazla iki tarayıcı işiyle çalıştırır ve yayın kanıtını doğrular.
import argparse,concurrent.futures,json,os,re,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
from native_marketplace_acceptance import marketplace_acceptance
parser=argparse.ArgumentParser();parser.add_argument('--scope',choices=['local','preview'],required=True);parser.add_argument('--base',required=True);args=parser.parse_args()
assert (args.scope=='local'and args.base=='https://127.0.0.1:3188/test')or(args.scope=='preview'and re.fullmatch(r'https://sexogate\.com/test/native-preview-[a-f0-9]{16}',args.base))
env=os.environ.copy();env.update(SEXOGATE_NATIVE_TEST_URL=args.base,SEXOGATE_MARKETPLACE_SCOPE=args.scope,PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
package=json.loads((ROOT/'.local/native-stage-package.json').read_text('utf8'));release=package['release'];results=[]
def run(name,command,scope=None):
 local=env.copy()
 if scope:local['SEXOGATE_NATIVE_TEST_SCOPE']=scope
 log=ROOT/('.local/acceptance-'+args.scope+'-'+name+'.log');start=time.time()
 with log.open('wb')as out:result=subprocess.run(command,cwd=ROOT,env=local,stdout=out,stderr=subprocess.STDOUT)
 row={'group':name,'exitCode':result.returncode,'seconds':round(time.time()-start,1),'log':str(log.relative_to(ROOT))};results.append(row);print(json.dumps(row),flush=True)
 if result.returncode:raise RuntimeError('ACCEPTANCE_FAILED_'+name)
def py(name,file,scope=None):run(name,[sys.executable,'-B','-X','utf8','scripts/'+file],scope)
def lane_a():
 py('navigation','test-native-browser.py','marketplace-mount-'+args.scope)
 py('actions','test-native-product-actions.py','marketplace-actions-'+args.scope)
 py('catalog','test-native-marketplace-browser.py')
 py('discovery','test-native-marketplace-discovery.py')
 if args.scope=='local':
  run('return-fixtures',[str(ROOT/'.local/php-runtime/php.exe'),'-d','extension=pdo_sqlite','-d','extension=sqlite3','scripts/seed-native-returns-local.php'])
  py('returns','test-native-returns-browser.py')
def lane_b():
 py('variants','test-native-marketplace-variants.py')
 py('age','test-native-adult-store.py','marketplace-adult-'+args.scope)
 py('polish','test-native-storefront-polish.py','marketplace-polish-'+args.scope)
 py('paint','test-native-first-paint.py','marketplace-paint-'+args.scope)
 py('cart-notifications','test-native-marketplace-cart-notifications.py','marketplace-cart-notifications-'+args.scope)
 py('returns-public','test-native-returns-public.py')
try:
 py('import','import-native-marketplace-batch.py')
 py('customer-copy','clean-native-marketplace-copy.py')
 run('source',[sys.executable,'-B','-X','utf8','scripts/test-native-marketplace-source-proof.py','--scope',args.scope,'--base',args.base])
 py('http','test-native-marketplace-http.py')
 with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
  futures=[pool.submit(lane_a),pool.submit(lane_b)]
  for future in futures:future.result()
 py('languages','test-native-languages.py','marketplace-mount-'+args.scope)
 assert json.loads((ROOT/'.local/native-stage-package.json').read_text('utf8'))['release']==release,'PACKAGE_CHANGED_DURING_ACCEPTANCE'
 proof=marketplace_acceptance(ROOT,args.scope,release,args.base,(ROOT/'.local/native-stage-package.json').stat().st_mtime)
 report={'base':args.base,'scope':args.scope,'release':release,'passed':True,'groups':results,'acceptance':proof,'realPayments':False};(ROOT/('.local/native-marketplace-acceptance-'+args.scope+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print(json.dumps({'passed':True,'release':release,'acceptance':proof}),flush=True)
except Exception as error:
 print(json.dumps({'passed':False,'release':release,'error':str(error)if isinstance(error,(RuntimeError,ValueError,AssertionError))else type(error).__name__,'finishedGroups':results}),flush=True);raise SystemExit(1)
