<?php
declare(strict_types=1);
require_once __DIR__.'/social-worker.php';

function nodenoStudioOverview(array $ctx,array $catalog,array $config):array {
 $db=$ctx['db'];$settings=nodenoStudioSettings($db);$channels=nodenoControlSetting($db,'social:channels',[]);$known=array_column($config['socials']??[],'url','id');$accounts=[];
 foreach(NODENO_SOCIAL_PLATFORMS as $p)$accounts[]=['platform'=>$p,'url'=>$known[$p]??null]+($channels[$p]??['verified'=>false,'status'=>'not_connected','checkedAt'=>null]);
 $posts=array_map('nodenoStudioPost',$db->query("SELECT * FROM social_posts ORDER BY CASE WHEN status='cancelled' THEN 1 ELSE 0 END,scheduled_at DESC LIMIT 250")->fetchAll());$counts=[];foreach($db->query('SELECT status,COUNT(*) AS n FROM social_posts GROUP BY status')->fetchAll() as $row)$counts[$row['status']]=(int)$row['n'];
 $providers=[];foreach(['meta','ayrshare','openai','shotstack'] as $name){$p=nodenoControlSetting($db,'social:provider:'.$name);$providers[$name]=['configured'=>(bool)$p,'version'=>$p['version']??0,'status'=>$p['status']??'not_configured'];}
 $metrics=[];foreach($db->query('SELECT m.*,p.platform,p.product_id FROM social_metrics m JOIN social_posts p ON p.id=m.post_id ORDER BY checked_at DESC LIMIT 100')->fetchAll() as $r)$metrics[]=['postId'=>$r['post_id'],'platform'=>$r['platform'],'productId'=>$r['product_id'],'values'=>json_decode($r['metrics_json'],true),'checkedAt'=>(int)$r['checked_at']];
 $sum=$db->prepare('SELECT COALESCE(SUM(reserved_minor),0) FROM social_budget WHERE month=?');$sum->execute([gmdate('Y-m')]);
 $referenced=array_fill_keys(array_column(array_filter($posts,static fn($p)=>$p['status']!=='cancelled'),'productId'),true);$selectable=[];foreach(nodenoStudioRank($db,$catalog) as $p)if((count($selectable)<350&&nodenoStudioSegment($p)==='finished')||isset($referenced[$p['id']]))$selectable[]=$p;
 $products=[];foreach($selectable as $p)$products[]=['id'=>$p['id'],'name'=>nodenoStudioName($p,'tr'),'image'=>$p['images'][$p['coverIndex']??0]??$p['images'][0]];
 return ['settings'=>$settings,'accounts'=>$accounts,'providers'=>$providers,'posts'=>$posts,'counts'=>$counts,'products'=>$products,'heartbeat'=>nodenoControlSetting($db,'social:heartbeat'), 'trendSources'=>nodenoControlSetting($db,'social:trend-sources',[]),'trends'=>$db->query('SELECT * FROM social_trends ORDER BY score DESC,observed_at DESC LIMIT 120')->fetchAll(),'music'=>array_map(static fn($r)=>['id'=>$r['id']]+json_decode($r['data_json'],true),$db->query('SELECT * FROM social_music ORDER BY created_at DESC LIMIT 50')->fetchAll()),'inbox'=>$db->query('SELECT id,platform,kind,post_id,product_id,text,received_at,status,reply,reason,version FROM social_inbox ORDER BY received_at DESC LIMIT 150')->fetchAll(),'metrics'=>$metrics,'events'=>array_map(static fn($r)=>['id'=>$r['id'],'type'=>$r['type'],'postId'=>$r['post_id'],'detail'=>json_decode($r['detail_json'],true),'createdAt'=>(int)$r['created_at']],$db->query('SELECT * FROM social_events ORDER BY id DESC LIMIT 60')->fetchAll()),'reservedBudgetMinor'=>(int)$sum->fetchColumn(),'at'=>time()];
}

function nodenoStudioUpdateSettings(array $ctx,array $body):array {
 nodenoControlRequire($ctx,'settings.write',true);$db=$ctx['db'];return nodenoControlTransaction($db,static function()use($ctx,$db,$body):array {
  $settings=nodenoStudioSettings($db);if(($body['version']??null)!==$settings['version'])throw new NodenoControlHttpError(409,'version_conflict');
  $allowed=['version','enabled','autoPublish','autoReplies','paidEnabled','monthlyBudgetMinor','dailyPerPlatform','planningDays','locales','countries','textReservationMinor','videoReservationMinor','xAiApproval','xApprovalReference'];foreach($body as $key=>$value)if(!in_array($key,$allowed,true))throw new NodenoControlHttpError(422,'social_setting_invalid');
  foreach(['enabled','autoPublish','autoReplies','paidEnabled','xAiApproval'] as $key)if(array_key_exists($key,$body)&&!is_bool($body[$key]))throw new NodenoControlHttpError(422,'social_setting_invalid');
  foreach(['monthlyBudgetMinor'=>[0,10000000],'dailyPerPlatform'=>[1,6],'planningDays'=>[1,14],'textReservationMinor'=>[100,100000],'videoReservationMinor'=>[100,1000000]] as $key=>$range)if(array_key_exists($key,$body)&&(!is_int($body[$key])||$body[$key]<$range[0]||$body[$key]>$range[1]))throw new NodenoControlHttpError(422,'social_setting_invalid');
  foreach(['locales'=>NODENO_SOCIAL_LOCALES,'countries'=>['TR','DE','GB','US','SA','RU','KZ','AZ']] as $key=>$values)if(array_key_exists($key,$body)&&(!is_array($body[$key])||!$body[$key]||count($body[$key])!==count(array_unique($body[$key]))||array_diff($body[$key],$values)))throw new NodenoControlHttpError(422,'social_setting_invalid');
  $new=array_replace($settings,$body);if($new['paidEnabled']&&$new['monthlyBudgetMinor']===0)throw new NodenoControlHttpError(422,'social_budget_required');if($new['xAiApproval']&&nodenoStudioText($new['xApprovalReference']??'',500)==='')throw new NodenoControlHttpError(422,'social_x_approval_required');$new['version']++;
  nodenoControlSetSetting($db,'social:settings',$new);nodenoStudioEvent($db,'settings_updated',null,['enabled'=>$new['enabled'],'autoPublish'=>$new['autoPublish'],'autoReplies'=>$new['autoReplies'],'paidEnabled'=>$new['paidEnabled']]);nodenoControlAudit($db,$ctx['root'],$ctx['user']['id'],'configure','social','settings');return $new;
 });
}

function nodenoStudioProviderSave(array $ctx,string $provider,array $body):array {
 nodenoControlRequire($ctx,'integrations.read',true);if(!in_array($provider,['meta','ayrshare','openai','shotstack'],true))throw new NodenoControlHttpError(404,'provider_unknown');
 return nodenoControlTransaction($ctx['db'],static function()use($ctx,$provider,$body):array {
  $db=$ctx['db'];$name='social:provider:'.$provider;$old=nodenoControlSetting($db,$name);if(($body['version']??null)!==($old['version']??0))throw new NodenoControlHttpError(409,'version_conflict');
  $keys=$provider==='meta'?['version','apiKey','pageId','apiVersion']:['version','apiKey','profileKey'];foreach($body as $key=>$value)if(!in_array($key,$keys,true))throw new NodenoControlHttpError(422,'social_credentials_invalid');$credentials=$old?nodenoStudioCredentials($db,$ctx['root'],$provider):[];
  foreach(['apiKey','profileKey'] as $key)if(isset($body[$key])&&$body[$key]!==''){if(!is_string($body[$key])||strlen($body[$key])>4000||preg_match('/[\r\n\x00-\x20]/',$body[$key]))throw new NodenoControlHttpError(422,'social_credentials_invalid');$credentials[$key]=$body[$key];}
  if($provider==='meta'){
   foreach(['pageId','apiVersion']as $key)if(isset($body[$key]))$credentials[$key]=$body[$key];
   if(!is_string($credentials['pageId']??null)||!preg_match('/^[0-9]{5,30}$/D',$credentials['pageId'])||!is_string($credentials['apiVersion']??null)||!preg_match('/^v[1-9][0-9]\.0$/D',$credentials['apiVersion']))throw new NodenoControlHttpError(422,'social_credentials_invalid');
   unset($credentials['pageAccessToken'],$credentials['instagramId']);
  }
  if(empty($credentials['apiKey']))throw new NodenoControlHttpError(422,'social_credentials_required');$stored=['version'=>($old['version']??0)+1,'encrypted'=>nodenoControlEncrypt($ctx['root'],json_encode($credentials,JSON_THROW_ON_ERROR),'social:'.$provider),'status'=>'configured_unverified'];
  nodenoControlSetSetting($db,$name,$stored);if($provider==='ayrshare')nodenoControlSetSetting($db,'social:channels',[]);if($provider==='meta'){$channels=nodenoControlSetting($db,'social:channels',[]);unset($channels['instagram'],$channels['facebook']);nodenoControlSetSetting($db,'social:channels',$channels);}nodenoControlAudit($db,$ctx['root'],$ctx['user']['id'],'configure','social',$provider);return ['configured'=>true,'version'=>$stored['version'],'status'=>$stored['status']];
 });
}

function nodenoStudioMusicSave(array $ctx,array $body):array {
 $title=nodenoStudioText($body['title']??'',160);$evidence=nodenoStudioText($body['evidence']??'',500);$countries=$body['countries']??[];$platforms=$body['platforms']??[];$expiry=$body['expiresAt']??0;$encoded=$body['audioBase64']??'';
 if(!$title||!$evidence||($body['rightsConfirmed']??false)!==true||!is_int($expiry)||$expiry<=time()||!is_array($platforms)||!$platforms||array_diff($platforms,NODENO_SOCIAL_PLATFORMS)||!is_array($countries)||!$countries||count($countries)>40)throw new NodenoControlHttpError(422,'social_music_license_required');
 foreach($countries as $country)if(!is_string($country)||!preg_match('/^(?:[A-Z]{2}|\*)$/D',$country))throw new NodenoControlHttpError(422,'social_music_license_required');
 if(!is_string($encoded)||strlen($encoded)>1500000||!$audio=base64_decode($encoded,true))throw new NodenoControlHttpError(422,'social_audio_invalid');$mime=(new finfo(FILEINFO_MIME_TYPE))->buffer($audio);if(!in_array($mime,['audio/mpeg','audio/mp3'],true)||strlen($audio)>1000000)throw new NodenoControlHttpError(422,'social_audio_invalid');
 $hash=nodenoStudioAsset($ctx['db'],$ctx['root'],$audio,'mp3','audio/mpeg');$id=nodenoControlId('sm_');$data=['title'=>$title,'evidence'=>$evidence,'countries'=>$countries,'platforms'=>$platforms,'expiresAt'=>$expiry,'rightsConfirmed'=>true,'url'=>'https://nodenohome.com/social-media/'.$hash.'.mp3'];
 $ctx['db']->prepare('INSERT INTO social_music(id,data_json,created_at) VALUES(?,?,?)')->execute([$id,json_encode($data,JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR),time()]);nodenoControlAudit($ctx['db'],$ctx['root'],$ctx['user']['id'],'license','social',$id);return ['id'=>$id]+$data;
}

function nodenoStudioAdmin(array $ctx,string $route,string $method,array $body,array $catalog,array $config):array {
 nodenoControlRequire($ctx,'marketing.read');nodenoStudioSchema($ctx['db']);$parts=explode('/',$route);$resource=$parts[1]??'overview';$id=$parts[2]??'';$action=$parts[3]??'';$db=$ctx['db'];
 if($method==='GET'&&$resource==='overview')return nodenoStudioOverview($ctx,$catalog,$config);
 if($method==='GET'&&$resource==='media'){$extension=$parts[3]??'png';if(!nodenoStudioServeAsset($id,$extension,$ctx['root'],true))throw new NodenoControlHttpError(404,'not_found');return ['_responded'=>true];}
 nodenoControlRequire($ctx,'marketing.write',true);
 if($resource==='settings'&&$method==='PUT')return nodenoStudioUpdateSettings($ctx,$body);
 if($resource==='providers'&&$method==='PUT')return nodenoStudioProviderSave($ctx,$id,$body);
 if($resource==='accounts'&&$method==='POST'){nodenoControlRequire($ctx,'integrations.read',true);return ['accounts'=>nodenoStudioVerifyChannels($db,$ctx['root'],$config)];}
 if($resource==='posts'&&in_array($method,['POST','PUT'],true)&&$action==='')return nodenoStudioSavePost($ctx,$body,$catalog,$method==='PUT'?$id:null);
 if($resource==='posts'&&$method==='POST'&&$action==='schedule')return nodenoStudioQueue($ctx,$id,$body);
 if($resource==='posts'&&$method==='POST'&&$action==='cancel')return nodenoControlTransaction($db,static function()use($ctx,$db,$id,$body):array {$old=nodenoStudioRead($db,$id);if((int)($body['version']??0)!==(int)$old['version'])throw new NodenoControlHttpError(409,'version_conflict');if(in_array($old['status'],['publishing','processing','posted','uncertain'],true))throw new NodenoControlHttpError(409,'social_post_locked');$db->prepare("UPDATE social_posts SET status='cancelled',version=version+1,updated_at=? WHERE id=?")->execute([time(),$id]);nodenoControlAudit($db,$ctx['root'],$ctx['user']['id'],'cancel','social',$id);return ['cancelled'=>true];});
 if($resource==='plan'&&$method==='POST')return ['created'=>nodenoStudioPlan($db,$catalog,nodenoStudioSettings($db),time())];
 if($resource==='music'&&$method==='POST')return nodenoStudioMusicSave($ctx,$body);
 if($resource==='inbox'&&$method==='POST'){
  $q=$db->prepare('SELECT * FROM social_inbox WHERE id=?');$q->execute([$id]);$message=$q->fetch();if(!$message)throw new NodenoControlHttpError(404,'not_found');if((int)($body['version']??0)!==(int)$message['version'])throw new NodenoControlHttpError(409,'version_conflict');
  if($action==='draft'){$decision=nodenoStudioReplyDecision($message,nodenoStudioSettings($db),$catalog,time());$reply=$decision['reply'];if(!$reply&&!empty($message['product_id']))$reply=nodenoStudioAi($db,$ctx['root'],nodenoStudioSettings($db),nodenoStudioProduct($catalog,$message['product_id']),'tr',$message['platform'],'customer reply draft',$message['text'])??'';
   $db->prepare("UPDATE social_inbox SET status='draft',reply=?,reason=?,version=version+1,updated_at=? WHERE id=? AND version=? AND status IN ('new','draft','review')")->execute([$reply,$decision['reason'],time(),$id,$message['version']]);return ['reply'=>$reply,'automaticEligible'=>$decision['safe']];}
  if($action==='reply'){$reply=nodenoStudioText($body['reply']??'',2200);if($reply==='')throw new NodenoControlHttpError(422,'social_text_invalid');return ['sent'=>nodenoStudioReplySend($db,$ctx['root'],$message,$reply,false)];}
 }
 throw new NodenoControlHttpError(405,'method_not_allowed');
}
