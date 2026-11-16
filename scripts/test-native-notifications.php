<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/test-native-notifications.php
 * Açıklama   : İzole SQLite, gerçek Web Push şifrelemesi ve sahte taşıyıcıyla kuyruk güvenliğini sınar.
 */
declare(strict_types=1);
$root=dirname(__DIR__);$packageFile=$root.'/.local/native-stage-package.json';
if(in_array('--source',$argv,true)||!is_file($packageFile)){
 $fixtureBase=sys_get_temp_dir().'/sexogate-notify-source-'.bin2hex(random_bytes(8));$private=$fixtureBase.'/release/private';mkdir($private,0700,true);
 foreach(glob($root.'/native-store/upstream/hosting/*.php')as $file)copy($file,$private.'/'.basename($file));
 copy($root.'/native-store/storefront/notifications.php',$private.'/sexogate-notifications.php');mkdir($private.'/notifications-vendor');file_put_contents($private.'/notifications-vendor/autoload.php','<?php require '.var_export($root.'/native-store/notifications/vendor/autoload.php',true).';');
}else{$package=json_decode(file_get_contents($packageFile),true,32,JSON_THROW_ON_ERROR);$private=$package['bundle'].'/private';}
require_once $private.'/sexogate-notifications.php';require_once $private.'/control-store.php';require_once $private.'/notifications-vendor/autoload.php';
$dir=isset($fixtureBase)?$fixtureBase.'/state':sys_get_temp_dir().'/sexogate-notification-test-'.bin2hex(random_bytes(8));mkdir($dir,0700);$db=nodenoControlDatabase($dir);sgNotifySchema($db);$assertions=0;
function checkNotify(bool $condition,string $label):void{global $assertions;if(!$condition)throw new RuntimeException($label);$assertions++;echo 'PASS '.$label.PHP_EOL;}
function rejectNotify(callable $operation,string $label):void{try{$operation();}catch(NodenoAccountHttpError $e){checkNotify($e->status===422,$label);return;}throw new RuntimeException('accepted_'.$label);}
$clientKeys=\Minishlink\WebPush\VAPID::createVapidKeys();$b64=static fn(string $raw)=>rtrim(strtr(base64_encode($raw),'+/','-_'),'=');$sub=['endpoint'=>'https://fcm.googleapis.com/wp/isolated-fixture','keys'=>['p256dh'=>$clientKeys['publicKey'],'auth'=>$b64(random_bytes(16))]];
foreach(['http://fcm.googleapis.com/a','https://127.0.0.1/a','https://fcm.googleapis.com.evil.example/a','https://fcm.googleapis.com:443/a','https://fcm.googleapis.com@evil.example/a','https://fcm.googleapis.com/a#fragment']as $url)rejectNotify(fn()=>sgNotifyEndpoint($url),'endpoint_reject_'.substr(hash('sha256',$url),0,8));
checkNotify(sgNotifySubscription($sub)['contentEncoding']==='aes128gcm','valid_subscription');$sub=sgNotifySubscription($sub);rejectNotify(fn()=>sgNotifySubscription(['endpoint'=>$sub['endpoint'],'keys'=>['p256dh'=>'bad','auth'=>'bad']]),'bad_client_keys');
rejectNotify(fn()=>sgNotifySubscription(['endpoint'=>$sub['endpoint'],'keys'=>'bad']),'invalid_key_shape');
$keys=sgNotifyKeys($dir);checkNotify(sgNotifyKeys($dir)===$keys,'persistent_vapid_keys');checkNotify(!str_contains(file_get_contents($dir.'/sg-notify-keys.bin'),$keys['privateKey']),'encrypted_vapid_key');
$senderClient=new class implements \Psr\Http\Client\ClientInterface{public ?\Psr\Http\Message\RequestInterface $request=null;public function sendRequest(\Psr\Http\Message\RequestInterface $request):\Psr\Http\Message\ResponseInterface{$this->request=$request;return new \GuzzleHttp\Psr7\Response(201);}};
$sdk=new \Minishlink\WebPush\WebPush(['VAPID'=>['subject'=>'mailto:info@sexogate.com',...$keys]],['TTL'=>3600],$senderClient);
$report=$sdk->sendOneNotification(\Minishlink\WebPush\Subscription::create($sub),'{"private":"İstanbul Şişli"}');if(!$report->isSuccess())echo 'SDK fixture: '.$report->getReason().PHP_EOL;checkNotify($report->isSuccess()&&$senderClient->request?->getHeaderLine('Content-Encoding')==='aes128gcm','real_sdk_encryption');checkNotify(str_starts_with($senderClient->request->getHeaderLine('Authorization'),'vapid ')&&!str_contains((string)$senderClient->request->getBody(),'İstanbul'),'authenticated_encrypted_payload');
$owner=str_repeat('a',64);$id='device_fixture';$encrypted=nodenoControlEncrypt($dir,json_encode($sub,JSON_THROW_ON_ERROR),'notify:'.$id);$db->prepare('INSERT INTO sg_notify_subscriptions VALUES(?,?,?,?,?,?)')->execute([$id,$owner,hash('sha256',$sub['endpoint']),$encrypted,'/test',time()+3600]);
$product=['id'=>'sg_test_item','stockKnown'=>true,'stockQuantity'=>0];$catalog=['products'=>[$product]];sgNotifyWatch($db,$owner,[$product['id']],$catalog);checkNotify(sgNotifyScan($db,$catalog,time())===0,'baseline_not_notified');
$unknown=['products'=>[array_replace($product,['stockKnown'=>false,'stockQuantity'=>999])]];checkNotify(sgNotifyScan($db,$unknown,time())===0,'supplier_public_availability_not_stock');
$available=['products'=>[array_replace($product,['stockQuantity'=>2])]];checkNotify(sgNotifyScan($db,$available,time())===1,'verified_restock_queued');checkNotify(sgNotifyScan($db,$available,time())===0,'scan_idempotent');
$failed=sgNotifyTick($dir,$available,static fn()=>503);checkNotify($failed['sent']===0&&(int)$db->query("SELECT attempts FROM sg_notify_jobs")->fetchColumn()===1,'timeout_retries_durable');$db->exec('UPDATE sg_notify_jobs SET next_at=0');
$sent=sgNotifyTick($dir,$available,static function($root,$subscription,$payload):int{checkNotify(!isset($payload['productName'],$payload['image'])&&$payload['url']==='/test/?product=sg_test_item','private_notification_payload');return 201;});checkNotify($sent['sent']===1,'worker_delivered_mock_transport');checkNotify(sgNotifyTick($dir,$available,static fn()=>throw new RuntimeException('duplicate'))['sent']===0,'delivered_event_not_repeated');
sgNotifyScan($db,$catalog,time());sgNotifyScan($db,$available,time());$stale=sgNotifyTick($dir,$unknown,static fn()=>throw new RuntimeException('unverified_stock_must_not_send'));checkNotify($stale['sent']===0&&(int)$db->query("SELECT COUNT(*) FROM sg_notify_jobs WHERE status='cancelled'")->fetchColumn()===1,'stock_rechecked_before_delivery');
rejectNotify(fn()=>sgNotifyWatch($db,$owner,[['nested'=>'invalid']],$catalog),'invalid_watch_shape');
sgNotifyWatch($db,str_repeat('b',64),[$product['id']],$catalog);sgNotifyRevoke($db,str_repeat('b',64));checkNotify((int)$db->query('SELECT COUNT(*) FROM sg_notify_subscriptions')->fetchColumn()===1,'device_ownership_isolated');
sgNotifyScan($db,$catalog,time());sgNotifyScan($db,$available,time());sgNotifyRevoke($db,$owner);checkNotify((int)$db->query('SELECT COUNT(*) FROM sg_notify_subscriptions')->fetchColumn()===0&&(int)$db->query("SELECT COUNT(*) FROM sg_notify_jobs WHERE status='queued'")->fetchColumn()===0,'revoke_cancels_delivery');
checkNotify($db->query('PRAGMA integrity_check')->fetchColumn()==='ok','database_integrity');echo json_encode(['assertions'=>$assertions,'externalPushDelivered'=>false,'transport'=>'isolated_mock','realEncryption'=>true],JSON_THROW_ON_ERROR).PHP_EOL;
