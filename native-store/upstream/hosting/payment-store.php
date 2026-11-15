<?php
declare(strict_types=1);
require_once __DIR__.'/control-store.php';
require_once __DIR__.'/payment-core.php';

function nodenoPaymentSchema(PDO $db):void {
 $db->exec("CREATE TABLE IF NOT EXISTS payment_orders (
 id TEXT PRIMARY KEY, user_id TEXT REFERENCES users(id) ON DELETE SET NULL, actor_hash TEXT NOT NULL, command_hash TEXT NOT NULL UNIQUE, request_hash TEXT NOT NULL,
 lookup_hash TEXT NOT NULL UNIQUE, contact_envelope TEXT NOT NULL, snapshot_json TEXT NOT NULL, seller_json TEXT NOT NULL,
 locale TEXT NOT NULL, stripe_account_id TEXT NOT NULL, live INTEGER NOT NULL, currency TEXT NOT NULL, total_minor INTEGER NOT NULL,
 status TEXT NOT NULL, stripe_session_id TEXT UNIQUE, checkout_url TEXT, payment_intent TEXT UNIQUE,
 created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL, paid_at INTEGER);
 CREATE INDEX IF NOT EXISTS payment_orders_actor ON payment_orders(actor_hash,created_at);
 CREATE TABLE IF NOT EXISTS payment_events (id TEXT PRIMARY KEY,order_id TEXT NOT NULL REFERENCES payment_orders(id),type TEXT NOT NULL,result TEXT NOT NULL,received_at INTEGER NOT NULL);");
 $db->exec("CREATE TABLE IF NOT EXISTS payment_refunds(order_id TEXT PRIMARY KEY REFERENCES payment_orders(id),amount_minor INTEGER NOT NULL,pending_minor INTEGER NOT NULL,refund_status TEXT NOT NULL,updated_at INTEGER NOT NULL);
 CREATE TABLE IF NOT EXISTS payment_refund_items(id TEXT PRIMARY KEY,payment_intent TEXT NOT NULL,account_id TEXT NOT NULL,live INTEGER NOT NULL,charge_id TEXT NOT NULL,currency TEXT NOT NULL,amount_minor INTEGER NOT NULL,status TEXT NOT NULL,event_created INTEGER NOT NULL,last_event_id TEXT NOT NULL);
 CREATE INDEX IF NOT EXISTS payment_refund_intent ON payment_refund_items(payment_intent)");
}
function nodenoPaymentOrder(PDO $db,string $id):?array {$s=$db->prepare('SELECT o.*,COALESCE(r.amount_minor,0) AS refunded_minor,COALESCE(r.pending_minor,0) AS refund_pending_minor,r.refund_status FROM payment_orders o LEFT JOIN payment_refunds r ON r.order_id=o.id WHERE o.id=?');$s->execute([$id]);return $s->fetch()?:null;}
function nodenoPaymentLookup(PDO $db,string $token):?array {
 if(!preg_match('/^[a-f0-9]{64}$/D',$token))return null;$s=$db->prepare('SELECT o.*,COALESCE(r.amount_minor,0) AS refunded_minor,COALESCE(r.pending_minor,0) AS refund_pending_minor,r.refund_status FROM payment_orders o LEFT JOIN payment_refunds r ON r.order_id=o.id WHERE o.lookup_hash=?');$s->execute([hash('sha256',$token)]);return $s->fetch()?:null;
}
function nodenoPaymentPrivate(string $root,array $row):array {return json_decode(nodenoControlDecrypt($root,$row['contact_envelope'],'payment:'.$row['id']),true,32,JSON_THROW_ON_ERROR);}
function nodenoPaymentBegin(PDO $db,string $root,string $actor,string $key,array $quote,array $contact,string $locale,array $config,?string $userId=null):array {
 if(!preg_match('/^[A-Za-z0-9_-]{16,100}$/D',$key))throw new NodenoControlHttpError(422,'payment_idempotency_required');
 $actorHash=hash_hmac('sha256',$actor,nodenoControlKey($root));$command=hash('sha256',$actorHash.':'.$key);
 $request=hash('sha256',json_encode([$quote,$contact,$locale,$config['accountId'],$config['mode'],$config['seller']],JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE));
 return nodenoControlTransaction($db,static function()use($db,$root,$command,$request,$actorHash,$quote,$contact,$locale,$config,$userId):array{
  if(isset($config['version'])){$current=nodenoControlSetting($db,'payment:stripe',[]);if(($current['version']??0)!==$config['version'])throw new NodenoControlHttpError(409,'payment_configuration_changed');}
  $s=$db->prepare('SELECT * FROM payment_orders WHERE command_hash=?');$s->execute([$command]);$old=$s->fetch();
  if($old){if(!hash_equals($old['request_hash'],$request))throw new NodenoControlHttpError(409,'payment_request_changed');if(time()-(int)$old['created_at']>82800||in_array($old['status'],['expired','failed','review'],true))throw new NodenoControlHttpError(409,'payment_session_expired');return $old+['returnToken'=>nodenoPaymentPrivate($root,$old)['returnToken']];}
  $id=nodenoControlId('pay_');$token=bin2hex(random_bytes(32));$now=time();$envelope=nodenoControlEncrypt($root,json_encode(['contact'=>$contact,'returnToken'=>$token],JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE),'payment:'.$id);
  $db->prepare('INSERT INTO payment_orders(id,actor_hash,command_hash,request_hash,lookup_hash,contact_envelope,snapshot_json,seller_json,locale,stripe_account_id,live,currency,total_minor,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)')->execute([$id,$actorHash,$command,$request,hash('sha256',$token),$envelope,json_encode($quote,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE),json_encode($config['seller'],JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE),$locale,$config['accountId'],(int)($config['mode']==='live'),$quote['currency'],$quote['totalMinor'],'creating',$now,$now]);
  if($userId!==null)$db->prepare('UPDATE payment_orders SET user_id=? WHERE id=?')->execute([$userId,$id]);
  return nodenoPaymentOrder($db,$id)+['returnToken'=>$token];
 });
}
function nodenoPaymentSessionMatches(array $order,array $session):bool {
 return is_string($session['id']??null)&&preg_match('/^cs_[a-zA-Z0-9_]+$/D',$session['id'])&&($session['client_reference_id']??'')===$order['id']&&($session['metadata']['nodeno_order_id']??'')===$order['id']&&($session['amount_total']??null)===(int)$order['total_minor']&&strtoupper($session['currency']??'')===$order['currency']&&is_bool($session['livemode']??null)&&$session['livemode']===(bool)$order['live'];
}
function nodenoPaymentBind(PDO $db,string $id,array $session):void {
 nodenoControlTransaction($db,static function()use($db,$id,$session):void{
  $order=nodenoPaymentOrder($db,$id);if(!$order||!nodenoPaymentSessionMatches($order,$session)||($order['stripe_session_id']!==null&&$order['stripe_session_id']!==$session['id']))throw new NodenoControlHttpError(503,'payment_provider_mismatch');
  $url=$session['url']??null;if(!is_string($url)||!str_starts_with($url,'https://checkout.stripe.com/')||strlen($url)>4096||preg_match('/[\x00-\x20]/',$url))throw new NodenoControlHttpError(503,'payment_provider_mismatch');
  $db->prepare("UPDATE payment_orders SET stripe_session_id=?,checkout_url=?,status=CASE WHEN status='creating' THEN 'pending' ELSE status END,updated_at=? WHERE id=?")->execute([$session['id'],$url,time(),$id]);
 });
}
function nodenoPaymentSyncRefunds(PDO $db,string $id):void {
 $order=nodenoPaymentOrder($db,$id);if(!$order||$order['payment_intent']===null||$order['paid_at']===null)return;
 $s=$db->prepare("SELECT COALESCE(SUM(CASE WHEN status='succeeded' THEN amount_minor ELSE 0 END),0) AS settled,COALESCE(SUM(CASE WHEN status IN ('pending','requires_action') THEN amount_minor ELSE 0 END),0) AS pending,COALESCE(SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END),0) AS failed FROM payment_refund_items WHERE payment_intent=? AND account_id=? AND live=? AND currency=?");$s->execute([$order['payment_intent'],$order['stripe_account_id'],(int)$order['live'],$order['currency']]);$totals=$s->fetch();$settled=(int)$totals['settled'];$pending=(int)$totals['pending'];$amount=(int)$order['total_minor'];
 if($settled+$pending>$amount)throw new NodenoControlHttpError(503,'payment_refund_totals_invalid');
 $state=$pending>0?'pending':($settled>0?'succeeded':((int)$totals['failed']>0?'failed':'none'));$status=$settled===$amount?'refunded':($settled>0?'partially_refunded':'paid');
 $db->prepare('INSERT INTO payment_refunds(order_id,amount_minor,pending_minor,refund_status,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(order_id) DO UPDATE SET amount_minor=excluded.amount_minor,pending_minor=excluded.pending_minor,refund_status=excluded.refund_status,updated_at=excluded.updated_at')->execute([$id,$settled,$pending,$state,time()]);
 $db->prepare('UPDATE payment_orders SET status=?,updated_at=? WHERE id=?')->execute([$status,time(),$id]);
}
function nodenoPaymentRefundApply(PDO $db,array $event):array {
 $refund=$event['data']['object']??[];$intent=$refund['payment_intent']??'';$amount=$refund['amount']??null;$status=$refund['status']??'';
 $valid=($refund['object']??'')==='refund'&&is_string($refund['id']??null)&&preg_match('/^re_[A-Za-z0-9_]+$/D',$refund['id'])&&is_string($intent)&&preg_match('/^pi_[A-Za-z0-9_]+$/D',$intent)&&is_string($refund['charge']??null)&&preg_match('/^ch_[A-Za-z0-9_]+$/D',$refund['charge'])&&is_int($amount)&&$amount>0&&$amount<=99999999&&in_array($status,['pending','requires_action','succeeded','failed','canceled'],true)&&is_bool($event['livemode']??null)&&(!array_key_exists('livemode',$refund)||$refund['livemode']===$event['livemode'])&&is_string($event['account']??null)&&preg_match('/^acct_[A-Za-z0-9_]+$/D',$event['account'])&&is_string($refund['currency']??null)&&preg_match('/^[a-zA-Z]{3}$/D',$refund['currency']);
 if(!$valid||(($event['type']??'')==='refund.failed'&&$status!=='failed'))return ['received'=>true,'ignored'=>true];
 $currency=strtoupper($refund['currency']);$s=$db->prepare('SELECT id FROM payment_orders WHERE payment_intent=?');$s->execute([$intent]);$id=$s->fetchColumn();$order=$id===false?null:nodenoPaymentOrder($db,$id);
 if($order&&(($event['account']??'')!==$order['stripe_account_id']||$event['livemode']!==(bool)$order['live']||$currency!==$order['currency']||$amount>(int)$order['total_minor']))return ['received'=>true,'ignored'=>true];
 $s=$db->prepare('SELECT * FROM payment_refund_items WHERE id=?');$s->execute([$refund['id']]);$old=$s->fetch();$created=is_int($event['created']??null)?$event['created']:0;
 if($old){
  if($old['last_event_id']===$event['id'])return ['received'=>true,'duplicate'=>true];
  if($old['payment_intent']!==$intent||$old['account_id']!==$event['account']||(bool)$old['live']!==$event['livemode']||$old['currency']!==$currency||(int)$old['amount_minor']!==$amount||$old['charge_id']!==$refund['charge'])return ['received'=>true,'ignored'=>true];
  if($created<(int)$old['event_created']||$event['type']==='refund.created'||in_array($old['status'],['failed','canceled'],true)||($old['status']==='succeeded'&&in_array($status,['pending','requires_action'],true)))return ['received'=>true,'ignored'=>true];
 }
 $db->prepare('INSERT INTO payment_refund_items(id,payment_intent,account_id,live,charge_id,currency,amount_minor,status,event_created,last_event_id) VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET status=excluded.status,event_created=excluded.event_created,last_event_id=excluded.last_event_id')->execute([$refund['id'],$intent,$event['account'],(int)$event['livemode'],$refund['charge'],$currency,$amount,$status,$created,$event['id']]);
 if($order){nodenoPaymentSyncRefunds($db,$id);$db->prepare('INSERT INTO payment_events(id,order_id,type,result,received_at) VALUES(?,?,?,?,?)')->execute([$event['id'],$id,$event['type'],'refund_'.$status,time()]);}
 return ['received'=>true,'duplicate'=>false,'refundRecorded'=>true,'refundApplied'=>$order!==null];
}
function nodenoPaymentApply(PDO $db,array $event):array {
 if(!is_string($event['id']??null)||!preg_match('/^evt_[a-zA-Z0-9_]+$/D',$event['id']))throw new InvalidArgumentException('payment_event_invalid');
 return nodenoControlTransaction($db,static function()use($db,$event):array{
  $s=$db->prepare('SELECT id FROM payment_events WHERE id=?');$s->execute([$event['id']]);if($s->fetchColumn())return ['received'=>true,'duplicate'=>true];
  if(in_array($event['type']??'',['refund.created','refund.updated','refund.failed'],true))return nodenoPaymentRefundApply($db,$event);
  $session=$event['data']['object']??[];$id=$session['metadata']['nodeno_order_id']??'';if(!is_string($id))return ['received'=>true,'ignored'=>true];$order=nodenoPaymentOrder($db,$id);if(!$order)return ['received'=>true,'ignored'=>true];
  // A signed event can arrive before the create request returns. Bind only after matching its immutable amount/reference/mode/account.
  if($order['stripe_session_id']===null&&($event['account']??'')===$order['stripe_account_id']&&($event['livemode']??null)===(bool)$order['live']&&nodenoPaymentSessionMatches($order,$session)){$db->prepare('UPDATE payment_orders SET stripe_session_id=? WHERE id=?')->execute([$session['id'],$id]);$order['stripe_session_id']=$session['id'];}
  $order['total_minor']=(int)$order['total_minor'];$result=nodenoPaymentEvent($order,$event);$status=$result['status'];
  if($status==='paid')$db->prepare("UPDATE payment_orders SET status=CASE WHEN status IN ('refunded','partially_refunded') THEN status ELSE 'paid' END,payment_intent=?,paid_at=COALESCE(paid_at,?),updated_at=? WHERE id=?")->execute([$result['paymentIntent'],time(),time(),$id]);
  elseif(in_array($status,['expired','failed','mismatch'],true)&&!in_array($order['status'],['paid','partially_refunded','refunded'],true))$db->prepare('UPDATE payment_orders SET status=?,updated_at=? WHERE id=?')->execute([$status==='mismatch'?'review':$status,time(),$id]);
  if($status==='paid')nodenoPaymentSyncRefunds($db,$id);
  $db->prepare('INSERT INTO payment_events(id,order_id,type,result,received_at) VALUES(?,?,?,?,?)')->execute([$event['id'],$id,$event['type'],$status,time()]);return ['received'=>true,'duplicate'=>false];
 });
}
function nodenoPaymentPublic(array $row):array {
 $snapshot=json_decode($row['snapshot_json'],true,64,JSON_THROW_ON_ERROR);
 return ['id'=>$row['id'],'status'=>$row['status'],'test'=>(int)$row['live']===0,'currency'=>$row['currency'],'totalMinor'=>(int)$row['total_minor'],'refundedMinor'=>(int)($row['refunded_minor']??0),'refundPendingMinor'=>(int)($row['refund_pending_minor']??0),'refundStatus'=>$row['refund_status']??'none','netMinor'=>$snapshot['netMinor']??null,'vatMinor'=>$snapshot['vatMinor']??null,'freight'=>$snapshot['freight']??null,'createdAt'=>(int)$row['created_at'],'paidAt'=>$row['paid_at']===null?null:(int)$row['paid_at']];
}
function nodenoPaymentUserOrders(PDO $db,string $userId):array {
 $s=$db->prepare("SELECT o.*,COALESCE(r.amount_minor,0) AS refunded_minor,COALESCE(r.pending_minor,0) AS refund_pending_minor,r.refund_status FROM payment_orders o LEFT JOIN payment_refunds r ON r.order_id=o.id WHERE o.user_id=? AND o.status IN ('paid','partially_refunded','refunded') AND o.live=1 ORDER BY o.created_at DESC LIMIT 300");$s->execute([$userId]);
 return array_map(static function($row){$snapshot=json_decode($row['snapshot_json'],true,64,JSON_THROW_ON_ERROR);return ['id'=>$row['id'],'status'=>$row['status'],'currency'=>$row['currency'],'totalMinor'=>(int)$row['total_minor'],'refundedMinor'=>(int)$row['refunded_minor'],'refundPendingMinor'=>(int)$row['refund_pending_minor'],'refundStatus'=>$row['refund_status']??'none','items'=>$snapshot['lines'],'netMinor'=>$snapshot['netMinor'],'vatMinor'=>$snapshot['vatMinor'],'createdAt'=>(int)$row['created_at'],'shipments'=>[]];},$s->fetchAll());
}
