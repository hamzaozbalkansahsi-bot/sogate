<?php
declare(strict_types=1);
require_once __DIR__.'/blog.php';
require_once __DIR__.'/blog-store.php';
function nodenoBlogHttp(string $path,string $method,string $private,string $public):bool {
 $asset=str_starts_with($path,'/assets/blog/');$publicPage=$path==='/blog'||str_starts_with($path,'/blog/')||$path==='/sitemap-blog.xml'||$asset;$adminApi=$path==='/api/admin/blog'||str_starts_with($path,'/api/admin/blog/');$adminPage=in_array($path,['/yonetim/blog','/yonetim/blog/'],true);
 if(!$publicPage&&!$adminApi&&!$adminPage)return false;
 if($adminPage){if(!in_array($method,['GET','HEAD'],true)){nodenoError(405,'method_not_allowed');return true;}nodenoRespond((string)file_get_contents(__DIR__.'/blog-admin.html'),200,'text/html; charset=utf-8',['Cache-Control'=>'no-store','X-Robots-Tag'=>'noindex,nofollow']);return true;}
 $configuration=nodenoRuntimeConfiguration();$storage=$configuration['storageRoot']??dirname(__DIR__).'/nodeno-data';if(!is_string($storage))throw new RuntimeException('Invalid blog storage');
 if($adminApi){
  require_once $private.'/control-http.php';require_once $private.'/blog-admin.php';
  try{
   $root=nodenoAccountStorage($storage);$ctx=nodenoControlSession(nodenoControlDatabase($root),$root);$ctx['publicRoot']=$public;
   if(preg_match('~^/api/admin/blog/articles/([a-z0-9][a-z0-9_-]{0,99})/image/(tr|en|ru|ar)$~D',$path,$match)){
    if(!in_array($method,['GET','HEAD'],true))throw new NodenoControlHttpError(405,'method_not_allowed');
    $preview=nodenoBlogAdmin($ctx,'blog/articles/'.$match[1],'GET',[],$private);$localized=nodenoBlogLocale($preview['article'],$match[2]);
    if($localized===null)throw new NodenoControlHttpError(404,'not_found');
    $bytes=nodenoBlogImageBytes($localized['image'],$private,$public);
    nodenoRespond($bytes,200,'image/svg+xml',['Cache-Control'=>'private,no-store','X-Robots-Tag'=>'noindex,nofollow','Content-Security-Policy'=>"sandbox; default-src 'none'; style-src 'unsafe-inline'; font-src data:"]);return true;
   }
   $body=in_array($method,['GET','HEAD'],true)?[]:nodenoControlBody();$result=nodenoBlogAdmin($ctx,substr($path,11),$method,$body,$private);nodenoAccountJson($result);
  }
  catch(NodenoControlHttpError $e){nodenoAccountJson(['error'=>$e->errorCode,'csrfToken'=>$_SESSION['csrf']??null],$e->status,$e->headers);}
  catch(Throwable $e){nodenoAccountJson(['error'=>'blog_service_unavailable'],503);}
  finally{if(session_status()===PHP_SESSION_ACTIVE)session_write_close();}return true;
 }
 if(!in_array($method,['GET','HEAD'],true)){nodenoError(405,'method_not_allowed');return true;}
 $db=nodenoBlogDatabase($storage);$bank=nodenoBlogReadBank($private);$locale=is_string($_GET['lang']??null)?$_GET['lang']:'tr';$locale=in_array($locale,['tr','en','ru','ar'],true)?$locale:'tr';
 $all=nodenoBlogPublished($db,$bank,'tr',['perPage'=>100]);$published=$all['items'];for($pg=2;$pg<=$all['pages'];$pg++)$published=array_merge($published,nodenoBlogPublished($db,$bank,'tr',['perPage'=>100,'page'=>$pg])['items']);
 if($asset){
  $image=nodenoBlogVisibleImage($published,$path);if($image===null){nodenoError(404,'not_found');return true;}
  try{$bytes=nodenoBlogImageBytes($image,$private,$public);}catch(Throwable $e){nodenoError(404,'not_found');return true;}
  $mime=str_ends_with($path,'.svg')?'image/svg+xml':(new finfo(FILEINFO_MIME_TYPE))->buffer($bytes);nodenoRespond($bytes,200,$mime,['Cache-Control'=>'public,max-age=86400','Content-Security-Policy'=>"sandbox; default-src 'none'; style-src 'unsafe-inline'; font-src data:",'ETag'=>'"'.$image['sha256'].'"']);return true;
 }
 if($path==='/sitemap-blog.xml'){nodenoRespond(nodenoBlogSitemapDocument($published,$bank),200,'application/xml; charset=utf-8',['Cache-Control'=>'public,max-age=300']);return true;}
 if($path==='/blog/feed.xml'){
  $e='nodenoBlogEscape';$xml='<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>NODENO Rehber</title><link>https://nodenohome.com/blog</link><description>Özgün NODENO yaşam alanı ve yenileme rehberleri</description><language>tr</language>';
  foreach(array_slice($published,0,30)as $a){$url=nodenoBlogOrigin().nodenoBlogUrl($a['slug']);$xml.='<item><title>'.$e($a['title']).'</title><link>'.$e($url).'</link><guid isPermaLink="true">'.$e($url).'</guid><pubDate>'.gmdate(DATE_RSS,strtotime($a['publishedAt'])).'</pubDate><description>'.$e($a['description']).'</description></item>';}
  nodenoRespond($xml.'</channel></rss>',200,'application/rss+xml; charset=utf-8',['Cache-Control'=>'public,max-age=300']);return true;
 }
 $query=[];foreach(['q','category','tool']as $key)if(isset($_GET[$key])&&is_string($_GET[$key]))$query[$key]=function_exists('mb_substr')?mb_substr($_GET[$key],0,120):substr($_GET[$key],0,120);
 $article=null;$status=200;$slug=$path==='/blog'?'':substr($path,6);
 if($slug!==''){$article=preg_match('/^[a-z0-9][a-z0-9-]{0,150}$/D',$slug)?nodenoBlogArticle($db,$bank,$slug,$locale):null;if($article===null){$status=404;$query['_notFound']=true;}}
 if(isset($query['tool'])&&!in_array($query['tool'],['paint','space','palette','surface'],true)){$status=404;$query['_notFound']=true;}
 if(isset($query['category'])&&!in_array($query['category'],['small-spaces','entryway','living','bedroom','work','care','planning','color','paint-math','surfaces','application','renewal'],true)){$status=404;$query['_notFound']=true;}
 $list=nodenoBlogPublished($db,$bank,$locale,array_merge($query,['page'=>max(1,(int)($_GET['pg']??1))]));
 if($article){$list=nodenoBlogPublished($db,$bank,$locale,['perPage'=>100]);}
 $html=nodenoBlogPageDocument($locale,$article,$list['items'],$bank,$query,$list);preg_match('/nonce="([a-f0-9]{32})"/',$html,$nonce);
 nodenoRespond($html,$status,'text/html; charset=utf-8',array_merge(nodenoSecurityHeaders($nonce[1]??null),['Cache-Control'=>'no-store','X-Robots-Tag'=>$status===200&&empty($query['q'])?'index,follow':'noindex,follow']));return true;
}
