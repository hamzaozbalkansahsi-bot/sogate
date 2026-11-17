#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-product-runtime-memory.py
# Açıklama   : Hazırlanmış aynı sürümde dört gerçek PHP yolunu 128 MB altında ölçer; sağlayıcı çağrısını kapalı tutar.
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOWED = Path('D:/sexogate-local-artifacts-20261114/private-installs').resolve()
OUTPUT = ROOT / '.local/native-product-runtime-memory.json'
LIMIT = 128 * 1024 * 1024
CASES = ('worker', 'customer', 'adminSchema', 'adminProducts')
BLOCKED_FUNCTIONS = 'curl_exec,curl_multi_exec,fsockopen,pfsockopen,stream_socket_client,mail,exec,shell_exec,system,passthru,popen,proc_open'
MODULES = (
    'public/index.php', 'deploy/worker.php', 'private/control-http.php',
    'private/control-catalog.php', 'private/control-store.php', 'private/sexogate-catalog.php',
    'private/sexogate-runtime-catalog.php', 'private/catalog.json',
    'private/catalog-active.json.gz', 'private/catalog-active.meta.json',
    'private/sexogate-storefront-content.php', 'private/sexogate-product-editorial.php',
    'private/sexogate-product-editorial-data.json', 'private/sexogate-product-gallery.php',
    'private/sexogate-product-gallery-data.json', 'private/sexogate-notifications.php',
)

PROBE = r'''<?php
declare(strict_types=1);
ini_set('display_errors','0');ini_set('log_errors','0');
$sgMemoryReserve=str_repeat('m',65536);$sgMemoryInitialBuffer=ob_get_level();ob_start();
$sgMemoryReport=['ok'=>false,'memoryLimit'=>ini_get('memory_limit'),'phpVersion'=>PHP_VERSION,'realProviderCalled'=>false];
register_shutdown_function(static function()use(&$sgMemoryReserve,&$sgMemoryReport,$sgMemoryInitialBuffer):void{
 $sgMemoryReserve=null;$last=error_get_last();$fatal=$last!==null&&in_array($last['type'],[E_ERROR,E_PARSE,E_CORE_ERROR,E_COMPILE_ERROR],true);
 if(($sgMemoryReport['case']??'')==='worker'){
  $healthFile=($sgMemoryReport['_home']??'').'/worker-health.json';$health=is_file($healthFile)?json_decode((string)file_get_contents($healthFile),true):null;
  $same=is_array($health)&&isset($GLOBALS['health'])&&$health===$GLOBALS['health']&&($health['at']??0)>=($sgMemoryReport['_started']??PHP_INT_MAX)&&($health['release']??'')===($sgMemoryReport['release']??'');
  $sgMemoryReport['healthOk']=$same&&($health['ok']??false)===true&&($health['externalPublishingEnabled']??true)===false&&($health['checkoutEnabled']??true)===false;
  $sgMemoryReport['notificationsSent']=$same?(int)($health['notifications']['sent']??-1):-1;
  $sgMemoryReport['notificationsRetryOrFailed']=$same?(int)($health['notifications']['retryOrFailed']??-1):-1;
  $sgMemoryReport['ok']=$sgMemoryReport['healthOk']&&$sgMemoryReport['notificationsSent']===0&&$sgMemoryReport['notificationsRetryOrFailed']===0;
 }
 $sgMemoryReport['memoryLimit']=ini_get('memory_limit');$sgMemoryReport['usageBytes']=memory_get_usage(true);$sgMemoryReport['peakBytes']=memory_get_peak_usage(true);
 $sgMemoryReport['fatal']=$fatal;$sgMemoryReport['ok']=!$fatal&&($sgMemoryReport['ok']??false)&&$sgMemoryReport['memoryLimit']==='128M'&&$sgMemoryReport['peakBytes']<=134217728;
 unset($sgMemoryReport['_home'],$sgMemoryReport['_started']);while(ob_get_level()>$sgMemoryInitialBuffer)ob_end_clean();
 echo json_encode($sgMemoryReport,JSON_THROW_ON_ERROR|JSON_UNESCAPED_SLASHES)."\n";
});
set_error_handler(static function(int $severity):bool{if(!(error_reporting()&$severity))return false;throw new RuntimeException('runtime_memory_php_warning');});
function memoryCheck(bool $ok,string $code):void{if(!$ok)throw new RuntimeException($code);}
function memoryPublicHash(array $products):string{
 $values=[];foreach($products as$p){memoryCheck(preg_match('/^sg_ty_[a-f0-9]{16}$/D',$p['id']??'')===1,'public_namespace');memoryCheck(is_int($p['salePriceMinor']??null)&&$p['salePriceMinor']>0,'public_price');memoryCheck(($p['stockKnown']??null)===false&&array_key_exists('stockQuantity',$p)&&$p['stockQuantity']===null,'public_stock');$values[$p['id']]=[$p['code']??null,$p['salePriceMinor'],$p['currency']??null,$p['stockKnown'],$p['stockQuantity']];}ksort($values);return hash('sha256',json_encode($values,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES));
}
try{
 $home=realpath($argv[1]??'');$release=$argv[2]??'';$case=$argv[3]??'';
 memoryCheck($home!==false&&preg_match('/^[a-f0-9]{24}$/D',$release)===1&&in_array($case,['worker','customer','adminSchema','adminProducts'],true),'probe_args');
 $active=json_decode((string)file_get_contents($home.'/active.json'),true);memoryCheck(($active['release']??'')===$release,'active_release');
 $releaseRoot=$home.'/releases/'.$release;$private=$releaseRoot.'/private';
 $sgMemoryReport+=['case'=>$case,'release'=>$release,'_home'=>$home,'_started'=>time(),'requestMethod'=>$case==='worker'?'CLI':'GET','requestUri'=>match($case){'customer'=>'/test/api/catalog','adminSchema'=>'/test/api/admin/schema','adminProducts'=>'/test/api/admin/products',default=>null}];
 memoryCheck(ini_get('memory_limit')==='128M'&&ini_get('allow_url_fopen')==='0'&&ini_get('allow_url_include')==='0','limits_not_locked');
 if($case==='worker'){unset($_SERVER['REQUEST_METHOD'],$_SERVER['REQUEST_URI']);}else{$_SERVER['REQUEST_METHOD']='GET';$_SERVER['REQUEST_URI']=$sgMemoryReport['requestUri'];}$_SERVER['DOCUMENT_ROOT']=$releaseRoot.'/public';
 $runtime=require $releaseRoot.'/nodeno-runtime.php';memoryCheck(realpath($runtime['privateRoot']??'')===realpath($private)&&realpath($runtime['storageRoot']??'')===realpath($home.'/state'),'runtime_paths');unset($runtime);
 if($case==='worker'){require $home.'/worker.php';throw new RuntimeException('worker_did_not_exit');}
 define('NODENO_RUNTIME_LIBRARY',true);require $releaseRoot.'/public/index.php';
 $state=nodenoStoreContext($private);$sgMemoryReport['sourceProducts']=count($state['sourceCatalog']['products']??[]);$sgMemoryReport['publicProducts']=count($state['catalog']['products']??[]);$sgMemoryReport['stories']=count(array_filter($state['catalog']['products']??[],static fn($p)=>isset($p['storefrontStory']['tr']['intro'],$p['storefrontStory']['en']['intro'])));
 $sgMemoryReport['publicProtectedSha256']=memoryPublicHash($state['catalog']['products']??[]);
 memoryCheck($sgMemoryReport['publicProducts']===803&&($state['paymentsReady']??false)===false&&($state['config']['checkoutEnabled']??false)===false,'public_or_provider_state');
 if($case==='customer'){
  memoryCheck($sgMemoryReport['sourceProducts']===958&&$sgMemoryReport['stories']===803,'customer_counts');
  $encoded=json_encode($state['catalog'],JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES);$sgMemoryReport['encodedPayload']='actual_customer_catalog';
 }else{
  require_once $private.'/control-http.php';$db=nodenoControlDatabase($state['storage']);
  if($case==='adminSchema'){
   memoryCheck($sgMemoryReport['sourceProducts']===3152,'admin_schema_full_source');
   unset($state['catalog']);$sgMemoryReport['unusedCatalogReleased']=!isset($state['catalog']);memoryCheck($sgMemoryReport['unusedCatalogReleased'],'admin_schema_unused_catalog_retained');
   $ctx=['db'=>$db,'root'=>$state['storage'],'user'=>['id'=>'local-memory-probe','role'=>'owner'],'permissions'=>['*']];
   $schema=nodenoControlSchema($ctx,$state['sourceCatalog'],$state['config']);$sgMemoryReport['schemaProducts']=count($schema['products']??[]);$sgMemoryReport['schemaVisibleProducts']=count(array_filter($schema['products']??[],static fn($p)=>($p['visible']??false)===true));
   memoryCheck($sgMemoryReport['schemaProducts']===3152&&$sgMemoryReport['schemaVisibleProducts']===803,'admin_schema_response_counts');$encoded=json_encode($schema,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES);$sgMemoryReport['encodedPayload']='actual_admin_schema';
  }else{
   memoryCheck($sgMemoryReport['sourceProducts']===958,'exact_admin_products_active_source');unset($state['catalog']);$sgMemoryReport['unusedCatalogReleased']=!isset($state['catalog']);
   $rows=nodenoControlStoredRows($db,'products');$sgMemoryReport['rows']=count($rows);$sgMemoryReport['publishedRows']=count(array_filter($rows,static fn($r)=>($r['publishedVersion']??0)>0));$sgMemoryReport['reviewRows']=$sgMemoryReport['rows']-$sgMemoryReport['publishedRows'];
   memoryCheck($sgMemoryReport['rows']===958&&$sgMemoryReport['publishedRows']===803&&$sgMemoryReport['reviewRows']===155,'admin_product_rows');$encoded=json_encode(['data'=>$rows],JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES);$sgMemoryReport['encodedPayload']='actual_admin_product_rows';
  }
 }
 $sgMemoryReport['encodedBytes']=strlen($encoded);$sgMemoryReport['encodedSha256']=hash('sha256',$encoded);memoryCheck($sgMemoryReport['encodedBytes']>0,'empty_encoding');$sgMemoryReport['ok']=true;
}catch(Throwable $error){$sgMemoryReport['ok']=false;$sgMemoryReport['errorCode']='runtime_memory_case_failed';$sgMemoryReport['exceptionClass']=get_class($error);exit(1);}
'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def require(ok, code):
    if not ok:
        raise RuntimeError(code)


def read_json(path):
    require(path.is_file() and not path.is_symlink(), 'metadata_file_invalid')
    return json.loads(path.read_text('utf8'))


def tree(path):
    result = {}
    for file in sorted(path.rglob('*')):
        require(not file.is_symlink() and not (hasattr(file, 'is_junction') and file.is_junction()), 'package_link_rejected')
        if file.is_file():
            result[file.relative_to(path).as_posix()] = sha(file)
    return result


def state_snapshot(state):
    file = state / 'accounts.sqlite'
    require(file.is_file() and not file.is_symlink(), 'accounts_database_missing')
    connection = sqlite3.connect(file.resolve().as_uri() + '?mode=ro', uri=True)
    try:
        rows = list(connection.execute("SELECT id,data_json,published_json,version,published_version FROM control_records WHERE resource='products' ORDER BY id"))
        require(len(rows) == 958, 'prepared_management_count_not_958')
        setting = connection.execute("SELECT value_json FROM control_settings WHERE name='payment:stripe'").fetchone()
        require(not setting or json.loads(setting[0]).get('enabled') is not True, 'payment_provider_enabled')
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if 'sg_notify_subscriptions' in tables:
            require(connection.execute('SELECT COUNT(*) FROM sg_notify_subscriptions WHERE expires_at>?', (int(time.time()),)).fetchone()[0] == 0, 'active_notification_subscription_rejected')
        return {'rows': len(rows), 'recordsSha256': canonical_sha(rows)}
    finally:
        connection.close()


def run():
    require(len(sys.argv) == 1, 'unexpected_arguments')
    package_file = ROOT / '.local/native-stage-package.json'
    local_file = ROOT / '.local/native-stage-local.json'
    package, local = read_json(package_file), read_json(local_file)
    release = package.get('release', '')
    require(re.fullmatch('[a-f0-9]{24}', release) is not None and local.get('release') == release, 'package_local_release_mismatch')
    require(package.get('dataset') == '057fb50f7d5887fee341e3d5b4a3dd64' and package.get('checkoutEnabled') is False and package.get('previewOnly') is True, 'package_profile_invalid')
    base, home, bundle, archive = (Path(value).resolve() for value in (local['base'], local['home'], package['bundle'], package['archive']))
    require(base.parent == ALLOWED and re.fullmatch('native-mount-local-[a-f0-9]{16}', base.name) is not None, 'local_base_rejected')
    require(home == base / 'private-home/.sexogate-native-test' and bundle.is_relative_to(ALLOWED) and archive.is_relative_to(ALLOWED), 'local_paths_rejected')
    require(read_json(home / 'active.json').get('release') == release, 'prepared_active_release_mismatch')
    prepared = home / 'releases' / release
    require(prepared.is_dir() and prepared.resolve().is_relative_to(home), 'prepared_release_rejected')
    for relative in MODULES:
        require((bundle / relative).is_file() and (prepared / relative).is_file(), 'required_module_missing')
        require(sha(bundle / relative) == sha(prepared / relative), 'prepared_module_differs_from_package')
    require(sha(home / 'worker.php') == sha(prepared / 'deploy/worker.php'), 'worker_differs_from_package')
    require(sha(archive) == package.get('sha256'), 'archive_hash_mismatch')
    meta = read_json(prepared / 'private/catalog-active.meta.json')
    require(meta.get('dataset') == package['dataset'] and meta.get('sourceCount') == 3152 and meta.get('activeCount') == 958, 'runtime_catalog_meta_mismatch')
    before = {'packageMetadata': sha(package_file), 'localMetadata': sha(local_file), 'active': sha(home / 'active.json'), 'worker': sha(home / 'worker.php'), 'archive': sha(archive), 'bundleTree': canonical_sha(tree(bundle)), 'modules': {name: sha(prepared / name) for name in MODULES}}
    state_before = state_snapshot(home / 'state')
    probe = home / ('runtime-memory-probe-' + uuid.uuid4().hex + '.php')
    require(probe.resolve().is_relative_to(home), 'probe_path_rejected')
    probe.write_text(PROBE, encoding='utf8')
    report = {'schema': 1, 'release': release, 'dataset': package['dataset'], 'scriptSha256': sha(Path(__file__)), 'probeSha256': sha(probe), 'executionEnvironment': 'local-isolated-php-128M', 'realProviderCalled': False, 'packageUnchanged': False, 'cases': {}, 'moduleHashes': before['modules'], 'packageArchiveSha256': before['archive'], 'packageTreeSha256': before['bundleTree'], 'packageMetadataSha256': before['packageMetadata'], 'localMetadataSha256': before['localMetadata'], 'activePointerSha256': before['active'], 'workerSha256': before['worker'], 'stateBefore': state_before, 'actualExecutions': 0, 'passed': False}
    php = ROOT / '.local/php-runtime/php.exe'
    require(php.is_file(), 'local_php_missing')
    try:
        for case in CASES:
            require(sha(probe) == report['probeSha256'], 'probe_changed')
            command = [str(php), '-d', 'memory_limit=128M', '-d', 'allow_url_fopen=0', '-d', 'allow_url_include=0', '-d', 'disable_functions=' + BLOCKED_FUNCTIONS, '-d', 'extension=pdo_sqlite', '-d', 'extension=sqlite3', str(probe), str(home), release, case]
            result = subprocess.run(command, cwd=home, capture_output=True, timeout=180)
            report['actualExecutions'] += 1
            value = json.loads(result.stdout)
            require(isinstance(value, dict) and value.get('case') == case and value.get('release') == release, 'probe_output_identity_invalid')
            value.update(exitCode=result.returncode, command=command, stdoutSha256=hashlib.sha256(result.stdout).hexdigest(), stderrSha256=hashlib.sha256(result.stderr).hexdigest(), stderrBytes=len(result.stderr))
            report['cases'][case] = value
        require(all(value.get('exitCode') == 0 and value.get('ok') is True and value.get('memoryLimit') == '128M' and 0 < value.get('peakBytes', LIMIT + 1) <= LIMIT and value.get('stderrBytes') == 0 for value in report['cases'].values()) and len(report['cases']) == 4, 'runtime_case_or_limit_failed')
        hashes = {report['cases'][case]['publicProtectedSha256'] for case in CASES if case != 'worker'}
        require(len(hashes) == 1, 'public_prices_stock_or_identity_differs')
        state_after = state_snapshot(home / 'state')
        require(state_before == state_after, 'prepared_product_records_changed')
        after = {'packageMetadata': sha(package_file), 'localMetadata': sha(local_file), 'active': sha(home / 'active.json'), 'worker': sha(home / 'worker.php'), 'archive': sha(archive), 'bundleTree': canonical_sha(tree(bundle)), 'modules': {name: sha(prepared / name) for name in MODULES}}
        require(before == after, 'package_or_prepared_modules_changed')
        require(sha(probe) == report['probeSha256'], 'probe_changed')
        report.update(packageUnchanged=True, stateAfter=state_after, protectedProductRecordsUnchanged=True, publicPricesStockIdentityEqual=True, verifiedAfterReload=True, passed=True)
    except Exception:
        report['errorCode'] = 'runtime_memory_verification_failed'
    finally:
        OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'passed': report['passed'], 'release': release, 'casesExecuted': report['actualExecutions'], 'report': str(OUTPUT)}, ensure_ascii=False))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    try:
        sys.exit(run())
    except Exception:
        print(json.dumps({'passed': False, 'errorCode': 'runtime_memory_prerequisite_failed', 'actualExecutions': 0}))
        sys.exit(1)
