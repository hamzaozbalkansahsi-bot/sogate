<?php
declare(strict_types=1);
require_once __DIR__.'/blog-store.php';

function nodenoBlogPublishable(array $article,string $public,string $private=''): void {
 $image=$article['image']??[];$url=$image['url']??'';$hash=$image['sha256']??'';
 if(!is_string($url)||!preg_match('~^/assets/blog/[a-z0-9][a-z0-9-]*\.(?:svg|webp|png|jpg)$~D',$url)||($image['kind']??'')!=='original-diagram'||!is_string($hash)||!preg_match('/^[a-f0-9]{64}$/D',$hash)||!empty($article['testOnly'])||!empty($image['testOnly']))throw new RuntimeException('blog_image_unapproved');
 nodenoBlogImageBytes($image,$private,$public);
 if(trim((string)($image['alt']??''))===''||(int)($image['width']??0)<1||(int)($image['height']??0)<1)throw new RuntimeException('blog_image_metadata_invalid');
 foreach($article['locales']??[] as $translation)if(isset($translation['image']))nodenoBlogPublishable(['image'=>$translation['image']],$public,$private);
}
function nodenoBlogPublishNow(PDO $db,array $bank,string $id,string $public,int $now,string $actor,string $private=''): array {
 if($private!==''){
  $storage=null;
  foreach($db->query('PRAGMA database_list')->fetchAll(PDO::FETCH_ASSOC)as $database){
   if($database['name']==='main'&&is_string($database['file'])&&$database['file']!==''){$storage=nodenoBlogStorage(dirname($database['file']));break;}
  }
  if($storage===null)throw new RuntimeException('blog_storage_unsafe');
  if(!nodenoBlogDeploymentSafe($storage,$private))throw new RuntimeException('blog_deployment_in_progress');
 }
 if(!preg_match('/^[a-z0-9][a-z0-9_-]{0,99}$/D',$id))throw new InvalidArgumentException('blog_article_id_invalid');
 $articles=array_column($bank['articles'],null,'id');
 return nodenoBlogTransaction($db,static function()use($db,$articles,$id,$public,$now,$actor,$private):array{
  $q=$db->prepare('SELECT * FROM blog_queue WHERE article_id=?');$q->execute([$id]);$row=$q->fetch();if(!$row)throw new InvalidArgumentException('blog_article_not_found');
  if($row['status']==='published')return ['published'=>true,'alreadyPublished'=>true,'id'=>$id,'publishedAt'=>nodenoBlogIso((int)$row['published_at'])];
  $article=$articles[$id]??null;if($article===null)throw new InvalidArgumentException('bank_article_missing');
  if(!hash_equals($row['content_hash'],hash('sha256',nodenoBlogJson($article))))throw new RuntimeException('blog_content_integrity_failed');
  nodenoBlogPublishable($article,$public,$private);
  $db->prepare("UPDATE blog_queue SET status='published',published_at=?,payload_json=?,last_error=NULL,updated_at=? WHERE article_id=?")->execute([$now,nodenoBlogJson($article),$now,$id]);
  nodenoBlogEvent($db,'published_manual',$id,$now,['scheduledAt'=>nodenoBlogIso((int)$row['scheduled_at'])],$actor);nodenoBlogSetMeta($db,'last_success_at',nodenoBlogIso($now));
  return ['published'=>true,'alreadyPublished'=>false,'id'=>$id,'publishedAt'=>nodenoBlogIso($now)];
 });
}
function nodenoBlogTick(string $storage,string $private,string $public,?int $now=null): array {
 $now=$now??time();$root=nodenoBlogStorage($storage);$lockPath=$root.'/blog-worker.lock';if(is_link($lockPath))throw new RuntimeException('blog_storage_unsafe');
 $lock=fopen($lockPath,'c');if($lock===false)throw new RuntimeException('blog_worker_lock_unavailable');chmod($lockPath,0600);
 if(!flock($lock,LOCK_EX|LOCK_NB)){fclose($lock);return ['status'=>'busy','published'=>0,'failed'=>0];}
 try{
  $db=nodenoBlogDatabase($root);
  if(!nodenoBlogDeploymentSafe($root,$private)){$waiting=['status'=>'deployment_wait','published'=>0,'failed'=>0,'checkedAt'=>nodenoBlogIso($now)];nodenoBlogSetMeta($db,'heartbeat',$waiting);return $waiting;}
  $bank=nodenoBlogReadBank($private);$seed=nodenoBlogSeed($db,$bank,$now);$articles=array_column($bank['articles'],null,'id');
  $paused=(bool)nodenoBlogMeta($db,'paused',false);$result=['status'=>$paused?'paused':'ok','published'=>0,'failed'=>0,'seeded'=>$seed['added'],'checkedAt'=>nodenoBlogIso($now)];
  if(!$paused){
   $q=$db->prepare("SELECT article_id FROM blog_queue WHERE status IN ('scheduled','retry') AND scheduled_at<=? AND next_attempt_at<=? ORDER BY scheduled_at,ordinal LIMIT 4");$q->execute([$now,$now]);$due=$q->fetchAll();
   foreach($due as $entry){
    $published=nodenoBlogTransaction($db,static function()use($db,$entry,$articles,$public,$now,$private):bool{
     $q=$db->prepare("SELECT * FROM blog_queue WHERE article_id=? AND status IN ('scheduled','retry') AND scheduled_at<=? AND next_attempt_at<=?");$q->execute([$entry['article_id'],$now,$now]);$row=$q->fetch();if(!$row)return false;
     try{
      $article=$articles[$row['article_id']]??null;if($article===null)throw new RuntimeException('bank_article_missing');
      if(!hash_equals($row['content_hash'],hash('sha256',nodenoBlogJson($article))))throw new RuntimeException('blog_content_integrity_failed');
      nodenoBlogPublishable($article,$public,$private);
      $db->prepare("UPDATE blog_queue SET status='published',published_at=?,payload_json=?,last_error=NULL,updated_at=? WHERE article_id=?")->execute([$now,nodenoBlogJson($article),$now,$row['article_id']]);
      nodenoBlogEvent($db,'published',$row['article_id'],$now,['scheduledAt'=>nodenoBlogIso((int)$row['scheduled_at'])]);nodenoBlogSetMeta($db,'last_success_at',nodenoBlogIso($now));return true;
     }catch(Throwable $error){
      $attempt=(int)$row['attempts']+1;$status=$attempt>=5?'dead':'retry';$code=preg_match('/^[a-z_]+$/D',$error->getMessage())?$error->getMessage():'blog_publication_failed';$next=$now+min(86400,300*(2**($attempt-1)));
      $db->prepare('UPDATE blog_queue SET status=?,attempts=?,next_attempt_at=?,last_error=?,updated_at=? WHERE article_id=?')->execute([$status,$attempt,$next,$code,$now,$row['article_id']]);
      nodenoBlogEvent($db,$status,$row['article_id'],$now,['error'=>$code,'attempt'=>$attempt,'nextAttemptAt'=>nodenoBlogIso($next)]);return false;
     }
    });
    if($published)$result['published']++;else $result['failed']++;
   }
  }
  $result['remaining']=(int)$db->query("SELECT COUNT(*) FROM blog_queue WHERE status IN ('scheduled','retry','held')")->fetchColumn();$result['exhausted']=$result['remaining']===0;
  nodenoBlogSetMeta($db,'heartbeat',$result);return $result;
 }finally{flock($lock,LOCK_UN);fclose($lock);}
}
function nodenoBlogMediaHealth(string $storage,string $private,string $public):array {
 $empty=['blogPublished'=>0,'blogMediaReady'=>true];
 if(!file_exists($storage)&&!is_link($storage))return $empty;
 $root=nodenoBlogStorage($storage);$file=$root.'/blog.sqlite';
 if(!file_exists($file)&&!is_link($file))return $empty;
 $db=nodenoBlogDatabase($root);$count=0;
 foreach($db->query("SELECT payload_json FROM blog_queue WHERE status='published'")as $row){
  $article=json_decode($row['payload_json'],true,64,JSON_THROW_ON_ERROR);
  nodenoBlogPublishable($article,$public,$private);$count++;
 }
 return ['blogPublished'=>$count,'blogMediaReady'=>true];
}
