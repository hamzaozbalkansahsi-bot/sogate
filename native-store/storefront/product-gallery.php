<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/product-gallery.php
 * Açıklama   : Kaynak ve mevcut kapak kaydını değiştirmeden incelenmiş ek galeri fotoğraflarını sunar.
 */
declare(strict_types=1);
function sgProductGalleryData():array{
 static $data=null;
 if($data===null){$file=__DIR__.'/sexogate-product-gallery-data.json';if(!is_file($file))$file=__DIR__.'/product-gallery-data.json';$data=json_decode((string)file_get_contents($file),true,128,JSON_THROW_ON_ERROR);if(($data['schema']??null)!==1||!is_array($data['products']??null))throw new RuntimeException('gallery_registry_invalid');}
 return $data;
}
function sgProductGalleryBinding(string $id,bool $full=false):?array{
 if(!preg_match('/^sg_ty_[a-f0-9]{16}$/D',$id))return null;static $cache=[];if(!$full&&array_key_exists($id,$cache))return $cache[$id];
 $file=__DIR__.'/product-gallery-bindings/'.$id.'.json';$value=is_file($file)?json_decode((string)file_get_contents($file),true,128,JSON_THROW_ON_ERROR):null;
 if(!is_array($value)||($value['schema']??null)!==1||($value['product']['id']??null)!==$id){if(!$full)$cache[$id]=null;return null;}
 // Katalogda zaten bulunan tam snapshot yüzlerce kez ikinci bir önbellekte tutulmaz.
 if($full)return $value;$cache[$id]=array_intersect_key($value,array_fill_keys(['schema','sourceDataset','sourceSha256','baseHashes','sourceImages'],true));$cache[$id]['product']=array_intersect_key($value['product'],array_fill_keys(['id','code','images'],true));return $cache[$id];
}
function sgProductGalleryBaseHashes(mixed $value):?array{
 if(!is_array($value))return null;$out=[];foreach($value as $index=>$hash){if(!preg_match('/^(?:0|[1-9][0-9]*)$/D',(string)$index)||!is_string($hash)||!preg_match('/^[a-f0-9]{64}$/D',$hash))return null;$out[(int)$index]=$hash;}ksort($out,SORT_NUMERIC);return $out;
}
function sgProductGalleryImages(array $product,?array $registry=null,?array $binding=null):array{
 $registry??=sgProductGalleryData();$row=$registry['products'][$product['id']??'']??null;
 if(!is_array($row))return [];$binding??=sgProductGalleryBinding((string)($product['id']??''));$frozen=$binding['product']??null;
 if(!is_array($binding)||!is_array($frozen)||($binding['sourceDataset']??null)!==($registry['sourceDataset']??null)||($frozen['id']??null)!==($product['id']??null)||!is_string($row['code']??null)||!hash_equals($row['code'],(string)($product['code']??''))||!hash_equals($row['code'],(string)($frozen['code']??''))||!is_string($row['sourceSha256']??null)||!preg_match('/^[a-f0-9]{64}$/D',$row['sourceSha256'])||!is_string($binding['sourceSha256']??null)||!hash_equals($row['sourceSha256'],$binding['sourceSha256']))return [];
 $base=sgProductGalleryBaseHashes($row['baseHashes']??null);$expected=sgProductGalleryBaseHashes($binding['baseHashes']??null);if($base===null||$expected===null||$base!==$expected||count($expected)!==count($frozen['images']??[])||!is_array($binding['sourceImages']??null))return [];
 $known=array_fill_keys(array_values($base),true);$out=[];
 foreach($row['images']??[]as $image){
  if(!is_array($image)||($image['approved']??false)!==true||!preg_match('/^[a-f0-9]{64}$/D',$image['sha256']??'')||!preg_match('/^'.preg_quote($image['sha256'],'/').'\.(?:jpg|jpeg|png|webp|avif|gif)$/D',$image['file']??'')||isset($known[$image['sha256']]))continue;
  $index=$image['sourceIndex']??null;if(!is_int($index)||$index<0||!is_string($image['sourceSha256']??null)||!hash_equals($row['sourceSha256'],$image['sourceSha256'])||!is_string($image['sourceUrl']??null)||!is_string($binding['sourceImages'][$index]??null)||!hash_equals($binding['sourceImages'][$index],$image['sourceUrl']))continue;
  $types=['image/jpeg'=>['jpg','jpeg'],'image/png'=>['png'],'image/webp'=>['webp'],'image/avif'=>['avif'],'image/gif'=>['gif']];$extension=pathinfo($image['file'],PATHINFO_EXTENSION);
  if(!in_array($extension,$types[$image['mime']??'']??[],true)||!is_int($image['width']??null)||!is_int($image['height']??null)||$image['width']<1||$image['height']<1||$image['width']*$image['height']>40000000)continue;
  $known[$image['sha256']]=true;$out[]=$image;
 }
 return $out;
}
function sgProductGalleryProject(array $product,bool $enabled=true,?array $registry=null,?array $binding=null):array{
 if(!$enabled||($product['published']??true)===false||!empty($product['hidden'])||empty($product['images'])||!preg_match('/^sg_ty_[a-f0-9]{16}$/D',$product['id']??''))return $product;
 foreach(sgProductGalleryImages($product,$registry,$binding)as $image)$product['images'][]='/media/'.$product['id'].'/gallery/'.$image['sha256'];
 return $product;
}
function sgProductGalleryIsPublic(?array $binding,?array $record):bool{
 $product=$binding['product']??null;$values=$record?json_decode($record['published_json']??'null',true):null;
 if(!$binding||!is_array($product)||($product['catalogOrigin']??'')!=='sexogate-marketplaces-v1'||($product['eligibilityHold']??true)!==false||!$record||(int)($record['published_version']??0)<1||!is_array($values)||($values['visible']??false)!==true||($values['extraGalleryEnabled']??true)!==true||!is_string($values['imageApprovedIndices']??null))return false;
 $base=sgProductGalleryBaseHashes($binding['baseHashes']??null);if(!$base||count($base)!==count($product['images']??[]))return false;
 foreach(explode(',',$values['imageApprovedIndices'])as $index)if(preg_match('/^(?:0|[1-9][0-9]*)$/D',$index)&&array_key_exists((int)$index,$base)&&isset($product['images'][(int)$index]))return true;return false;
}
function sgProductGalleryHandle(string $private,string $path,string $method):void{
 if(!preg_match('~^/media/(sg_ty_[a-f0-9]{16})/gallery/([a-f0-9]{64})$~D',$path,$match)){nodenoRespond('',404);return;}
 if(!in_array($method,['GET','HEAD'],true)){nodenoRespond('',405,'text/plain; charset=utf-8',['Allow'=>'GET, HEAD','Cache-Control'=>'private, no-store']);return;}
 try{
  require_once $private.'/control-http.php';$runtime=nodenoRuntimeConfiguration();$db=nodenoControlDatabase(nodenoAccountStorage($runtime['storageRoot']));
  $query=$db->prepare("SELECT published_version,published_json FROM control_records WHERE resource='products' AND id=?");$query->execute([$match[1]]);$record=$query->fetch();$values=$record?json_decode($record['published_json']??'null',true):null;
  $registry=sgProductGalleryData();$binding=sgProductGalleryBinding($match[1],true);
  if(!sgProductGalleryIsPublic($binding,$record)){nodenoRespond('',404,'text/plain; charset=utf-8',['Cache-Control'=>'private, no-store']);return;}
  $product=sexogateCatalogProjection($binding['product'],$values);
  if(($product['published']??false)!==true||!empty($product['hidden'])||empty($product['images'])){nodenoRespond('',404,'text/plain; charset=utf-8',['Cache-Control'=>'private, no-store']);return;}
  $image=null;foreach(sgProductGalleryImages($product,$registry,$binding)as $candidate)if(hash_equals($match[2],$candidate['sha256'])){$image=$candidate;break;}
  if(!$image){nodenoRespond('',404,'text/plain; charset=utf-8',['Cache-Control'=>'private, no-store']);return;}
  $base=realpath($runtime['mediaRoot']);$file=$base?$base.DIRECTORY_SEPARATOR.$image['file']:'';$actual=realpath($file);
  if(!$base||!$actual||is_link($file)||!is_file($file)||!str_starts_with(str_replace('\\','/',$actual),str_replace('\\','/',$base).'/')||filesize($file)>12000000||!hash_equals($image['sha256'],hash_file('sha256',$file)))throw new RuntimeException('gallery_media_unavailable');
  $mime=(new finfo(FILEINFO_MIME_TYPE))->file($file);if($mime!==$image['mime'])throw new RuntimeException('gallery_media_type_invalid');
  header('Content-Type: '.$mime);header('Content-Length: '.filesize($file));header('Cache-Control: private, no-store');header('ETag: "'.$image['sha256'].'"');header('X-Content-Type-Options: nosniff');if($method!=='HEAD')readfile($file);
 }catch(Throwable $error){nodenoRespond('',503,'text/plain; charset=utf-8',['Cache-Control'=>'private, no-store']);}
}
