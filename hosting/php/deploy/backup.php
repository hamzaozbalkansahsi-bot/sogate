<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/deploy/backup.php
 * Açıklama   : Sabit test uygulamasının tek kullanımlık, sunucuda şifrelenen DB yedeği.
 */
declare(strict_types=1);
ini_set('display_errors','0');set_time_limit(120);header('Content-Type: application/json');header('Cache-Control: no-store');header('X-Robots-Tag: noindex, nofollow');
$request=__DIR__.'/app/backup-request.json';$db=null;$lock=null;
try{
    if(($_SERVER['REQUEST_METHOD']??'')!=='POST'||!is_file($request))throw new RuntimeException('BACKUP_NOT_AVAILABLE');$v=json_decode(file_get_contents($request),true,32,JSON_THROW_ON_ERROR);$token=$_SERVER['HTTP_X_BACKUP_TOKEN']??'';
    if(!is_string($token)||strlen($token)!==64||!hash_equals($v['token_hash'],hash('sha256',$token))||$v['expires']<time()||!preg_match('/\A[a-f0-9]{24}\z/',$v['id']))throw new RuntimeException('BACKUP_NOT_AVAILABLE');
    $active=require __DIR__.'/app/active.php';if(!is_string($active)||!preg_match('/\A[a-f0-9]{24}\z/',$active))throw new RuntimeException('BACKUP_RELEASE_INVALID');require __DIR__.'/app/releases/'.$active.'/vendor/autoload.php';
    $config=Sexogate\Config::load(__DIR__.'/app/config.local.json');if(!$config->local()||$config->get('app_url')!=='https://sexogate.com/test')throw new RuntimeException('TEST_BACKUP_ONLY');$db=new Sexogate\Database($config);$schema=$db->one('SELECT DATABASE() name')['name'];if(!str_ends_with($schema,'_test'))throw new RuntimeException('TEST_DATABASE_REQUIRED');
    $lock='sexogate:migrate:'.substr(hash('sha256',$schema),0,40);if((int)$db->one('SELECT GET_LOCK(?,10) acquired',[$lock])['acquired']!==1)throw new RuntimeException('BACKUP_LOCK_FAILED');
    $snapshot=(new Sexogate\Backup($db,$config))->snapshot();$snapshot['configuration']=json_decode(file_get_contents(__DIR__.'/app/config.local.json'),true,32,JSON_THROW_ON_ERROR);$bytes=Sexogate\Backup::encrypt($snapshot,hex2bin($v['key']));
    $folder=__DIR__.'/app/backups';if(!is_dir($folder))mkdir($folder,0700);$file=$folder.'/'.$v['id'].'.aesgcm';if(is_file($file))throw new RuntimeException('BACKUP_EXISTS');file_put_contents($file,$bytes,LOCK_EX);chmod($file,0600);unlink($request);echo json_encode(['created'=>true,'id'=>$v['id'],'bytes'=>strlen($bytes),'sha256'=>hash('sha256',$bytes),'tables'=>count($snapshot['tables']),'rows'=>array_sum(array_column($snapshot['tables'],'count'))]);
}catch(Throwable $e){http_response_code(503);echo json_encode(['created'=>false,'errorType'=>get_class($e)]);}
finally{if($db&&$lock)$db->one('SELECT RELEASE_LOCK(?) released',[$lock]);}
