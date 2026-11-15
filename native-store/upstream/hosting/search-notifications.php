<?php
declare(strict_types=1);

// Durable change detection and delivery. All storage stays outside the web root.
function nodenoSearchUrl(string $url):bool {
 if(strlen($url)>2048)return false;
 $p=parse_url($url);if(!$p||($p['scheme']??'')!=='https'||($p['host']??'')!=='nodenohome.com'||isset($p['port'])||isset($p['fragment'])||isset($p['user'])||isset($p['pass']))return false;
 $path=$p['path']??'/';parse_str($p['query']??'',$q);
 if($path==='/')return !array_diff(array_keys($q),['lang','product','page','category','set','pg'])&&isset($q['lang'])&&in_array($q['lang'],['tr','en','ru','ar','de','az','kk','tk','uz','ky','fa'],true)&&!array_filter($q,'is_array')&&(!isset($q['page'])||in_array($q['page'],['home','catalog','categories','help','shipping','wholesale','sets'],true));
 return (bool)preg_match('~^/blog(?:/[a-z0-9]+(?:-[a-z0-9]+)*)?$~D',$path)&&!array_diff(array_keys($q),['lang'])&&(!isset($q['lang'])||in_array($q['lang'],['tr','en','ru','ar'],true));
}
function nodenoSearchSchema(PDO $db):void {
 $db->exec('CREATE TABLE IF NOT EXISTS search_snapshot(url TEXT PRIMARY KEY,fingerprint TEXT NOT NULL);CREATE TABLE IF NOT EXISTS search_meta(name TEXT PRIMARY KEY,value_json TEXT NOT NULL);');
}
function nodenoSearchMeta(PDO $db,string $name,$default=null){$q=$db->prepare('SELECT value_json FROM search_meta WHERE name=?');$q->execute([$name]);$v=$q->fetchColumn();return $v===false?$default:json_decode($v,true,64,JSON_THROW_ON_ERROR);}
function nodenoSearchSet(PDO $db,string $name,$value):void {$db->prepare('INSERT INTO search_meta(name,value_json)VALUES(?,?) ON CONFLICT(name)DO UPDATE SET value_json=excluded.value_json')->execute([$name,json_encode($value,JSON_THROW_ON_ERROR)]);}
function nodenoSearchScan(PDO $db,array $current,array $baseline,int $now):array {
 foreach($current as $u=>$h)if(!nodenoSearchUrl($u)||!is_string($h)||!preg_match('/^[a-f0-9]{64}$/D',$h))throw new RuntimeException('search_snapshot_invalid');
 $db->exec('BEGIN IMMEDIATE');
 try{
  $old=$db->query('SELECT url,fingerprint FROM search_snapshot')->fetchAll(PDO::FETCH_KEY_PAIR);$first=nodenoSearchMeta($db,'initialized',false)!==true;$accepted=$first?array_fill_keys($baseline,true):[];
  $insert=$db->prepare("INSERT OR IGNORE INTO control_jobs(id,type,status,request_json,next_attempt_at,created_at,updated_at,idempotency_key)VALUES(?,'indexnow','queued',?,?,?,?,?)");$queued=0;
  $enqueue=static function(string $url,string $fingerprint)use($db,$insert,$now,&$queued):void {
   // Each change has its own key. A->B->A is still a new publication event.
   $id=bin2hex(random_bytes(16));$insert->execute(['search_'.$id,json_encode([$url],JSON_THROW_ON_ERROR|JSON_UNESCAPED_SLASHES),$now,$now,$now,hash('sha256',$url."\0".$fingerprint."\0".$id)]);$queued++;
  };
  foreach($current as $url=>$hash)if(($old[$url]??null)!==$hash&&!($first&&isset($accepted[$url])))$enqueue($url,$hash);
  if(!$first)foreach($old as $url=>$hash)if(!isset($current[$url]))$enqueue($url,'deleted');
  $upsert=$db->prepare('INSERT INTO search_snapshot(url,fingerprint)VALUES(?,?) ON CONFLICT(url)DO UPDATE SET fingerprint=excluded.fingerprint');foreach($current as $u=>$h)$upsert->execute([$u,$h]);
  foreach($old as $u=>$h)if(!isset($current[$u]))$db->prepare('DELETE FROM search_snapshot WHERE url=?')->execute([$u]);
  nodenoSearchSet($db,'initialized',true);nodenoSearchSet($db,'lastScanAt',$now);$db->exec('COMMIT');return ['tracked'=>count($current),'queued'=>$queued,'baselineApplied'=>$first];
 }catch(Throwable $e){$db->exec('ROLLBACK');throw $e;}
}
function nodenoSearchRetry(int $code,int $attempt,?string $header,int $now):array {
 if($code===200)return ['status'=>'submitted','next'=>$now];
 if(in_array($code,[400,404,405,410,422],true)||$attempt>=20)return ['status'=>'dead','next'=>$now];
 $delay=min(21600,300*(2**min(7,max(0,$attempt-1))));
 if($code===403)$delay=max(900,$delay);
 if($code===429){$given=ctype_digit($header??'')?(int)$header:((strtotime($header??'')?:$now)-$now);$delay=max($delay,min(86400,max(60,$given)));}
 return ['status'=>$code===202?'pending_verification':'retry','next'=>$now+$delay];
}
function nodenoSearchPost(array $urls,string $key,string $endpoint):array {
 if(!in_array($endpoint,['https://yandex.com/indexnow','https://api.indexnow.org/indexnow'],true)||!preg_match('/^[a-zA-Z0-9-]{8,128}$/D',$key)||!$urls||count($urls)>10000||count(array_filter($urls,'nodenoSearchUrl'))!==count($urls))throw new RuntimeException('search_request_invalid');
 $retry=null;$c=curl_init($endpoint);curl_setopt_array($c,[CURLOPT_POST=>true,CURLOPT_POSTFIELDS=>json_encode(['host'=>'nodenohome.com','key'=>$key,'keyLocation'=>'https://nodenohome.com/'.$key.'.txt','urlList'=>array_values($urls)],JSON_THROW_ON_ERROR|JSON_UNESCAPED_SLASHES),CURLOPT_HTTPHEADER=>['Content-Type: application/json; charset=utf-8'],CURLOPT_RETURNTRANSFER=>true,CURLOPT_CONNECTTIMEOUT=>10,CURLOPT_TIMEOUT=>45,CURLOPT_FOLLOWLOCATION=>false,CURLOPT_SSL_VERIFYPEER=>true,CURLOPT_SSL_VERIFYHOST=>2,CURLOPT_HEADERFUNCTION=>static function($c,string $line)use(&$retry):int{if(stripos($line,'Retry-After:')===0)$retry=trim(substr($line,12));return strlen($line);}]);
 $body=curl_exec($c);$code=$body===false?0:(int)curl_getinfo($c,CURLINFO_HTTP_CODE);curl_close($c);return ['httpStatus'=>$code,'retryAfter'=>$retry];
}
function nodenoSearchDrain(PDO $db,int $now,string $key,string $endpoint,?callable $transport=null):array {
 $transport=$transport??'nodenoSearchPost';
 $db->prepare("UPDATE control_jobs SET status='retry',next_attempt_at=? WHERE type='indexnow' AND status='processing' AND updated_at<?")->execute([$now,$now-600]);
 $jobs=$db->prepare("SELECT * FROM control_jobs WHERE type='indexnow' AND status IN ('queued','failed','retry','pending_verification') AND next_attempt_at<=? ORDER BY created_at,id LIMIT 500");$jobs->execute([$now]);$selected=[];$urls=[];
 foreach($jobs->fetchAll(PDO::FETCH_ASSOC)as $job){
  $list=json_decode($job['request_json'],true);if(!is_array($list)||!$list||count($list)>10000||array_filter($list,static fn($u)=>!is_string($u)||!nodenoSearchUrl($u))){$db->prepare("UPDATE control_jobs SET status='dead',result_json=?,updated_at=? WHERE id=?")->execute(['{"error":"invalid_public_urls"}',$now,$job['id']]);continue;}
  if(count($urls)+count($list)>10000)break;
  foreach($list as $url)$urls[$url]=true;$selected[]=$job;
 }
 if(!$selected)return ['httpStatus'=>null,'urlCount'=>0,'jobs'=>0];
 // Commit a recoverable lease before network I/O; publication never waits for the engine.
 foreach($selected as $job)$db->prepare("UPDATE control_jobs SET status='processing',updated_at=? WHERE id=?")->execute([$now,$job['id']]);
 try{$response=$transport(array_keys($urls),$key,$endpoint);}catch(Throwable $e){$response=['httpStatus'=>0,'retryAfter'=>null];}
 $code=(int)($response['httpStatus']??0);
 foreach($selected as $job){$attempt=(int)$job['attempts']+1;$next=nodenoSearchRetry($code,$attempt,$response['retryAfter']??null,$now);$result=['httpStatus'=>$code,'urlCount'=>count($urls),'endpoint'=>$endpoint,'ownershipVerified'=>$code===200];$db->prepare('UPDATE control_jobs SET status=?,attempts=?,next_attempt_at=?,result_json=?,updated_at=? WHERE id=? AND status=\'processing\'')->execute([$next['status'],$attempt,$next['next'],json_encode($result,JSON_THROW_ON_ERROR),$now,$job['id']]);}
 return ['httpStatus'=>$code,'urlCount'=>count($urls),'jobs'=>count($selected),'ownershipVerified'=>$code===200];
}
function nodenoSearchSnapshot(array $catalog,array $config,array $blog=[]):array {
 require_once __DIR__.'/seo.php';$out=[];$hashes=[];$seo=hash('sha256',json_encode($config['seo']??[],JSON_THROW_ON_ERROR));
 foreach($catalog['products']??[]as $p)$hashes[(string)$p['id']]=hash('sha256',json_encode($p,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE));
 $pageHash=hash('sha256',json_encode([$catalog['categories']??[],$config['collections']??[],$config['seo']??[]],JSON_THROW_ON_ERROR));
 foreach(NODENO_SEO_LOCALES as $lang)foreach(['products','pages']as $kind){
  $xml=simplexml_load_string(nodenoSeoSitemap($catalog,$config,$kind,$lang));if($xml===false)throw new RuntimeException('search_sitemap_invalid');
  foreach($xml->url as $entry){$url=(string)$entry->loc;parse_str(parse_url($url,PHP_URL_QUERY)??'',$q);$base=isset($q['product'])?($hashes[$q['product']]??''):$pageHash;$out[$url]=hash('sha256',$base.$lang.$seo);}
 }
 if($blog){require_once __DIR__.'/blog.php';foreach(['tr','en','ru','ar']as $lang){$out['https://nodenohome.com'.nodenoBlogUrl('',$lang)]=hash('sha256',json_encode(array_column($blog,'id')).$lang);foreach($blog as $a)if($lang==='tr'||isset($a['locales'][$lang]))$out['https://nodenohome.com'.nodenoBlogUrl($a['slug'],$lang)]=hash('sha256',json_encode($a,JSON_THROW_ON_ERROR).$lang);}}
 return $out;
}
function nodenoSearchLock(string $root,callable $work):array {
 $path=$root.'/search-notifications.lock';if(is_link($path))throw new RuntimeException('search_storage_unsafe');$h=fopen($path,'c');if($h===false)throw new RuntimeException('search_lock_failed');chmod($path,0600);
 if(!flock($h,LOCK_EX|LOCK_NB)){fclose($h);return ['status'=>'busy'];}
 try{return $work();}finally{flock($h,LOCK_UN);fclose($h);}
}
function nodenoSearchTick(string $storage,string $private,array $bootstrap,int $now,?callable $transport=null):array {
 require_once $private.'/control-indexnow.php';$root=nodenoAccountStorage($storage);$db=nodenoControlDatabase($root);nodenoSearchSchema($db);
 return nodenoSearchLock($root,static function()use($db,$root,$private,$bootstrap,$now,$transport):array{
  if(!nodenoSearchMeta($db,'configured',false)){
   if(!preg_match('/^[a-f0-9]{32}$/D',$bootstrap['key']??'')||($bootstrap['endpoint']??'')!=='https://yandex.com/indexnow')throw new RuntimeException('search_bootstrap_invalid');
   nodenoControlSetSetting($db,'indexnow:key',$bootstrap['key']);nodenoControlSetSetting($db,'indexnow:endpoint',$bootstrap['endpoint']);nodenoSearchSet($db,'configured',true);
  }
  $manifest=json_decode(file_get_contents($private.'/release.json'),true,512,JSON_THROW_ON_ERROR);$release=$manifest['releaseHash'];$scan=[];
  if($now-(int)nodenoSearchMeta($db,'lastScanAt',0)>=300||nodenoSearchMeta($db,'releaseHash')!==$release||nodenoSearchMeta($db,'scanRequested',false)){
   $catalog=json_decode(file_get_contents($private.'/catalog.json'),true,512,JSON_THROW_ON_ERROR);$config=json_decode(file_get_contents($private.'/config.json'),true,512,JSON_THROW_ON_ERROR);$projection=nodenoControlPublicState($db,$catalog,$config);$blog=[];
   if(is_file($private.'/blog-worker.php')){require_once $private.'/blog-worker.php';$blogDb=nodenoBlogDatabase($root);foreach($blogDb->query("SELECT payload_json FROM blog_queue WHERE status='published'")as $row){$article=json_decode($row['payload_json'],true,64,JSON_THROW_ON_ERROR);if(is_array($article))$blog[]=$article;}}
   $snapshot=nodenoSearchSnapshot($projection['catalog'],$projection['config'],$blog);unset($catalog,$projection,$config,$blog,$blogDb);$scan=nodenoSearchScan($db,$snapshot,$bootstrap['baselineUrls']??[],$now);nodenoSearchSet($db,'releaseHash',$release);nodenoSearchSet($db,'scanRequested',false);
  }
  $sent=nodenoSearchDrain($db,$now,(string)nodenoControlSetting($db,'indexnow:key'),(string)nodenoControlSetting($db,'indexnow:endpoint','https://yandex.com/indexnow'),$transport);
  $counts=[];foreach($db->query("SELECT status,COUNT(*) n FROM control_jobs WHERE type='indexnow' GROUP BY status")as $r)$counts[$r['status']]=(int)$r['n'];$heartbeat=['status'=>'ok','checkedAt'=>$now,'releaseHash'=>$release,'scan'=>$scan,'delivery'=>$sent,'counts'=>$counts];nodenoSearchSet($db,'heartbeat',$heartbeat);return $heartbeat;
 });
}
