<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/catalog/catalog.php
 * Açıklama   : Yerel kaynak kataloğunu özgün yönetim doğrulaması, sürüm ve işlem kayıtlarıyla yönetir.
 */
declare(strict_types=1);
function sexogateCatalogManaged(array $product):bool{return ($product['catalogOrigin']??'')==='sexogate-suppliers-v1';}
function sexogateCatalogWork(string $private,string $id):array{
 if(!preg_match('/^sg_(?:xsh|lio|sis)_([a-f0-9]{16})$/D',$id,$match))throw new NodenoControlHttpError(404,'product_unknown');
 static $cache=[];$file=$private.'/catalog-workbench/'.substr($match[1],0,2).'.json';
 if(!array_key_exists($file,$cache))$cache[$file]=is_file($file)?json_decode((string)file_get_contents($file),true,128,JSON_THROW_ON_ERROR):[];
 $row=$cache[$file][$id]??null;if(!is_array($row))throw new NodenoControlHttpError(404,'product_unknown');return $row;
}
function sexogateCatalogFields():array{
 $labels=['sku'=>'Mağaza stok kodu','brand'=>'Marka','barcode'=>'Gerçek barkod','manufacturer'=>'Üretici','origin'=>'Menşe','materials'=>'Malzeme / kumaş','dimensions'=>'Ölçü bilgisi','sizeOptions'=>'Beden seçenekleri','colorOptions'=>'Renk seçenekleri','batteryInformation'=>'Pil ve şarj bilgisi','shippingWeight'=>'Doğrulanmış kargo ağırlığı','packageDimensions'=>'Paket ölçüleri','ingredients'=>'İçerik bilgisi','warranty'=>'Garanti bilgisi','care'=>'Üreticinin bakım talimatları','safety'=>'Üreticinin güvenlik uyarıları','documents'=>'Ürün belge referansları','slug'=>'Ürün bağlantı adı','coverIndex'=>'Kapak görseli sırası'];$fields=[];
 $labels['imageApprovedIndices']='Vitrin için incelenen görsel sıraları';foreach($labels as $key=>$label)$fields[$key]=['label'=>$label,'type'=>in_array($key,['materials','dimensions','sizeOptions','colorOptions','batteryInformation','ingredients','care','safety','documents'],true)?'textarea':($key==='coverIndex'?'integer':'text')];
 foreach(['sourceVendor'=>'Kaynak tedarikçi','sourceSku'=>'Tedarikçinin gerçek ürün kodu','sourceUrl'=>'Kaynak ürün bağlantısı','referenceRetailMinor'=>'Kaynak kamu fiyatı · alış maliyeti değildir','sourceObservedAt'=>'Kaynağın gözlem zamanı','initialMarkup'=>'İlk yükleme fiyatlandırması','sourceAvailability'=>'Kamu bulunabilirliği · depo miktarı değildir','sourceCategories'=>'Kaynak kategoriler','sourceVariants'=>'Kaynak varyant bilgileri','sourceDescription'=>'Kaynak açıklaması · doğrulama için','sourceImages'=>'Kaynak görsel bağlantıları','rightsBasis'=>'Görsel ve içerik izin kaydı','missingSourceFacts'=>'Kaynakta bulunmayan bilgiler','publicationReview'=>'Yayın inceleme durumu']as $key=>$label)$fields[$key]=['label'=>$label,'type'=>$key==='referenceRetailMinor'?'money':(in_array($key,['sourceCategories','sourceVariants','sourceDescription','sourceImages','missingSourceFacts','publicationReview'],true)?'textarea':'text'),'readonly'=>true];
 return $fields;
}
function sexogateCatalogDefinitions(array $definitions):array{
 if(!isset($definitions['products']))return $definitions;
 $definitions['products']['fields']=array_merge($definitions['products']['fields'],sexogateCatalogFields());
 foreach(['stockKnown','stockQuantity']as $key)$definitions['products']['fields'][$key]=array_replace($definitions['products']['fields'][$key],['hidden'=>true,'readonly'=>true]);
 return $definitions;
}
function sexogateCatalogEditor(array $product,array $values,string $private):array{
 if(!sexogateCatalogManaged($product))return $values;$work=sexogateCatalogWork($private,$product['id']);$source=$work['source'];$fields=sexogateCatalogFields();$facts=$work['facts'];
 foreach($facts as $key=>$value)if(isset($fields[$key])&&!array_key_exists($key,$values))$values[$key]=$value??'';
 foreach(['sku','brand','slug','coverIndex']as $key)if(!array_key_exists($key,$values))$values[$key]=$product[$key]??'';
 if(!array_key_exists('imageApprovedIndices',$values))$values['imageApprovedIndices']=implode(',',$product['visualApprovedIndices']??[]);
 $json=static fn($value):string=>json_encode($value,JSON_PRETTY_PRINT|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR);
 $missing=[];foreach($work['missingFields']as $key)$missing[]=$fields[$key]['label']??$key;
 return array_replace($values,['sourceVendor'=>$source['vendor'],'sourceSku'=>$source['sourceSku']??'','sourceUrl'=>$source['url'],'referenceRetailMinor'=>$source['retailPriceMinor'],'sourceObservedAt'=>$source['observedAt']??'','initialMarkup'=>'İlk aktarımda kaynak kamu fiyatı +%30. Sonraki aktarım yönetici fiyatını değiştirmez.','sourceAvailability'=>$source['publicInStock']===true?'Kaynakta bulunabilir görünmüş; doğrulanmış tedarikçi miktarı ve depo stoğu yok.':($source['publicInStock']===false?'Kaynakta stok dışı gözlenmiş; fiziksel depo bakiyesi değildir.':'Kaynak bulunabilirliği belirtilmemiş.'),'sourceCategories'=>$json($work['sourceCategories']),'sourceVariants'=>$json($work['sourceVariants']),'sourceDescription'=>$work['sourceDescription'],'sourceImages'=>implode("\n",$work['sourceImages']),'rightsBasis'=>'15 Kasım 2026 kullanıcı beyanı · ürün fotoğrafları ve içerikleri; yazılı sözleşme varlığı iddia edilmez.','missingSourceFacts'=>implode("\n",$missing),'publicationReview'=>$work['eligibilityHold']?'Düzenlemeye tabi ürün veya doğrulanmamış sağlık iddiası: yayın incelemesi gerekiyor.':(($product['salePriceMinor']??null)===null?'Kaynak fiyatı eksik; ücretsiz ürün değildir.':'Katalog önizlemesi hazırlanabilir; gerçek ödeme ve ülke/taşıyıcı onayları ayrıca gerekir.')]);
}
function sexogateCatalogValidate(string $resource,string $id,array $data,array $catalog,?PDO $db=null):void{
 if($resource!=='products')return;$product=array_column($catalog['products'],null,'id')[$id]??null;if(!$product||!sexogateCatalogManaged($product))return;
 if(isset($data['barcode'])&&$data['barcode']!==''){$code=$data['barcode'];if(!preg_match('/^(?:\d{8}|\d{12,14})$/D',$code))throw new NodenoControlHttpError(422,'barcode_invalid');$sum=0;$index=0;for($i=strlen($code)-2;$i>=0;$i--,$index++)$sum+=(int)$code[$i]*($index%2===0?3:1);if((10-$sum%10)%10!==(int)substr($code,-1))throw new NodenoControlHttpError(422,'barcode_invalid');}
 if(isset($data['slug'])&&$data['slug']!==''&&!preg_match('/^[a-z0-9]+(?:-[a-z0-9]+)*$/D',$data['slug']))throw new NodenoControlHttpError(422,'slug_invalid');
 if(isset($data['coverIndex'])&&($data['coverIndex']<0||($product['images']?$data['coverIndex']>=count($product['images']):$data['coverIndex']!==0)))throw new NodenoControlHttpError(422,'cover_invalid');
 if(isset($data['sku'])&&$data['sku']!==$product['code']){
  if($data['sku']==='')throw new NodenoControlHttpError(422,'sku_required');
  foreach($catalog['products']as $other)if($other['id']!==$id&&$other['code']===$data['sku'])throw new NodenoControlHttpError(422,'sku_duplicate');
  if($db){$query=$db->prepare("SELECT 1 FROM control_records WHERE resource='products' AND id<>? AND json_extract(data_json,'$.sku')=? LIMIT 1");$query->execute([$id,$data['sku']]);if($query->fetchColumn())throw new NodenoControlHttpError(422,'sku_duplicate');}
 }
 $approved=trim($data['imageApprovedIndices']??implode(',',$product['visualApprovedIndices']??[]));if($approved!==''&&(!preg_match('/^(?:0|[1-9][0-9]{0,2})(?:,(?:0|[1-9][0-9]{0,2}))*$/D',$approved)||max(array_map('intval',explode(',',$approved)))>=count($product['images'])))throw new NodenoControlHttpError(422,'image_review_invalid');
 if(($data['visible']??false)===true){if(!empty($product['eligibilityHold'])||!$product['images']||$approved===''||!is_int($data['priceMinor']??$product['salePriceMinor']??null)||($data['priceMinor']??$product['salePriceMinor'])<1)throw new NodenoControlHttpError(422,'catalog_review_required');}
}
function sexogateCatalogProjection(array $product,array $data):array{
 if(!sexogateCatalogManaged($product))return $product;
 $product['published']=($data['visible']??false)===true&&!($product['eligibilityHold']??true);$product['hidden']=!$product['published'];
 foreach(['sku','brand','slug','coverIndex']as $key)if(isset($data[$key]))$product[$key]=$data[$key];
 if(isset($data['sku']))$product['code']=$data['sku'];
 foreach(array_keys(sexogateCatalogFields())as $key)if(array_key_exists($key,$product['facts'])&&array_key_exists($key,$data))$product['facts'][$key]=$data[$key];
 static $labels=null;if($labels===null)$labels=json_decode((string)file_get_contents(__DIR__.'/catalog-spec-labels.json'),true,32,JSON_THROW_ON_ERROR);$product['attributes']=[];foreach($labels as $key=>$label)if(trim((string)($product['facts'][$key]??''))!=='')$product['attributes'][]=['name'=>$label,'value'=>array_fill_keys(NODENO_STORE_LOCALES,(string)$product['facts'][$key])];
 $product['specs']=array_map(static fn($attribute)=>['label'=>$attribute['name'],'value'=>$attribute['value']],$product['attributes']);$product['productBrand']=$product['brand']??'';
 $indices=array_values(array_unique(array_filter(explode(',',$data['imageApprovedIndices']??implode(',',$product['visualApprovedIndices']??[])),static fn($v)=>$v!=='')));$approved=[];foreach($indices as $index)if(isset($product['images'][(int)$index]))$approved[]=$product['images'][(int)$index];$cover=$data['coverIndex']??0;$selected=$product['images'][$cover]??null;if($selected&&in_array($selected,$approved,true))$approved=array_values(array_unique([$selected,...$approved]));$product['images']=$approved;$product['coverIndex']=0;if(!$approved){$product['published']=false;$product['hidden']=true;}
 $product['stockKnown']=false;$product['stockQuantity']=null;unset($product['privateRetailReference'],$product['sourceVendor']);return $product;
}
function sexogateCatalogInitial(array $product,string $private):array{
 $data=['visible'=>is_int($product['salePriceMinor']??null)&&$product['salePriceMinor']>0&&count($product['images'])>0&&!$product['eligibilityHold']&&!empty($product['visualApprovedIndices']),'sku'=>$product['code'],'brand'=>$product['brand']??'','slug'=>$product['slug'],'coverIndex'=>$product['coverIndex']??0,'imageApprovedIndices'=>implode(',',$product['visualApprovedIndices']??[])];
 foreach(['title'=>'name','description'=>'description','seoTitle'=>'seoTitle','seoDescription'=>'seoDescription']as $prefix=>$source)foreach(NODENO_STORE_LOCALES as $locale)$data[$prefix.'_'.$locale]=$product[$source][$locale]??'';
 foreach($product['facts']as $key=>$value)if($value!==null&&isset(sexogateCatalogFields()[$key]))$data[$key]=$value;
 if(is_int($product['salePriceMinor']??null))$data['priceMinor']=$product['salePriceMinor'];return $data;
}
function sexogateCatalogReviewedUpgrade(array $record,array $initial):?array{
 if(($record['version']??0)!==1||($record['publishedVersion']??0)!==0||empty($initial['visible'])||!empty($record['data']['visible']))return null;
 $previous=$record['data'];$next=array_map(static fn($value)=>is_string($value)?trim($value):$value,$initial);
 foreach(['visible','coverIndex','imageApprovedIndices']as $field){unset($previous[$field],$next[$field]);}
 ksort($previous);ksort($next);
 // İlk aktarımın dokunulmamış taslağı dışında fiyat/içerik/görünürlük kararı değiştirilmez.
 return $previous===$next?$initial:null;
}
function sexogateCatalogAdmin(array $ctx,string $route,string $method,array $body,array $catalog,array $config):?array{
 if($route==='products'&&$method==='GET'){nodenoControlRequire($ctx,'catalog.read');return ['data'=>nodenoControlStoredRows($ctx['db'],'products')];}
 if(!in_array($route,['catalog-source','catalog-import'],true))return null;
 nodenoControlRequire($ctx,$method==='GET'?'catalog.read':'catalog.write',$method!=='GET');$private=__DIR__;$file=$private.'/catalog-sources.json';
 if(!is_file($file))return ['configured'=>false,'products'=>0];$manifest=json_decode((string)file_get_contents($file),true,128,JSON_THROW_ON_ERROR);$products=array_values(array_filter($catalog['products'],'sexogateCatalogManaged'));
 if($route==='catalog-source'&&$method==='GET'){
  $q=$ctx['db']->query("SELECT COUNT(*) FROM control_records WHERE resource='products' AND id LIKE 'sg_%'");$loaded=(int)$q->fetchColumn();
  return ['configured'=>true,'dataset'=>$manifest['dataset'],'products'=>count($products),'loaded'=>$loaded,'sourceCategories'=>$manifest['sourceCategories'],'sources'=>$manifest['sources'],'markupPercent'=>30,'checkoutEnabled'=>false,'reviewRequired'=>count(array_filter($products,static fn($p)=>$p['eligibilityHold']||!is_int($p['salePriceMinor']??null)||!$p['images']||empty($p['visualApprovedIndices'])))];
 }
 if($route!=='catalog-import'||$method!=='POST')throw new NodenoControlHttpError(405,'method_not_allowed');
 if(($body['dataset']??'')!==$manifest['dataset']||!is_int($body['offset']??null)||$body['offset']<0||$body['offset']>count($products))throw new NodenoControlHttpError(422,'catalog_batch_invalid');
 $offset=$body['offset'];$rows=array_slice($products,$offset,40);$key='sg-catalog-'.$manifest['dataset'].'-'.$offset;
 return nodenoControlCommand($ctx,$key,[$manifest['dataset'],$offset],static function()use($ctx,$rows,$private,$catalog,$config,$offset,$products):array{
  return nodenoControlTransaction($ctx['db'],static function()use($ctx,$rows,$private,$catalog,$config,$offset,$products):array{
   $created=$published=$preserved=0;
   foreach($rows as $product){$id=$product['id'];$record=nodenoControlRead($ctx['db'],'products',$id);$data=sexogateCatalogInitial($product,$private);
    if($record){$upgrade=sexogateCatalogReviewedUpgrade($record,$data);if($upgrade===null){$preserved++;continue;}$data=$upgrade;}
    $saved=nodenoControlResource($ctx,'products',$id,'PUT',['version'=>$record['version']??0,'data'=>$data],$catalog,$config);if(!$record)$created++;
    if($data['visible']){nodenoControlResource($ctx,'products',$id,'PUBLISH',['version'=>$saved['data']['version']],$catalog,$config);$published++;}
   }
   return ['created'=>$created,'published'=>$published,'preserved'=>$preserved,'nextOffset'=>$offset+count($rows),'total'=>count($products),'done'=>$offset+count($rows)>=count($products),'checkoutEnabled'=>false];
  });
 });
}
function sexogateCatalogMedia(string $private,string $path,bool $head):bool{
 if(!preg_match('~^/media/(sg_(?:xsh|lio|sis)_[a-f0-9]{16})/([0-9]{1,3})$~D',$path,$match))return false;
 try{
  require_once $private.'/control-http.php';$runtime=nodenoRuntimeConfiguration();$root=nodenoAccountStorage($runtime['storageRoot']);$db=nodenoControlDatabase($root);$query=$db->prepare("SELECT published_json,published_version FROM control_records WHERE resource='products' AND id=?");$query->execute([$match[1]]);$record=$query->fetch();$published=$record?json_decode($record['published_json']??'null',true):null;$isPublic=($record['published_version']??0)>0&&($published['visible']??false)===true;
  $work=sexogateCatalogWork($private,$match[1]);$approved=explode(',',$published['imageApprovedIndices']??'');$isPublic=$isPublic&&in_array($match[2],$approved,true);$image=$work['media'][(int)$match[2]]??null;if(!is_array($image))throw new RuntimeException('image_missing');
  if(!$isPublic){$ctx=nodenoControlSession($db,$root);try{nodenoControlRequire($ctx,'catalog.read');}finally{if(session_status()===PHP_SESSION_ACTIVE)session_write_close();}}
  $home=realpath($runtime['mediaRoot']);$file=$home.'/'.$image['file'];if(!$home||is_link($file)||!is_file($file)||!str_starts_with((string)realpath($file),$home.DIRECTORY_SEPARATOR)||!hash_equals($image['sha256'],hash_file('sha256',$file)))throw new RuntimeException('image_unavailable');
  nodenoRespond('',200,$image['mime'],['Cache-Control'=>$isPublic?'public,max-age=86400':'private,no-store','Content-Length'=>(string)filesize($file),'X-Content-SHA256'=>$image['sha256'],'X-Content-Type-Options'=>'nosniff','Cross-Origin-Resource-Policy'=>'same-origin']);if(!$head)readfile($file);
 }catch(Throwable $error){nodenoError(404,'image_not_found');}return true;
}
function sexogateCatalogPreview(string $private,string $id):void{
 require_once $private.'/control-http.php';$state=nodenoStoreContext($private);$root=$state['storage'];$db=nodenoControlDatabase($root);$ctx=nodenoControlSession($db,$root);
 try{
  nodenoControlRequire($ctx,'catalog.read');$product=array_column($state['sourceCatalog']['products'],null,'id')[$id]??null;if(!$product||!sexogateCatalogManaged($product))throw new NodenoControlHttpError(404,'product_unknown');
  if(in_array($id,array_column($state['catalog']['products'],'id'),true)){nodenoRespond('',302,'text/html; charset=utf-8',['Location'=>SEXOGATE_NATIVE_MOUNT.'/?product='.rawurlencode($id).'&lang=tr','Cache-Control'=>'private,no-store']);return;}
  require_once $private.'/seo.php';$catalog=$state['sourceCatalog'];$product['published']=true;$product['hidden']=false;$catalog['products']=[$product];$page=nodenoSeoPage($catalog,$state['config'],['product'=>$id,'lang'=>'tr']);$html=nodenoSeoDocument((string)file_get_contents($private.'/index.html'),$page);
  $html=preg_replace('~<script\b(?![^>]*type="application/ld\+json")[^>]*>[\s\S]*?</script>~i','',$html);$html=preg_replace('~((?:href|src|action)=["\'])/(?!/|__SEXOGATE_MOUNT__)~','$1/__SEXOGATE_MOUNT__/',$html);$html=sexogateNativeUrls($html,SEXOGATE_NATIVE_MOUNT);nodenoRespond($html,200,'text/html; charset=utf-8',['Cache-Control'=>'private,no-store','X-Robots-Tag'=>'noindex,nofollow']);
 }catch(NodenoControlHttpError $error){nodenoAccountJson(['error'=>$error->errorCode],$error->status);}finally{if(session_status()===PHP_SESSION_ACTIVE)session_write_close();}
}
