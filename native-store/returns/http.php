<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/returns/http.php
 * Açıklama   : Müşteri kayıt sahipliği, süreli erişim, yönetici rolü ve iade API sınırlarını uygular.
 */
declare(strict_types=1);
require_once __DIR__.'/sg-returns-core.php';require_once __DIR__.'/sg-returns-jobs.php';
function sgReturnGrant(string $root,array $order,?array $user,int $now):string{
 $data=['orderId'=>$order['id'],'expiresAt'=>$now+1800,'userId'=>$user['id']??null,'session'=>hash_hmac('sha256',session_id(),nodenoControlKey($root))];$value=rtrim(strtr(base64_encode(sgReturnJson($data)),'+/','-_'),'=');return $value.'.'.hash_hmac('sha256','return-grant:'.$value,nodenoControlKey($root));
}
function sgReturnGrantOrder(PDO $db,string $root,?array $user,string $proof,int $now):array{
 if(strlen($proof)>1200||!preg_match('/^([A-Za-z0-9_-]+)\.([a-f0-9]{64})$/D',$proof,$m)||!hash_equals(hash_hmac('sha256','return-grant:'.$m[1],nodenoControlKey($root)),$m[2]))sgReturnError(403,'return_access_denied');
 $data=json_decode(base64_decode(strtr($m[1],'-_','+/'),true)?:'null',true);if(!is_array($data)||!is_int($data['expiresAt']??null)||$data['expiresAt']<$now||($data['userId']??null)!==($user['id']??null)||!hash_equals($data['session']??'',hash_hmac('sha256',session_id(),nodenoControlKey($root))))sgReturnError(403,'return_access_expired');
 $order=nodenoPaymentOrder($db,(string)($data['orderId']??''));if(!$order)sgReturnError(404,'return_order_not_found');if($user&&$order['user_id']!==$user['id'])sgReturnError(403,'return_access_denied');return $order;
}
function sgReturnCustomerLine(array $line):array{
 $p=$line['snapshot']??$line;$name=$p['name']??$p['code']??'';$selection=$p['selectionSnapshot']['summary']??'';
 return ['name'=>$name,'code'=>$p['code']??'','quantity'=>(int)($line['quantity']??$p['quantity']??0),'selection'=>$selection];
}
function sgReturnView(PDO $db,string $root,array $case,bool $financial,bool $customer=false):array{
 $out=['code'=>$case['code'],'orderId'=>$case['order_id'],'reason'=>$case['reason'],'status'=>$case['status'],'version'=>(int)$case['version'],'requestedAt'=>(int)$case['requested_at'],'refundState'=>$case['refund_state'],'fiscalState'=>$case['fiscal_state']];
 if($financial||$customer)$out+=['grossMinor'=>(int)$case['gross_minor'],'currency'=>$case['currency']];if($financial)$out+=['netMinor'=>(int)$case['net_minor'],'vatMinor'=>(int)$case['vat_minor'],'jobs'=>[]];
 $shipping=json_decode($case['shipping_json'],true);$out['shipping']=array_intersect_key($shipping,array_flip(['carrier','handoffCode','expiresAt','trackingNumber','handedOverAt']));$out['qc']=array_intersect_key(json_decode($case['qc_json'],true),array_flip(['receivedAt','disposition','inspectionComplete','stockIncreased']));$out['reviewFlags']=json_decode($case['review_flags_json'],true);
 $q=$db->prepare('SELECT * FROM sg_return_lines WHERE case_code=?ORDER BY line_key');$q->execute([$case['code']]);$out['lines']=array_map(static function($r){return sgReturnCustomerLine(array_replace(json_decode($r['snapshot_json'],true),['quantity'=>(int)$r['quantity']]));},$q->fetchAll());
 $q=$db->prepare('SELECT kind,details_json,created_at FROM sg_return_events WHERE case_code=?ORDER BY id');$q->execute([$case['code']]);$out['events']=array_map(static function($r){$d=json_decode($r['details_json'],true);return ['kind'=>$r['kind'],'at'=>(int)$r['created_at'],'reason'=>$d['decisionReason']??null];},$q->fetchAll());
 if(!$customer){$out['note']=nodenoControlDecrypt($root,$case['note_envelope'],'return:'.$case['code']);if($financial){$q=$db->prepare('SELECT id,kind,status,attempts,error_code,next_at FROM sg_return_jobs WHERE case_code=?');$q->execute([$case['code']]);$out['jobs']=$q->fetchAll();}}
 return $out;
}
function sgReturnOrderView(PDO $db,string $root,array $order,?array $user,int $now):array{
 $lines=sgReturnOrderLines($order);$result=[];
 foreach($lines as $key=>$line){$q=$db->prepare("SELECT COALESCE(SUM(l.quantity),0)FROM sg_return_lines l JOIN sg_return_cases c ON c.code=l.case_code WHERE c.order_id=?AND l.line_key=?AND c.status NOT IN('rejected','cancelled')");$q->execute([$order['id'],$key]);$result[]=['key'=>$key,'availableQuantity'=>max(0,$line['quantity']-(int)$q->fetchColumn()),'grossMinor'=>$line['totalMinor']]+sgReturnCustomerLine($line);}
 $q=$db->prepare('SELECT * FROM sg_return_cases WHERE order_id=?ORDER BY requested_at DESC');$q->execute([$order['id']]);return ['id'=>$order['id'],'currency'=>$order['currency'],'lines'=>$result,'cases'=>array_map(static fn($c)=>sgReturnView($db,$root,$c,false,true),$q->fetchAll()),'proof'=>sgReturnGrant($root,$order,$user,$now),'proofExpiresAt'=>$now+1800];
}
function sgReturnPublicHandle(string $private,string $path,string $method):void{
 try{
  require_once $private.'/control-http.php';require_once $private.'/payment-store.php';$runtime=nodenoRuntimeConfiguration();$root=nodenoAccountStorage($runtime['storageRoot']);$db=nodenoControlDatabase($root);sgReturnSchema($db);$user=nodenoAccountSession($root,$db);nodenoControlRate($db,$root,'returns-public',$_SERVER['REMOTE_ADDR']??'',180,600);$route=substr($path,strlen('/api/returns'));$now=time();
  if($route===''&&$method==='GET'){
   $orders=[];if($user){$q=$db->prepare('SELECT id,status,currency,total_minor,created_at FROM payment_orders WHERE user_id=?AND paid_at IS NOT NULL ORDER BY created_at DESC LIMIT 100');$q->execute([$user['id']]);$orders=$q->fetchAll();}
   $result=['csrfToken'=>$_SESSION['csrf'],'signedIn'=>$user!==null,'orders'=>$orders];
  }elseif($route==='/order'&&$method==='POST'){
   $body=nodenoAccountBody();if(array_diff(array_keys($body),['orderId','lookupToken']))sgReturnError(422,'return_request_invalid');$order=null;
   if(is_string($body['orderId']??null)&&$user){$order=nodenoPaymentOrder($db,$body['orderId']);if(!$order||$order['user_id']!==$user['id'])sgReturnError(404,'return_order_not_found');}
   elseif(is_string($body['lookupToken']??null)){$order=nodenoPaymentLookup($db,$body['lookupToken']);if($user&&$order&&$order['user_id']!==$user['id'])sgReturnError(403,'return_access_denied');}
   if(!$order||$order['paid_at']===null)sgReturnError(404,'return_order_not_found');$result=sgReturnOrderView($db,$root,$order,$user,$now);
  }elseif($route==='/quote'&&$method==='POST'){
   $body=nodenoAccountBody();if(array_diff(array_keys($body),['lines'])||!is_array($body['lines']??null)||!$body['lines']||count($body['lines'])>30)sgReturnError(422,'return_lines_invalid');$order=sgReturnGrantOrder($db,$root,$user,(string)($_SERVER['HTTP_X_RETURN_PROOF']??''),$now);$lines=$body['lines'];ksort($lines);$plan=sgReturnPlan($db,$order,$lines);$result=['grossMinor'=>$plan['grossMinor'],'currency'=>$order['currency'],'quoteHash'=>$plan['quoteHash']];
  }elseif($route==='/cases'&&$method==='POST'){
   $body=nodenoAccountBody();if(!preg_match('/^[a-f0-9]{64}$/D',$body['quoteHash']??''))sgReturnError(422,'return_preview_required');$order=sgReturnGrantOrder($db,$root,$user,(string)($_SERVER['HTTP_X_RETURN_PROOF']??''),$now);$policy=nodenoControlSetting($db,'returns:policy',['version'=>'draft-20261116','approved'=>false,'country'=>'TR','customerPacks'=>true,'customerHandsOver'=>true]);$actor=hash_hmac('sha256','return-customer:'.($user['id']??session_id()),nodenoControlKey($root));$result=sgReturnCreate($db,$root,$order,$actor,$body,$policy,$now);$result['case']=sgReturnView($db,$root,sgReturnCase($db,$result['code']),false,true);
  }elseif(preg_match('~^/cases/(SGR-[0-9]{6}-[A-F0-9]{12})/cancel$~D',$route,$m)&&$method==='POST'){
   $body=nodenoAccountBody();if($body!==[])sgReturnError(422,'return_request_invalid');$order=sgReturnGrantOrder($db,$root,$user,(string)($_SERVER['HTTP_X_RETURN_PROOF']??''),$now);$c=sgReturnCase($db,$m[1]);if($c['order_id']!==$order['id'])sgReturnError(404,'return_not_found');if(!in_array($c['status'],['requested','awaiting_dispatch','cancelled'],true))sgReturnError(409,'return_transition_invalid');if($c['status']!=='cancelled')$c=sgReturnCommand($db,$c['code'],'customer',['version'=>(int)$c['version'],'action'=>'cancel','decisionReason'=>'Müşteri talebi'],time());$result=sgReturnView($db,$root,$c,false,true);
  }elseif(preg_match('~^/cases/(SGR-[0-9]{6}-[A-F0-9]{12})$~D',$route,$m)&&$method==='GET'){
   $order=sgReturnGrantOrder($db,$root,$user,(string)($_SERVER['HTTP_X_RETURN_PROOF']??''),$now);$c=sgReturnCase($db,$m[1]);if($c['order_id']!==$order['id'])sgReturnError(404,'return_not_found');$result=sgReturnView($db,$root,$c,false,true);
  }else sgReturnError(405,'method_not_allowed');
  nodenoAccountJson($result);
 }catch(NodenoControlHttpError|NodenoAccountHttpError $e){nodenoAccountJson(['error'=>$e->errorCode],$e->status);}catch(Throwable $e){nodenoAccountJson(['error'=>'return_service_unavailable'],503);}finally{if(session_status()===PHP_SESSION_ACTIVE)session_write_close();}
}
function sgReturnCanFinance(array $ctx):bool{return in_array('*',$ctx['permissions'],true)||in_array('returns.finance',$ctx['permissions'],true);}
function sgReturnAdmin(array $ctx,string $route,string $method,array $body):?array{
 if($route!=='return-center'&&!str_starts_with($route,'return-center/'))return null;$db=$ctx['db'];$root=$ctx['root'];sgReturnSchema($db);$financial=sgReturnCanFinance($ctx);$permission=$financial?'returns.finance':'operations.read';nodenoControlRequire($ctx,$permission);$now=time();
 if($route==='return-center'&&$method==='GET'){
  $page=max(1,min(100000,(int)($_GET['page']??1)));$query=sgReturnText($_GET['q']??'',100);$state=sgReturnText($_GET['status']??'',30);$where='1=1';$args=[];
  if($query!==''){$where.=' AND(code LIKE ?OR order_id LIKE ?)';$args[]='%'.str_replace(['%','_'],['',''],$query).'%';$args[]=$args[count($args)-1];}if($state!==''){$where.=' AND status=?';$args[]=$state;}
  $q=$db->prepare('SELECT COUNT(*)FROM sg_return_cases WHERE '.$where);$q->execute($args);$total=(int)$q->fetchColumn();$q=$db->prepare('SELECT * FROM sg_return_cases WHERE '.$where.' ORDER BY requested_at DESC,code LIMIT 25 OFFSET '.(($page-1)*25));$q->execute($args);return ['data'=>array_map(static fn($c)=>sgReturnView($db,$root,$c,$financial),$q->fetchAll()),'page'=>$page,'pageSize'=>25,'total'=>$total,'financial'=>$financial];
 }
 if($route==='return-center/report'&&$method==='GET'){nodenoControlRequire($ctx,'returns.finance');return sgReturnFinancialReport($db,($_GET['mode']??'live')!=='test');}
 if($route==='return-center/settings'){
  if($method==='GET')return ['policy'=>nodenoControlSetting($db,'returns:policy',['approved'=>false,'country'=>'TR','version'=>'draft-20261116']),'refundProviderReady'=>false,'invoiceProviderReady'=>false,'carrierProviderReady'=>false];
  $actor=nodenoControlRequire($ctx,'settings.write',true);if($method!=='PUT'||array_diff(array_keys($body),['version','country','approved','legalReviewRef','returnAddress','carrierName']))sgReturnError(422,'return_policy_invalid');$policy=['version'=>sgReturnText($body['version']??'',80),'country'=>sgReturnText($body['country']??'',2),'approved'=>($body['approved']??false)===true,'legalReviewRef'=>sgReturnText($body['legalReviewRef']??'',200),'returnAddress'=>sgReturnText($body['returnAddress']??'',1200),'carrierName'=>sgReturnText($body['carrierName']??'',120),'customerPacks'=>true,'customerHandsOver'=>true];if($policy['country']!=='TR'||($policy['approved']&&($policy['legalReviewRef']===''||$policy['returnAddress']===''||$policy['carrierName']==='')))sgReturnError(422,'return_policy_review_required');nodenoControlSetSetting($db,'returns:policy',$policy);nodenoControlAudit($db,$root,$actor['id'],'configure','returns','policy',['version'=>$policy['version'],'approved'=>$policy['approved']]);return ['policy'=>$policy];
 }
 if(preg_match('~^return-center/(SGR-[0-9]{6}-[A-F0-9]{12})(?:/(command|fiscal|expense))?$~D',$route,$m)){
  $case=sgReturnCase($db,$m[1]);$action=$m[2]??'';if($method==='GET'&&$action==='')return sgReturnView($db,$root,$case,$financial);
  if($method!=='POST')sgReturnError(405,'method_not_allowed');$needsFinance=$action!=='command'||($body['action']??'')==='approve';$actor=nodenoControlRequire($ctx,$needsFinance?'returns.finance':'operations.write',true);
  if($action==='command')sgReturnCommand($db,$case['code'],$actor['id'],$body,$now);
  elseif($action==='fiscal'){if(($body['verifiedByOperator']??false)!==true)sgReturnError(422,'fiscal_confirmation_required');sgReturnFiscalConfirm($db,$case['code'],$actor['id'],$body,$now);}
  elseif($action==='expense')sgReturnExpense($db,nodenoPaymentOrder($db,$case['order_id']),$case,$actor['id'],$body,$now);
  else sgReturnError(404,'return_action_unknown');
  nodenoControlAudit($db,$root,$actor['id'],$action,'returns',$case['code'],['action'=>$body['action']??$action]);return sgReturnView($db,$root,sgReturnCase($db,$case['code']),$financial);
 }
 sgReturnError(404,'not_found');
}
