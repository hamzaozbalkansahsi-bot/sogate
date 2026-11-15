<?php
declare(strict_types=1);
require_once __DIR__.'/localization.php';
require_once __DIR__.'/exchange-rates.php';
require_once __DIR__.'/cabinet-fronts.php';
function nodenoShippingCatalog(array $catalog):array {
 if(($catalog['meta']['shippingPolicyVersion']??'')!=='2026-11-12-included')return $catalog;
 $lift=static fn($v)=>is_int($v)&&$v>0?intdiv($v*120+50,100):$v;
 foreach($catalog['products']as &$p){
  if(!empty($p['shippingAdjustmentApplied']))continue;
  if(in_array($p['productType']??'',['door','door-profile','cabinet-front','cabinet-profile'],true)){
   foreach(['salePriceMinor','previousPriceMinor']as $key)if(isset($p[$key]))$p[$key]=$lift($p[$key]);
   if(isset($p['salePriceMinor']))$p['salePrice']=$p['salePriceMinor']/100;
   foreach($p['door']['charges']??[]as $key=>$fee){if(is_array($fee)){foreach($fee as $k=>$v)$p['door']['charges'][$key][$k]=$lift($v);}else $p['door']['charges'][$key]=$lift($fee);}
  }
  $old=['Aksesuar, KDV ve nakliye hariçtir.','Hardware, VAT and freight are excluded.','Фурнитура, НДС и перевозка оплачиваются отдельно.','الملحقات والضريبة والنقل غير مشمولة.'];
  $new=['Aksesuar ve KDV hariçtir. Türkiye içi kargo dahildir.','Hardware and VAT are excluded. Shipping within Türkiye is included.','Фурнитура и НДС оплачиваются отдельно. Доставка по Турции включена.','الملحقات والضريبة غير مشمولة. الشحن داخل تركيا مشمول.'];
  foreach($p['description']??[]as $lang=>$text)$p['description'][$lang]=str_replace($old,$new,$text);
  $p['shippingAdjustmentApplied']=true;$p['domesticFreightIncluded']=true;
 }unset($p);return $catalog;
}

function nodenoDoorOptions(array $input,array $product):array {
 $defaults=['frameDepth'=>15,'height'=>207,'architrave18'=>false,'glazed'=>false,'hardware'=>false,'handle'=>false,'openingWidthMm'=>0,'handing'=>'unspecified'];
 $measuredKeys=['heightMm','leafWidthMm','frameWidthMm','glassModelId'];
 if(array_diff(array_keys($input),array_merge(array_keys($defaults),$measuredKeys)))throw new InvalidArgumentException('door_options_invalid');$o=array_replace($defaults,$input);
 if(array_intersect(array_keys($input),$measuredKeys)){
  if(!is_int($o['heightMm']??null)||$o['heightMm']<1000||$o['heightMm']>3500||!in_array($o['leafWidthMm']??null,[770,870],true)||!in_array($o['frameWidthMm']??null,[95,115,145,165,185,215],true))throw new InvalidArgumentException('door_measurements_invalid');
  $frame=$o['frameWidthMm']<=145?15:($o['frameWidthMm']===165?17:($o['frameWidthMm']===185?19:21));$height=(int)ceil($o['heightMm']/10);
  if((isset($input['height'])&&$input['height']!==$height)||(isset($input['frameDepth'])&&$input['frameDepth']!==$frame))throw new InvalidArgumentException('door_measurements_conflict');
  $o['height']=$height;$o['frameDepth']=$frame;$o['glassModelId']=$input['glassModelId']??'';
  if(!is_string($o['glassModelId'])||strlen($o['glassModelId'])>100||($o['glassModelId']!==''&&!preg_match('/^[a-z0-9-]+$/D',$o['glassModelId']))||($o['glassModelId']!==''&&!$o['glazed']))throw new InvalidArgumentException('door_glass_model_invalid');
  if($o['glazed']&&$o['glassModelId']==='')throw new InvalidArgumentException('door_glass_model_required');
 }
 if(!in_array($o['frameDepth'],[15,17,19,21],true)||!is_int($o['height'])||$o['height']<100||$o['height']>350||!is_int($o['openingWidthMm'])||$o['openingWidthMm']<0||$o['openingWidthMm']>5000||!in_array($o['handing'],['unspecified','left','right'],true))throw new InvalidArgumentException('door_options_invalid');
 foreach(['architrave18','glazed','hardware','handle']as $key)if(!is_bool($o[$key]))throw new InvalidArgumentException('door_options_invalid');
 if($o['glazed']&&empty($product['door']['glassAvailable'])&&($product['door']['kind']??'')!=='glazed')throw new InvalidArgumentException('door_glazing_unavailable');return $o;
}
function nodenoDoorLineKey(string $id,array $o):string {return $id.'@'.implode('-',[$o['frameDepth'],$o['height'],(int)$o['architrave18'],(int)$o['glazed'],(int)$o['hardware'],(int)$o['handle'],$o['openingWidthMm'],$o['handing']]).(isset($o['heightMm'])?'-mm'.$o['heightMm'].'x'.$o['leafWidthMm'].'x'.$o['frameWidthMm'].'-'.($o['glassModelId']?:'solid'):'');}
function nodenoDoorPrice(array $p,array $input=[]):array {
 $o=nodenoDoorOptions($input,$p);$known=$p['salePriceMinor']??null;$reasons=[];$fees=$p['door']['charges']??[];
 if(!is_int($known)||$known<=0){$known=null;$reasons[]='source_price_missing';}
 $add=static function($amount,string $reason)use(&$known,&$reasons):void{if(!is_int($amount)||$amount<0){$reasons[]=$reason;return;}if($known!==null)$known+=$amount;};
 if($o['frameDepth']>17)$add($fees['depth'][$o['frameDepth']]??null,'frame_price_missing');
 if($o['architrave18'])$add($fees['architrave18']??null,'architrave_price_missing');
 if($o['glazed'])$add($fees['glazing']??null,'glazing_price_missing');
 if($o['hardware'])$add($fees['hardware']??null,'hardware_price_missing');
 if($o['height']>207)$reasons[]='special_height';if($o['openingWidthMm']>0)$reasons[]='opening_measurement';if($o['handle'])$reasons[]='handle_model';if(($p['door']['finishGroup']??'')==='veneer')$reasons[]='veneer_paint';
 if($known!==null&&(!is_int($known)||$known>9007199254740991))throw new InvalidArgumentException('door_price_overflow');
 return ['unitPriceMinor'=>$reasons?null:$known,'knownUnitMinor'=>$known,'requiresQuote'=>(bool)$reasons,'reasons'=>$reasons];
}
function nodenoDoorCartLine(array $item,array $product):array {
 if(array_diff(array_keys($item),['id','quantity','key','options']))throw new InvalidArgumentException('door_line_invalid');
 $input=$item['options']??[];if(!is_array($input))throw new InvalidArgumentException('door_options_invalid');$options=nodenoDoorOptions($input,$product);$key=nodenoDoorLineKey($product['id'],$options);
 if(isset($item['key'])&&$item['key']!==$key)throw new InvalidArgumentException('door_line_key_invalid');return ['id'=>$product['id'],'quantity'=>$item['quantity'],'options'=>$options,'key'=>$key];
}
function nodenoDoorCountry(string $country):void {
 if($country!=='TR'&&(!function_exists('nodenoWholesaleCountries')||!isset(nodenoWholesaleCountries()[$country])))throw new InvalidArgumentException('delivery_country_required');
}
function nodenoCommerceQuote(array $catalog,array $items,string $country,string $currency='TRY',?array $fx=null):array {
 $catalog=nodenoShippingCatalog($catalog);
 nodenoDoorCountry($country);
 if(!$items||count($items)>100||!array_is_list($items))throw new InvalidArgumentException('commerce_items_invalid');
 $byId=array_column($catalog['products'],null,'id');$seen=[];$lines=[];$doorQuantity=0;$area=0;$sum=0;$unpriced=0;
 foreach($items as $item){
  if(!is_array($item)||!is_string($item['id']??null)||!isset($byId[$item['id']])||!is_int($item['quantity']??null))throw new InvalidArgumentException('commerce_item_invalid');
  $p=$byId[$item['id']];$type=$p['productType']??'furniture';$quantity=$item['quantity'];
  if($quantity<1||$quantity>(in_array($type,['door','cabinet-front'],true)?10000:99))throw new InvalidArgumentException('commerce_item_invalid');
  if($type==='supplier-item'){if($p['variationSelectionRequired']??false)throw new InvalidArgumentException('commerce_variant_required');$q=$p['quantityPolicy'];if($quantity<$q['minimum']||($quantity-$q['minimum'])%$q['step']!==0)throw new InvalidArgumentException('commerce_quantity_invalid');}
  if(($p['hidden']??false)||($p['published']??true)===false)throw new InvalidArgumentException('product_unavailable');
  if($type==='door'){
   $clean=nodenoDoorCartLine($item,$p);$o=$clean['options'];
   if(isset($o['heightMm'])&&$o['glazed']){
    $models=array_filter($catalog['products'],static fn($v)=>($v['modelId']??null)===($p['modelId']??'')&&($v['productType']??'')==='door'&&($v['door']['kind']??'')==='glazed');
    $valid=$models?in_array($o['glassModelId'],array_column($models,'id'),true):$o['glassModelId']==='standard';if(!$valid)throw new InvalidArgumentException('door_glass_model_invalid');
   }
   $pricing=nodenoDoorPrice($p,$clean['options']);$doorQuantity+=$quantity;
   $total=$pricing['unitPriceMinor']===null?null:$pricing['unitPriceMinor']*$quantity;
  }elseif($type==='cabinet-front'){
   $clean=nodenoFrontCartLine($item,$p);$pricing=nodenoFrontPrice($p,$clean['options'],$quantity);
   if(($p['front']['minimumApplies']??true)!==false)$area+=$pricing['areaMm2'];
   $total=$pricing['lineTotalMinor'];$pricing['knownUnitMinor']=$pricing['unitPriceMinor'];$pricing['reasons']=$pricing['requiresQuote']?['front_application_quote_required']:[];
  }else{
   if(array_diff(array_keys($item),['id','quantity']))throw new InvalidArgumentException('commerce_item_invalid');
   $clean=['id'=>$p['id'],'quantity'=>$quantity];$unit=$p['salePriceMinor']??null;
   if(!is_int($unit)||$unit<=0)$unit=null;
   $pricing=['unitPriceMinor'=>$unit,'knownUnitMinor'=>$unit,'reasons'=>[]];$total=$unit===null?null:$unit*$quantity;
  }
  $key=$clean['key']??$clean['id'];if(isset($seen[$key]))throw new InvalidArgumentException('commerce_duplicate_line');$seen[$key]=true;
  if($total!==null)$sum+=$total;else $unpriced++;
  if(!is_int($sum)||$sum>9007199254740991)throw new InvalidArgumentException('commerce_amount_overflow');
  $line=$clean+['code'=>$p['code'],'name'=>$p['modelName']??$p['name'],'variant'=>$p['variantColor']??null,'productType'=>$type,'saleUnit'=>$p['saleUnit']??'piece','unitPriceMinor'=>$pricing['unitPriceMinor'],'lineTotalMinor'=>$total,'knownUnitMinor'=>$pricing['knownUnitMinor'],'quoteReasons'=>$pricing['reasons'],'taxIncluded'=>in_array($type,['door','cabinet-front'],true)?false:(($p['priceTaxPolicy']??'')==='vat_included'?true:null)];
  if($type==='cabinet-front')$line+=['areaMm2'=>$pricing['areaMm2'],'unitAreaMm2'=>$pricing['unitAreaMm2'],'unitRateMinor'=>$pricing['unitRateMinor']];
  $lines[]=$line;
 }
 $minimum=$country==='TR'?5:10;$missing=$doorQuantity?max(0,$minimum-$doorQuantity):0;
 $minArea=($country==='TR'?5:10)*1000000;$missingArea=$area?max(0,$minArea-$area):0;
 $result=['schema'=>1,'priceRevision'=>$catalog['meta']['controlRevision']??0,'doorCatalogVersion'=>$catalog['meta']['doorCatalogVersion']??null,'frontCatalogVersion'=>$catalog['meta']['frontCatalogVersion']??null,'deliveryCountry'=>$country,'currency'=>$currency,'lines'=>$lines,'doorQuantity'=>$doorQuantity,'minimumDoorSets'=>$minimum,'missingDoorSets'=>$missing,'frontAreaMm2'=>$area,'minimumFrontAreaMm2'=>$minArea,'missingFrontAreaMm2'=>$missingArea,'minimumEligible'=>$missing===0&&$missingArea===0,'requiresQuote'=>$unpriced>0,'pricedSubtotalTryMinor'=>$sum,'subtotalTryMinor'=>$unpriced?null:$sum,'taxAndFreightFinalized'=>false,'checkoutEnabled'=>false];
 if($currency==='TRY')$result['displaySubtotalMinor']=$result['subtotalTryMinor'];
 else{
  if(!$fx||!isset($fx['rates'][$currency])||($fx['stale']??false)||($fx['validUntil']??0)<time())throw new InvalidArgumentException('exchange_rate_unavailable');
  $exponent=$currency==='JPY'?0:(in_array($currency,['KWD','BHD','OMR','JOD','TND'],true)?3:2);
  $result['exchangeRevision']=$fx['revision'];$result['exchangeRate']=$fx['rates'][$currency];$result['exchangeWeekStart']=$fx['weekStart'];
  $result['displaySubtotalMinor']=$result['subtotalTryMinor']===null?null:nodenoFxConvert($sum,$fx['rates'][$currency],$exponent);
 }
 $result['revision']=hash('sha256',json_encode($result,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE));return $result;
}
function nodenoDoorMedia(string $private,string $id,int $index):?array {
 $front=str_starts_with($id,'front-');if(!$front&&!str_starts_with($id,'door-'))return null;
 $body=nodenoPrivateFile($private,$front?'cabinet-fronts.json':'door-catalog.json');$data=json_decode($body,true,64,JSON_THROW_ON_ERROR);if(($data['publicationReady']??false)!==true)throw new RuntimeException('door_media_unapproved');
 $product=null;foreach($data['products']as $p)if($p['id']===$id){$product=$p;break;}
 $hash=$product['assetHashes'][$index]??null;$asset=$data['assets'][$hash]??null;if(!$asset||!preg_match('~^/assets/(?:doors|fronts)/[a-f0-9]{64}\.(jpg|png|webp)$~D',$asset['path']))throw new RuntimeException('door_image_missing');
 $public=null;
 // The executing entry point supplies the actual document root in both local QA and hosting.
 $public=realpath($_SERVER['DOCUMENT_ROOT']??'')?:$public;if(!$public)throw new RuntimeException('door_image_missing');
 $file=$public.$asset['path'];if(is_link($file)||!is_file($file)||!hash_equals($hash,hash_file('sha256',$file)))throw new RuntimeException('door_image_unapproved');
 return ['file'=>$file,'sha256'=>$hash,'mime'=>str_ends_with($file,'.jpg')?'image/jpeg':(str_ends_with($file,'.png')?'image/png':'image/webp')];
}
function nodenoCommerceHandle(string $path,string $method,array $state):bool {
 if(!in_array($path,['/api/exchange-rates','/api/commerce/status','/api/commerce/quote','/api/door-inquiries'],true))return false;
 try{
  if($path==='/api/commerce/status'&&$method==='GET'){$token=$_COOKIE['NODENODOOR']??'';if(!is_string($token)||!preg_match('/^[a-f0-9]{64}$/D',$token)){$token=bin2hex(random_bytes(32));setcookie('NODENODOOR',$token,['path'=>'/','secure'=>!empty($_SERVER['HTTPS']),'httponly'=>true,'samesite'=>'Strict']);}nodenoRespond(json_encode(['checkoutEnabled'=>false,'paymentProviderConfigured'=>false,'csrfToken'=>$token,'countries'=>array_merge(['TR'],array_keys(nodenoWholesaleCountries())),'doorMinimum'=>['TR'=>5,'international'=>10]],JSON_THROW_ON_ERROR),200,'application/json; charset=utf-8',['Cache-Control'=>'no-store']);return true;}
  if($path==='/api/exchange-rates'&&$method==='GET'){$result=nodenoFxSnapshot($state['storage']);nodenoRespond(json_encode($result,JSON_THROW_ON_ERROR),200,'application/json; charset=utf-8',['Cache-Control'=>'no-store']);return true;}
  if($path==='/api/door-inquiries'&&$method==='POST'){$body=nodenoControlPublicBody();$token=$_COOKIE['NODENODOOR']??'';if(!is_string($token)||!preg_match('/^[a-f0-9]{64}$/D',$token)||!is_string($_SERVER['HTTP_X_CSRF_TOKEN']??null)||!hash_equals($token,$_SERVER['HTTP_X_CSRF_TOKEN']))throw new NodenoControlHttpError(403,'csrf_rejected');$db=nodenoControlDatabase($state['storage']);nodenoControlRate($db,$state['storage'],'door-inquiry',$_SERVER['REMOTE_ADDR']??'',12,3600);$result=nodenoDoorInquiry($db,$state,$body,$token);nodenoRespond(json_encode($result,JSON_THROW_ON_ERROR),201,'application/json; charset=utf-8',['Cache-Control'=>'no-store']);return true;}
  if($path!=='/api/commerce/quote'||$method!=='POST'){nodenoError(405,'method_not_allowed');return true;}
  $body=nodenoControlPublicBody();if(array_diff(array_keys($body),['items','country','currency','priceRevision','exchangeRevision']))throw new InvalidArgumentException('commerce_field_invalid');
  if(!is_array($body['items']??null)||!is_string($body['country']??null)||!is_string($body['currency']??null))throw new InvalidArgumentException('commerce_field_invalid');
  if(($body['priceRevision']??null)!==($state['catalog']['meta']['controlRevision']??0))throw new InvalidArgumentException('price_revision_changed');
  $fx=$body['currency']==='TRY'?null:nodenoFxSnapshot($state['storage']);if($fx&&($body['exchangeRevision']??null)!==$fx['revision'])throw new InvalidArgumentException('exchange_revision_changed');
  $result=nodenoCommerceQuote($state['catalog'],$body['items'],$body['country'],$body['currency'],$fx);nodenoRespond(json_encode($result,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE),200,'application/json; charset=utf-8',['Cache-Control'=>'no-store']);
 }catch(NodenoControlHttpError $e){nodenoError($e->status,$e->errorCode);}catch(InvalidArgumentException $e){nodenoError(str_ends_with($e->getMessage(),'_changed')?409:422,$e->getMessage());}catch(Throwable $e){nodenoError(503,'exchange_or_pricing_unavailable');}return true;
}
function nodenoDoorDefinitions(callable $f):array {
 return ['doorRequests'=>['label'=>'Kapı, kapak ve proje talepleri','group'=>'operations','fields'=>['title'=>$f('Talep','text',['readonly'=>true]),'company'=>$f('Firma','text',['readonly'=>true]),'name'=>$f('Yetkili / müşteri','text',['readonly'=>true]),'email'=>$f('E-posta','email',['readonly'=>true]),'phone'=>$f('Telefon','text',['readonly'=>true]),'country'=>$f('Teslimat ülkesi','text',['readonly'=>true]),'city'=>$f('Şehir','text',['readonly'=>true]),'requestSummary'=>$f('Talep anındaki ürün, ölçü ve uygulama seçimi','textarea',['readonly'=>true]),'buyerNote'=>$f('Müşteri notu','textarea',['readonly'=>true]),'status'=>$f('Durum','enum',['options'=>['open','in_progress','quoted','closed','cancelled'],'required'=>true]),'quoteTerms'=>$f('Teklif koşulları','textarea'),'note'=>$f('İç not','textarea')]]];
}
function nodenoDoorInquiry(PDO $db,array $state,array $body,string $visitor):array {
 if(array_diff(array_keys($body),['items','country','currency','priceRevision','exchangeRevision','contact','consent','idempotencyKey','locale','website']))throw new InvalidArgumentException('door_inquiry_field_invalid');
 $key=$body['idempotencyKey']??'';if(!is_string($key)||!preg_match('/^[A-Za-z0-9_-]{16,100}$/D',$key)||($body['consent']??null)!==true||!empty($body['website']))throw new InvalidArgumentException('door_inquiry_invalid');
 $contact=$body['contact']??null;if(!is_array($contact)||array_diff(array_keys($contact),['name','company','email','phone','city','note']))throw new InvalidArgumentException('door_contact_invalid');
 $values=[];foreach(['name'=>200,'company'=>300,'email'=>254,'phone'=>60,'city'=>200,'note'=>3000]as $field=>$max){$value=$contact[$field]??'';if(!is_string($value)||strlen($value)>$max||preg_match('//u',$value)!==1||preg_match('/[\x00-\x08\x0b\x0c\x0e-\x1f]/',$value))throw new InvalidArgumentException('door_contact_invalid');$values[$field]=trim($value);}
 if(!$values['name']||!filter_var($values['email'],FILTER_VALIDATE_EMAIL)||!preg_match('/^[+0-9() .-]{7,60}$/D',$values['phone'])||!$values['city'])throw new InvalidArgumentException('door_contact_invalid');
 if(!in_array($body['locale']??null,NODENO_STORE_LOCALES,true)||!is_string($body['country']??null)||!is_string($body['currency']??null)||!is_array($body['items']??null))throw new InvalidArgumentException('door_inquiry_invalid');
 $catalog=$state['catalog'];$hash=hash('sha256',json_encode($body,JSON_THROW_ON_ERROR));$keyHash=hash_hmac('sha256','doors|'.$visitor.'|'.$key,nodenoControlKey($state['storage']));
 $q=$db->prepare('SELECT request_hash,response_json FROM control_commands WHERE key_hash=?');$q->execute([$keyHash]);
 if($old=$q->fetch()){if(!hash_equals($old['request_hash'],$hash))throw new NodenoControlHttpError(409,'idempotency_conflict');return json_decode($old['response_json'],true,8,JSON_THROW_ON_ERROR);}
 if(($body['priceRevision']??null)!==($catalog['meta']['controlRevision']??0))throw new InvalidArgumentException('price_revision_changed');
 $fx=$body['currency']==='TRY'?null:nodenoFxSnapshot($state['storage']);if($fx&&($body['exchangeRevision']??null)!==$fx['revision'])throw new InvalidArgumentException('exchange_revision_changed');
 $quote=nodenoCommerceQuote($catalog,$body['items'],$body['country'],$body['currency'],$fx);if(!$quote['minimumEligible'])throw new InvalidArgumentException('door_minimum_not_reached');
 return nodenoControlTransaction($db,static function()use($db,$state,$body,$values,$catalog,$hash,$keyHash,$quote):array{
  $q=$db->prepare('SELECT request_hash,response_json FROM control_commands WHERE key_hash=?');$q->execute([$keyHash]);if($old=$q->fetch()){if(!hash_equals($old['request_hash'],$hash))throw new NodenoControlHttpError(409,'idempotency_conflict');return json_decode($old['response_json'],true,8,JSON_THROW_ON_ERROR);}
  $summary=[];foreach($quote['lines']as $line){if(!in_array($line['productType'],['door','door-profile','cabinet-front','cabinet-profile'],true))throw new InvalidArgumentException('door_products_only');$summary[]=($line['name']['tr']??$line['code']).' · '.($line['variant']['tr']??'').' · '.$line['quantity'].' '.($line['saleUnit']==='set'?'takım':'adet').(isset($line['options'])?"\n".json_encode($line['options'],JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE):'');}
  $id=nodenoControlId('door_');$now=time();$data=['title'=>($values['company']?:$values['name']).' · '.$body['country'],'name'=>$values['name'],'company'=>$values['company'],'email'=>$values['email'],'phone'=>$values['phone'],'city'=>$values['city'],'country'=>$body['country'],'buyerNote'=>$values['note'],'locale'=>$body['locale'],'requestSummary'=>implode("\n\n",$summary),'quoteSnapshot'=>$quote,'lines'=>$quote['lines'],'status'=>'open','consentAt'=>$now];
  $json=json_encode($data,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE);$db->prepare('INSERT INTO control_records(resource,id,data_json,created_at,updated_at) VALUES(?,?,?,?,?)')->execute(['doorRequests',$id,$json,$now,$now]);$db->prepare('INSERT INTO control_record_versions(resource,record_id,version,data_json,actor_id,created_at) VALUES(?,?,?,?,?,?)')->execute(['doorRequests',$id,1,$json,'public-door',$now]);nodenoControlAudit($db,$state['storage'],'public-door','inquiry','doorRequests',$id,['lines'=>count($quote['lines']),'country'=>$body['country']]);
  $result=['reference'=>$id];$db->prepare('INSERT INTO control_commands(key_hash,actor_id,request_hash,response_json,created_at) VALUES(?,?,?,?,?)')->execute([$keyHash,'public-door',$hash,json_encode($result,JSON_THROW_ON_ERROR),$now]);return $result;
 });
}
