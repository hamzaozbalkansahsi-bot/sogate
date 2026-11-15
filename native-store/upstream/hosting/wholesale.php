<?php
declare(strict_types=1);
require_once __DIR__.'/localization.php';
require_once __DIR__.'/control-store.php';
require_once __DIR__.'/furniture-sets.php';

/** Commercial packs are not the component cartons of a flat-pack item. */
function nodenoWholesaleDefinitions(callable $f):array {
 $fields=['productId'=>$f('Ürün ve renk','product',['required'=>true]),'enabled'=>$f('Toplu teklif kabul et','boolean'),'unitsPerPack'=>$f('Bir ticari paketteki ürün adedi','integer',['min'=>1,'max'=>1000]),'packsPerPallet'=>$f('Bir paletteki ticari paket sayısı','integer',['min'=>1,'max'=>1000]),'minimumQuantity'=>$f('Asgari adet / takım','integer',['min'=>1,'max'=>10000]),'minimumPacks'=>$f('Asgari paket alımı','integer',['min'=>1,'max'=>10000]),'minimumPallets'=>$f('Asgari palet alımı','integer',['min'=>1,'max'=>10000]),'currency'=>$f('Toptan fiyat para birimi','enum',['options'=>['TRY','EUR','USD','GBP']])];
 foreach(['unitsPerPack','packsPerPallet','minimumPacks','minimumPallets'] as $legacy)$fields[$legacy]['hidden']=true;
 for($i=1;$i<=3;$i++){$fields['tier'.$i.'Units']=$f('Kademe '.$i.' · en az ürün adedi','integer',['min'=>1,'max'=>10000000]);$fields['tier'.$i.'PriceMinor']=$f('Kademe '.$i.' · ürün başına fiyat','money',['min'=>1,'max'=>100000000]);}
 $fields['minimumDays']=$f('Doğrulanmış en az hazırlık günü','integer',['min'=>1,'max'=>365]);$fields['maximumDays']=$f('Doğrulanmış en fazla hazırlık günü','integer',['min'=>1,'max'=>365]);
 return ['wholesale'=>['label'=>'Toptan adet, takım ve fiyat','group'=>'catalog','publish'=>true,'fields'=>$fields],
 'wholesaleRequests'=>['label'=>'Yurt dışı toplu teklifler','group'=>'operations','fields'=>[
 'title'=>$f('Talep','text',['readonly'=>true]),'company'=>$f('Firma','text',['readonly'=>true]),'name'=>$f('Yetkili','text',['readonly'=>true]),'email'=>$f('E-posta','email',['readonly'=>true]),'phone'=>$f('Telefon','text',['readonly'=>true]),'country'=>$f('Teslimat ülkesi','text',['readonly'=>true]),'city'=>$f('Şehir / bölge','text',['readonly'=>true]),'requestSummary'=>$f('Talep anındaki takım içeriği ve ürünler','textarea',['readonly'=>true]),'buyerNote'=>$f('Alıcının teslimat notu','textarea',['readonly'=>true]),'status'=>$f('Durum','enum',['options'=>['open','in_progress','quoted','closed','cancelled'],'required'=>true]),'quoteTerms'=>$f('Hazırlanan teklif koşulları','textarea'),'note'=>$f('İç not','textarea')]]];
}
function nodenoWholesalePrepare(string $resource,?array $old,array $data,string $id):array {
 if($resource==='wholesale'){
  foreach(['unitsPerPack','packsPerPallet','minimumPacks','minimumPallets'] as $legacy)if(!isset($data[$legacy])&&isset($old['data'][$legacy]))$data[$legacy]=$old['data'][$legacy];
  if(($data['productId']??'')!==$id)throw new NodenoControlHttpError(422,'wholesale_product_id_required');
  if(isset($data['packsPerPallet'])&&!isset($data['unitsPerPack']))throw new NodenoControlHttpError(422,'pack_capacity_required');
  $previousUnits=0;$previousPrice=PHP_INT_MAX;$gap=false;
  for($i=1;$i<=3;$i++){$units=$data['tier'.$i.'Units']??null;$price=$data['tier'.$i.'PriceMinor']??null;if($units===null&&$price===null){$gap=true;continue;}if($gap||$units===null||$price===null||empty($data['currency'])||$units<=$previousUnits||$price>$previousPrice)throw new NodenoControlHttpError(422,'wholesale_tiers_invalid');$previousUnits=$units;$previousPrice=$price;}
  if(isset($data['minimumDays'],$data['maximumDays'])&&$data['minimumDays']>$data['maximumDays'])throw new NodenoControlHttpError(422,'wholesale_days_invalid');
 }
 if($resource==='wholesaleRequests'){
  if(!$old)throw new NodenoControlHttpError(422,'inquiry_public_flow_required');
  if(($data['status']??'')==='quoted'&&empty($data['quoteTerms']))throw new NodenoControlHttpError(422,'quote_terms_required');
  $immutable=$old['data'];unset($immutable['status'],$immutable['quoteTerms'],$immutable['note']);$data=array_merge($immutable,$data);
 }
 return $data;
}
function nodenoWholesaleProjection(PDO $db,array $catalog):array {
 $visible=array_fill_keys(array_map('strval',array_column($catalog['products'],'id')),true);$products=[];
 foreach(nodenoControlPublished($db,'wholesale') as $row)if(isset($visible[$row['id']]))$products[]=$row['data'];
 return ['compositionVersion'=>$catalog['meta']['furnitureSetsVersion']??'','revision'=>(int)nodenoControlSetting($db,'public_revision',0),'products'=>$products,'countries'=>nodenoWholesaleCountries(),'checkoutEnabled'=>false];
}
function nodenoWholesaleCountries():array {
 $codes=explode(' ','AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH BI BJ BL BM BN BO BQ BR BS BT BV BW BY BZ CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ DE DJ DK DM DO DZ EC EE EG EH ER ES ET FI FJ FK FM FO FR GA GB GD GE GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY HK HM HN HR HT HU ID IE IL IM IN IO IQ IR IS IT JE JM JO JP KE KG KH KI KM KN KP KR KW KY KZ LA LB LC LI LK LR LS LT LU LV LY MA MC MD ME MF MG MH MK ML MM MN MO MP MQ MR MS MT MU MV MW MX MY MZ NA NC NE NF NG NI NL NO NP NR NU NZ OM PA PE PF PG PH PK PL PM PN PR PS PT PW PY QA RE RO RS RU RW SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR SS ST SV SX SY SZ TC TD TF TG TH TJ TK TL TM TN TO TT TV TW TZ UA UG UM US UY UZ VA VC VE VG VI VN VU WF WS YE YT ZA ZM ZW');$names=nodenoControlCountries();$result=[];foreach($codes as $code)$result[$code]=$names[$code]??$code;return $result;
}
function nodenoWholesaleText(array $body,string $key,int $max,bool $required=true):string {
 $value=$body[$key]??'';if(!is_string($value)||strlen($value)>$max||preg_match('//u',$value)!==1||preg_match('/[\x00-\x08\x0b\x0c\x0e-\x1f]/',$value))throw new NodenoControlHttpError(422,'inquiry_field_invalid');$value=trim($value);if($required&&$value==='')throw new NodenoControlHttpError(422,'required_'.$key);return $value;
}
function nodenoWholesaleRequest(PDO $db,string $root,array $catalog,array $body,string $visitor):array {
 $allowed=['idempotencyKey','revision','company','name','email','phone','country','city','consent','locale','items','sets','compositionVersion','note','website'];foreach($body as $key=>$value)if(!in_array($key,$allowed,true))throw new NodenoControlHttpError(422,'inquiry_field_invalid');
 $key=$body['idempotencyKey']??'';if(!is_string($key)||!preg_match('/^[A-Za-z0-9_-]{16,100}$/D',$key))throw new NodenoControlHttpError(422,'idempotency_key_required');
 if(($body['consent']??null)!==true||!empty($body['website']))throw new NodenoControlHttpError(422,'consent_required');
 $company=nodenoWholesaleText($body,'company',300);$name=nodenoWholesaleText($body,'name',200);$email=nodenoWholesaleText($body,'email',254);$phone=nodenoWholesaleText($body,'phone',60);$country=nodenoWholesaleText($body,'country',2);$city=nodenoWholesaleText($body,'city',200);$note=nodenoWholesaleText($body,'note',3000,false);$locale=$body['locale']??'tr';
 if(!filter_var($email,FILTER_VALIDATE_EMAIL))throw new NodenoControlHttpError(422,'email_invalid');if(!isset(nodenoWholesaleCountries()[$country]))throw new NodenoControlHttpError(422,'international_country_required');if(!in_array($locale,NODENO_STORE_LOCALES,true))throw new NodenoControlHttpError(422,'locale_invalid');

 $requestHash=hash('sha256',json_encode($body,JSON_THROW_ON_ERROR));$keyHash=hash_hmac('sha256','wholesale|'.$visitor.'|'.$key,nodenoControlKey($root));
 return nodenoControlTransaction($db,static function()use($db,$root,$catalog,$body,$visitor,$company,$name,$email,$phone,$country,$city,$note,$locale,$requestHash,$keyHash):array {
  $q=$db->prepare('SELECT * FROM control_commands WHERE key_hash=?');$q->execute([$keyHash]);$old=$q->fetch();if($old){if(!hash_equals($old['request_hash'],$requestHash))throw new NodenoControlHttpError(409,'idempotency_conflict');return json_decode($old['response_json'],true,8,JSON_THROW_ON_ERROR);}
  $projection=nodenoWholesaleProjection($db,$catalog);if(!is_int($body['revision']??null)||$body['revision']!==$projection['revision'])throw new NodenoControlHttpError(409,'wholesale_revision_changed');
  $lines=nodenoWholesaleResolveLines($db,$catalog,$body);$doorCount=0;$byId=array_column($catalog['products'],null,'id');foreach($lines as $line)if(in_array($byId[$line['productId']??'']['productType']??'',['door','door-profile','cabinet-front','cabinet-profile'],true))throw new NodenoControlHttpError(422,'project_configuration_required');foreach($lines as $line)if(($byId[$line['productId']??'']['productType']??'')==='door')$doorCount+=$line['quantity'];if($doorCount>0&&$doorCount<10)throw new NodenoControlHttpError(422,'door_minimum_not_reached');$id=nodenoControlId('rfq_');$now=time();$summary=array_map('nodenoWholesaleLineSummary',$lines);
  $data=['title'=>$company.' · '.$country,'company'=>$company,'name'=>$name,'email'=>$email,'phone'=>$phone,'country'=>$country,'city'=>$city,'buyerNote'=>$note,'locale'=>$locale,'requestSummary'=>implode("\n\n",$summary),'lines'=>$lines,'status'=>'open','consentAt'=>$now,'priceRevision'=>$projection['revision'],'compositionVersion'=>$catalog['meta']['furnitureSetsVersion']??''];
  $json=json_encode($data,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE);$db->prepare('INSERT INTO control_records(resource,id,data_json,created_at,updated_at) VALUES(?,?,?,?,?)')->execute(['wholesaleRequests',$id,$json,$now,$now]);$db->prepare('INSERT INTO control_record_versions(resource,record_id,version,data_json,actor_id,created_at) VALUES(?,?,?,?,?,?)')->execute(['wholesaleRequests',$id,1,$json,'public-wholesale',$now]);nodenoControlAudit($db,$root,'public-wholesale','inquiry','wholesaleRequests',$id,['lines'=>count($lines),'country'=>$country]);
  $result=['reference'=>$id];$db->prepare('INSERT INTO control_commands(key_hash,actor_id,request_hash,response_json,created_at) VALUES(?,?,?,?,?)')->execute([$keyHash,'public-wholesale',$requestHash,json_encode($result,JSON_THROW_ON_ERROR),$now]);return $result;
 });
}
function nodenoWholesaleHandle(string $path,string $method,array $catalog,string $root):bool {
 if($path!=='/api/wholesale'&&$path!=='/api/wholesale/inquiries')return false;
 try{$db=nodenoControlDatabase($root);
  if($path==='/api/wholesale'&&$method==='GET'){$token=$_COOKIE['NODENOQUOTE']??'';if(!is_string($token)||!preg_match('/^[a-f0-9]{64}$/D',$token)){$token=bin2hex(random_bytes(32));$local=PHP_SAPI==='cli-server'&&in_array($_SERVER['REMOTE_ADDR']??'',['127.0.0.1','::1'],true);setcookie('NODENOQUOTE',$token,['path'=>'/','secure'=>!$local,'httponly'=>true,'samesite'=>'Strict']);}nodenoAccountJson(nodenoWholesaleProjection($db,$catalog));return true;}
  if($path!=='/api/wholesale/inquiries'||$method!=='POST')throw new NodenoControlHttpError(405,'method_not_allowed');$body=nodenoControlPublicBody();$token=$_COOKIE['NODENOQUOTE']??null;if(!is_string($token)||!preg_match('/^[a-f0-9]{64}$/D',$token))throw new NodenoControlHttpError(403,'inquiry_session_required');nodenoControlRate($db,$root,'wholesale',$_SERVER['REMOTE_ADDR']??'',12,3600);nodenoAccountJson(nodenoWholesaleRequest($db,$root,$catalog,$body,$token),201);
 }catch(NodenoControlHttpError $e){nodenoAccountJson(['error'=>$e->errorCode],$e->status,$e->headers);}catch(Throwable $e){error_log('NODENO wholesale '.get_class($e));nodenoAccountJson(['error'=>'service_unavailable'],503);}return true;
}
