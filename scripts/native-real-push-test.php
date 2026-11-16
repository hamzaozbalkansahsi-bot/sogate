<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/native-real-push-test.php
 * Açıklama   : Süreli tek kullanımlık bakım izniyle yalnız izole test cihazına bir push gönderir.
 */
declare(strict_types=1);
ini_set('display_errors','0');header('Content-Type: application/json; charset=utf-8');header('Cache-Control: private, no-store');header('X-Robots-Tag: noindex');
try{
 if(($_SERVER['HTTP_HOST']??'')!=='sexogate.com'||($_SERVER['HTTPS']??'')!=='on'||($_SERVER['REQUEST_METHOD']??'')!=='POST')throw new RuntimeException('scope');
 $path=__DIR__.'/app/native-push-request.json';$lock=fopen($path,'r+');if(!$lock||!flock($lock,LOCK_EX))throw new RuntimeException('request');
 $request=json_decode(stream_get_contents($lock),true,16,JSON_THROW_ON_ERROR);
 if(time()>($request['expires']??0)||!empty($request['consumed'])||!hash_equals($request['tokenHash']??'',hash('sha256',$_SERVER['HTTP_X_NATIVE_PUSH']??'')))throw new RuntimeException('authorization');
 foreach(['release'=>24,'endpointHash'=>64,'tag'=>64]as $field=>$length)if(!preg_match('/^[a-f0-9]{'.$length.'}$/D',$request[$field]??''))throw new RuntimeException('request');
 $home=dirname(realpath($_SERVER['DOCUMENT_ROOT'])).'/.sexogate-native-test';$owner=json_decode(file_get_contents($home.'/owner.json'),true,16,JSON_THROW_ON_ERROR);$active=json_decode(file_get_contents($home.'/active.json'),true,16,JSON_THROW_ON_ERROR);
 if(($owner['purpose']??'')!=='sexogate-native-test-v1'||!hash_equals($owner['owner']??'',$request['owner']??'')||($active['release']??'')!==$request['release'])throw new RuntimeException('owner');
 $release=$home.'/releases/'.$request['release'];define('NODENO_RUNTIME_LIBRARY',true);require $release.'/public/index.php';require $release.'/private/sexogate-notifications.php';require_once $release.'/private/control-store.php';
 $context=nodenoStoreContext($release.'/private');$known=array_column($context['catalog']['products'],null,'id');if(!isset($known[$request['productId']??'']))throw new RuntimeException('product');
 $db=nodenoControlDatabase($home.'/state');$read=$db->prepare('SELECT id,encrypted FROM sg_notify_subscriptions WHERE endpoint_hash=? AND expires_at>?');$read->execute([$request['endpointHash'],time()]);$row=$read->fetch(PDO::FETCH_ASSOC);if(!$row)throw new RuntimeException('test_subscription');
 // Önce tüketilir: yanıt kaybolduğunda yeniden çalıştırma ikinci bildirim göndermez.
 $request['consumed']=true;rewind($lock);ftruncate($lock,0);fwrite($lock,json_encode($request,JSON_THROW_ON_ERROR));fflush($lock);flock($lock,LOCK_UN);fclose($lock);
 $subscription=json_decode(nodenoControlDecrypt($home.'/state',$row['encrypted'],'notify:'.$row['id']),true,16,JSON_THROW_ON_ERROR);
 $code=sgNotifySend($home.'/state',$subscription,['title'=>'SEXOGATE','body'=>'İzole bağlantı testi','tag'=>$request['tag'],'url'=>'/test/?product='.rawurlencode($request['productId'])]);
 echo json_encode(['senderAccepted'=>$code>=200&&$code<300,'httpStatus'=>$code,'realStockEvent'=>false],JSON_THROW_ON_ERROR);
}catch(Throwable $error){http_response_code(503);echo '{"error":"controlled_push_test_failed"}';}
