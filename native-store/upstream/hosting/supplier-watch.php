<?php
declare(strict_types=1);

/** Server-side monitoring observes source prices; it never mutates retail prices. */
function nodenoPaintWatchSchema(PDO $db):void {
 $db->exec('CREATE TABLE IF NOT EXISTS supplier_price_watch(product_id TEXT PRIMARY KEY,identity TEXT NOT NULL,data_json TEXT NOT NULL,next_at INTEGER NOT NULL,checked_at INTEGER NOT NULL)');
 $db->exec('CREATE TABLE IF NOT EXISTS supplier_price_alerts(id TEXT PRIMARY KEY,product_id TEXT NOT NULL,data_json TEXT NOT NULL,created_at INTEGER NOT NULL,ack_at INTEGER)');
}
function nodenoPaintWatchUrl(string $url):bool {
 $p=parse_url($url);if(!$p||($p['scheme']??'')!=='https'||($p['host']??'')!=='www.trendyol.com'||isset($p['user'])||isset($p['pass'])||isset($p['port'])||isset($p['fragment'])||!preg_match('~-p-[0-9]+$~D',$p['path']??''))return false;
 parse_str($p['query']??'',$q);return count($q)===1&&isset($q['merchantId'])&&is_string($q['merchantId'])&&preg_match('/^[0-9]+$/D',$q['merchantId'])===1;
}
function nodenoPaintWatchIdentity(array $p):string {
 return hash('sha256',json_encode([$p['sourceUrl']??null,$p['sourceCode']??null,$p['sourceVariant']??null],JSON_THROW_ON_ERROR));
}
function nodenoPaintWatchParse(string $html,array $p):array {
 if(strlen($html)>3000000||!preg_match('~window\["__envoy__SHARED_PROPS"\]=(\{.*?\})\s*</script>~s',$html,$m))throw new RuntimeException('source_document_changed');
 $data=json_decode($m[1],true,128,JSON_THROW_ON_ERROR);$product=$data['product']??[];$listing=$product['merchantListing']??[];$variant=$listing['winnerVariant']??[];$expected=$p['sourceVariant']??[];
 if((string)($product['id']??'')!==($expected['productId']??'')||(string)($listing['merchant']['id']??'')!==($expected['merchantId']??'')||(string)($variant['itemNumber']??'')!==($expected['itemNumber']??'')||(string)($variant['barcode']??'')!==($expected['barcode']??'')||($product['productCode']??'')!==($p['sourceCode']??'')||($product['slicingAttributes']['DsmColor']??'')!==($expected['color']??''))throw new RuntimeException('source_identity_changed');
 $selected=array_values(array_filter($product['variants']??[],static fn($v)=>!empty($v['isSelected'])));
 if(count($selected)!==1||(string)($selected[0]['itemNumber']??'')!==($expected['itemNumber']??'')||($selected[0]['value']??'')!==($expected['selectedSize']??''))throw new RuntimeException('source_package_changed');
 if(empty($variant['inStock'])||empty($variant['sellable']))throw new RuntimeException('source_unavailable');
 $price=$variant['price']??[];$value=$price['sellingPrice']['value']??null;
 if(($price['currency']??'')!=='TRY'||(!is_int($value)&&!is_float($value))||!is_finite((float)$value)||$value<=0||$value>10000000||abs($value*100-round($value*100))>0.00001)throw new RuntimeException('source_price_invalid');
 return ['priceMinor'=>(int)round($value*100),'currency'=>'TRY'];
}
function nodenoPaintWatchRedirect(string $original,string $location):string {
 if(!nodenoPaintWatchUrl($original)||$location===''||preg_match('/[\r\n]/',$location))throw new RuntimeException('source_identity_changed');
 if(str_starts_with($location,'/')&&!str_starts_with($location,'//'))$location='https://www.trendyol.com'.$location;
 $a=parse_url($original);$b=parse_url($location);parse_str($a['query'],$expected);parse_str($b['query']??'',$actual);
 if(!$b||($b['scheme']??'')!=='https'||($b['host']??'')!=='www.trendyol.com'||isset($b['user'])||isset($b['pass'])||isset($b['port'])||isset($b['fragment'])||!preg_match('~-p-([0-9]+)$~D',$a['path'],$first)||!preg_match('~-p-([0-9]+)$~D',$b['path']??'',$next)||$first[1]!==$next[1]||array_diff(array_keys($actual),['merchantId'])||isset($actual['merchantId'])&&$actual['merchantId']!==$expected['merchantId'])throw new RuntimeException('source_identity_changed');
 $target='https://www.trendyol.com'.$b['path'].'?merchantId='.$expected['merchantId'];
 if(!nodenoPaintWatchUrl($target))throw new RuntimeException('source_identity_changed');return $target;
}
function nodenoPaintWatchFetch(string $url):string {
 if(!nodenoPaintWatchUrl($url)||!function_exists('curl_init'))throw new RuntimeException('source_fetch_unavailable');
 $current=$url;
 for($hop=0;$hop<3;$hop++){
  $body='';$location='';$c=curl_init($current);curl_setopt_array($c,[CURLOPT_FOLLOWLOCATION=>false,CURLOPT_PROTOCOLS=>CURLPROTO_HTTPS,CURLOPT_CONNECTTIMEOUT=>8,CURLOPT_TIMEOUT=>18,CURLOPT_USERAGENT=>'NODENO price monitoring (+https://nodenohome.com)',CURLOPT_HTTPHEADER=>['Accept-Language: tr-TR,tr;q=0.9'],CURLOPT_HEADERFUNCTION=>static function($c,string $header)use(&$location):int{if(stripos($header,'Location:')===0)$location=trim(substr($header,9));return strlen($header);},CURLOPT_WRITEFUNCTION=>static function($c,string $chunk)use(&$body):int{if(strlen($body)+strlen($chunk)>3000000)return 0;$body.=$chunk;return strlen($chunk);}]);
  try{$ok=curl_exec($c);$status=(int)curl_getinfo($c,CURLINFO_RESPONSE_CODE);if($ok===false)throw new RuntimeException('source_request_failed');if(in_array($status,[301,302,307,308],true)){$current=nodenoPaintWatchRedirect($url,$location);continue;}if($status!==200)throw new RuntimeException(in_array($status,[403,429],true)?'source_access_limited':'source_request_failed');return $body;}finally{curl_close($c);}
 }
 throw new RuntimeException('source_request_failed');
}
function nodenoPaintWatchObserve(PDO $db,array $p,?array $observed,?string $error,int $now):array {
 nodenoPaintWatchSchema($db);$identity=nodenoPaintWatchIdentity($p);$q=$db->prepare('SELECT * FROM supplier_price_watch WHERE product_id=?');$q->execute([$p['id']]);$old=$q->fetch();$before=$old&&hash_equals($old['identity'],$identity)?json_decode($old['data_json'],true):null;
 $baseline=$before['lastPriceMinor']??$p['sourcePriceMinor'];$data=$before??['lastPriceMinor'=>$baseline,'lastSuccessAt'=>null,'errorCount'=>0];$data['checkedAt']=$now;
 if($error!==null){$data['status']='error';$data['error']=$error;$data['errorCount']++;$next=$now+min(86400,900*(2**min($data['errorCount'],6)));}
 else{if(!is_int($observed['priceMinor']??null)||$observed['priceMinor']<=0||($observed['currency']??'')!=='TRY')throw new RuntimeException('source_price_invalid');$value=$observed['priceMinor'];$data=array_merge($data,['status'=>'ok','error'=>null,'errorCount'=>0,'lastPriceMinor'=>$value,'lastSuccessAt'=>$now]);$next=$now+86400;}
 $q=$db->prepare('INSERT INTO supplier_price_watch(product_id,identity,data_json,next_at,checked_at) VALUES(?,?,?,?,?) ON CONFLICT(product_id) DO UPDATE SET identity=excluded.identity,data_json=excluded.data_json,next_at=excluded.next_at,checked_at=excluded.checked_at');$q->execute([$p['id'],$identity,json_encode($data,JSON_THROW_ON_ERROR),$next,$now]);
 $kind=$error!==null?'check_failed':($value!==$baseline?'price_changed':null);
 if($kind&&($kind!=='check_failed'||($before['error']??null)!==$error)){
  $event=['productId'=>$p['id'],'title'=>$p['title'],'supplierId'=>$p['supplierId'],'sourceUrl'=>$p['sourceUrl'],'kind'=>$kind,'previousMinor'=>$baseline,'currentMinor'=>$error===null?$value:null,'suggestedSaleMinor'=>$error===null?intdiv($value*130+50,100):null,'error'=>$error,'observedAt'=>$now,'retailPriceChanged'=>false];
  $id=hash('sha256',$identity.'|'.$kind.'|'.($error??$value).'|'.($before['lastSuccessAt']??'initial').'|'.($before['status']??'initial'));
  $db->prepare('INSERT OR IGNORE INTO supplier_price_alerts(id,product_id,data_json,created_at) VALUES(?,?,?,?)')->execute([$id,$p['id'],json_encode($event,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE),$now]);
 }
 return $data;
}
function nodenoPaintWatchTick(PDO $db,array $seed,?callable $transport=null,int $limit=5):array {
 nodenoPaintWatchSchema($db);$now=time();$enabled=nodenoControlSetting($db,'paint-watch:enabled',true);if(!$enabled)return ['enabled'=>false,'checked'=>0];
 $done=0;$errors=0;$paused=(int)nodenoControlSetting($db,'paint-watch:pause-until',0);if($paused>$now)return ['enabled'=>true,'checked'=>0,'pausedUntil'=>$paused];
 $seed=nodenoSupplierEffectiveSeed($db,$seed);
 foreach($seed['products']as $p){
  if(empty($p['priceWatch'])||$done>=max(1,min(8,$limit)))continue;$q=$db->prepare('SELECT next_at FROM supplier_price_watch WHERE product_id=?');$q->execute([$p['id']]);$next=$q->fetchColumn();if($next!==false&&(int)$next>$now)continue;
  try{if(!nodenoPaintWatchUrl((string)$p['sourceUrl'])||!hash_equals((string)($p['sourceWatchIdentity']??''),nodenoPaintWatchIdentity($p)))throw new RuntimeException('mapping_review_required');$body=$transport?$transport($p['sourceUrl']):nodenoPaintWatchFetch($p['sourceUrl']);$observed=nodenoPaintWatchParse($body,$p);nodenoPaintWatchObserve($db,$p,$observed,null,$now);}
  catch(Throwable $e){$known=['source_document_changed','source_identity_changed','source_package_changed','source_unavailable','source_price_invalid','source_fetch_unavailable','source_access_limited','source_request_failed','mapping_review_required'];$error=in_array($e->getMessage(),$known,true)?$e->getMessage():'source_document_changed';nodenoPaintWatchObserve($db,$p,null,$error,$now);$errors++;if($error==='source_access_limited')nodenoControlSetSetting($db,'paint-watch:pause-until',$now+3600);}
  $done++;if($paused=(int)nodenoControlSetting($db,'paint-watch:pause-until',0))if($paused>$now)break;
 }
 $result=['enabled'=>true,'checked'=>$done,'errors'=>$errors,'at'=>$now,'intervalHours'=>24];nodenoControlSetSetting($db,'paint-watch:heartbeat',$result);return $result;
}
function nodenoPaintWatchOverview(PDO $db):array {
 nodenoPaintWatchSchema($db);$rows=$db->query('SELECT * FROM supplier_price_watch')->fetchAll();$states=[];foreach($rows as $r)$states[$r['product_id']]=json_decode($r['data_json'],true)+['nextAt'=>(int)$r['next_at']];$alerts=[];foreach($db->query('SELECT * FROM supplier_price_alerts ORDER BY ack_at IS NULL DESC,created_at DESC,id DESC LIMIT 250')->fetchAll()as $r)$alerts[]=['id'=>$r['id'],'ackAt'=>$r['ack_at']? (int)$r['ack_at']:null,'data'=>json_decode($r['data_json'],true)];
 return ['enabled'=>nodenoControlSetting($db,'paint-watch:enabled',true),'intervalHours'=>24,'heartbeat'=>nodenoControlSetting($db,'paint-watch:heartbeat',null),'states'=>$states,'alerts'=>$alerts,'unread'=>(int)$db->query('SELECT COUNT(*) FROM supplier_price_alerts WHERE ack_at IS NULL')->fetchColumn()];
}
function nodenoPaintWatchCommand(array $ctx,string $action,array $body):array {
 nodenoPaintWatchSchema($ctx['db']);if($action==='watch-settings'){if(!is_bool($body['enabled']??null))throw new NodenoControlHttpError(422,'supplier_setting_invalid');nodenoControlSetSetting($ctx['db'],'paint-watch:enabled',$body['enabled']);return ['saved'=>true];}
 if($action==='watch-ack'){$id=nodenoSupplierText($body['id']??'',100);$ctx['db']->prepare('UPDATE supplier_price_alerts SET ack_at=? WHERE id=? AND ack_at IS NULL')->execute([time(),$id]);return ['saved'=>true];}
 throw new NodenoControlHttpError(405,'method_not_allowed');
}
