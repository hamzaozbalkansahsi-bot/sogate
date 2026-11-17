<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/deploy/worker.php
 * Açıklama   : Yalnız CLI üzerinden özgün içerik kuyruğunu işler ve mahremiyetsiz kalp atışı yazar.
 */
declare(strict_types=1);
if(PHP_SAPI!=='cli'){http_response_code(404);exit;}
ini_set('display_errors','0');$home=__DIR__;$active=json_decode((string)file_get_contents($home.'/active.json'),true);
if(!preg_match('/^[a-f0-9]{24}$/D',$active['release']??''))exit(1);
$lock=fopen($home.'/worker.lock','c');if(!$lock||!flock($lock,LOCK_EX|LOCK_NB))exit;
try{
 $release=$home.'/releases/'.$active['release'];define('NODENO_RUNTIME_LIBRARY',true);require $release.'/public/index.php';require $release.'/private/blog-worker.php';
 $result=nodenoBlogTick($home.'/state',$release.'/private',$release.'/public');require_once $release.'/private/sexogate-notifications.php';$context=nodenoStoreContext($release.'/private');$notifications=sgNotifyTick($home.'/state',$context['catalog']);unset($context);$health=['ok'=>true,'at'=>time(),'release'=>$active['release'],'blog'=>$result,'notifications'=>$notifications,'externalPublishingEnabled'=>false,'checkoutEnabled'=>false];
}catch(Throwable $error){$health=['ok'=>false,'at'=>time(),'error'=>'native_worker_failed'];}
file_put_contents($home.'/worker-health.json.tmp',json_encode($health,JSON_THROW_ON_ERROR),LOCK_EX);chmod($home.'/worker-health.json.tmp',0600);rename($home.'/worker-health.json.tmp',$home.'/worker-health.json');flock($lock,LOCK_UN);fclose($lock);exit($health['ok']?0:1);
