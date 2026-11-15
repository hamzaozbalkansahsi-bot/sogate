<?php
declare(strict_types=1);
require_once __DIR__.'/localization.php';
require_once __DIR__.'/control-analytics.php';
require_once __DIR__.'/search-notifications.php';

function nodenoControlIndexNowQueue(PDO $db,string $resource,string $id,array $data=[]):void {
 $ids=$resource==='products'?[$id]:($resource==='campaigns'?array_filter(array_map('trim',explode(',',$data['productIds']??''))):[]);$urls=[];foreach(NODENO_STORE_LOCALES as $locale){if($ids)foreach($ids as $product)$urls[]='https://nodenohome.com/?lang='.$locale.'&product='.rawurlencode($product);else $urls[]='https://nodenohome.com/?lang='.$locale;}
 nodenoSearchSchema($db);nodenoSearchSet($db,'scanRequested',true);$key=hash('sha256',json_encode([$urls,nodenoControlSetting($db,'public_revision',0)]));$db->prepare('INSERT OR IGNORE INTO control_jobs(id,type,status,request_json,next_attempt_at,created_at,updated_at,idempotency_key) VALUES(?,?,?,?,?,?,?,?)')->execute([nodenoControlId('job_'),'indexnow','queued',json_encode($urls),time(),time(),time(),$key]);
}
function nodenoControlIndexNow(array $ctx,string $method,array $body):array {
 nodenoControlRequire($ctx,'integrations.read',$method!=='GET');$db=$ctx['db'];$root=$ctx['root'];$key=nodenoControlSetting($db,'indexnow:key');
 if($method==='POST'&&($body['action']??'')==='prepare'){if(!$key){$key=bin2hex(random_bytes(16));nodenoControlSetSetting($db,'indexnow:key',$key);}nodenoControlIndexNowQueue($db,'seo','default');nodenoControlAudit($db,$root,$ctx['user']['id'],'prepare','indexnow','key');}
 elseif($method==='POST'&&($body['action']??'')==='submit'){
  if(!$key)throw new NodenoControlHttpError(422,'indexnow_key_required');nodenoSearchSchema($db);$result=nodenoSearchLock($root,static fn()=>nodenoSearchDrain($db,time(),$key,(string)nodenoControlSetting($db,'indexnow:endpoint','https://yandex.com/indexnow')));nodenoControlAudit($db,$root,$ctx['user']['id'],'submit','indexnow','',$result);
 }elseif($method!=='GET')throw new NodenoControlHttpError(422,'action_invalid');
 nodenoSearchSchema($db);$heartbeat=nodenoSearchMeta($db,'heartbeat');$q=$db->query("SELECT id,status,result_json,created_at,updated_at FROM control_jobs WHERE type='indexnow' ORDER BY created_at DESC LIMIT 50");return ['keyReady'=>is_string($key),'keyLocation'=>$key?'https://nodenohome.com/'.$key.'.txt':null,'data'=>$q->fetchAll(),'worker'=>$heartbeat,'endpoint'=>nodenoControlSetting($db,'indexnow:endpoint','https://yandex.com/indexnow'),'notice'=>(($heartbeat&&time()-(int)$heartbeat['checkedAt']<180)?'Otomatik bildirim çalışıyor. Yeni ve değişen içerik en geç 5 dakika içinde kuyruğa alınır. ':'Otomatik bildirim kontrolü bekleniyor. ').'HTTP 200 kabulü kaydedilir; 202 doğrulama bekliyor durumudur. Dizine ekleme veya sıralama garantisi değildir.'];
}
