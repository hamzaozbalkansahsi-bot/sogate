<?php
declare(strict_types=1);
require_once __DIR__.'/localization.php';
require_once __DIR__.'/control-auth.php';
require_once __DIR__.'/wholesale.php';
require_once __DIR__.'/suppliers.php';

/** Explicit field contracts drive both validation and the operator forms. */
function nodenoControlDefinitions():array {
 $f=static fn(string $label,string $type='text',array $extra=[]):array=>array_merge(['label'=>$label,'type'=>$type],$extra);
 $locale=[];foreach(['tr'=>'Türkçe','en'=>'İngilizce','ru'=>'Rusça','ar'=>'Arapça','de'=>'Almanca','az'=>'Azerbaycanca','kk'=>'Kazakça','tk'=>'Türkmence','uz'=>'Özbekçe','ky'=>'Kırgızca','fa'=>'Farsça'] as $lang=>$label){$locale['title_'.$lang]=$f('Ürün adı · '.$label);$locale['description_'.$lang]=$f('Açıklama · '.$label,'textarea');$locale['seoTitle_'.$lang]=$f('SEO başlığı · '.$label);$locale['seoDescription_'.$lang]=$f('SEO açıklaması · '.$label,'textarea');}
 $definitions=[
  'business'=>['label'=>'Firma ve vergi ayarları','group'=>'settings','singleton'=>true,'fields'=>['legalName'=>$f('Yasal firma unvanı'),'taxId'=>$f('Vergi numarası'),'taxOffice'=>$f('Vergi dairesi'),'address'=>$f('Firma adresi','textarea'),'country'=>$f('Ülke','country'),'email'=>$f('Firma e-postası','email'),'priceTaxPolicy'=>$f('Katalog fiyatlarının vergi esası','enum',['options'=>['vat_included','vat_excluded'],'required'=>true])]],
  'products'=>['label'=>'Ürünler ve fiyatlar','group'=>'catalog','publish'=>true,'fields'=>array_merge($locale,['priceMinor'=>$f('Satış fiyatı (TRY)','money'),'visible'=>$f('Vitrinde göster','boolean'),'stockKnown'=>$f('Stok miktarı doğrulandı','boolean'),'stockQuantity'=>$f('Stok adedi','integer',['max'=>1000000]),'weight'=>$f('Öneri önceliği','integer',['max'=>100])])],
  'campaigns'=>['label'=>'Kampanyalar','group'=>'marketing','publish'=>true,'fields'=>['title'=>$f('Kampanya adı','text',['required'=>true]),'productIds'=>$f('Ürünler','products',['required'=>true]),'percent'=>$f('İndirim oranı','integer',['min'=>1,'max'=>90,'required'=>true]),'startsAt'=>$f('Başlangıç','datetime',['required'=>true]),'endsAt'=>$f('Bitiş','datetime',['required'=>true]),'enabled'=>$f('Kampanyayı etkinleştir','boolean')]],
  'coupons'=>['label'=>'Kuponlar','group'=>'marketing','publish'=>true,'fields'=>['title'=>$f('Kupon adı','text',['required'=>true]),'code'=>$f('Kupon kodu','text',['required'=>true]),'percent'=>$f('İndirim oranı','integer',['min'=>1,'max'=>90]),'minimumMinor'=>$f('Asgari sepet tutarı','money'),'limit'=>$f('Kullanım sınırı','integer',['min'=>1]),'startsAt'=>$f('Başlangıç','datetime'),'endsAt'=>$f('Bitiş','datetime'),'enabled'=>$f('Etkin','boolean')]],
  'collections'=>['label'=>'Koleksiyonlar','group'=>'catalog','publish'=>true,'fields'=>['title'=>$f('Koleksiyon adı','text',['required'=>true]),'description'=>$f('Açıklama','textarea'),'productIds'=>$f('Koleksiyondaki ürünler','products',['required'=>true]),'cover'=>$f('Kapak görseli','media',['required'=>true]),'position'=>$f('Sıralama','integer',['max'=>1000]),'enabled'=>$f('Vitrinde göster','boolean')]],
  'appearance'=>['label'=>'Vitrin düzeni','group'=>'settings','publish'=>true,'singleton'=>true,'fields'=>['heroProductId'=>$f('Ana vitrin ürünü','product'),'heroTitle_tr'=>$f('Vitrin başlığı · Türkçe'),'heroTitle_en'=>$f('Vitrin başlığı · İngilizce'),'heroTitle_ru'=>$f('Vitrin başlığı · Rusça'),'heroTitle_ar'=>$f('Vitrin başlığı · Arapça'),'heroBody_tr'=>$f('Vitrin açıklaması · Türkçe','textarea'),'heroBody_en'=>$f('Vitrin açıklaması · İngilizce','textarea'),'heroBody_ru'=>$f('Vitrin açıklaması · Rusça','textarea'),'heroBody_ar'=>$f('Vitrin açıklaması · Arapça'),'enabled'=>$f('Özel vitrin ayarlarını kullan','boolean')]],
  'seo'=>['label'=>'Arama motorları','group'=>'settings','publish'=>true,'singleton'=>true,'fields'=>['homeTitle_tr'=>$f('Ana sayfa başlığı · Türkçe'),'homeTitle_en'=>$f('Ana sayfa başlığı · İngilizce'),'homeTitle_ru'=>$f('Ana sayfa başlığı · Rusça'),'homeTitle_ar'=>$f('Ana sayfa başlığı · Arapça'),'homeDescription_tr'=>$f('Ana sayfa açıklaması · Türkçe','textarea'),'homeDescription_en'=>$f('Ana sayfa açıklaması · İngilizce','textarea'),'homeDescription_ru'=>$f('Ana sayfa açıklaması · Rusça','textarea'),'homeDescription_ar'=>$f('Ana sayfa açıklaması · Arapça','textarea'),'googleVerification'=>$f('Google doğrulama değeri'),'bingVerification'=>$f('Bing doğrulama değeri'),'yandexVerification'=>$f('Yandex doğrulama değeri')]],
  'markets'=>['label'=>'Ülkeler ve satış koşulları','group'=>'settings','publish'=>true,'fields'=>['country'=>$f('Ülke','country',['required'=>true]),'title'=>$f('Pazar adı','text',['required'=>true]),'language'=>$f('İçerik dili','enum',['options'=>NODENO_STORE_LOCALES,'required'=>true]),'enabled'=>$f('Satışa hazır','boolean'),'delivery'=>$f('Doğrulanmış teslimat koşulları','textarea'),'returns'=>$f('İade koşulları','textarea'),'taxes'=>$f('Vergi ve gümrük bilgisi','textarea')]],
  'ranking'=>['label'=>'Ürün öneri ayarları','group'=>'settings','publish'=>true,'singleton'=>true,'fields'=>['views'=>$f('Ürün görüntüleme ağırlığı','integer',['max'=>100]),'cart'=>$f('Sepete ekleme ağırlığı','integer',['max'=>100]),'favorites'=>$f('Favori ağırlığı','integer',['max'=>100]),'days'=>$f('Değerlendirme dönemi (gün)','integer',['min'=>1,'max'=>90])]],
 ];
 forEach(['appearance'=>['heroTitle','heroBody'],'seo'=>['homeTitle','homeDescription']]as $resource=>$prefixes)foreach(NODENO_NATIVE_LOCALES as $lang)foreach($prefixes as $prefix)$definitions[$resource]['fields'][$prefix.'_'.$lang]=$f($prefix.' · '.$lang,str_contains($prefix,'Body')||str_contains($prefix,'Description')?'textarea':'text');
 if(function_exists('nodenoControlOperationDefinitions'))$definitions=array_merge($definitions,nodenoControlOperationDefinitions($f));if(function_exists('nodenoDoorDefinitions'))$definitions=array_merge($definitions,nodenoDoorDefinitions($f));return array_merge($definitions,nodenoWholesaleDefinitions($f));
}
/** Unknown customer copy is kept as a draft until native translations exist. */
function nodenoControlNativePublication(string $resource,array $data):void {
 $prefixes=match($resource){'products'=>['title','description','seoTitle','seoDescription'],'appearance'=>['heroTitle','heroBody'],'seo'=>['homeTitle','homeDescription'],default=>[]};
 foreach($prefixes as $prefix){$source=$data[$prefix.'_en']??'';if($source==='')continue;foreach(NODENO_NATIVE_LOCALES as $locale){
  if(trim($data[$prefix.'_'.$locale]??'')!=='')continue;
  try{nodenoNativeText($source,$locale);}catch(Throwable $error){throw new NodenoControlHttpError(422,'native_translation_required');}
 }}
}
function nodenoControlCountries():array {return ['TR'=>'Türkiye','DE'=>'Almanya','GB'=>'Birleşik Krallık','KZ'=>'Kazakistan','TM'=>'Türkmenistan','AZ'=>'Azerbaycan','IQ'=>'Irak','SY'=>'Suriye','IR'=>'İran','UZ'=>'Özbekistan','KG'=>'Kırgızistan'];}
function nodenoControlRead(PDO $db,string $resource,string $id):?array {$q=$db->prepare('SELECT * FROM control_records WHERE resource=? AND id=?');$q->execute([$resource,$id]);$row=$q->fetch();return $row?['id'=>$row['id'],'data'=>json_decode($row['data_json'],true),'version'=>(int)$row['version'],'publishedVersion'=>(int)$row['published_version'],'updatedAt'=>(int)$row['updated_at'],'publishedAt'=>$row['published_at']?(int)$row['published_at']:null]:null;}
function nodenoControlPublished(PDO $db,string $resource):array {$q=$db->prepare('SELECT id,published_json,published_at FROM control_records WHERE resource=? AND published_version>0 ORDER BY id');$q->execute([$resource]);return array_map(static fn($r)=>['id'=>$r['id'],'data'=>json_decode($r['published_json'],true),'publishedAt'=>(int)$r['published_at']],$q->fetchAll());}
function nodenoControlAuthoriseResource(array $ctx,string $resource,string $method):array {
 $definition=nodenoControlDefinitions()[$resource]??null;
 if(!$definition)throw new NodenoControlHttpError(404,'resource_unknown');
 if($resource==='business')nodenoControlRequire($ctx,'integrations.read',$method!=='GET');
 nodenoControlRequire($ctx,$definition['group'].($method==='GET'?'.read':'.write'),in_array($method,['PUBLISH','UNPUBLISH','SAVE_PUBLISH'],true));
 return $definition;
}
function nodenoControlOrderCatalog(PDO $db,array $catalog,?array $old,array $body):array {
 $state=nodenoControlPublicState($db,$catalog,[]);$live=$state['catalog'];
 if(isset($body['refreshPrices'])&&!is_bool($body['refreshPrices']))throw new NodenoControlHttpError(422,'refresh_prices_invalid');
 $refresh=$body['refreshPrices']??false;$snapshots=array_column($old['data']['items']??[],null,'productId');$items=$body['data']['items']??null;
 if(!is_array($items))throw new NodenoControlHttpError(422,'items_invalid');
 $usesCurrentPrices=$old===null||$refresh;
 foreach($items as $item){if(!is_array($item)||!is_string($item['productId']??null))throw new NodenoControlHttpError(422,'item_invalid');if(!isset($snapshots[$item['productId']]))$usesCurrentPrices=true;}
 if($usesCurrentPrices&&(!is_int($body['priceRevision']??null)||$body['priceRevision']!==$state['revision']))throw new NodenoControlHttpError(409,'price_revision_changed');
 if($refresh||!$old)return $live;
 $present=[];
 foreach($live['products'] as &$product){$id=$product['id'];$present[$id]=true;if(isset($snapshots[$id])){$s=$snapshots[$id];$product['salePriceMinor']=$s['unitPriceMinor'];$product['currency']='TRY';$product['code']=$s['code'];$product['name']['tr']=$s['title'];}}unset($product);
 foreach($snapshots as $snapshot)if(!isset($present[$snapshot['productId']]))$live['products'][]=['id'=>$snapshot['productId'],'code'=>$snapshot['code'],'name'=>['tr'=>$snapshot['title']],'currency'=>'TRY','salePriceMinor'=>$snapshot['unitPriceMinor']];
 return $live;
}
function nodenoControlValidate(string $resource,array $data,array $catalog):array {
 $def=nodenoControlDefinitions()[$resource]??null;if(!$def)throw new NodenoControlHttpError(404,'resource_unknown');$fields=$def['fields'];$byId=array_column($catalog['products'],null,'id');$out=[];
 foreach($data as $key=>$value){if(!isset($fields[$key]))throw new NodenoControlHttpError(422,'field_not_allowed');$field=$fields[$key];$type=$field['type'];if(!empty($field['readonly']))continue;
  if($type==='items'){if(!is_array($value))throw new NodenoControlHttpError(422,'items_invalid');$computed=nodenoControlItems($value,$catalog);$out['totalMinor']=$computed['totalMinor'];$value=$computed['items'];}
  elseif($type==='boolean'){if(!is_bool($value))throw new NodenoControlHttpError(422,'boolean_required');}
  elseif(in_array($type,['money','integer','datetime'],true)){if($value===null&&empty($field['required']))continue;if(!is_int($value)||$value<($field['min']??0)||$value>($field['max']??($type==='money'?10000000000:4102444800)))throw new NodenoControlHttpError(422,'number_invalid');}
  else {if(!is_string($value)||preg_match('//u',$value)!==1||strlen($value)>($type==='products'?max(2000,count($byId)*101):($type==='textarea'?12000:2000))||preg_match('/[\x00-\x08\x0b\x0c\x0e-\x1f]/',$value))throw new NodenoControlHttpError(422,'text_invalid');$value=trim($value);if($type==='enum'&&!in_array($value,$field['options'],true))throw new NodenoControlHttpError(422,'option_invalid');if($type==='country'&&!isset(nodenoControlCountries()[$value]))throw new NodenoControlHttpError(422,'country_invalid');if($type==='product'&&$value!==''&&!isset($byId[$value]))throw new NodenoControlHttpError(422,'product_unknown');if($type==='products'){$ids=array_values(array_unique(array_filter(array_map('trim',explode(',',$value)),static fn($id)=>$id!=='')));$value=implode(',',$ids);foreach($ids as $id)if(!isset($byId[$id]))throw new NodenoControlHttpError(422,'product_unknown');}if($type==='media'&&$value!==''){if(!preg_match('~^/media/([A-Za-z0-9_-]+)/(0|[1-9][0-9]{0,3})$~D',$value,$m)||!in_array($value,$byId[$m[1]]['images']??[],true))throw new NodenoControlHttpError(422,'media_not_approved');}if($type==='email'&&$value!==''&&!filter_var($value,FILTER_VALIDATE_EMAIL))throw new NodenoControlHttpError(422,'email_invalid');if($type==='url'&&$value!==''){if(!filter_var($value,FILTER_VALIDATE_URL)||parse_url($value,PHP_URL_SCHEME)!=='https'||parse_url($value,PHP_URL_USER)||parse_url($value,PHP_URL_PASS))throw new NodenoControlHttpError(422,'https_url_required');}}
  $out[$key]=$value;
 }
 foreach($fields as $key=>$field)if(!empty($field['required'])&&(!isset($out[$key])||$out[$key]===''))throw new NodenoControlHttpError(422,'required_'.$key);
 if(isset($out['startsAt'],$out['endsAt'])&&$out['endsAt']<=$out['startsAt'])throw new NodenoControlHttpError(422,'date_range_invalid');if($resource==='markets'&&($out['enabled']??false)&&(!$out['delivery']||!$out['returns']||!$out['taxes']))throw new NodenoControlHttpError(422,'market_conditions_required');return $out;
}
function nodenoControlResource(array $ctx,string $resource,string $id,string $method,array $body,array $catalog,array $config=[]):array {
 $def=nodenoControlAuthoriseResource($ctx,$resource,$method);$actor=$ctx['user'];$db=$ctx['db'];$root=$ctx['root'];
 if($method==='SAVE_PUBLISH'){
  if(empty($def['publish']))throw new NodenoControlHttpError(422,'publication_unavailable');
  return nodenoControlTransaction($db,static function()use($ctx,$resource,$id,$body,$catalog):array{
   $saved=nodenoControlResource($ctx,$resource,$id,'PUT',$body,$catalog);
   return nodenoControlResource($ctx,$resource,$saved['data']['id'],'PUBLISH',['version'=>$saved['data']['version']],$catalog);
  });
 }
 if($method==='GET'){
  $source=nodenoControlSourceRecords($resource,$catalog,$config);
  if($source){$rows=nodenoControlMergeRecords($source,nodenoControlStoredRows($db,$resource));if($id!=='')return ['data'=>$rows[$id]??null];return ['data'=>array_values($rows)];}
  if($id!==''){$row=nodenoControlRead($db,$resource,$id);return ['data'=>$resource==='campaigns'&&$row?nodenoControlCampaignView($db,$row,$catalog):$row];}
  $q=$db->prepare('SELECT id FROM control_records WHERE resource=? ORDER BY updated_at DESC LIMIT 2000');$q->execute([$resource]);
  $ids=$q->fetchAll();$live=$resource==='campaigns'?array_column(nodenoControlPublicState($db,$catalog,[])['catalog']['products'],null,'id'):null;
  return ['data'=>array_map(static function($r)use($db,$resource,$catalog,$live){$row=nodenoControlRead($db,$resource,$r['id']);return $resource==='campaigns'?nodenoControlCampaignView($db,$row,$catalog,$live):$row;},$ids)];
 }
 if(!in_array($method,['PUT','PUBLISH','UNPUBLISH'],true))throw new NodenoControlHttpError(405,'method_not_allowed');
 if($id==='')$id=nodenoControlId('r_');
 if(!preg_match('/^[A-Za-z0-9_-]{1,100}$/D',$id))throw new NodenoControlHttpError(422,'id_invalid');
 if(!empty($def['singleton'])&&$id!=='default')throw new NodenoControlHttpError(422,'singleton_required');
 if($resource==='products'&&!in_array($id,array_column($catalog['products'],'id'),true))throw new NodenoControlHttpError(422,'product_unknown');
 return nodenoControlTransaction($db,static function()use($ctx,$db,$root,$actor,$def,$resource,$id,$method,$body,$catalog):array{
  $old=nodenoControlRead($db,$resource,$id);
  if(!is_int($body['version']??null)||$body['version']!==($old['version']??0))throw new NodenoControlHttpError(409,'version_conflict');
  $now=time();$version=($old['version']??0)+1;
  if($method==='PUT'){
   if(!is_array($body['data']??null))throw new NodenoControlHttpError(422,'data_required');
   $validationCatalog=$resource==='orders'?nodenoControlOrderCatalog($db,$catalog,$old,$body):$catalog;
   $defaults=nodenoControlSourceRecords($resource,$catalog,[])[$id]['data']??[];
   $data=nodenoControlValidate($resource,array_replace($defaults,$body['data']),$validationCatalog);
   $data=nodenoWholesalePrepare($resource,$old,$data,$id);
   if($defaults){$data=array_intersect_key($data,$body['data']);if($resource==='wholesale')$data['productId']=$id;}
   if($resource==='doorRequests'){if(!$old)throw new NodenoControlHttpError(422,'door_request_public_only');$immutable=$old['data'];unset($immutable['status'],$immutable['quoteTerms'],$immutable['note']);$data=array_merge($immutable,$data);}
   if(function_exists('nodenoControlOperationValidate'))nodenoControlOperationValidate($ctx,$resource,$old,$data);
   $json=json_encode($data,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE);
   $db->prepare('INSERT INTO control_records(resource,id,data_json,version,created_at,updated_at) VALUES(?,?,?,?,?,?) ON CONFLICT(resource,id) DO UPDATE SET data_json=excluded.data_json,version=excluded.version,updated_at=excluded.updated_at')->execute([$resource,$id,$json,$version,$now,$now]);
  }else{
   if(empty($def['publish'])||!$old)throw new NodenoControlHttpError(422,'publication_unavailable');
   $published=$method==='PUBLISH';
   if($published)nodenoControlNativePublication($resource,$old['data']);
   if($published&&$resource==='campaigns'){nodenoControlValidate($resource,$old['data'],$catalog);$bases=nodenoControlCampaignBases($db,$catalog);foreach(explode(',',$old['data']['productIds'])as $pid){$base=$bases[$pid]??null;if(is_int($base)&&$base>0&&intdiv($base*(100-$old['data']['percent'])+50,100)<1)throw new NodenoControlHttpError(422,'campaign_zero_price');}}
   if($published&&$old['publishedVersion']===$old['version'])throw new NodenoControlHttpError(409,'already_published');
   if(!$published&&$old['publishedVersion']===0)throw new NodenoControlHttpError(409,'not_published');
   $json=json_encode($old['data'],JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE);
   $db->prepare('UPDATE control_records SET version=?,updated_at=?,published_json=?,published_version=?,published_at=? WHERE resource=? AND id=?')->execute([$version,$now,$published?$json:null,$published?$version:0,$published?$now:null,$resource,$id]);
   nodenoControlSetSetting($db,'public_revision',(int)nodenoControlSetting($db,'public_revision',0)+1);
   if(function_exists('nodenoControlIndexNowQueue'))nodenoControlIndexNowQueue($db,$resource,$id,$old['data']);
   if($resource==='campaigns')foreach(array_filter(array_map('trim',explode(',',$old['data']['productIds']??''))) as $productId)nodenoControlSetSetting($db,'reference_suppressed:'.$productId,true);
   if($resource==='products'&&isset($old['data']['priceMinor'])){
    nodenoControlSetSetting($db,'reference_suppressed:'.$id,true);
    if($published){$history=nodenoControlSetting($db,'price_history:'.$id,[]);$history[]=['at'=>$now,'minor'=>$old['data']['priceMinor']];nodenoControlSetSetting($db,'price_history:'.$id,array_slice($history,-1000));}
   }
  }
  $db->prepare('INSERT INTO control_record_versions(resource,record_id,version,data_json,actor_id,created_at) VALUES(?,?,?,?,?,?)')->execute([$resource,$id,$version,$json,$actor['id'],$now]);
  nodenoControlAudit($db,$root,$actor['id'],strtolower($method),$resource,$id,['fromVersion'=>$old['version']??0,'toVersion'=>$version]);
  return ['data'=>nodenoControlRead($db,$resource,$id),'revision'=>(int)nodenoControlSetting($db,'public_revision',0)];
 });
}
function nodenoControlCampaignBases(PDO $db,array $catalog):array {
 $bases=[];foreach($catalog['products']as $p)$bases[$p['id']]=$p['salePriceMinor']??null;
 foreach(nodenoControlProductOverrides($db,$catalog)as $record)if(isset($record['data']['priceMinor']))$bases[$record['id']]=$record['data']['priceMinor'];return $bases;
}
function nodenoControlProductOverrides(PDO $db,array $catalog):array {
 $records=nodenoControlPublished($db,'products');$reset=$catalog['meta']['priceRefresh']??[];$ids=array_fill_keys($reset['productIds']??[],true);$at=$reset['effectiveAt']??0;
 foreach($records as &$record)if(isset($ids[$record['id']])&&$record['publishedAt']<$at)unset($record['data']['priceMinor']);unset($record);return $records;
}
function nodenoControlCampaignView(PDO $db,array $row,array $catalog,?array $live=null):array {
 $q=$db->prepare("SELECT published_json FROM control_records WHERE resource='campaigns' AND id=?");$q->execute([$row['id']]);$row['publishedData']=json_decode($q->fetchColumn()?:'null',true);$c=$row['publishedData'];$now=time();
 $status=!$c?'draft':(empty($c['enabled'])?'disabled':($c['startsAt']>$now?'scheduled':($c['endsAt']<=$now?'expired':'active')));
 $live=$live??array_column(nodenoControlPublicState($db,$catalog,[])['catalog']['products'],null,'id');$selected=$c?array_values(array_unique(array_filter(array_map('trim',explode(',',$c['productIds']??''))))):[];$products=[];$overridden=[];$eligible=0;$bases=nodenoControlCampaignBases($db,$catalog);$rates=[];
 if($status==='active')foreach(nodenoControlPublished($db,'campaigns')as $record){$offer=$record['data'];if(empty($offer['enabled'])||$offer['startsAt']>$now||$offer['endsAt']<=$now)continue;foreach(explode(',',$offer['productIds']??'')as $pid)$rates[$pid]=max($rates[$pid]??0,$offer['percent']);}
 foreach($selected as $id){$p=$live[$id]??null;$base=$bases[$id]??null;if(!$p||!is_int($base)||$base<1)continue;$eligible++;if($status!=='active')continue;$price=$p['salePriceMinor']??null;if(!is_int($price)||$price<1)continue;$r=['id'=>$id,'priceMinor'=>$price,'appliedPercent'=>$rates[$id]??0];if(($rates[$id]??0)>$c['percent'])$overridden[]=$r;else $products[]=$r;}
 if($status==='active'&&!$eligible)$status='no_eligible_products';
 $row['activity']=['status'=>$status,'at'=>$now,'selectedProducts'=>count($selected),'eligibleProducts'=>$eligible,'appliedProducts'=>count($products),'overriddenProducts'=>count($overridden),'products'=>$products,'strongerOffers'=>$overridden];return $row;
}
function nodenoControlPublicState(PDO $db,array $catalog,array $config):array {
 $suppressed=[];foreach($db->query("SELECT name FROM control_settings WHERE name LIKE 'reference_suppressed:%' AND value_json='true'")->fetchAll() as $row)$suppressed[substr($row['name'],strlen('reference_suppressed:'))]=true;
 $overrides=[];foreach(nodenoControlProductOverrides($db,$catalog) as $record)$overrides[$record['id']]=$record['data'];$campaigns=nodenoControlPublished($db,'campaigns');$now=time();$products=[];
 foreach($catalog['products'] as $p){$data=$overrides[$p['id']]??[];if(isset($data['visible'])&&!$data['visible'])continue;foreach(NODENO_STORE_LOCALES as $lang){foreach(['title'=>'name','description'=>'description','seoTitle'=>'seoTitle','seoDescription'=>'seoDescription'] as $field=>$target)if(!empty($data[$field.'_'.$lang]))$p[$target][$lang]=$data[$field.'_'.$lang];}
  foreach(NODENO_STORE_LOCALES as $lang)if(!empty($data['title_'.$lang]))$p['modelName'][$lang]=$data['title_'.$lang];
  if(isset($data['priceMinor'])){$p['salePriceMinor']=$data['priceMinor'];$p['salePrice']=$data['priceMinor']/100;$p['currency']='TRY';unset($p['previousPriceMinor'],$p['discountPercent']);}
  if(isset($data['stockKnown'])){$p['stockKnown']=$data['stockKnown'];$p['stockQuantity']=$data['stockKnown']?($data['stockQuantity']??0):null;}
  $base=$p['salePriceMinor']??null;$discount=0;foreach($campaigns as $campaign){$c=$campaign['data'];if(!empty($c['enabled'])&&$c['startsAt']<=$now&&$c['endsAt']>$now&&in_array($p['id'],array_map('trim',explode(',',$c['productIds']??'')),true))$discount=max($discount,$c['percent']);}
  if($discount&&is_int($base)&&$base>0&&intdiv($base*(100-$discount)+50,100)>0){$p['salePriceMinor']=intdiv($base*(100-$discount)+50,100);$p['salePrice']=$p['salePriceMinor']/100;unset($p['previousPriceMinor'],$p['discountPercent']);}
  if(isset($suppressed[$p['id']]))unset($p['previousPriceMinor'],$p['discountPercent']);
  $products[]=$p;
 }
 $catalog['products']=$products;if(($catalog['meta']['shippingPolicyVersion']??'')==='2026-11-12-included'){if(!function_exists('nodenoShippingCatalog'))require_once __DIR__.'/door-commerce.php';$catalog=nodenoShippingCatalog($catalog);}$revision=(int)nodenoControlSetting($db,'public_revision',0);if($revision)$catalog['meta']['controlRevision']=$revision;
 if($revision){foreach(['appearance','seo','ranking'] as $resource){$records=nodenoControlPublished($db,$resource);if($records)$config[$resource]=$records[0]['data'];}$config['collections']=nodenoControlPublished($db,'collections');$config['markets']=nodenoControlPublished($db,'markets');$config['controlRevision']=$revision;}$config['collections']=nodenoControlCollectionsProjection($db,$catalog,$config);$config['collectionsConfigured']=count($config['collections'])>0;$config['checkoutEnabled']=false;return ['catalog'=>$catalog,'config'=>$config,'revision'=>$revision];
}

/** Read the real starting values separately from the operator's sparse changes. */
function nodenoControlEditor(array $ctx,string $resource,string $id,array $catalog,array $config):array {
 nodenoControlAuthoriseResource($ctx,$resource,'GET');
 if(!in_array($resource,['products','business','ranking','collections','markets','wholesale'],true)||($resource==='business'&&$id!=='default'))throw new NodenoControlHttpError(404,'not_found');
 $record=nodenoControlRead($ctx['db'],$resource,$id)??['id'=>$id,'data'=>[],'version'=>0,'publishedVersion'=>0];$values=[];$inherited=[];
 if($resource==='products'){
  $product=null;foreach($catalog['products']??[]as $p)if($p['id']===$id){$product=$p;break;}
  if(!$product)throw new NodenoControlHttpError(404,'product_unknown');
  if(($product['productType']??'')==='supplier-item'&&!empty($product['supplierDetailsHash'])){
   require_once __DIR__.'/supplier-products.php';
   $details=nodenoSupplierDetails(__DIR__,$id,['products'=>[array_replace($product,['hidden'=>false,'published'=>true])]]);
   if($details)$product['description']=$details['description'];
  }
  require_once __DIR__.'/seo.php';
  foreach(NODENO_STORE_LOCALES as $lang){
   $values['title_'.$lang]=nodenoSeoName($product,$lang);$values['description_'.$lang]=nodenoLocaleLocal($product['description']??[],$lang);
   $color=empty($product['colorReviewPending'])?nodenoLocaleLocal($product['variantColor']??[],$lang):'';
   $values['seoTitle_'.$lang]=nodenoLocaleLocal($product['seoTitle']??[],$lang)?:nodenoSeoSearchName($product,$catalog,$lang).($color!==''?' - '.$color:'');
   $values['seoDescription_'.$lang]=nodenoLocaleLocal($product['seoDescription']??[],$lang)?:nodenoSeoDescription($product,$lang,$catalog);
  }
  if(is_int($product['salePriceMinor']??null))$values['priceMinor']=$product['salePriceMinor'];
  $values['visible']=($product['hidden']??false)!==true&&($product['published']??true)!==false;
  $values['stockKnown']=($product['stockKnown']??false)===true;
  if($values['stockKnown']&&is_int($product['stockQuantity']??null))$values['stockQuantity']=$product['stockQuantity'];
  $refresh=$catalog['meta']['priceRefresh']??[];
  if(in_array($id,$refresh['productIds']??[],true)&&($record['updatedAt']??0)<($refresh['effectiveAt']??0))unset($record['data']['priceMinor']);
 }elseif($resource==='business'){
  $seller=nodenoControlSetting($ctx['db'],'payment:stripe',[])['seller']??[];
  if(($seller['authorityConfirmed']??false)===true&&($seller['taxConfirmed']??false)===true){
   foreach(['name'=>'legalName','address'=>'address','email'=>'email']as $source=>$target)if(is_string($seller[$source]??null)&&trim($seller[$source])!==''){$values[$target]=$seller[$source];$inherited[]=$target;}
  }
 }
 if(!in_array($resource,['products','business'],true)){$source=nodenoControlSourceRecords($resource,$catalog,$config);if(!isset($source[$id])&&!$record['version'])throw new NodenoControlHttpError(404,'not_found');$values=$source[$id]['data']??[];}
 foreach($record['data']as $key=>$value)if($value!==''&&$value!==null)$values[$key]=$value;
 return ['record'=>$record,'values'=>$values,'inheritedFields'=>$inherited];
}

function nodenoControlRankingDefaults():array {return ['views'=>1,'cart'=>5,'favorites'=>3,'days'=>30];}
function nodenoControlSourceRecords(string $resource,array $catalog,array $config):array {
 $rows=[];$add=static function(string $id,array $data,array $meta=[])use(&$rows):void{$rows[$id]=array_merge(['id'=>$id,'data'=>$data,'version'=>0,'publishedVersion'=>0,'source'=>true],$meta);};
 if($resource==='ranking')$add('default',nodenoControlRankingDefaults());
 if($resource==='markets'){
  require_once __DIR__.'/visitor-market.php';
  foreach(nodenoControlCountries()as $country=>$title)$add($country,['country'=>$country,'title'=>$title,'language'=>nodenoInitialLocale(null,null,$country),'enabled'=>$country==='TR'||isset(nodenoWholesaleCountries()[$country]),'delivery'=>$country==='TR'?'Kargo veya ambar bedeli alıcı tarafından doğrudan taşıyıcıya ödenir.':'Teslimat ve taşıma koşulları ürün ve teslimat ülkesine göre teklif sırasında kesinleştirilir.','returns'=>'Satış ve iade belgelerinde yayımlanan koşullar geçerlidir.','taxes'=>$country==='TR'?'Vergi ürün türüne göre ödeme öncesinde hesaplanır.':'Vergi ve gümrük koşulları teslimat ülkesi ve teklif kapsamında belirlenir.']);
 }
 if($resource==='wholesale')foreach($catalog['products']??[]as $p){
  if(in_array($p['productType']??'',['door','door-profile','cabinet-front','cabinet-profile'],true))continue;
  $add((string)$p['id'],['productId'=>(string)$p['id'],'enabled'=>true,'minimumQuantity'=>1]);
 }
 if($resource==='collections'){
  require_once __DIR__.'/seo.php';$position=0;
  foreach(['portmantolar','calisma-odasi-masalari','tv-uniteleri','genc-odasi-calisma-gruplari']as $id){
   $category=null;foreach($catalog['categories']??[]as $c)if($c['id']===$id){$category=$c;break;}if(!$category)continue;
   $family=nodenoSeoFamily($catalog['categories'],$id);$products=array_values(array_filter($catalog['products']??[],static fn($p)=>nodenoSeoVisible($p)&&count(array_intersect(array_keys($family),$p['categoryIds']??[]))>0));
   $photo=null;foreach($products as $p)if(!empty($p['images'])){$photo=$p;break;}if(!$photo)continue;
   $add('category_'.$id,['title'=>nodenoLocaleLocal($category['name'],'tr'),'description'=>count($products).' ürün','productIds'=>implode(',',array_column($products,'id')),'cover'=>$photo['images'][$photo['coverIndex']??0],'position'=>$position++,'enabled'=>true],['localizedTitle'=>$category['name'],'sourceCategory'=>$id,'sourceDescription'=>count($products).' ürün']);
  }
 }
 return $rows;
}
function nodenoControlStoredRows(PDO $db,string $resource):array {
 $q=$db->prepare('SELECT id FROM control_records WHERE resource=? ORDER BY updated_at DESC');$q->execute([$resource]);return array_map(static fn($r)=>nodenoControlRead($db,$resource,$r['id']),$q->fetchAll());
}
function nodenoControlMergeRecords(array $source,array $saved):array {
 foreach($saved as $record){$id=$record['id'];$base=$source[$id]??null;if($base){$data=$base['data'];foreach($record['data']as $key=>$value)if($value!==''&&$value!==null)$data[$key]=$value;$record=array_merge($base,$record,['data'=>$data]);if(isset($record['localizedTitle'])&&!empty($record['data']['title'])&&$record['data']['title']!==$base['data']['title'])unset($record['localizedTitle']);}$source[$id]=$record;}return $source;
}
function nodenoControlCollectionsProjection(PDO $db,array $catalog,array $config):array {return array_values(nodenoControlMergeRecords(nodenoControlSourceRecords('collections',$catalog,$config),nodenoControlPublished($db,'collections')));}
