<?php
declare(strict_types=1);
require_once __DIR__.'/localization.php';
require_once __DIR__.'/payment-admin.php';
require_once __DIR__.'/payment-documents.php';

function nodenoPaymentAllowTest():bool {return PHP_SAPI==='cli-server'&&in_array($_SERVER['REMOTE_ADDR']??'',['127.0.0.1','::1'],true);}
function nodenoPaymentWebhook(PDO $db,string $root,array $cfg,?callable $provider=null):array {
 $raw=file_get_contents('php://input',false,null,0,1000001);if(!is_string($raw)||strlen($raw)>1000000)throw new NodenoControlHttpError(413,'body_too_large');
 try{$event=json_decode($raw,true,64,JSON_THROW_ON_ERROR);if(!is_array($event)||!is_string($event['id']??null)||!preg_match('/^evt_[A-Za-z0-9_]+$/D',$event['id']))throw new InvalidArgumentException('payment_event_invalid');}catch(Throwable $e){throw new NodenoControlHttpError(400,'payment_signature_invalid');}
 $matched=null;$active=false;$candidates=[$cfg,...array_values(array_filter($cfg['retiredWebhooks']??[],static fn($entry)=>$entry['expiresAt']>time()))];
 foreach($candidates as $index=>$candidate){try{nodenoPaymentVerifySignature($raw,(string)($_SERVER['HTTP_STRIPE_SIGNATURE']??''),$candidate['credentials']['webhookSecret']??'',time());$matched=$candidate;$active=$index===0;break;}catch(InvalidArgumentException $e){}}
 if($matched===null)throw new NodenoControlHttpError(400,'payment_signature_invalid');
 if(($event['livemode']??null)!==($matched['mode']==='live')||($event['account']??$matched['accountId'])!==$matched['accountId'])throw new NodenoControlHttpError(400,'payment_account_or_mode_mismatch');
 if(empty($matched['webhookVerifiedAt'])){
  // Direct account events omit event.account. Retrieve the first signed event using this account's own API credential before trusting that binding.
  $remote=($provider??'nodenoPaymentStripe')($matched['credentials'],'GET','/v1/events/'.$event['id']);
  if(($remote['id']??null)!==$event['id']||($remote['livemode']??null)!==$event['livemode']||($remote['type']??null)!==($event['type']??null)||($remote['data']['object']??null)!=($event['data']['object']??null))throw new NodenoControlHttpError(400,'payment_event_account_mismatch');
  if($active)nodenoControlTransaction($db,static function()use($db,$cfg):void{$stored=nodenoControlSetting($db,'payment:stripe',[]);if(($stored['version']??0)!==($cfg['version']??0))throw new NodenoControlHttpError(503,'payment_configuration_changed');$stored['webhookVerifiedAt']=time();$stored['version']=($stored['version']??0)+1;nodenoControlSetSetting($db,'payment:stripe',$stored);});
 }
 $event['account']=$event['account']??$matched['accountId'];return nodenoPaymentApply($db,$event);
}
function nodenoPaymentsHandle(string $path,string $method,array $catalog,string $root,?callable $provider=null):void {
 try{
  $root=nodenoAccountStorage($root);$db=nodenoControlDatabase($root);nodenoPaymentSchema($db);$cfg=nodenoPaymentConfiguration($db,$root);$route=substr($path,14);
  if($route==='stripe/webhook'){
   if($method!=='POST')throw new NodenoControlHttpError(405,'method_not_allowed');$result=nodenoPaymentWebhook($db,$root,$cfg,$provider);
  }else{
   $user=nodenoAccountSession($root,$db);$ready=nodenoPaymentReady($cfg,nodenoPaymentAllowTest());
   nodenoControlRate($db,$root,'payment-public',$_SERVER['REMOTE_ADDR']??'unknown',180,600);
   if($route==='status'&&$method==='GET')$result=['enabled'=>$ready,'test'=>($cfg['mode']??'test')==='test','currency'=>'TRY','countries'=>['TR'],'csrfToken'=>$_SESSION['csrf'],'seller'=>$ready?$cfg['seller']:null,'termsRevision'=>$ready?nodenoPaymentTermsRevision($cfg['seller']):null,'freight'=>['kind'=>'included','includedInCharge'=>true,'feeMinor'=>0]];
   elseif(preg_match('~^order/([a-f0-9]{64})/documents$~D',$route,$matches)&&$method==='GET'){
    $order=nodenoPaymentLookup($db,$matches[1]);if(!$order)throw new NodenoControlHttpError(404,'not_found');
    $actor=($user['id']??'guest').':'.($_SESSION['paymentActor']??'');
    $actorHash=hash_hmac('sha256',$actor,nodenoControlKey($root));if(($order['user_id']??null)!==($user['id']??null)||$user===null){if(!hash_equals($order['actor_hash'],$actorHash))throw new NodenoControlHttpError(403,'payment_document_access_denied');}
    nodenoPaymentEnsureDocuments($db,$root,$order);$doc=nodenoPaymentDocument($db,$root,$order,$user['id']??null,$actor);$db->prepare('UPDATE payment_documents SET served_at=COALESCE(served_at,?) WHERE order_id=?')->execute([time(),$order['id']]);
    header('Content-Type: text/html; charset=utf-8');header('Cache-Control: private, no-store');header('X-Content-Type-Options: nosniff');header('Referrer-Policy: no-referrer');header('X-Robots-Tag: noindex, nofollow');header('Content-Security-Policy: default-src \'none\'; style-src \'unsafe-inline\'; sandbox');header('Content-Disposition: attachment; filename="NODENO-'.$order['id'].'.html"');echo $doc['html'];return;
   }
   elseif(preg_match('~^order/([a-f0-9]{64})$~D',$route,$matches)&&$method==='GET'){$order=nodenoPaymentLookup($db,$matches[1]);if(!$order)throw new NodenoControlHttpError(404,'not_found');$result=nodenoPaymentPublic($order);}
   elseif(in_array($route,['quote','checkout'],true)&&$method==='POST'){
    $body=nodenoAccountBody();if(array_diff(array_keys($body),$route==='quote'?['items','country']:['items','country','contact','locale','quoteRevision','termsVersion','termsRevision','acceptTerms','acceptFreight','idempotencyKey','documentFlowVersion']))throw new NodenoControlHttpError(422,'payment_request_invalid');
    if(!is_array($body['items']??null)||!is_string($body['country']??null))throw new NodenoControlHttpError(422,'payment_request_invalid');
    $quote=nodenoPaymentQuote($catalog,$body['items'],$body['country']);
    if($route==='quote')$result=$quote;
    else{
     if(!$ready)throw new NodenoControlHttpError(409,'payment_not_configured');
     if(($body['documentFlowVersion']??null)!==2)throw new NodenoControlHttpError(409,'payment_documents_refresh_required');
     if(($body['acceptTerms']??false)!==true||($body['termsVersion']??null)!==$cfg['seller']['termsVersion']||($body['termsRevision']??null)!==nodenoPaymentTermsRevision($cfg['seller']))throw new NodenoControlHttpError(409,'payment_consent_required');
     if(($body['quoteRevision']??null)!==$quote['revision'])throw new NodenoControlHttpError(409,'payment_price_changed');
     if(!is_array($body['contact']??null)||!in_array($body['locale']??'',NODENO_STORE_LOCALES,true)||!is_string($body['idempotencyKey']??null))throw new NodenoControlHttpError(422,'payment_request_invalid');
     $contact=nodenoPaymentContact($body['contact']);$locale=$body['locale'];
     nodenoControlRate($db,$root,'payment-create',$_SERVER['REMOTE_ADDR']??'unknown',15,3600);
     $_SESSION['paymentActor']??=bin2hex(random_bytes(32));$actor=($user['id']??'guest').':'.$_SESSION['paymentActor'];
     $order=nodenoPaymentBegin($db,$root,$actor,$body['idempotencyKey'],$quote,$contact,$locale,$cfg,$user['id']??null);
     nodenoPaymentEnsureDocuments($db,$root,$order);
     // No SQLite transaction or PHP session lock is held during network I/O.
     session_write_close();
     if(in_array($order['status'],['paid','partially_refunded','refunded'],true))$result=nodenoPaymentPublic($order)+['returnToken'=>$order['returnToken']];
     else{
      if(!$order['checkout_url']){
       if(time()>(int)$order['created_at']+1800)throw new NodenoControlHttpError(409,'payment_session_expired');
       $host=strtolower($_SERVER['HTTP_HOST']??'');$local=nodenoPaymentAllowTest()&&preg_match('/^127\.0\.0\.1:[0-9]+$/D',$host);
       if(!$local&&!in_array($host,['nodenohome.com','www.nodenohome.com','nodenohome.com.tr','www.nodenohome.com.tr'],true))throw new NodenoControlHttpError(403,'origin_rejected');
       $origin=($local?'http':'https').'://'.$host;$private=nodenoPaymentPrivate($root,$order);
       $session=nodenoPaymentStripe($cfg['credentials'],'POST','/v1/checkout/sessions',nodenoPaymentStripeForm($order,$private,$origin),'nodeno_'.$order['id']);nodenoPaymentBind($db,$order['id'],$session);$order=nodenoPaymentOrder($db,$order['id'])+['returnToken'=>$private['returnToken']];
      }
      $result=['id'=>$order['id'],'checkoutUrl'=>$order['checkout_url'],'returnToken'=>$order['returnToken'],'documentUrl'=>'/api/payments/order/'.$order['returnToken'].'/documents','test'=>(int)$order['live']===0];
     }
    }
   }else throw new NodenoControlHttpError(404,'not_found');
  }
  nodenoAccountJson($result);
 }catch(InvalidArgumentException $e){nodenoAccountJson(['error'=>$e->getMessage()],422);}catch(NodenoControlHttpError|NodenoAccountHttpError $e){nodenoAccountJson(['error'=>$e->errorCode],$e->status,$e->headers);}catch(Throwable $e){$reference=bin2hex(random_bytes(6));error_log('NODENO payment '.$reference.' '.get_class($e));nodenoAccountJson(['error'=>'payment_service_unavailable','reference'=>$reference],503);}finally{if(session_status()===PHP_SESSION_ACTIVE)session_write_close();}
}
