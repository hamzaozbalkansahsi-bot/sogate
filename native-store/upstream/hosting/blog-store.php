<?php
declare(strict_types=1);

// Blog content and its durable queue are isolated from customer/account storage.
function nodenoBlogIso(int $time): string { return gmdate('Y-m-d\TH:i:s\Z',$time); }
function nodenoBlogJson(array $value): string { return json_encode($value,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR); }
function nodenoBlogDeploymentSafe(string $storage,string $private):bool {
 $home=dirname($storage);$runtime=$home.'/nodeno-runtime.php';if(!is_file($runtime))return true;
 if(is_link($runtime)||is_dir($home.'/nodeno-deploy-lock'))return false;if(function_exists('opcache_invalidate'))@opcache_invalidate($runtime,true);
 $configuration=require $runtime;$active=$configuration['privateRoot']??null;if(!is_string($active)||realpath($active)!==realpath($private))return false;return !is_dir($home.'/nodeno-deploy-lock');
}
function nodenoBlogWithin(string $path,string $root): bool {
 $path=str_replace('\\','/',$path);$root=rtrim(str_replace('\\','/',$root),'/');
 if(DIRECTORY_SEPARATOR==='\\'){$path=strtolower($path);$root=strtolower($root);}
 return $path===$root||str_starts_with($path,$root.'/');
}
function nodenoBlogImageBytes(array $image,string $private,string $public):string {
 $url=$image['url']??'';if(!is_string($url)||!preg_match('~^/assets/blog/[a-z0-9][a-z0-9-]*\.(?:svg|webp|png|jpg)$~D',$url))throw new RuntimeException('blog_image_unapproved');
 if(($image['storage']??'')==='private-bundle'){
  $root=realpath($private);$indexPath=$private.'/blog-images.json';$blobPath=$private.'/blog-images.bin';$index=realpath($indexPath);$blob=realpath($blobPath);
  if($root===false||$index===false||$blob===false||!nodenoBlogWithin($index,$root)||!nodenoBlogWithin($blob,$root)||is_link($indexPath)||is_link($blobPath))throw new RuntimeException('blog_image_bundle_unavailable');
  static $indexes=[];if(!isset($indexes[$index]))$indexes[$index]=json_decode((string)file_get_contents($index),true,512,JSON_THROW_ON_ERROR);$record=$indexes[$index]['files'][$url]??null;
  if(!is_array($record)||!is_int($record['offset']??null)||!is_int($record['length']??null)||$record['offset']<0||$record['length']<1||$record['length']>2000000||$record['offset']+$record['length']>filesize($blob)||!hash_equals((string)($image['sha256']??''),(string)($record['sha256']??'')))throw new RuntimeException('image_integrity_failed');
  $bytes=file_get_contents($blob,false,null,$record['offset'],$record['length']);if(!is_string($bytes)||strlen($bytes)!==$record['length']||!hash_equals((string)$image['sha256'],hash('sha256',$bytes)))throw new RuntimeException('image_integrity_failed');return $bytes;
 }
 $root=realpath($public);$file=realpath($public.$url);if($root===false||$file===false||!nodenoBlogWithin($file,$root)||is_link($public.$url)||!is_file($file))throw new RuntimeException('image_integrity_failed');$bytes=file_get_contents($file);if(!is_string($bytes)||!hash_equals((string)($image['sha256']??''),hash('sha256',$bytes)))throw new RuntimeException('image_integrity_failed');return $bytes;
}
function nodenoBlogStorage(string $storage): string {
 if(is_link($storage))throw new RuntimeException('blog_storage_unsafe');
 $root=realpath($storage);$requestedDocument=$_SERVER['DOCUMENT_ROOT']??'';$document=$requestedDocument===''?false:realpath($requestedDocument);
 $stat=@lstat($storage);
 // Windows directory junctions have a zero lstat type even though is_link is false.
 if($root===false||!is_dir($root)||$stat===false||($stat['mode']&0170000)!==0040000||($document!==false&&nodenoBlogWithin($root,$document)))throw new RuntimeException('blog_storage_unsafe');
 return $root;
}
function nodenoBlogDatabase(string $storage): PDO {
 $root=nodenoBlogStorage($storage);$file=$root.'/blog.sqlite';
 foreach([$file,$file.'-wal',$file.'-shm'] as $part)if(is_link($part))throw new RuntimeException('blog_storage_unsafe');
 $db=new PDO('sqlite:'.$file,null,null,[PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION,PDO::ATTR_DEFAULT_FETCH_MODE=>PDO::FETCH_ASSOC]);
 chmod($file,0600);$db->exec('PRAGMA busy_timeout=5000; PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL; PRAGMA foreign_keys=ON');
 $db->exec("CREATE TABLE IF NOT EXISTS blog_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
 CREATE TABLE IF NOT EXISTS blog_queue(article_id TEXT PRIMARY KEY,slug TEXT NOT NULL UNIQUE,ordinal INTEGER NOT NULL UNIQUE,scheduled_at INTEGER NOT NULL,status TEXT NOT NULL CHECK(status IN ('scheduled','retry','held','published','dead')),attempts INTEGER NOT NULL DEFAULT 0,next_attempt_at INTEGER NOT NULL DEFAULT 0,published_at INTEGER,last_error TEXT,content_hash TEXT NOT NULL,payload_json TEXT,updated_at INTEGER NOT NULL);
 CREATE INDEX IF NOT EXISTS blog_queue_due ON blog_queue(status,scheduled_at,next_attempt_at);
 CREATE TABLE IF NOT EXISTS blog_events(id INTEGER PRIMARY KEY AUTOINCREMENT,article_id TEXT,event TEXT NOT NULL,actor TEXT NOT NULL,occurred_at INTEGER NOT NULL,detail_json TEXT NOT NULL)");
 foreach([$file.'-wal',$file.'-shm'] as $part)if(is_file($part))chmod($part,0600);
 return $db;
}
function nodenoBlogTransaction(PDO $db,callable $work) {
 $db->exec('BEGIN IMMEDIATE');try{$result=$work();$db->exec('COMMIT');return $result;}catch(Throwable $e){$db->exec('ROLLBACK');throw $e;}
}
function nodenoBlogMeta(PDO $db,string $key,$default=null) {
 $q=$db->prepare('SELECT value FROM blog_meta WHERE key=?');$q->execute([$key]);$value=$q->fetchColumn();return $value===false?$default:json_decode($value,true,64,JSON_THROW_ON_ERROR);
}
function nodenoBlogSetMeta(PDO $db,string $key,$value): void {
 $q=$db->prepare('INSERT INTO blog_meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value');$q->execute([$key,json_encode($value,JSON_THROW_ON_ERROR)]);
}
function nodenoBlogEvent(PDO $db,string $event,?string $id,int $now,array $detail=[],string $actor='worker'): void {
 $db->prepare('INSERT INTO blog_events(article_id,event,actor,occurred_at,detail_json) VALUES(?,?,?,?,?)')->execute([$id,$event,$actor,$now,nodenoBlogJson($detail)]);
}
function nodenoBlogReadBank(string $private): array {
 $root=realpath($private);$file=$private.'/blog-bank.json';$resolved=realpath($file);$rootStat=@lstat($private);
 if($root===false||$resolved===false||is_link($private)||$rootStat===false||($rootStat['mode']&0170000)!==0040000||is_link($file)||!nodenoBlogWithin($resolved,$root)||filesize($resolved)>100000000)throw new RuntimeException('blog_bank_unavailable');
 $bank=json_decode(file_get_contents($resolved),true,64,JSON_THROW_ON_ERROR);
 if(!is_array($bank)||($bank['schemaVersion']??0)!==1||($bank['timezone']??'')!=='Europe/Istanbul'||($bank['dailySlots']??[])!==['09:30','18:30']||!is_array($bank['articles']??null)||count($bank['articles'])===0)throw new RuntimeException('blog_bank_invalid');
 $ids=[];$slugs=[];
 foreach($bank['articles'] as $article){
  $id=$article['id']??'';$slug=$article['slug']??'';
  if(!is_string($id)||!is_string($slug)||!preg_match('/^[a-z0-9][a-z0-9_-]{0,99}$/D',$id)||!preg_match('/^[a-z0-9]+(?:-[a-z0-9]+)*$/D',$slug)||strlen($slug)>180||isset($ids[$id])||isset($slugs[$slug]))throw new RuntimeException('bank_article_identity_invalid');
  if(!is_string($article['title']??null)||trim($article['title'])===''||!is_array($article['sections']??null)||!is_array($article['image']??null)||!empty($article['testOnly']))throw new RuntimeException('bank_article_invalid');
  $ids[$id]=true;$slugs[$slug]=true;
 }
 if(isset($bank['startDate'])&&(!is_string($bank['startDate'])||!preg_match('/^\d{4}-\d{2}-\d{2}$/D',$bank['startDate'])))throw new RuntimeException('bank_start_date_invalid');
 return $bank;
}
function nodenoBlogSeed(PDO $db,array $bank,int $now): array {
 return nodenoBlogTransaction($db,static function()use($db,$bank,$now):array{
  $start=nodenoBlogMeta($db,'start_date');
  if($start===null){$start=$bank['startDate']??(new DateTimeImmutable('@'.$now))->setTimezone(new DateTimeZone('Europe/Istanbul'))->format('Y-m-d');nodenoBlogSetMeta($db,'start_date',$start);nodenoBlogSetMeta($db,'paused',false);}
  $inserted=0;$ordinal=(int)$db->query('SELECT COALESCE(MAX(ordinal),-1) FROM blog_queue')->fetchColumn()+1;
  $find=$db->prepare('SELECT slug,status,content_hash FROM blog_queue WHERE article_id=?');
  foreach($bank['articles'] as $article){
   $hash=hash('sha256',nodenoBlogJson($article));$find->execute([$article['id']]);$existing=$find->fetch();
   if($existing){
    if($existing['slug']!==$article['slug'])throw new RuntimeException('blog_article_slug_changed');
    if($existing['status']!=='published'&&!hash_equals($existing['content_hash'],$hash)){$db->prepare('UPDATE blog_queue SET content_hash=?,updated_at=? WHERE article_id=?')->execute([$hash,$now,$article['id']]);nodenoBlogEvent($db,'content_updated',$article['id'],$now);}
    continue;
   }
   $date=(new DateTimeImmutable($start.' 00:00:00',new DateTimeZone('Europe/Istanbul')))->modify('+'.intdiv($ordinal,2).' days');
   [$hour,$minute]=array_map('intval',explode(':',$bank['dailySlots'][$ordinal%2]));$scheduled=$date->setTime($hour,$minute)->getTimestamp();
   if(($bank['launchImmediately']??false)===true&&$ordinal<2)$scheduled=$now;
   $db->prepare("INSERT INTO blog_queue(article_id,slug,ordinal,scheduled_at,status,content_hash,updated_at) VALUES(?,?,?,?,'scheduled',?,?)")->execute([$article['id'],$article['slug'],$ordinal,$scheduled,$hash,$now]);
   $inserted++;$ordinal++;
  }
  if($inserted)nodenoBlogEvent($db,'seeded',null,$now,['added'=>$inserted]);
  nodenoBlogSetMeta($db,'bank_count',count($bank['articles']));return ['added'=>$inserted,'total'=>(int)$db->query('SELECT COUNT(*) FROM blog_queue')->fetchColumn()];
 });
}
function nodenoBlogLocale(array $article,string $locale): ?array {
 if($locale==='tr')$value=$article;
 else{if(!isset($article['locales'][$locale])||!is_array($article['locales'][$locale]))return null;$translation=$article['locales'][$locale];foreach(['title','description','intro','sections'] as $field)if(empty($translation[$field]))return null;$value=array_replace($article,$translation);if(isset($translation['imageAlt']))$value['image']['alt']=$translation['imageAlt'];}
 $value['locale']=$locale;$value['availableLocales']=['tr'];
 foreach($article['locales']??[] as $code=>$translation)if(!empty($translation['title'])&&!empty($translation['description'])&&!empty($translation['intro'])&&!empty($translation['sections']))$value['availableLocales'][]=$code;
 $value['imageVariants']=['tr'=>$article['image']];foreach($article['locales']??[] as $code=>$translation)if(isset($translation['image']))$value['imageVariants'][$code]=$translation['image'];
 unset($value['locales']);return $value;
}
function nodenoBlogSnapshot(array $row,string $locale): ?array {
 if($row['status']!=='published'||empty($row['payload_json'])||$row['published_at']===null)return null;
 $article=nodenoBlogLocale(json_decode($row['payload_json'],true,64,JSON_THROW_ON_ERROR),$locale);if($article===null)return null;
 $article['publishedAt']=nodenoBlogIso((int)$row['published_at']);$article['scheduledAt']=nodenoBlogIso((int)$row['scheduled_at']);return $article;
}
function nodenoBlogPublished(PDO $db,array $bank,string $locale='tr',array $options=[]): array {
 $items=[];$query=trim((string)($options['q']??''));$category=(string)($options['category']??'');
 foreach($db->query("SELECT * FROM blog_queue WHERE status='published' ORDER BY published_at DESC,ordinal DESC") as $row){
  $article=nodenoBlogSnapshot($row,$locale);if($article===null||($category!==''&&$article['category']!==$category))continue;
  $fold=static fn(string $text):string=>strtr($text,['İ'=>'i','I'=>'i','ı'=>'i','Ş'=>'s','ş'=>'s','Ğ'=>'g','ğ'=>'g','Ç'=>'c','ç'=>'c','Ü'=>'u','ü'=>'u','Ö'=>'o','ö'=>'o']);
  $searchText=$article['title'].' '.$article['description'].' '.implode(' ',$article['keywords']??[]).' '.$article['intro'].' '.implode(' ',$article['checklist']??[]);foreach($article['sections']as $section)$searchText.=' '.$section['heading'].' '.implode(' ',$section['paragraphs']).' '.implode(' ',$section['list']??[]);
  if($query!==''&&!preg_match('/'.preg_quote($fold($query),'/').'/iu',$fold($searchText)))continue;
  $items[]=$article;
 }
 $total=count($items);$perPage=max(1,min(100,(int)($options['perPage']??12)));$pages=max(1,(int)ceil($total/$perPage));$page=max(1,min($pages,(int)($options['page']??1)));
 return ['items'=>array_slice($items,($page-1)*$perPage,$perPage),'total'=>$total,'page'=>$page,'pages'=>$pages,'perPage'=>$perPage];
}
function nodenoBlogArticle(PDO $db,array $bank,string $slug,string $locale='tr'): ?array {
 $q=$db->prepare("SELECT * FROM blog_queue WHERE slug=? AND status='published'");$q->execute([$slug]);$row=$q->fetch();return $row?nodenoBlogSnapshot($row,$locale):null;
}
function nodenoBlogQueueRow(array $row,array $articles): array {
 $article=$articles[$row['article_id']]??[];
 if($row['status']==='published'&&!empty($row['payload_json']))$article=json_decode($row['payload_json'],true,64,JSON_THROW_ON_ERROR);
 $localized=$article?nodenoBlogLocale($article,'tr'):null;
 return ['id'=>$row['article_id'],'slug'=>$row['slug'],'title'=>$article['title']??$row['slug'],'category'=>$article['category']??null,'tool'=>$article['tool']??null,'sourceCount'=>count($article['sources']??[]),'availableLocales'=>$localized['availableLocales']??[],'status'=>$row['status'],'scheduledAt'=>nodenoBlogIso((int)$row['scheduled_at']),'publishedAt'=>$row['published_at']===null?null:nodenoBlogIso((int)$row['published_at']),'attempts'=>(int)$row['attempts'],'nextAttemptAt'=>$row['next_attempt_at']?nodenoBlogIso((int)$row['next_attempt_at']):null,'lastError'=>$row['last_error']];
}
function nodenoBlogStatus(PDO $db,array $bank): array {
 $counts=array_fill_keys(['scheduled','retry','held','published','dead'],0);foreach($db->query('SELECT status,COUNT(*) AS count FROM blog_queue GROUP BY status') as $row)$counts[$row['status']]=(int)$row['count'];
 $articles=array_column($bank['articles'],null,'id');$next=[];foreach($db->query("SELECT * FROM blog_queue WHERE status IN ('scheduled','retry','held','dead') ORDER BY scheduled_at LIMIT 100") as $row)$next[]=nodenoBlogQueueRow($row,$articles);
 $queue=[];foreach($db->query('SELECT * FROM blog_queue ORDER BY ordinal LIMIT 1000') as $row)$queue[]=nodenoBlogQueueRow($row,$articles);
 $ready=$counts['scheduled']+$counts['retry'];$last=$db->query("SELECT MAX(scheduled_at) FROM blog_queue WHERE status IN ('scheduled','retry')")->fetchColumn();
 $logs=[];foreach($db->query('SELECT * FROM blog_events ORDER BY id DESC LIMIT 100') as $row){$detail=json_decode($row['detail_json'],true,64,JSON_THROW_ON_ERROR);$logs[]=['id'=>(int)$row['id'],'articleId'=>$row['article_id'],'event'=>$row['event'],'actor'=>$row['actor'],'at'=>nodenoBlogIso((int)$row['occurred_at']),'error'=>$detail['error']??null,'detail'=>$detail];}
 return ['timezone'=>'Europe/Istanbul','dailySlots'=>['09:30','18:30'],'dailyTarget'=>2,'paused'=>(bool)nodenoBlogMeta($db,'paused',false),'total'=>array_sum($counts),'counts'=>$counts,'next'=>$next,'queue'=>$queue,'queueTruncated'=>array_sum($counts)>count($queue),'logs'=>$logs,'heartbeat'=>nodenoBlogMeta($db,'heartbeat'),'lastSuccessAt'=>nodenoBlogMeta($db,'last_success_at'),'bankRemaining'=>$counts['scheduled']+$counts['retry']+$counts['held'],'readyRemaining'=>$ready,'daysRemaining'=>(int)ceil($ready/2),'lastScheduledAt'=>$last===null||$last===false?null:nodenoBlogIso((int)$last),'lowBankWarning'=>$ready<28,'lowBankThresholdDays'=>14,'exhausted'=>($counts['scheduled']+$counts['retry']+$counts['held'])===0];
}
function nodenoBlogCommand(PDO $db,array $bank,string $action,array $body,string $actor,int $now): array {
 return nodenoBlogTransaction($db,static function()use($db,$bank,$action,$body,$actor,$now):array{
  if($action==='pause'||$action==='resume'){nodenoBlogSetMeta($db,'paused',$action==='pause');nodenoBlogEvent($db,$action,null,$now,[],$actor);return ['paused'=>$action==='pause'];}
  $id=$body['id']??'';if(!is_string($id)||!preg_match('/^[a-z0-9][a-z0-9_-]{0,99}$/D',$id))throw new InvalidArgumentException('blog_article_id_invalid');
  $q=$db->prepare('SELECT * FROM blog_queue WHERE article_id=?');$q->execute([$id]);$row=$q->fetch();if(!$row)throw new InvalidArgumentException('blog_article_not_found');
  if($row['status']==='published')throw new InvalidArgumentException('blog_published_immutable');
  if($action==='retry')$db->prepare("UPDATE blog_queue SET status='scheduled',attempts=0,next_attempt_at=0,last_error=NULL,updated_at=? WHERE article_id=?")->execute([$now,$id]);
  elseif($action==='hold')$db->prepare("UPDATE blog_queue SET status='held',updated_at=? WHERE article_id=?")->execute([$now,$id]);
  elseif($action==='schedule'){
   $date=$body['scheduledAt']??'';if(!is_string($date)||!preg_match('/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})$/D',$date))throw new InvalidArgumentException('blog_schedule_invalid');
   $timestamp=(new DateTimeImmutable($date))->getTimestamp();if($timestamp<$now)throw new InvalidArgumentException('blog_schedule_in_past');
   $db->prepare("UPDATE blog_queue SET scheduled_at=?,status='scheduled',next_attempt_at=0,updated_at=? WHERE article_id=?")->execute([$timestamp,$now,$id]);
  }else throw new InvalidArgumentException('blog_action_invalid');
  nodenoBlogEvent($db,$action,$id,$now,[],$actor);return ['saved'=>true,'id'=>$id];
 });
}
