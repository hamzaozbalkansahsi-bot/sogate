<?php
declare(strict_types=1);
require_once __DIR__.'/control-indexnow.php';

function nodenoControlBody():array {
 $host=strtolower($_SERVER['HTTP_HOST']??'');$local=PHP_SAPI==='cli-server'&&in_array($_SERVER['REMOTE_ADDR']??'',['127.0.0.1','::1'],true)&&preg_match('/^(127\.0\.0\.1|localhost)(:[0-9]+)?$/D',$host);if(!$local&&!in_array($host,['nodenohome.com','www.nodenohome.com','nodenohome.com.tr','www.nodenohome.com.tr'],true))throw new NodenoControlHttpError(403,'origin_rejected');$expected=($local&&empty($_SERVER['HTTPS'])?'http':'https').'://'.$host;
 if(($_SERVER['HTTP_ORIGIN']??'')!==$expected)throw new NodenoControlHttpError(403,'origin_rejected');if(!hash_equals($_SESSION['csrf'],(string)($_SERVER['HTTP_X_CSRF_TOKEN']??'')))throw new NodenoControlHttpError(403,'csrf_rejected');if(strtolower(explode(';',$_SERVER['CONTENT_TYPE']??'')[0])!=='application/json')throw new NodenoControlHttpError(415,'json_required');$raw=file_get_contents('php://input',false,null,0,2000001);if($raw===false||strlen($raw)>2000000)throw new NodenoControlHttpError(413,'body_too_large');try{$body=json_decode($raw,true,32,JSON_THROW_ON_ERROR);}catch(Throwable $e){throw new NodenoControlHttpError(400,'json_invalid');}if(!is_array($body)||(!str_starts_with(ltrim($raw),'{')))throw new NodenoControlHttpError(400,'object_required');return $body;
}
function nodenoControlTeam(array $ctx,string $method,array $body):array {
 $actor=nodenoControlRequire($ctx,'team.read',$method!=='GET');$db=$ctx['db'];$root=$ctx['root'];if($method==='GET')return ['data'=>array_map('nodenoControlSafeUser',$db->query('SELECT * FROM control_users ORDER BY created_at')->fetchAll())];
 if($method==='POST'){$email=nodenoControlEmail($body['email']??null);$role=(string)($body['role']??'');if(!nodenoControlPermissions($role))throw new NodenoControlHttpError(422,'role_invalid');$token=bin2hex(random_bytes(32));$id=nodenoControlId('invite_');$db->prepare('INSERT INTO control_invites(id,email,role,token_hash,expires_at,created_by,created_at) VALUES(?,?,?,?,?,?,?)')->execute([$id,$email,$role,hash('sha256',$token),time()+86400,$actor['id'],time()]);nodenoControlAudit($db,$root,$actor['id'],'invite','team',$id,['email'=>$email,'role'=>$role]);return ['id'=>$id,'invitationCode'=>$token,'expiresAt'=>time()+86400,'_status'=>201];}
 if($method==='PATCH')return nodenoControlTransaction($db,static function()use($db,$root,$actor,$body):array{$q=$db->prepare('SELECT * FROM control_users WHERE id=?');$q->execute([(string)($body['id']??'')]);$row=$q->fetch();if(!$row)throw new NodenoControlHttpError(404,'not_found');if((int)($body['version']??0)!==(int)$row['version'])throw new NodenoControlHttpError(409,'version_conflict');$role=(string)($body['role']??$row['role']);$active=$body['active']??(bool)$row['active'];if(!nodenoControlPermissions($role)||!is_bool($active))throw new NodenoControlHttpError(422,'role_invalid');if($row['role']==='owner'&&$row['active']&&($role!=='owner'||!$active)&&(int)$db->query("SELECT COUNT(*) FROM control_users WHERE role='owner' AND active=1")->fetchColumn()<=1)throw new NodenoControlHttpError(409,'last_owner_required');$db->prepare('UPDATE control_users SET role=?,active=?,auth_version=auth_version+1,version=version+1,updated_at=? WHERE id=?')->execute([$role,(int)$active,time(),$row['id']]);nodenoControlAudit($db,$root,$actor['id'],'permissions','team',$row['id'],['role'=>$role,'active'=>$active]);return ['saved'=>true,'version'=>(int)$row['version']+1];});throw new NodenoControlHttpError(405,'method_not_allowed');
}
function nodenoControlHandle(string $path,string $method,array $catalog,array $config,string $storageRoot):bool {
 if(!str_starts_with($path,'/api/admin/'))return false;
 try{$root=nodenoAccountStorage($storageRoot);$db=nodenoControlDatabase($root);$ctx=nodenoControlSession($db,$root);$route=substr($path,11);$body=in_array($method,['GET','HEAD'],true)?[]:nodenoControlBody();$result=nodenoControlAuth($ctx,$route,$method,$body);
  if($result===null)$result=nodenoControlDispatch($ctx,$route,$method,$body,$catalog,$config);
  if(empty($result['_responded'])){$status=$result['_status']??200;unset($result['_status']);nodenoAccountJson($result,$status);}
 }catch(NodenoControlHttpError $e){nodenoAccountJson(['error'=>$e->errorCode,'csrfToken'=>$_SESSION['csrf']??null],$e->status,$e->headers);}catch(Throwable $e){$reference=bin2hex(random_bytes(6));error_log('NODENO control '.$reference.' '.get_class($e));nodenoAccountJson(['error'=>'service_unavailable','reference'=>$reference],503);}finally{if(session_status()===PHP_SESSION_ACTIVE)session_write_close();}return true;
}
function nodenoControlDispatch(array $ctx,string $route,string $method,array $body,array $catalog,array $config):array {
 require_once __DIR__.'/payment-admin.php';
 $actor=nodenoControlRequire($ctx,'dashboard.read');$db=$ctx['db'];$root=$ctx['root'];$parts=explode('/',$route);$resource=$parts[0];$id=$parts[1]??'';$action=$parts[2]??'';
 if($route==='team')return nodenoControlTeam($ctx,$method,$body);
 if($resource==='social'){require_once __DIR__.'/social-admin.php';$effective=nodenoControlPublicState($ctx['db'],$catalog,$config);return nodenoStudioAdmin($ctx,$route,$method,$body,$effective['catalog'],$config);}
 if($resource==='payments'||$route==='payment-orders')return nodenoPaymentAdmin($ctx,$route,$method,$body);
 if($route==='schema'&&$method==='GET')return nodenoControlSchema($ctx,$catalog,$config);
 if($resource==='suppliers')return nodenoSupplierCommand($ctx,$id?:'overview',$method,$body,nodenoSupplierSeed());
 if($route==='dashboard'&&$method==='GET'){$counts=[];$defs=nodenoControlDefinitions();foreach(['orders','shipments','support','campaigns'] as $name){$def=$defs[$name];if(in_array('*',$ctx['permissions'],true)||in_array($def['group'].'.read',$ctx['permissions'],true)){$q=$db->prepare('SELECT COUNT(*) FROM control_records WHERE resource=?');$q->execute([$name]);$counts[$name]=(int)$q->fetchColumn();}}return nodenoControlDashboardWork($ctx,$catalog)+['products'=>count($catalog['products']),'models'=>count(array_unique(array_map(static fn($p)=>$p['modelId']??$p['id'],$catalog['products']))),'categories'=>count($catalog['categories']),'counts'=>$counts,'revision'=>(int)nodenoControlSetting($db,'public_revision',0),'checkoutEnabled'=>nodenoPaymentReady(nodenoPaymentConfiguration($db,$root)),'markets'=>nodenoControlCountries(),'readiness'=>['payment'=>nodenoPaymentReady(nodenoPaymentConfiguration($db,$root))?'Stripe kartla ödeme açık':'Stripe ve satıcı doğrulamaları bekleniyor','kolaybi'=>nodenoControlSetting($db,'integration:kolaybi')['status']??'not_configured','shipping'=>'Kargo kuralları ve anlaşmaları panelden tanımlanmalı','social'=>'Google ve Apple uygulama ayarları bekleniyor'],'at'=>time()];}
 if($route==='analytics'&&$method==='GET')return nodenoControlAnalyticsReport($ctx);
 if($route==='indexnow')return nodenoControlIndexNow($ctx,$method,$body);
 if($route==='audit'&&$method==='GET'){nodenoControlRequire($ctx,'audit.read');return ['data'=>$db->query('SELECT id,actor_id,action,resource,record_id,detail_json,occurred_at,previous_hash,entry_hash FROM control_audit ORDER BY id DESC LIMIT 300')->fetchAll()];}
 if($resource==='integrations')return nodenoControlIntegration($ctx,$id,$action==='verify'&&$method==='POST'?'VERIFY':$method,$body);
 if($route==='customers'&&$method==='GET'){nodenoControlRequire($ctx,'operations.read');return ['data'=>$db->query('SELECT id,email,name,created_at FROM users ORDER BY created_at DESC LIMIT 2000')->fetchAll()];}
 if($route==='customer-orders'&&$method==='GET'){nodenoControlRequire($ctx,'operations.read');return ['data'=>$db->query('SELECT o.*,u.email,u.name FROM orders o JOIN users u ON u.id=o.user_id ORDER BY o.created_at DESC LIMIT 2000')->fetchAll()];}
 if($resource==='documents'&&$method==='GET'){ $html=nodenoControlDocument($ctx,$id,$action);nodenoRespond($html,200,'text/html; charset=utf-8',['Cache-Control'=>'no-store','X-Robots-Tag'=>'noindex,nofollow']);return ['_responded'=>true]; }
 if($resource==='invoices'&&in_array($action,['status','pdf'],true)&&$method==='GET')return nodenoControlKolaybiDocument($ctx,$id,$action);
 if($resource==='invoices'&&in_array($action,['create-draft','issue'],true)&&$method==='POST')return nodenoControlKolaybiInvoice($ctx,$id,$action,$body);
 if($route==='system'&&$method==='GET'){nodenoControlRequire($ctx,'integrations.read');return ['runtime'=>PHP_VERSION,'database'=>'SQLite / WAL','storagePrivate'=>true,'checkoutEnabled'=>nodenoPaymentReady(nodenoPaymentConfiguration($db,$root)),'socialActivationPending'=>true,'seo'=>['sitemap'=>'https://nodenohome.com/sitemap.xml','robots'=>'https://nodenohome.com/robots.txt','languages'=>NODENO_STORE_LOCALES],'integrations'=>array_map(static fn($name)=>nodenoControlIntegration($ctx,$name,'GET',[]),['kolaybi','email','sms','googleAds','metaAds'])];}
 if(isset(nodenoControlDefinitions()[$resource])){
  if($action==='editor'&&$method==='GET'&&in_array($resource,['products','business','ranking','collections','markets','wholesale'],true))return nodenoControlEditor($ctx,$resource,$id,$catalog,$config);
  if($action!==''&&!in_array($action,['publish','unpublish','save-publish'],true))throw new NodenoControlHttpError(404,'not_found');
  $operation=$action!==''?str_replace('-','_',strtoupper($action)):$method;
  if($action!==''&&$method!=='POST')throw new NodenoControlHttpError(405,'method_not_allowed');
  nodenoControlAuthoriseResource($ctx,$resource,$operation);
  if(in_array($operation,['PUT','SAVE_PUBLISH'],true)&&$id===''&&!isset($body['idempotencyKey']))throw new NodenoControlHttpError(422,'idempotency_key_required');
  if($operation!=='GET'&&isset($body['idempotencyKey']))return nodenoControlCommand($ctx,(string)$body['idempotencyKey'],[$resource,$id,$operation,$body],static fn()=>nodenoControlResource($ctx,$resource,$id,$operation,$body,$catalog));
  return nodenoControlResource($ctx,$resource,$id,$operation,$body,$catalog,$config);
 }
 throw new NodenoControlHttpError(404,'not_found');
}
function nodenoControlSchema(array $ctx,array $catalog,array $config):array {
 $definitions=[];
 foreach(nodenoControlDefinitions() as $name=>$def)if(($name!=='business'||in_array('*',$ctx['permissions'],true))&&(in_array('*',$ctx['permissions'],true)||in_array($def['group'].'.read',$ctx['permissions'],true)))$definitions[$name]=$def;
 $state=nodenoControlPublicState($ctx['db'],$catalog,$config);$effective=array_column($state['catalog']['products'],null,'id');
 $products=[];$baseOverrides=[];foreach(nodenoControlProductOverrides($ctx['db'],$catalog)as $record)$baseOverrides[$record['id']]=$record['data']['priceMinor']??null;
 foreach($catalog['products'] as $p){$live=$effective[$p['id']]??null;$products[]=['id'=>$p['id'],'code'=>$p['code'],'name'=>$p['modelName']['tr']??$p['name']['tr']??$p['code'],'image'=>$p['images'][$p['coverIndex']??0]??null,'images'=>$p['images']??[],'priceMinor'=>$live['salePriceMinor']??null,'campaignBaseMinor'=>$baseOverrides[$p['id']]??$p['salePriceMinor']??null,'sourcePriceMinor'=>$p['salePriceMinor']??null,'visible'=>$live!==null,'color'=>$p['variantColor']['tr']??''];}
 $connection=nodenoControlSetting($ctx['db'],'integration:kolaybi');$safeConnection=$connection?['connectionId'=>$connection['connectionId']??null,'environment'=>$connection['environment']??null,'status'=>$connection['status'],'companies'=>$connection['companies']??[]]:null;
 return ['resources'=>$definitions,'countries'=>nodenoControlCountries(),'products'=>$products,'priceRevision'=>$state['revision'],'kolaybiConnection'=>$safeConnection,'roles'=>['owner'=>'Sahip','manager'=>'Mağaza yöneticisi','catalog'=>'Katalog','operations'=>'Operasyon','marketing'=>'Pazarlama','analyst'=>'Analiz']];
}

function nodenoControlDashboardWork(array $ctx,array $catalog):array {
 $queue=[];$campaigns=[];$db=$ctx['db'];$defs=nodenoControlDefinitions();
 foreach($defs as $resource=>$def){if(empty($def['publish'])||(!in_array('*',$ctx['permissions'],true)&&!in_array($def['group'].'.read',$ctx['permissions'],true)))continue;
  $q=$db->prepare('SELECT COUNT(*) FROM control_records WHERE resource=? AND version>published_version');$q->execute([$resource]);$pending=(int)$q->fetchColumn();if($pending)$queue[]=['resource'=>$resource,'label'=>$def['label'],'pending'=>$pending];
 }
 if(in_array('*',$ctx['permissions'],true)||in_array('marketing.read',$ctx['permissions'],true)){
  $q=$db->query("SELECT id FROM control_records WHERE resource='campaigns' ORDER BY updated_at DESC LIMIT 5");$ids=$q->fetchAll();$live=array_column(nodenoControlPublicState($db,$catalog,[])['catalog']['products'],null,'id');foreach($ids as $r)$campaigns[]=nodenoControlCampaignView($db,nodenoControlRead($db,'campaigns',$r['id']),$catalog,$live);
 }
 return ['publicationQueue'=>$queue,'campaigns'=>$campaigns];
}
