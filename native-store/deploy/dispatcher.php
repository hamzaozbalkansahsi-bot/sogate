<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/deploy/dispatcher.php
 * Açıklama   : Özel NODENO sürümünü yalnız izinli test alt yolunda güvenli biçimde çalıştırır.
 */
declare(strict_types=1);
// Kaynak katalog ve yönetim sürümleri aynı istekte açılır; bellek bütçesi sınırlı ve ölçülebilirdir.
$memory=trim((string)ini_get('memory_limit'));$bytes=(int)$memory;if(preg_match('/([KMG])$/i',$memory,$unit))$bytes*=1024**(array_search(strtoupper($unit[1]),['K','M','G'],true)+1);if($bytes>0&&$bytes<268435456)ini_set('memory_limit','256M');
ini_set('display_errors','0');
$mount=SEXOGATE_NATIVE_MOUNT;
if(!preg_match('~^/test(?:/native-preview-[a-f0-9]{16})?$~D',$mount)){http_response_code(503);exit;}
header('X-Robots-Tag: noindex, nofollow');header('X-Content-Type-Options: nosniff');header('Referrer-Policy: no-referrer');
function sexogateNativeFail(int $status,string $code):never{http_response_code($status);header('Content-Type: application/json; charset=utf-8');header('Cache-Control: private, no-store');echo json_encode(['error'=>$code]);exit;}
$host=strtolower($_SERVER['HTTP_HOST']??'');
$local=PHP_SAPI==='cli-server'&&in_array($_SERVER['REMOTE_ADDR']??'',['127.0.0.1','::1'],true)&&$host==='127.0.0.1:3188';
if(!$local&&(!in_array($host,['sexogate.com','www.sexogate.com'],true)||($_SERVER['HTTPS']??'')!=='on'))sexogateNativeFail(403,'host_or_tls_rejected');
if($local&&getenv('SEXOGATE_NATIVE_LOCAL_TLS')==='loopback-only')$_SERVER['HTTPS']='on';
$uri=$_SERVER['REQUEST_URI']??'/';$raw=parse_url($uri,PHP_URL_PATH);
if(!is_string($raw)||preg_match('~%(?:2f|5c|00)|[\\\\\x00-\x1f\x7f]~i',$raw))sexogateNativeFail(404,'not_found');
if($raw!==$mount&&!str_starts_with($raw,$mount.'/'))sexogateNativeFail(404,'not_found');
$relative=rawurldecode(substr($raw,strlen($mount))?:'/');
if(preg_match('~(?:^|/)(?:\.{1,2}|app|private|hosting|data|lib|scripts|tests|node_modules|artifacts|cache)(?:/|$)|(?:^|/)\.~i',$relative))sexogateNativeFail(404,'not_found');
$home=dirname(__DIR__,3);$active=$home.'/active.json';
if(defined('SEXOGATE_NATIVE_RELEASE'))$pointer=['release'=>SEXOGATE_NATIVE_RELEASE];
else{if(!is_file($active)||is_link($active))sexogateNativeFail(503,'native_not_installed');$pointer=json_decode((string)file_get_contents($active),true);}
if(!is_array($pointer)||!preg_match('/^[a-f0-9]{24}$/D',$pointer['release']??''))sexogateNativeFail(503,'native_release_invalid');
$release=$home.'/releases/'.$pointer['release'];$public=realpath($release.'/public');$private=realpath($release.'/private');
if($public===false||$private===false||is_link($release))sexogateNativeFail(503,'native_release_missing');
$assetRevision=json_decode((string)file_get_contents($release.'/deployment-manifest.json'),true)['assetVersion']??$pointer['release'];
function sexogateNativeUrls(string $body,string $mount):string{return str_replace(['\\/__SEXOGATE_MOUNT__','/__SEXOGATE_MOUNT__'],[str_replace('/','\\/',$mount),$mount],$body);}
$static=!preg_match('~^/(?:api|social-media|assets/blog)(?:/|$)~',$relative)&&(preg_match('~\.(?:css|js|svg|png|jpe?g|webp|gif|avif|ico|woff2?|ttf|webmanifest)$~i',$relative)||preg_match('~^/locales/(?:de|az|kk|tk|uz|ky|fa)(?:\.catalogue)?\.json$~D',$relative));
if($static&&in_array($_SERVER['REQUEST_METHOD'],['GET','HEAD'],true)){
 $file=realpath($public.$relative);if($file===false||!str_starts_with(str_replace('\\','/',$file),str_replace('\\','/',$public).'/')||!is_file($file)||is_link($file))sexogateNativeFail(404,'asset_not_found');
 $extension=strtolower(pathinfo($file,PATHINFO_EXTENSION));$types=['css'=>'text/css; charset=utf-8','js'=>'text/javascript; charset=utf-8','json'=>'application/json; charset=utf-8','svg'=>'image/svg+xml','woff'=>'font/woff','woff2'=>'font/woff2','ttf'=>'font/ttf','webmanifest'=>'application/manifest+json','ico'=>'image/x-icon','png'=>'image/png','jpg'=>'image/jpeg','jpeg'=>'image/jpeg','webp'=>'image/webp','gif'=>'image/gif','avif'=>'image/avif'];
 $bytes=file_get_contents($file);if($bytes===false)sexogateNativeFail(503,'asset_unavailable');
 if(in_array($extension,['js','css','json','svg','webmanifest'],true))$bytes=sexogateNativeUrls($bytes,$mount);
 header('Content-Type: '.$types[$extension]);header('Cache-Control: public, max-age=3600');header('Cross-Origin-Resource-Policy: same-origin');header('ETag: "'.hash('sha256',$bytes).'"');header('Content-Length: '.strlen($bytes));if($_SERVER['REQUEST_METHOD']!=='HEAD')echo $bytes;exit;
}
if($relative==='/api/payments/checkout')sexogateNativeFail(409,'live_sales_not_approved');
define('NODENO_RUNTIME_LIBRARY',true);require $public.'/index.php';
if(is_file($private.'/sexogate-catalog.php')){
 require_once $private.'/sexogate-catalog.php';
 if(str_starts_with($relative,'/media/sg_')&&in_array($_SERVER['REQUEST_METHOD'],['GET','HEAD'],true)){sexogateCatalogMedia($private,$relative,$_SERVER['REQUEST_METHOD']==='HEAD');exit;}
 if($relative==='/yonetim/urun-onizleme'&&$_SERVER['REQUEST_METHOD']==='GET'){sexogateCatalogPreview($private,is_string($_GET['product']??null)?$_GET['product']:'');exit;}
}
if($relative==='/api/deployment-status'){
 try{$state=nodenoStoreContext($private);$db=nodenoControlDatabase($state['storage']);$ok=$db->query('PRAGMA quick_check')->fetchColumn()==='ok';$products=count($state['catalog']['products']??[]);$report=['status'=>$ok?'preview':'unavailable','runtime'=>'php','database'=>$ok,'release'=>$pointer['release'],'products'=>$products,'sourceProducts'=>count($state['sourceCatalog']['products']??[]),'checkoutEnabled'=>false,'catalogReady'=>$products>0,'strictMediaHealth'=>'sales_and_country_acceptance_pending','basePath'=>$mount];http_response_code($ok?200:503);header('Content-Type: application/json; charset=utf-8');header('Cache-Control: private, no-store');echo json_encode($report,JSON_THROW_ON_ERROR);exit;}catch(Throwable $error){sexogateNativeFail(503,'deployment_check_failed');}
}
$_SERVER['REQUEST_URI']=substr($uri,strlen($mount))?:'/';
ob_start(static function(string $body)use($mount,$assetRevision):string{
 foreach(headers_list()as $header){if(str_starts_with(strtolower($header),'location: /')&&!str_starts_with(substr($header,10),'//'))header('Location: '.$mount.substr($header,10),true,http_response_code());}
 $type='';foreach(headers_list()as $header)if(str_starts_with(strtolower($header),'content-type:'))$type=strtolower($header);
 header('X-Robots-Tag: noindex, nofollow');
 if(str_contains($type,'text/html')){
  $body=preg_replace('~((?:href|src|action|poster)=["\'])/(?!/|__SEXOGATE_MOUNT__)~i','$1/__SEXOGATE_MOUNT__/',$body);
  if(!str_contains($body,'sexogate.css'))$body=str_replace('</head>','<link rel="stylesheet" href="/__SEXOGATE_MOUNT__/sexogate.css?v=sexogate-'.$assetRevision.'"><script defer src="/__SEXOGATE_MOUNT__/sexogate-branding.js?v=sexogate-'.$assetRevision.'"></script></head>',$body);
 }
 if(str_contains($type,'json')){
  $body=preg_replace('~("(?:\\\\/|/))(api|assets|media|legal|social-media|locales|blog|yonetim)(?=\\\\/|/|["?])~','$1__SEXOGATE_MOUNT__/$2',$body);
 }
 if(preg_match('~text/|json|xml~',$type)){header_remove('Content-Length');$body=sexogateNativeUrls($body,$mount);}
 return $body;
});
set_error_handler(static function(int $severity,string $message,string $file,int $line):bool{if(!(error_reporting()&$severity))return false;throw new ErrorException($message,0,$severity,$file,$line);});
nodenoRun();
