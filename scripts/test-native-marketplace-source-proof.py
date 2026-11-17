#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-marketplace-source-proof.py
# Açıklama   : Kaynak fiyat/kod, gerçek PHP paketi ve izole iade testlerini çalıştırıp aynı sürüm/veriye bağlı kabul kanıtı üretir.
import argparse,datetime,hashlib,json,os,re,subprocess,sys
from pathlib import Path
from native_marketplace_acceptance import SOURCE_TESTS,file_sha,marketplace_source_fingerprint,validate_marketplace_source_proof

ROOT=Path(__file__).resolve().parent.parent

def execute(name,arguments):
 command=([sys.executable,'-B','-X','utf8']if name=='data'else[str(ROOT/'.local/php-runtime/php.exe'),'-d','extension=pdo_sqlite','-d','extension=sqlite3'])+[str(ROOT/SOURCE_TESTS[name])]+arguments
 # Sıkıştırılmış yerel kaynakta 958 ayrı ham dosya açılır; gerçek hash denetimi atlanmaz.
 timeout=900 if name=='data'else 300
 print(json.dumps({'execution':name,'phase':'started','timeoutSeconds':timeout}),flush=True)
 completed=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=timeout)
 stdout=completed.stdout.decode('utf-8-sig');stderr=completed.stderr.decode('utf-8-sig')
 if completed.returncode!=0:
  print(json.dumps({'execution':name,'exitCode':completed.returncode,'stdout':stdout[-4000:],'stderr':stderr[-4000:]},ensure_ascii=False),file=sys.stderr)
  raise ValueError('MARKETPLACE_SOURCE_TEST_FAILED')
 if name=='data':
  counts=re.findall(r'^Ran (\d+) tests? in ',stderr,re.M)
  if len(counts)!=1 or not re.search(r'^OK\s*$',stderr,re.M):raise ValueError('MARKETPLACE_SOURCE_UNIT_OUTPUT_INVALID')
  result={'passed':int(counts[0])}
 else:
  result=json.loads(stdout)
  if not isinstance(result,dict):raise ValueError('MARKETPLACE_SOURCE_PHP_OUTPUT_INVALID')
 result.update(exitCode=completed.returncode,scriptSha256=file_sha(ROOT/SOURCE_TESTS[name]),arguments=arguments,stdoutSha256=hashlib.sha256(completed.stdout).hexdigest(),stderrSha256=hashlib.sha256(completed.stderr).hexdigest())
 print(json.dumps({'execution':name,'passed':result.get('passed'),'exitCode':completed.returncode}),flush=True)
 return result

def main():
 parser=argparse.ArgumentParser(description='Sunucuya bağlanmadan yerel izole testlerden sürüme bağlı kaynak kabul kanıtı üretir.')
 parser.add_argument('--scope',choices=['local','preview','remote'],default=os.environ.get('SEXOGATE_MARKETPLACE_SCOPE','local'))
 parser.add_argument('--base',default=os.environ.get('SEXOGATE_NATIVE_TEST_URL','https://127.0.0.1:3188/test'))
 args=parser.parse_args();base=args.base.rstrip('/')
 if not re.fullmatch(r'https://(?:127\.0\.0\.1:3188|sexogate\.com)/test(?:/native-preview-[a-f0-9]{16})?',base):raise ValueError('MARKETPLACE_SOURCE_BASE_INVALID')
 output=ROOT/('docs/native-marketplace-source-'+args.scope+'-results.json')
 # Başarısız yeni koşu, aynı dosya adındaki önceki başarılı sonucu bırakamaz.
 output.unlink(missing_ok=True)
 before=marketplace_source_fingerprint(ROOT)
 executions={name:execute(name,['--source']if name.endswith('Source')else[])for name in SOURCE_TESTS}
 after=marketplace_source_fingerprint(ROOT)
 if before!=after:raise ValueError('MARKETPLACE_SOURCE_INPUT_CHANGED_DURING_TEST')
 selection=json.loads((ROOT/'.local/native-marketplace-selection.json').read_text('utf-8-sig'))
 proof={'schema':1,'profile':'marketplace-source-v1','scope':args.scope,'targetBase':base,'release':before['release'],'dataset':before['dataset'],'sourceDetails':before['sourceDetails'],'loadedNew':before['loadedNew'],'runnerSha256':file_sha(Path(__file__)),'fingerprint':before,'executions':executions,'executionEnvironment':'local-isolated-cli','allMarketplaceProductsTransferred':False,'publishedToRemote':False,'realPaymentOrFiscalApiCalled':False,'completedAt':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 validate_marketplace_source_proof(ROOT,proof,args.scope,before['release'],base,selection,executions['payload'].get('publishCandidates'))
 temporary=output.with_suffix('.json.tmp');temporary.write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding='utf8');temporary.replace(output)
 print(json.dumps({'sourceProof':str(output.relative_to(ROOT)),'scope':args.scope,'targetBase':base,'release':before['release'],'dataset':before['dataset'],'sourceDetails':before['sourceDetails'],'loadedNew':before['loadedNew'],'passed':{name:result['passed']for name,result in executions.items()},'allMarketplaceProductsTransferred':False,'publishedToRemote':False,'realPaymentOrFiscalApiCalled':False}),flush=True)

if __name__=='__main__':
 try:main()
 except Exception as error:
  code=str(error)if isinstance(error,ValueError)and re.fullmatch('[A-Z_0-9]+',str(error))else type(error).__name__
  print(json.dumps({'sourceProofCreated':False,'code':code}),file=sys.stderr);raise SystemExit(1)
