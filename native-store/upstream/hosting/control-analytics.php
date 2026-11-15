<?php
declare(strict_types=1);
require_once __DIR__.'/localization.php';
require_once __DIR__.'/control-marketing.php';

function nodenoControlAnalyticsSchema(PDO $db):void {
 $db->exec('CREATE TABLE IF NOT EXISTS control_consents(visitor TEXT PRIMARY KEY,expires_at INTEGER NOT NULL);CREATE TABLE IF NOT EXISTS control_events(visitor TEXT NOT NULL,day INTEGER NOT NULL,event TEXT NOT NULL,product_id TEXT NOT NULL,locale TEXT NOT NULL,device TEXT NOT NULL,market TEXT NOT NULL DEFAULT \'\',PRIMARY KEY(visitor,day,event,product_id));CREATE INDEX IF NOT EXISTS control_events_date ON control_events(day,product_id);');
 foreach(['source'=>"TEXT NOT NULL DEFAULT 'unknown'",'referrer'=>"TEXT NOT NULL DEFAULT ''"]as $column=>$definition){
  $columns=array_column($db->query('PRAGMA table_info(control_events)')->fetchAll(),'name');
  if(!in_array($column,$columns,true))try{$db->exec('ALTER TABLE control_events ADD COLUMN '.$column.' '.$definition);}catch(PDOException $error){if(!in_array($column,array_column($db->query('PRAGMA table_info(control_events)')->fetchAll(),'name'),true))throw $error;}
 }
}
function nodenoControlVisitor(string $root,string $token):string {return hash_hmac('sha256',$token,nodenoControlKey($root));}
function nodenoControlAnalyticsCleanup(PDO $db):void {
 nodenoControlTransaction($db,static function()use($db):void{
  $db->prepare('DELETE FROM control_events WHERE day<=? OR visitor NOT IN (SELECT visitor FROM control_consents WHERE expires_at>?)')->execute([intdiv(time(),86400)-90,time()]);
  $db->prepare('DELETE FROM control_consents WHERE expires_at<=?')->execute([time()]);
 });
}
function nodenoControlConsent(PDO $db,string $root,bool $granted,?string $token):?string {
 nodenoControlAnalyticsSchema($db);nodenoControlAnalyticsCleanup($db);if(!$granted){if($token){$visitor=nodenoControlVisitor($root,$token);nodenoControlTransaction($db,static function()use($db,$visitor):void{$db->prepare('DELETE FROM control_consents WHERE visitor=?')->execute([$visitor]);$db->prepare('DELETE FROM control_events WHERE visitor=?')->execute([$visitor]);});}return null;}$token=$token&&preg_match('/^[a-f0-9]{64}$/D',$token)?$token:bin2hex(random_bytes(32));$db->prepare('INSERT OR REPLACE INTO control_consents(visitor,expires_at) VALUES(?,?)')->execute([nodenoControlVisitor($root,$token),time()+90*86400]);return $token;
}
function nodenoControlEvent(PDO $db,string $root,?string $token,array $body,array $catalog):void {
 nodenoControlAnalyticsSchema($db);nodenoControlAnalyticsCleanup($db);
 if(!$token||!preg_match('/^[a-f0-9]{64}$/D',$token))throw new NodenoControlHttpError(403,'analytics_consent_required');
 $visitor=nodenoControlVisitor($root,$token);$q=$db->prepare('SELECT expires_at FROM control_consents WHERE visitor=?');$q->execute([$visitor]);if((int)$q->fetchColumn()<time())throw new NodenoControlHttpError(403,'analytics_consent_required');
 foreach($body as $key=>$value)if(!in_array($key,['event','productId','locale','device','market','source','referrer'],true)||!is_string($value))throw new NodenoControlHttpError(422,'analytics_payload_rejected');
 require_once __DIR__.'/visitor-market.php';
 $visit=($body['event']??'')==='visit';$source=$body['source']??'unknown';$referrer=$body['referrer']??'';
 if(!in_array($body['event']??'',['visit','view','cart','favorite'],true)||!in_array($body['locale']??'',NODENO_STORE_LOCALES,true)||!in_array($body['device']??'',['mobile','desktop'],true)||($visit?($body['productId']??null)!=='':!in_array($body['productId']??'',array_column($catalog['products'],'id'),true))||isset($body['market'])&&nodenoMarketForCountry($body['market'])['country']===null||!in_array($source,['unknown','direct','search','social','referral','campaign'],true)||strlen($referrer)>253||($referrer!==''&&(!preg_match('/^(?=.{1,253}$)[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?\.[a-z]{2,63}$/D',$referrer)||filter_var($referrer,FILTER_VALIDATE_IP))))throw new NodenoControlHttpError(422,'analytics_payload_rejected');
 nodenoControlRate($db,$root,'analytics',$visitor,300,3600);$day=intdiv(time(),86400);
 $first=$db->prepare("SELECT source,referrer FROM control_events WHERE visitor=? AND day=? AND event='visit' LIMIT 1");$first->execute([$visitor,$day]);$entry=$first->fetch();if($entry){$source=$entry['source'];$referrer=$entry['referrer'];}
 // Consent is rechecked by the insert itself, so an overlapping withdrawal
 // cannot recreate an event after deletion.
 $db->prepare('INSERT OR IGNORE INTO control_events(visitor,day,event,product_id,locale,device,market,source,referrer) SELECT ?,?,?,?,?,?,?,?,? WHERE EXISTS(SELECT 1 FROM control_consents WHERE visitor=? AND expires_at>?)')->execute([$visitor,$day,$body['event'],$body['productId'],$body['locale'],$body['device'],$body['market']??'',$source,$referrer,$visitor,time()]);
}
function nodenoControlRecommendations(PDO $db,array $catalog,string $current):array {
 nodenoControlAnalyticsSchema($db);nodenoControlAnalyticsCleanup($db);$settings=nodenoControlPublished($db,'ranking')[0]['data']??nodenoControlRankingDefaults();$weights=['view'=>$settings['views']??1,'cart'=>$settings['cart']??5,'favorite'=>$settings['favorites']??3];$days=$settings['days']??30;$q=$db->prepare("SELECT product_id,event,COUNT(*) AS n FROM control_events WHERE day>=? AND event IN ('view','cart','favorite') GROUP BY product_id,event");$q->execute([intdiv(time(),86400)-$days+1]);$scores=[];foreach($q->fetchAll() as $row)$scores[$row['product_id']]=($scores[$row['product_id']]??0)+$row['n']*($weights[$row['event']]??0);$manual=[];foreach(nodenoControlPublished($db,'products') as $row)$manual[$row['id']]=$row['data']['weight']??0;$source=array_column($catalog['products'],null,'id');$active=$source[$current]??null;$rank=[];
 foreach($source as $id=>$p){$id=(string)$p['id'];if(($p['hidden']??false)||($p['published']??true)===false||($p['stockKnown']??false)&&($p['stockQuantity']??0)<=0)continue;if($active&&($p['modelId']??$id)===($active['modelId']??$current))continue;$match=$active&&count(array_intersect($active['categoryIds']??[],$p['categoryIds']??[]))>0?10:0;$rank[]=['id'=>$id,'model'=>$p['modelId']??$id,'score'=>($scores[$id]??0)+($manual[$id]??0)+$match];}
 usort($rank,static fn($a,$b)=>($b['score']<=>$a['score'])?:strcmp($a['id'],$b['id']));$seen=[];$ids=[];foreach($rank as $r){if(isset($seen[$r['model']]))continue;$seen[$r['model']]=true;$ids[]=$r['id'];if(count($ids)>=12)break;}return ['ids'=>$ids,'basis'=>$scores?'aggregate_and_category':'category_and_catalogue','revision'=>(int)nodenoControlSetting($db,'public_revision',0)];
}
function nodenoControlAnalyticsReport(array $ctx):array {
 nodenoControlRequire($ctx,'analytics.read');$db=$ctx['db'];nodenoControlAnalyticsSchema($db);nodenoControlAnalyticsCleanup($db);$since=intdiv(time(),86400)-29;
 $query=static function(string $sql)use($db,$since):array{$q=$db->prepare($sql);$q->execute([$since]);return $q->fetchAll();};
 $data=$query('SELECT day,event,locale,device,market,source,referrer,COUNT(*) AS count FROM control_events WHERE day>=? GROUP BY day,event,locale,device,market,source,referrer ORDER BY day DESC');
 $summary=$query("SELECT COUNT(DISTINCT visitor) AS visitors,COUNT(DISTINCT CASE WHEN event='visit' THEN visitor||':'||day END) AS visitorDays,COUNT(*) AS events FROM control_events WHERE day>=?")[0];$summary=array_map('intval',$summary);
 $groups=[];foreach(['countries'=>'market','devices'=>'device','languages'=>'locale','sources'=>'source,referrer']as $name=>$fields)$groups[$name]=$query('SELECT '.$fields.',COUNT(DISTINCT visitor) AS visitors,COUNT(*) AS events FROM control_events WHERE day>=? GROUP BY '.$fields.' ORDER BY visitors DESC');
 return ['periodDays'=>30,'data'=>$data,'summary'=>$summary,'countries'=>$groups['countries'],'devices'=>$groups['devices'],'languages'=>$groups['languages'],'sources'=>$groups['sources'],'daily'=>$query('SELECT day,event,COUNT(*) AS count FROM control_events WHERE day>=? GROUP BY day,event ORDER BY day DESC'),'products'=>$query("SELECT product_id,event,COUNT(*) AS count FROM control_events WHERE day>=? AND event IN ('view','cart','favorite') GROUP BY product_id,event ORDER BY count DESC LIMIT 50"),'demographics'=>['available'=>false,'ageGroups'=>[],'genders'=>[]],'notice'=>'Son 30 gün · yalnız analiz izni veren ziyaretçiler. Ülke, seçilen pazarı gösterir. Eski kayıtlarda toplanmayan kaynak bilgisi bilinmiyor olarak görünür.'];
}
function nodenoControlPublicBody():array {
 $host=strtolower($_SERVER['HTTP_HOST']??'');$local=PHP_SAPI==='cli-server'&&in_array($_SERVER['REMOTE_ADDR']??'',['127.0.0.1','::1'],true)&&preg_match('/^(127\.0\.0\.1|localhost)(:[0-9]+)?$/D',$host);if(!$local&&!in_array($host,['nodenohome.com','www.nodenohome.com','nodenohome.com.tr','www.nodenohome.com.tr'],true))throw new NodenoControlHttpError(403,'origin_rejected');if(($_SERVER['HTTP_ORIGIN']??'')!==($local&&empty($_SERVER['HTTPS'])?'http':'https').'://'.$host)throw new NodenoControlHttpError(403,'origin_rejected');if(explode(';',strtolower($_SERVER['CONTENT_TYPE']??''))[0]!=='application/json')throw new NodenoControlHttpError(415,'json_required');$raw=file_get_contents('php://input',false,null,0,32769);if(strlen($raw)>32768)throw new NodenoControlHttpError(413,'body_too_large');try{$body=json_decode($raw,true,12,JSON_THROW_ON_ERROR);}catch(Throwable $e){throw new NodenoControlHttpError(400,'json_invalid');}if(!is_array($body)||!str_starts_with(ltrim($raw),'{'))throw new NodenoControlHttpError(400,'object_required');return $body;
}
function nodenoControlPublicHandle(string $path,string $method,array $catalog,string $root):bool {
 if(!str_starts_with($path,'/api/insights/')&&$path!=='/api/recommendations'&&$path!=='/api/support'&&$path!=='/api/shipping-quote')return false;
 try{$db=nodenoControlDatabase($root);if($path==='/api/recommendations'&&$method==='GET'){$current=is_string($_GET['product']??null)?$_GET['product']:'';nodenoAccountJson(nodenoControlRecommendations($db,$catalog,$current));return true;}if($path==='/api/shipping-quote'&&$method==='POST'){$body=nodenoControlPublicBody();$computed=nodenoControlItems($body['items']??[],$catalog);$country=$body['country']??'';if(!is_string($country)||!isset(nodenoControlCountries()[$country]))throw new NodenoControlHttpError(422,'country_invalid');nodenoAccountJson(nodenoControlShippingQuote($db,$computed['totalMinor'],$country));return true;}
  if(!in_array($method,['POST','DELETE'],true))throw new NodenoControlHttpError(405,'method_not_allowed');$body=nodenoControlPublicBody();$token=$_COOKIE['NODENOINSIGHTS']??null;
  if($path==='/api/insights/consent'){nodenoControlRate($db,$root,'consent',$_SERVER['REMOTE_ADDR']??'',60,3600);if(!is_bool($body['granted']??null))throw new NodenoControlHttpError(422,'consent_required');$granted=$body['granted'];$token=nodenoControlConsent($db,$root,$granted,$token);setcookie('NODENOINSIGHTS',$token??'',['expires'=>$granted?time()+90*86400:time()-3600,'path'=>'/','secure'=>true,'httponly'=>true,'samesite'=>'Lax']);nodenoAccountJson(['granted'=>$granted]);}
  elseif($path==='/api/insights/event') {if($method!=='POST')throw new NodenoControlHttpError(405,'method_not_allowed');nodenoControlEvent($db,$root,$token,$body,$catalog);nodenoAccountJson(['accepted'=>true],202);}
  elseif($path==='/api/support'&&$method==='POST'){nodenoControlRate($db,$root,'support',$_SERVER['REMOTE_ADDR']??'',5,3600);$data=nodenoControlValidate('support',['title'=>$body['title']??'','email'=>$body['email']??'','message'=>$body['message']??'','status'=>'open'],$catalog);$id=nodenoControlId('request_');$db->prepare('INSERT INTO control_records(resource,id,data_json,created_at,updated_at) VALUES(?,?,?,?,?)')->execute(['support',$id,json_encode($data,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE),time(),time()]);nodenoAccountJson(['reference'=>$id],201);}
  else throw new NodenoControlHttpError(404,'not_found');
 }catch(NodenoControlHttpError $e){nodenoAccountJson(['error'=>$e->errorCode],$e->status,$e->headers);}catch(Throwable $e){error_log('NODENO insights '.get_class($e));nodenoAccountJson(['error'=>'service_unavailable'],503);}return true;
}
