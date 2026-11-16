<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/notifications.php
 * Açıklama   : İzinli cihaz aboneliklerini, doğrulanmış stok geçişlerini ve kalıcı bildirim kuyruğunu yönetir.
 */
declare(strict_types=1);

function sgNotifySchema(PDO $db):void {
 $db->exec("CREATE TABLE IF NOT EXISTS sg_notify_subscriptions(id TEXT PRIMARY KEY,owner TEXT NOT NULL,endpoint_hash TEXT NOT NULL UNIQUE,encrypted TEXT NOT NULL,mount TEXT NOT NULL,expires_at INTEGER NOT NULL);
 CREATE TABLE IF NOT EXISTS sg_notify_watches(owner TEXT NOT NULL,product_id TEXT NOT NULL,available INTEGER,revision INTEGER NOT NULL DEFAULT 0,PRIMARY KEY(owner,product_id));
 CREATE TABLE IF NOT EXISTS sg_notify_jobs(id TEXT PRIMARY KEY,subscription_id TEXT NOT NULL,product_id TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'queued',attempts INTEGER NOT NULL DEFAULT 0,next_at INTEGER NOT NULL,lease_until INTEGER NOT NULL DEFAULT 0,created_at INTEGER NOT NULL);
 CREATE INDEX IF NOT EXISTS sg_notify_due ON sg_notify_jobs(status,next_at);");
}
function sgNotifyKeys(string $root):array {
 require_once __DIR__.'/notifications-vendor/autoload.php';
 $path=$root.'/sg-notify-keys.bin';$lock=fopen($root.'/sg-notify-keys.lock','c');
 if(!$lock||!flock($lock,LOCK_EX))throw new RuntimeException('notify_keys_unavailable');
 try{
  if(is_link($path))throw new RuntimeException('notify_keys_path');
  if(!is_file($path)){
   $keys=\Minishlink\WebPush\VAPID::createVapidKeys();$tmp=$path.'.'.bin2hex(random_bytes(6));
   file_put_contents($tmp,nodenoControlEncrypt($root,json_encode($keys,JSON_THROW_ON_ERROR),'notify:vapid'),LOCK_EX);chmod($tmp,0600);rename($tmp,$path);
  }
  return json_decode(nodenoControlDecrypt($root,(string)file_get_contents($path),'notify:vapid'),true,8,JSON_THROW_ON_ERROR);
 }finally{flock($lock,LOCK_UN);fclose($lock);}
}
function sgNotifyEndpoint(string $endpoint):string {
 $p=parse_url($endpoint);
 if(!$p||strlen($endpoint)>2048||($p['scheme']??'')!=='https'||isset($p['user'],$p['pass'])||isset($p['user'])||isset($p['pass'])||isset($p['fragment'])||isset($p['port'])||!in_array($p['host']??'',['fcm.googleapis.com','updates.push.services.mozilla.com','web.push.apple.com'],true)||empty($p['path'])||preg_match('/[\x00-\x20\x7f]/',$endpoint))throw new NodenoAccountHttpError(422,'push_endpoint_invalid');
 return $p['host'];
}
function sgNotifySubscription(array $value):array {
 $endpoint=$value['endpoint']??null;$keys=$value['keys']??[];if(!is_array($keys))throw new NodenoAccountHttpError(422,'push_keys_invalid');
 if(!is_string($endpoint))throw new NodenoAccountHttpError(422,'push_endpoint_invalid');sgNotifyEndpoint($endpoint);
 foreach(['p256dh'=>65,'auth'=>16]as $key=>$length){$raw=$keys[$key]??null;if(!is_string($raw)||!preg_match('/^[a-zA-Z0-9_-]+={0,2}$/D',$raw)||strlen((string)base64_decode(strtr($raw,'-_','+/'),true))!==$length)throw new NodenoAccountHttpError(422,'push_keys_invalid');}
 return ['endpoint'=>$endpoint,'keys'=>['p256dh'=>$keys['p256dh'],'auth'=>$keys['auth']],'contentEncoding'=>'aes128gcm'];
}
function sgNotifyAvailability(array $product):?bool {
 // Kamu tedarikçi bulunabilirliği, teyitli satılabilir stok yerine kullanılmaz.
 if(($product['stockKnown']??false)!==true||!is_int($product['stockQuantity']??null)||$product['stockQuantity']<0)return null;
 return $product['stockQuantity']>0;
}
function sgNotifyWatch(PDO $db,string $owner,array $ids,array $catalog):void {
 if(!array_is_list($ids)||count($ids)>100)throw new NodenoAccountHttpError(422,'watch_limit');
 $known=array_column($catalog['products']??[],null,'id');
 foreach($ids as $id)if(!is_string($id)||!isset($known[$id]))throw new NodenoAccountHttpError(422,'watch_product_invalid');
 $ids=array_values(array_unique($ids));
 nodenoControlTransaction($db,static function()use($db,$owner,$ids,$known):void{
  $read=$db->prepare('SELECT product_id FROM sg_notify_watches WHERE owner=?');$read->execute([$owner]);
  foreach($read->fetchAll(PDO::FETCH_COLUMN)as $id)if(!in_array($id,$ids,true)){$db->prepare('DELETE FROM sg_notify_watches WHERE owner=? AND product_id=?')->execute([$owner,$id]);$db->prepare("UPDATE sg_notify_jobs SET status='cancelled' WHERE product_id=? AND subscription_id IN(SELECT id FROM sg_notify_subscriptions WHERE owner=?) AND status IN('queued','processing')")->execute([$id,$owner]);}
  $insert=$db->prepare('INSERT OR IGNORE INTO sg_notify_watches(owner,product_id,available)VALUES(?,?,?)');
  foreach($ids as $id)$insert->execute([$owner,$id,sgNotifyAvailability($known[$id])===null?null:(int)sgNotifyAvailability($known[$id])]);
 });
}
function sgNotifyRevoke(PDO $db,string $owner):void {
 nodenoControlTransaction($db,static function()use($db,$owner):void{
  $db->prepare("UPDATE sg_notify_jobs SET status='cancelled' WHERE subscription_id IN(SELECT id FROM sg_notify_subscriptions WHERE owner=?) AND status IN('queued','processing')")->execute([$owner]);
  $db->prepare('DELETE FROM sg_notify_subscriptions WHERE owner=?')->execute([$owner]);$db->prepare('DELETE FROM sg_notify_watches WHERE owner=?')->execute([$owner]);
 });
}
function sgNotifyScan(PDO $db,array $catalog,int $now):int {
 $known=array_column($catalog['products']??[],null,'id');$queued=0;
 nodenoControlTransaction($db,static function()use($db,$known,$now,&$queued):void{
  foreach($db->query('SELECT * FROM sg_notify_watches')->fetchAll(PDO::FETCH_ASSOC)as $watch){
   $id=$watch['product_id'];$value=isset($known[$id])?sgNotifyAvailability($known[$id]):null;
   if($value===null)continue;
   $changed=$watch['available']!==null&&(bool)$watch['available']!==$value;$revision=(int)$watch['revision']+($changed?1:0);
   if($changed&&$value){
    $subs=$db->prepare('SELECT id FROM sg_notify_subscriptions WHERE owner=? AND expires_at>?');$subs->execute([$watch['owner'],$now]);
    foreach($subs->fetchAll(PDO::FETCH_COLUMN)as $sub){$job=hash('sha256',$sub.'|'.$id.'|'.$revision);$statement=$db->prepare('INSERT OR IGNORE INTO sg_notify_jobs(id,subscription_id,product_id,next_at,created_at)VALUES(?,?,?,?,?)');$statement->execute([$job,$sub,$id,$now,$now]);$queued+=$statement->rowCount();}
   }
   $db->prepare('UPDATE sg_notify_watches SET available=?,revision=? WHERE owner=? AND product_id=?')->execute([(int)$value,$revision,$watch['owner'],$id]);
  }
 });return $queued;
}
function sgNotifySend(string $root,array $subscription,array $payload):int {
 $host=sgNotifyEndpoint($subscription['endpoint']);$ips=gethostbynamel($host)?:[];
 $ips=array_values(array_filter($ips,static fn($ip)=>filter_var($ip,FILTER_VALIDATE_IP,FILTER_FLAG_IPV4|FILTER_FLAG_NO_PRIV_RANGE|FILTER_FLAG_NO_RES_RANGE)!==false));
 if(!$ips)throw new RuntimeException('push_dns_unavailable');
 $keys=sgNotifyKeys($root);$client=new \GuzzleHttp\Client(['handler'=>\GuzzleHttp\HandlerStack::create(new \GuzzleHttp\Handler\CurlHandler()),'connect_timeout'=>4,'timeout'=>8,'allow_redirects'=>false,'verify'=>true,'curl'=>[CURLOPT_RESOLVE=>[$host.':443:'.$ips[0]]]]);
 $sender=new \Minishlink\WebPush\WebPush(['VAPID'=>['subject'=>'mailto:info@sexogate.com',...$keys]],['TTL'=>3600],$client);
 $report=$sender->sendOneNotification(\Minishlink\WebPush\Subscription::create($subscription),json_encode($payload,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE));
 return $report->getResponse()?->getStatusCode()??0;
}
function sgNotifyTick(string $root,array $catalog,?callable $transport=null):array {
 require_once __DIR__.'/control-store.php';$db=nodenoControlDatabase($root);sgNotifySchema($db);$now=time();$queued=sgNotifyScan($db,$catalog,$now);$sent=0;$failed=0;
 $db->prepare("UPDATE sg_notify_jobs SET status='queued' WHERE status='processing' AND lease_until<?")->execute([$now]);
 $known=array_column($catalog['products']??[],null,'id');$rows=$db->prepare("SELECT j.*,s.encrypted,s.mount,s.expires_at FROM sg_notify_jobs j JOIN sg_notify_subscriptions s ON s.id=j.subscription_id WHERE j.status='queued' AND j.next_at<=? ORDER BY j.created_at LIMIT 5");$rows->execute([$now]);
 foreach($rows->fetchAll(PDO::FETCH_ASSOC)as $job){
  $claim=$db->prepare("UPDATE sg_notify_jobs SET status='processing',lease_until=? WHERE id=? AND status='queued'");$claim->execute([$now+120,$job['id']]);if(!$claim->rowCount())continue;
  if((int)$job['expires_at']<=$now||!isset($known[$job['product_id']])||sgNotifyAvailability($known[$job['product_id']])!==true){$db->prepare("UPDATE sg_notify_jobs SET status='cancelled' WHERE id=?")->execute([$job['id']]);continue;}
  try{$subscription=json_decode(nodenoControlDecrypt($root,$job['encrypted'],'notify:'.$job['subscription_id']),true,16,JSON_THROW_ON_ERROR);$payload=['title'=>'SEXOGATE','body'=>'Takip ettiğiniz bir ürün yeniden stokta. Ayrıntıları güvenli ekrandan inceleyin.','url'=>$job['mount'].'/?product='.rawurlencode($job['product_id']),'tag'=>$job['id']];$code=($transport??'sgNotifySend')($root,$subscription,$payload);}catch(Throwable $e){$code=0;}
  $attempt=(int)$job['attempts']+1;$status=$code>=200&&$code<300?'sent':((in_array($code,[400,401,403,404,410],true)||$attempt>=8)?'failed':'queued');
  if(in_array($code,[404,410],true))$db->prepare('DELETE FROM sg_notify_subscriptions WHERE id=?')->execute([$job['subscription_id']]);
  $db->prepare('UPDATE sg_notify_jobs SET status=?,attempts=?,next_at=?,lease_until=0 WHERE id=?')->execute([$status,$attempt,$now+min(21600,60*(2**$attempt)),$job['id']]);if($status==='sent')$sent++;else $failed++;
 }
 $db->prepare('DELETE FROM sg_notify_jobs WHERE created_at<?')->execute([$now-90*86400]);
 $db->prepare('DELETE FROM sg_notify_subscriptions WHERE expires_at<?')->execute([$now]);
 $db->exec('DELETE FROM sg_notify_watches WHERE owner NOT IN(SELECT owner FROM sg_notify_subscriptions)');
 return ['queued'=>$queued,'sent'=>$sent,'retryOrFailed'=>$failed];
}
function sgNotifyHandle(string $private,string $mount,string $method):void {
 require_once $private.'/account.php';require_once $private.'/control-store.php';$state=nodenoStoreContext($private);$root=$state['storage'];$db=nodenoControlDatabase($root);sgNotifySchema($db);
 try{
  $accounts=nodenoAccountDatabase($root);nodenoAccountSession($root,$accounts);
  $cookie='__Host-sgNotify';$token=$_COOKIE[$cookie]??'';
  if(!is_string($token)||!preg_match('/^[a-f0-9]{64}$/D',$token)){$token=bin2hex(random_bytes(32));setcookie($cookie,$token,['expires'=>time()+90*86400,'path'=>'/','secure'=>true,'httponly'=>true,'samesite'=>'Strict']);}
  $owner=hash('sha256',$token);nodenoAccountRateLimit($accounts,'notifications-ip',120,60);nodenoAccountRateLimit($accounts,'notifications',60,60,$owner);
  if($method==='GET'){
   $read=$db->prepare('SELECT product_id FROM sg_notify_watches WHERE owner=?');$read->execute([$owner]);$subscriptions=$db->prepare('SELECT COUNT(*) FROM sg_notify_subscriptions WHERE owner=? AND expires_at>?');$subscriptions->execute([$owner,time()]);$key=sgNotifyKeys($root);
   nodenoAccountJson(['csrfToken'=>$_SESSION['csrf'],'publicKey'=>$key['publicKey'],'enabled'=>(int)$subscriptions->fetchColumn()>0,'productIds'=>$read->fetchAll(PDO::FETCH_COLUMN),'retentionDays'=>90]);
  }elseif(in_array($method,['POST','PUT','DELETE'],true)){
   $body=nodenoAccountBody();
   if($method==='DELETE'){sgNotifyRevoke($db,$owner);nodenoAccountJson(['enabled'=>false]);}
   else{
    $ids=$body['productIds']??[];if(!is_array($ids))throw new NodenoAccountHttpError(422,'watch_product_invalid');
    nodenoControlTransaction($db,static function()use($db,$body,$owner,$mount,$root,$state,$ids,$method):void{
     if($method==='POST'){
      if(($body['consent']??false)!==true)throw new NodenoAccountHttpError(422,'push_consent_required');
      if(!is_array($body['subscription']??null))throw new NodenoAccountHttpError(422,'push_subscription_invalid');
      $subscription=sgNotifySubscription($body['subscription']);$hash=hash('sha256',$subscription['endpoint']);$existing=$db->prepare('SELECT owner,id FROM sg_notify_subscriptions WHERE endpoint_hash=?');$existing->execute([$hash]);$row=$existing->fetch(PDO::FETCH_ASSOC);
      if($row&&$row['owner']!==$owner)throw new NodenoAccountHttpError(409,'push_device_owned');
      $id=$row['id']??bin2hex(random_bytes(16));$encrypted=nodenoControlEncrypt($root,json_encode($subscription,JSON_THROW_ON_ERROR),'notify:'.$id);
      $db->prepare('INSERT INTO sg_notify_subscriptions(id,owner,endpoint_hash,encrypted,mount,expires_at)VALUES(?,?,?,?,?,?) ON CONFLICT(id)DO UPDATE SET encrypted=excluded.encrypted,expires_at=excluded.expires_at')->execute([$id,$owner,$hash,$encrypted,$mount,time()+90*86400]);
     }else{$active=$db->prepare('SELECT COUNT(*) FROM sg_notify_subscriptions WHERE owner=? AND expires_at>?');$active->execute([$owner,time()]);if(!(int)$active->fetchColumn())throw new NodenoAccountHttpError(409,'push_not_enabled');}
     sgNotifyWatch($db,$owner,$ids,$state['catalog']);
    });nodenoAccountJson(['enabled'=>true,'productIds'=>$ids]);
   }
  }else nodenoAccountJson(['error'=>'method_not_allowed'],405,['Allow'=>'GET, POST, PUT, DELETE']);
 }catch(NodenoAccountHttpError $error){nodenoAccountJson(['error'=>$error->errorCode],$error->status);}catch(Throwable $error){nodenoAccountJson(['error'=>'notifications_unavailable'],503);}finally{if(session_status()===PHP_SESSION_ACTIVE)session_write_close();}
}
