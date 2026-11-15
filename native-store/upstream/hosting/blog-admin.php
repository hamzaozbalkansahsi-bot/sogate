<?php
declare(strict_types=1);
require_once __DIR__.'/blog-store.php';

// Called by the existing same-origin, CSRF-checked admin dispatcher only.
function nodenoBlogAdmin(array $ctx,string $route,string $method,array $body,string $private): array {
 if($route!=='blog'&&!str_starts_with($route,'blog/'))throw new NodenoControlHttpError(404,'not_found');
 $write=$method!=='GET';$actor=nodenoControlRequire($ctx,$write?'marketing.write':'marketing.read',$write);
 if(!in_array($method,['GET','POST'],true))throw new NodenoControlHttpError(405,'method_not_allowed');
 $db=nodenoBlogDatabase($ctx['root']);$bank=nodenoBlogReadBank($private);
 if($method==='GET'){
  if(preg_match('~^blog/articles/([a-z0-9][a-z0-9_-]{0,99})$~D',$route,$match)){
   $articles=array_column($bank['articles'],null,'id');$article=$articles[$match[1]]??null;if($article===null)throw new NodenoControlHttpError(404,'not_found');
   $q=$db->prepare('SELECT * FROM blog_queue WHERE article_id=?');$q->execute([$match[1]]);$row=$q->fetch();
   if($row&&$row['status']==='published'&&!empty($row['payload_json']))$article=json_decode($row['payload_json'],true,64,JSON_THROW_ON_ERROR);
   return ['article'=>$article,'publication'=>$row?nodenoBlogQueueRow($row,$articles):null];
  }
  if($route!=='blog'&&$route!=='blog/status')throw new NodenoControlHttpError(404,'not_found');
  return nodenoBlogStatus($db,$bank);
 }
 $action=substr($route,5);if(!in_array($action,['pause','resume','retry','hold','schedule','publish'],true))throw new NodenoControlHttpError(404,'not_found');
 try{
  if($action==='publish'){
   require_once __DIR__.'/blog-worker.php';$id=$body['id']??'';if(!is_string($id))throw new InvalidArgumentException('blog_article_id_invalid');
   $result=nodenoBlogPublishNow($db,$bank,$id,(string)($ctx['publicRoot']??$_SERVER['DOCUMENT_ROOT']??''),time(),(string)$actor['id'],$private);
  }else $result=nodenoBlogCommand($db,$bank,$action,$body,(string)$actor['id'],time());
  if(($ctx['db']??null) instanceof PDO&&function_exists('nodenoControlAudit')&&empty($result['alreadyPublished']))nodenoControlAudit($ctx['db'],$ctx['root'],(string)$actor['id'],$action,'blog',(string)($body['id']??''),['timezone'=>'Europe/Istanbul']);
  return $result;
 }catch(InvalidArgumentException $e){throw new NodenoControlHttpError(422,$e->getMessage());}
}
