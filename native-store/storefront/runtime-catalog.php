<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/runtime-catalog.php
 * Açıklama   : Arşivi korurken müşteri ve işçi isteklerinde doğrulanmış küçük katalog kaynağını yükler.
 */
declare(strict_types=1);
function sexogateRuntimeAdminSource(string $uri):bool{
 $path=parse_url($uri,PHP_URL_PATH);return is_string($path)&&(preg_match('~^(?:/test(?:/native-preview-[a-f0-9]{16})?)?/api/admin/~D',$path)===1||preg_match('~^(?:/test(?:/native-preview-[a-f0-9]{16})?)?/yonetim/urun-onizleme$~D',$path)===1);
}
function sexogateRuntimeNeedsFullSource(string $uri,string $method='GET'):bool{
 if(!sexogateRuntimeAdminSource($uri))return false;$path=parse_url($uri,PHP_URL_PATH);
 return !($method==='GET'&&is_string($path)&&preg_match('~^(?:/test(?:/native-preview-[a-f0-9]{16})?)?/api/admin/products$~D',$path)===1);
}
function sexogateRuntimeCatalogMeta(string $private):array{
 $file=$private.'/catalog-active.meta.json';clearstatcache(true,$file);if(!is_file($file)||is_link($file)||filesize($file)>4096)throw new RuntimeException('runtime_catalog_meta_invalid');$bytes=file_get_contents($file,false,null,0,4097);
 if(!is_string($bytes)||strlen($bytes)>4096)throw new RuntimeException('runtime_catalog_meta_invalid');
 $meta=json_decode($bytes,true,32,JSON_THROW_ON_ERROR);
 if(!is_array($meta)||($meta['schema']??null)!==1||($meta['sourceCount']??null)!==3152||($meta['activeCount']??null)!==958||!preg_match('/^[a-f0-9]{32}$/D',$meta['dataset']??''))throw new RuntimeException('runtime_catalog_meta_invalid');
 foreach(['sourceSha256','rawSha256','gzipSha256','identitySha256']as $key)if(!is_string($meta[$key]??null)||!preg_match('/^[a-f0-9]{64}$/D',$meta[$key]))throw new RuntimeException('runtime_catalog_meta_invalid');
 foreach(['sourceBytes','rawBytes','gzipBytes']as $key)if(!is_int($meta[$key]??null)||$meta[$key]<1||$meta[$key]>32000000)throw new RuntimeException('runtime_catalog_meta_invalid');
 return $meta;
}
function sexogateRuntimeCatalogSummary(string $private):array{$meta=sexogateRuntimeCatalogMeta($private);return ['sourceProducts'=>$meta['sourceCount'],'activeProducts'=>$meta['activeCount'],'dataset'=>$meta['dataset']];}
function sexogateRuntimeCatalogLoad(string $private,?string $uri=null,?string $method=null):array{
 $meta=sexogateRuntimeCatalogMeta($private);$admin=sexogateRuntimeNeedsFullSource($uri??($_SERVER['REQUEST_URI']??''),$method??($_SERVER['REQUEST_METHOD']??'GET'));
 $file=$private.($admin?'/catalog.json':'/catalog-active.json.gz');$size=$meta[$admin?'sourceBytes':'gzipBytes'];$hash=$meta[$admin?'sourceSha256':'gzipSha256'];
 clearstatcache(true,$file);
 if(!is_file($file)||is_link($file)||filesize($file)!==$size)throw new RuntimeException('runtime_catalog_bytes_invalid');$bytes=file_get_contents($file,false,null,0,$size+1);
 if(!is_string($bytes)||strlen($bytes)!==$size||!hash_equals($hash,hash('sha256',$bytes)))throw new RuntimeException('runtime_catalog_bytes_invalid');
 if(!$admin){if(!function_exists('gzdecode'))throw new RuntimeException('runtime_catalog_zlib_required');$raw=@gzdecode($bytes,$meta['rawBytes']+1);unset($bytes);if(!is_string($raw)||strlen($raw)!==$meta['rawBytes']||!hash_equals($meta['rawSha256'],hash('sha256',$raw)))throw new RuntimeException('runtime_catalog_gzip_invalid');}
 else{$raw=$bytes;unset($bytes);}
 $catalog=json_decode($raw,true,512,JSON_THROW_ON_ERROR);unset($raw);
 if(!is_array($catalog)||($catalog['catalogOrigin']??null)!=='sexogate-catalog-v2'||($catalog['dataset']??null)!==$meta['dataset']||!is_array($catalog['products']??null)||!array_is_list($catalog['products'])||count($catalog['products'])!==$meta[$admin?'sourceCount':'activeCount'])throw new RuntimeException('runtime_catalog_context_invalid');
 $seen=[];$identities=[];foreach($catalog['products']as $p){$id=$p['id']??null;if(!is_string($id)||isset($seen[$id])||!is_string($p['code']??null)||$p['code']==='')throw new RuntimeException('runtime_catalog_identity_invalid');$seen[$id]=true;if(!$admin){if(!preg_match('/^sg_ty_[a-f0-9]{16}$/D',$id)||($p['catalogOrigin']??null)!=='sexogate-marketplaces-v1')throw new RuntimeException('runtime_catalog_identity_invalid');$identities[]=[$id,$p['code']];}}
 if(!$admin&&!hash_equals($meta['identitySha256'],hash('sha256',json_encode($identities,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR))))throw new RuntimeException('runtime_catalog_identity_invalid');
 return $catalog;
}
