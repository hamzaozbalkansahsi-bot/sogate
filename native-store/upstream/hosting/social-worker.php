<?php
declare(strict_types=1);
require_once __DIR__.'/social-media.php';
require_once __DIR__.'/control-catalog.php';

function nodenoStudioRank(PDO $db,array $catalog):array {
 $products=array_values(array_filter($catalog['products']??[],static fn($p)=>!empty($p['images'])&&empty($p['hidden'])));$scores=[];
 foreach($db->query('SELECT p.product_id,m.metrics_json FROM social_metrics m JOIN social_posts p ON p.id=m.post_id WHERE m.checked_at>'.(time()-28*86400))->fetchAll() as $row){$m=json_decode($row['metrics_json'],true);$views=max(1,(int)($m['views']??$m['impressions']??1));$scores[$row['product_id']]=($scores[$row['product_id']]??0)+min(10,((int)($m['likes']??0)+(int)($m['comments']??0)*2+(int)($m['shares']??0)*3)/$views)*100;}
 usort($products,static function($a,$b)use($scores):int{$difference=($scores[$b['id']]??0)<=>($scores[$a['id']]??0);return $difference?:strcmp(hash('sha256',gmdate('Y-W').'|'.$a['id']),hash('sha256',gmdate('Y-W').'|'.$b['id']));});return $products;
}

function nodenoStudioPlan(PDO $db,array $catalog,array $settings,int $now):int {
 if(!$settings['enabled'])return 0;
 nodenoStudioRetireOldCampaign($db,$catalog);$ranked=array_values(array_filter(nodenoStudioRank($db,$catalog),static fn($p)=>nodenoStudioSegment($p)==='finished'));$reviewed=array_values(array_filter($ranked,static fn($p)=>nodenoStudioCreativeProfile($p)!==null));if($reviewed)$ranked=$reviewed;$unique=[];foreach($ranked as $product){$key=$product['modelId']??$product['id'];if(!isset($unique[$key]))$unique[$key]=$product;}$products=array_values($unique);if(!$products)return 0;
 $added=0;$tz=new DateTimeZone('Europe/Istanbul');$today=(new DateTimeImmutable('@'.$now))->setTimezone($tz)->setTime(0,0);$locales=$settings['locales'];
 foreach(NODENO_SOCIAL_PLATFORMS as $pi=>$platform){
  for($day=0;$day<$settings['planningDays'];$day++){
   $date=$today->modify('+'.$day.' days');$start=$date->getTimestamp();
   // Cancelled slots still count: the planner must honour an operator's cancellation.
   $q=$db->prepare('SELECT id,payload_json FROM social_posts WHERE platform=? AND scheduled_at>=? AND scheduled_at<?');$q->execute([$platform,$start,$start+86400]);$existing=0;foreach($q->fetchAll() as $row)if(!str_starts_with($row['id'],'auto_')||(json_decode($row['payload_json'],true)['creativeVersion']??null)===NODENO_SOCIAL_CREATIVE_VERSION)$existing++;
   for($position=$existing;$position<$settings['dailyPerPlatform'];$position++){
    $locale=$locales[($day+$pi+$position)%count($locales)];$hours=$platform==='linkedin'?[10,14,17]:[12,19,21];$hour=$hours[($day+$position)%count($hours)];
    $slot=$date->setTime($hour,$pi*4+$position)->getTimestamp();if($slot<$now+180)$slot=$now+300+$pi*60+$position*60;
    $themes=['coffee','work','storage','entry','living','kids'];$theme=$themes[($day+$pi+$position)%count($themes)];$pool=array_values(array_filter($products,static fn($p)=>nodenoStudioTopic($p)===$theme));if(!$pool)$pool=$products;$priority=['5015','4088','2395','4775','3808'];usort($pool,static fn($a,$b)=>(array_search($a['id'],$priority,true)===false?999:array_search($a['id'],$priority,true))<=>(array_search($b['id'],$priority,true)===false?999:array_search($b['id'],$priority,true)));$p=$pool[($day+$position+intdiv($pi,6))%count($pool)];$id='auto_'.substr(hash('sha256',NODENO_SOCIAL_CREATIVE_VERSION.'|'.$platform.'|'.$date->format('Y-m-d').'|'.$position),0,40);
    $payload=nodenoStudioCaption($p,$locale,$platform,$day+$position);$format=in_array($platform,['youtube','tiktok'],true)||($platform==='instagram'&&($day+$position)%3===1)?'video':($platform==='instagram'&&count(nodenoStudioCreativeProfile($p)['frames']??[])>=2?'carousel':'image');
    $trend=$db->query('SELECT id FROM social_trends WHERE score>=20 AND observed_at>'.($now-86400).' ORDER BY score DESC,observed_at DESC LIMIT 1')->fetchColumn();if($trend)$payload['trendId']=$trend;
    $q=$db->prepare("INSERT OR IGNORE INTO social_posts(id,platform,locale,product_id,format,payload_json,status,scheduled_at,created_at,updated_at) VALUES(?,?,?,?,?,?,'draft',?,?,?)");$params=[$id,$platform,$locale,$p['id'],$format,json_encode($payload,JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR),$slot,$now,$now];$q->execute($params);if(!$q->rowCount()){ $exists=$db->prepare('SELECT 1 FROM social_posts WHERE id=?');$exists->execute([$id]);if(!$exists->fetchColumn()){for($retry=1;$retry<=10;$retry++){$params[6]=$slot+$retry*60;$q->execute($params);if($q->rowCount())break;}}}$added+=$q->rowCount();
   }
  }
 }
 if($added)nodenoStudioEvent($db,'calendar_planned',null,['posts'=>$added]);return $added;
}

function nodenoStudioTrendFetch(string $country):string {
 if(!in_array($country,['TR','DE','GB','US','SA','RU','KZ','AZ'],true))throw new RuntimeException('Unsupported trend country');
 $body='';$ch=curl_init('https://trends.google.com/trending/rss?geo='.$country);curl_setopt_array($ch,[CURLOPT_FOLLOWLOCATION=>false,CURLOPT_CONNECTTIMEOUT=>8,CURLOPT_TIMEOUT=>12,CURLOPT_SSL_VERIFYPEER=>true,CURLOPT_SSL_VERIFYHOST=>2,CURLOPT_PROTOCOLS=>CURLPROTO_HTTPS,CURLOPT_HTTPHEADER=>['User-Agent: NODENO-Trends/1.0','Accept: application/rss+xml, text/xml'],CURLOPT_WRITEFUNCTION=>static function($ch,string $part)use(&$body):int {if(strlen($body)+strlen($part)>1000000)return 0;$body.=$part;return strlen($part);}]);
 curl_exec($ch);$code=(int)curl_getinfo($ch,CURLINFO_RESPONSE_CODE);$error=curl_errno($ch);curl_close($ch);
 if($error!==0||$code!==200||$body==='')throw new RuntimeException('trend_source_unavailable');return $body;
}

function nodenoStudioTrendImport(PDO $db,string $country,string $xml,int $now):int {
 if(strlen($xml)>1000000||stripos($xml,'<!DOCTYPE')!==false||stripos($xml,'<!ENTITY')!==false)throw new RuntimeException('Unsafe trend source');$previous=libxml_use_internal_errors(true);
 try{$rss=simplexml_load_string($xml,SimpleXMLElement::class,LIBXML_NONET|LIBXML_NOCDATA);if(!$rss||!isset($rss->channel))throw new RuntimeException('Invalid trend feed');$count=0;
  foreach($rss->channel->item as $item){if($count>=60)break;$title=nodenoStudioText((string)$item->title,500);$url=(string)$item->link;$u=parse_url($url);if(($u['scheme']??'')!=='https'||!in_array($u['host']??'',['trends.google.com','www.google.com','google.com'],true))$url='https://trends.google.com/trending?geo='.$country;
   $published=strtotime((string)$item->pubDate)?:$now;if($published>$now+3600||$published<$now-3*86400)continue;$score=nodenoStudioRelevant($title);$id=hash('sha256',$country.'|'.$title);
   $db->prepare('INSERT INTO social_trends(id,source,title,url,country,score,observed_at,published_at) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET observed_at=excluded.observed_at,score=excluded.score')->execute([$id,'google_trends_rss',$title,$url,$country,$score,$now,$published]);$count++;
  }return $count;
 }finally{libxml_clear_errors();libxml_use_internal_errors($previous);}
}

function nodenoStudioRefreshTrends(PDO $db,array $settings,?callable $fetch=null):array {
 $result=[];foreach($settings['countries'] as $country){try{$xml=($fetch??'nodenoStudioTrendFetch')($country);$result[$country]=['ok'=>true,'items'=>nodenoStudioTrendImport($db,$country,$xml,time()),'checkedAt'=>time()];}catch(Throwable $e){$result[$country]=['ok'=>false,'reason'=>'source_unavailable','checkedAt'=>time()];}}
 nodenoControlSetSetting($db,'social:trend-sources',$result);$db->prepare('DELETE FROM social_trends WHERE observed_at<?')->execute([time()-7*86400]);return $result;
}

function nodenoStudioComments(PDO $db,string $root,?callable $transport=null):int {
 $count=0;$posts=$db->query("SELECT * FROM social_posts WHERE status='posted' AND remote_id IS NOT NULL ORDER BY updated_at DESC LIMIT 4")->fetchAll();$channels=nodenoControlSetting($db,'social:channels',[]);
 foreach($posts as $p){$r=nodenoStudioSend($db,$root,'GET','/comments/'.rawurlencode($p['remote_id']),null,$transport);if($r['code']!==200)continue;$remote=nodenoStudioRemotePlatform($p['platform']);foreach(array_slice($r['data'][$remote]??[],0,50) as $m){if(empty($m['commentId'])||!is_string($m['comment']??null)||!empty($m['company']))continue;$sender=(string)($m['from']['id']??$m['userId']??'');if($sender!==''&&$sender===($channels[$p['platform']]['remoteId']??''))continue;$created=strtotime($m['created']??'')?:0;if($created<=0||$created>time()+60)continue;
   $id='si_'.hash('sha256',$p['platform'].'|comment|'.$m['commentId']);$q=$db->prepare("INSERT OR IGNORE INTO social_inbox(id,platform,kind,remote_id,post_id,product_id,sender_id,text,received_at,verified,updated_at) VALUES(?,?,'comment',?,?,?,?,?,?,1,?)");$q->execute([$id,$p['platform'],(string)$m['commentId'],$p['id'],$p['product_id'],$sender,nodenoStudioSlice($m['comment'],6000),$created,time()]);$count+=$q->rowCount();
  }}return $count;
}

function nodenoStudioAnalytics(PDO $db,string $root,?callable $transport=null):int {
 $q=$db->prepare("SELECT p.* FROM social_posts p LEFT JOIN social_metrics m ON p.id=m.post_id WHERE p.status='posted' AND p.remote_id IS NOT NULL AND (m.checked_at IS NULL OR m.checked_at<?) ORDER BY COALESCE(m.checked_at,0) LIMIT 4");$q->execute([time()-1800]);$count=0;
 foreach($q->fetchAll() as $p){$r=nodenoStudioSend($db,$root,'POST','/analytics/post',['id'=>$p['remote_id'],'platforms'=>[nodenoStudioRemotePlatform($p['platform'])]],$transport);if($r['code']!==200)continue;$raw=$r['data'][nodenoStudioRemotePlatform($p['platform'])]['analytics']??null;if(!is_array($raw))continue;$metrics=[];
  foreach(['views'=>['views','videoViews'],'impressions'=>['impressions'],'likes'=>['likes','likeCount'],'comments'=>['comments','commentsCount'],'shares'=>['shares','shareCount'],'clicks'=>['clicks','linkClicks']] as $target=>$fields)foreach($fields as $field)if(isset($raw[$field])&&is_numeric($raw[$field])&&$raw[$field]>=0){$metrics[$target]=(int)$raw[$field];break;}
  if(!$metrics)continue;$db->prepare('INSERT INTO social_metrics(post_id,metrics_json,checked_at) VALUES(?,?,?) ON CONFLICT(post_id) DO UPDATE SET metrics_json=excluded.metrics_json,checked_at=excluded.checked_at')->execute([$p['id'],json_encode($metrics),time()]);$count++;
 }return $count;
}

function nodenoStudioTick(string $root,string $private,string $vault,string $publicRoot,?callable $transport=null,?callable $renderImage=null,?callable $trendFetch=null):array {
 $folder=nodenoStudioRoot($root);$lock=fopen($folder.'/worker.lock','c+b');if(!$lock||!flock($lock,LOCK_EX|LOCK_NB)){if($lock)fclose($lock);return ['status'=>'already_running'];}
 $started=time();$db=nodenoControlDatabase($root);nodenoStudioSchema($db);$result=['status'=>'ok','startedAt'=>$started,'planned'=>0,'rendered'=>0,'published'=>0,'inboxImported'=>0];
 try{
  $catalog=json_decode(file_get_contents($private.'/catalog.json'),true,512,JSON_THROW_ON_ERROR);$config=json_decode(file_get_contents($private.'/config.json'),true,512,JSON_THROW_ON_ERROR);$effective=nodenoControlPublicState($db,$catalog,$config);$catalog=$effective['catalog'];$settings=nodenoStudioSettings($db);
  $actualTransport=$transport??'nodenoStudioHttp';$transport=static function(...$args)use($actualTransport,$started):array {if(time()-$started>=50)return ['code'=>429,'data'=>[]];return $actualTransport(...$args);};
  nodenoControlSetSetting($db,'social:heartbeat',['startedAt'=>$started,'finishedAt'=>null,'status'=>'running','gd'=>function_exists('imagecreatefromstring'),'php'=>PHP_VERSION]);
  if(!$settings['enabled']){$result['status']='paused';return $result;}
  if((nodenoControlSetting($db,'social:last-trend-check',0))<time()-900){nodenoStudioRefreshTrends($db,$settings,$trendFetch);nodenoControlSetSetting($db,'social:last-trend-check',time());}
  nodenoStudioExpire($db,time());
  $result['planned']=nodenoStudioPlan($db,$catalog,$settings,time());
  $drafts=$db->query("SELECT * FROM social_posts WHERE status IN ('draft','ready','blocked') ORDER BY scheduled_at,id LIMIT 200")->fetchAll();
  foreach($drafts as $post){if($result['rendered']>=3||time()-$started>35)break;$payload=json_decode($post['payload_json'],true);if($post['format']==='video'&&!$settings['paidEnabled']&&$post['reason']==='social_budget_or_video_connection_required')continue;if(!empty($payload['assetHashes'])||!empty($payload['videoUrl'])){
    $channel=nodenoControlSetting($db,'social:channels',[])[$post['platform']]??[];
    if($settings['autoPublish']&&!empty($channel['verified'])&&($channel['checkedAt']??0)>time()-86400&&in_array($post['status'],['ready','blocked'],true)&&in_array($post['reason'],['','account_connection_required','publishing_paused','provider_credentials_required'],true))$db->prepare("UPDATE social_posts SET status='scheduled',reason='',version=version+1,updated_at=? WHERE id=? AND version=?")->execute([time(),$post['id'],$post['version']]);
    continue;
   }
   try{$p=nodenoStudioProduct($catalog,$post['product_id']);if($post['format']==='video'){$payload=nodenoStudioRenderVideo($db,$root,$post,$p,$settings,$transport);$reason=empty($payload['videoUrl'])?'video_render_pending':'';}else{$payload['assetHashes']=($renderImage??'nodenoStudioRenderImage')($db,$root,$post,$p,$private,$vault,$publicRoot);$reason='';}
    $status=$reason?'blocked':($settings['autoPublish']||!empty($payload['resumeScheduled'])?'scheduled':'ready');$db->prepare('UPDATE social_posts SET payload_json=?,status=?,reason=?,version=version+1,updated_at=? WHERE id=? AND version=?')->execute([json_encode($payload,JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR),$status,$reason,time(),$post['id'],$post['version']]);$result['rendered']++;
   }catch(Throwable $e){$reason=$e instanceof NodenoControlHttpError?$e->errorCode:'media_preparation_failed';if($post['reason']!==$reason)$db->prepare("UPDATE social_posts SET status='blocked',reason=?,version=version+1,updated_at=? WHERE id=? AND version=?")->execute([$reason,time(),$post['id'],$post['version']]);}
  }
  $provider=nodenoControlSetting($db,'social:provider:meta')??nodenoControlSetting($db,'social:provider:ayrshare');if($provider){$channels=nodenoControlSetting($db,'social:channels',[]);$oldest=$channels?min(array_column($channels,'checkedAt')):0;if($oldest<time()-3600)try{nodenoStudioVerifyChannels($db,$root,$config,$transport);}catch(Throwable $e){nodenoStudioEvent($db,'accounts_check_failed',null);}
   nodenoStudioPollPosts($db,$root,$transport);
   if($settings['autoPublish']){for($i=0;$i<3&&time()-$started<45;$i++){$currentSettings=nodenoStudioSettings($db);if(!$currentSettings['enabled']||!$currentSettings['autoPublish'])break;if(!$post=nodenoStudioClaim($db,time()))break;nodenoStudioPublish($db,$root,$post,$currentSettings,$catalog,$transport);$result['published']+=nodenoStudioRead($db,$post['id'])['status']==='posted'?1:0;}}
   if(time()-$started<40&&nodenoControlSetting($db,'social:last-inbox-check',0)<time()-300){$result['inboxImported']=nodenoStudioReadInbox($db,$root,$transport)+nodenoStudioComments($db,$root,$transport);nodenoControlSetSetting($db,'social:last-inbox-check',time());}
   if(time()-$started<40)nodenoStudioAnalytics($db,$root,$transport);
   $messages=$db->query("SELECT * FROM social_inbox WHERE status='new' ORDER BY received_at DESC LIMIT 5")->fetchAll();foreach($messages as $message){$decision=nodenoStudioReplyDecision($message,$settings,$catalog,time());if($decision['safe']&&$settings['autoReplies'])nodenoStudioReplySend($db,$root,$message,$decision['reply'],true,$transport);else{$db->prepare("UPDATE social_inbox SET status=?,reply=?,reason=?,version=version+1,updated_at=? WHERE id=? AND status='new'")->execute([$decision['safe']?'draft':'review',$decision['reply'],$decision['reason'],time(),$message['id']]);}}
  }
  // No retroactive replies to old messages; retain a bounded private inbox.
  $db->prepare('DELETE FROM social_inbox WHERE received_at<?')->execute([time()-90*86400]);$db->prepare('DELETE FROM social_events WHERE created_at<?')->execute([time()-90*86400]);return $result;
 }catch(Throwable $e){$result['status']='failed';$result['reason']='worker_action_failed';nodenoStudioEvent($db,'worker_failed',null,['exception'=>get_class($e)]);return $result;
 }finally{$result['finishedAt']=time();nodenoControlSetSetting($db,'social:heartbeat',$result+['gd'=>function_exists('imagecreatefromstring'),'php'=>PHP_VERSION]);flock($lock,LOCK_UN);fclose($lock);}
}
