<?php
declare(strict_types=1);
require_once __DIR__.'/control-auth.php';
require_once __DIR__.'/social-campaigns.php';

const NODENO_SOCIAL_PLATFORMS=['instagram','facebook','youtube','tiktok','x','pinterest','linkedin'];
const NODENO_SOCIAL_LOCALES=['tr','en','ru','ar'];
function nodenoStudioLength(string $value):int {return preg_match_all('/./us',$value);}
function nodenoStudioSlice(string $value,int $length):string {return implode('',array_slice(preg_split('//u',$value,-1,PREG_SPLIT_NO_EMPTY),0,$length));}

function nodenoStudioSchema(PDO $db):void {
 $db->exec("CREATE TABLE IF NOT EXISTS social_posts(id TEXT PRIMARY KEY,platform TEXT NOT NULL,locale TEXT NOT NULL,product_id TEXT NOT NULL,format TEXT NOT NULL,payload_json TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'draft',reason TEXT NOT NULL DEFAULT '',scheduled_at INTEGER NOT NULL,version INTEGER NOT NULL DEFAULT 1,lease_token TEXT,lease_until INTEGER,attempts INTEGER NOT NULL DEFAULT 0,remote_id TEXT,remote_url TEXT,created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL,UNIQUE(platform,product_id,locale,scheduled_at));
 CREATE INDEX IF NOT EXISTS social_posts_due ON social_posts(status,scheduled_at);
 CREATE TABLE IF NOT EXISTS social_events(id INTEGER PRIMARY KEY AUTOINCREMENT,type TEXT NOT NULL,post_id TEXT,detail_json TEXT NOT NULL,created_at INTEGER NOT NULL);
 CREATE TABLE IF NOT EXISTS social_trends(id TEXT PRIMARY KEY,source TEXT NOT NULL,title TEXT NOT NULL,url TEXT NOT NULL,country TEXT NOT NULL,score INTEGER NOT NULL DEFAULT 0,observed_at INTEGER NOT NULL,published_at INTEGER NOT NULL);
 CREATE TABLE IF NOT EXISTS social_inbox(id TEXT PRIMARY KEY,platform TEXT NOT NULL,kind TEXT NOT NULL,remote_id TEXT NOT NULL,post_id TEXT,product_id TEXT,sender_id TEXT NOT NULL,text TEXT NOT NULL,received_at INTEGER NOT NULL,verified INTEGER NOT NULL DEFAULT 0,status TEXT NOT NULL DEFAULT 'new',reply TEXT NOT NULL DEFAULT '',reason TEXT NOT NULL DEFAULT '',version INTEGER NOT NULL DEFAULT 1,lease_token TEXT,updated_at INTEGER NOT NULL,UNIQUE(platform,kind,remote_id));
 CREATE TABLE IF NOT EXISTS social_metrics(post_id TEXT PRIMARY KEY,metrics_json TEXT NOT NULL,checked_at INTEGER NOT NULL);
 CREATE TABLE IF NOT EXISTS social_assets(hash TEXT PRIMARY KEY,extension TEXT NOT NULL,mime TEXT NOT NULL,bytes INTEGER NOT NULL,public INTEGER NOT NULL DEFAULT 0,created_at INTEGER NOT NULL);
 CREATE TABLE IF NOT EXISTS social_music(id TEXT PRIMARY KEY,data_json TEXT NOT NULL,created_at INTEGER NOT NULL);
 CREATE TABLE IF NOT EXISTS social_budget(id TEXT PRIMARY KEY,month TEXT NOT NULL,kind TEXT NOT NULL,reserved_minor INTEGER NOT NULL,actual_usage_json TEXT,created_at INTEGER NOT NULL);");
}

function nodenoStudioSettings(PDO $db):array {
 $defaults=['version'=>0,'enabled'=>true,'autoPublish'=>false,'autoReplies'=>false,'paidEnabled'=>false,'monthlyBudgetMinor'=>0,'dailyPerPlatform'=>1,'planningDays'=>7,'locales'=>NODENO_SOCIAL_LOCALES,'countries'=>['TR','DE','GB'],'timezone'=>'Europe/Istanbul','textReservationMinor'=>1000,'videoReservationMinor'=>10000,'xAiApproval'=>false];
 return array_replace($defaults,nodenoControlSetting($db,'social:settings',[]));
}

function nodenoStudioEvent(PDO $db,string $type,?string $id,array $detail=[]):void {
 $db->prepare('INSERT INTO social_events(type,post_id,detail_json,created_at) VALUES(?,?,?,?)')->execute([$type,$id,json_encode(nodenoControlRedact($detail),JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE),time()]);
}

function nodenoStudioRoot(string $root):string {
 $base=nodenoAccountStorage($root);$path=$base.'/social-media';
 if(is_link($path))throw new RuntimeException('Unsafe social storage');
 if(!is_dir($path)&&!mkdir($path,0700,true))throw new RuntimeException('Social storage unavailable');
 return $path;
}

function nodenoStudioText($value,int $maximum=3000):string {
 if(!is_string($value)||!preg_match('//u',$value)||nodenoStudioLength($value)>$maximum||preg_match('/[\x00-\x08\x0b\x0c\x0e-\x1f]/',$value))throw new NodenoControlHttpError(422,'social_text_invalid');
 return trim($value);
}

function nodenoStudioPlatform($platform):string {
 if(!is_string($platform)||!in_array($platform,NODENO_SOCIAL_PLATFORMS,true))throw new NodenoControlHttpError(422,'social_platform_invalid');return $platform;
}

function nodenoStudioPost(array $row):array {
 return ['id'=>$row['id'],'platform'=>$row['platform'],'locale'=>$row['locale'],'productId'=>$row['product_id'],'format'=>$row['format'],'payload'=>json_decode($row['payload_json'],true),'status'=>$row['status'],'reason'=>$row['reason'],'scheduledAt'=>(int)$row['scheduled_at'],'version'=>(int)$row['version'],'remoteUrl'=>$row['remote_url'],'remoteId'=>$row['remote_id'],'attempts'=>(int)$row['attempts'],'updatedAt'=>(int)$row['updated_at']];
}

function nodenoStudioRead(PDO $db,string $id):array {
 $q=$db->prepare('SELECT * FROM social_posts WHERE id=?');$q->execute([$id]);$row=$q->fetch();if(!$row)throw new NodenoControlHttpError(404,'social_post_missing');return $row;
}

function nodenoStudioProduct(array $catalog,string $id):array {
 foreach($catalog['products']??[] as $p)if($p['id']===$id&&empty($p['hidden'])&&!empty($p['images']))return $p;
 throw new NodenoControlHttpError(422,'social_product_unavailable');
}

function nodenoStudioName(array $p,string $locale):string {return (string)($p['modelName'][$locale]??$p['name'][$locale]??$p['name']['en']??$p['name']['tr']??'');}
function nodenoStudioLink(string $id,string $locale,string $platform):string {return 'https://nodenohome.com/?'.http_build_query(['lang'=>$locale,'product'=>$id,'utm_source'=>$platform,'utm_medium'=>'social','utm_campaign'=>'nodeno_collection']);}
function nodenoStudioProductCopy(array $p,string $locale):string {
 $raw=$p['description'][$locale]??'';if(!is_string($raw))$raw='';$raw=preg_replace('~<(?:br\s*/?|/p|/li|li)[^>]*>~iu',"\n",$raw);$plain=html_entity_decode(strip_tags($raw),ENT_QUOTES|ENT_HTML5,'UTF-8');$parts=preg_split('/(?<=[.!?])\s+|[\r\n]+/u',$plain);$kept=[];$length=0;
 foreach($parts as $part){$part=trim(preg_replace('/\s+/u',' ',$part));if($part===''||preg_match('/adore|alka|altın.?iş|fiyat|stok|indirim|kargo|teslim|garanti|şık|modern|zarif|eşsiz|mükemmel|price|stock|discount|shipping|delivery|warranty|stylish|elegant|perfect|достав|скид|цен[аыу]|гарант|шикар|идеаль|سعر|خصم|شحن|توصيل|ضمان|%/iu',$part))continue;
  if(preg_match('/^'.preg_quote(nodenoStudioName($p,$locale),'/').'/iu',$part))continue;$n=nodenoStudioLength($part);if($length+$n>480)continue;$kept[]=$part;$length+=$n;if(count($kept)>=2)break;
 }
 if(!$kept)foreach($p['specs']??[] as $spec){$label=$spec['label'][$locale]??null;$value=$spec['value'][$locale]??null;if(!is_string($label)||!is_string($value)||preg_match('/kod|code|код|رمز|adore|alka|fiyat|price|stock|stok/iu',$label.' '.$value))continue;$fact=trim($label).': '.trim($value);if(nodenoStudioLength($fact)>220)continue;$kept[]=$fact;if(count($kept)>=2)break;}
 return implode(' ',$kept);
}

function nodenoStudioCaption(array $p,string $locale,string $platform,int $angle=0):array {
 $name=nodenoStudioName($p,$locale);$link=nodenoStudioLink($p['id'],$locale,$platform);$segment=nodenoStudioSegment($p);$topic=$segment==='diy'?'diy':nodenoStudioTopic($p);
 $profile=nodenoStudioCreativeProfile($p);$description=$profile['copy'][$locale]??nodenoStudioProductCopy($p,$locale);$slogan=nodenoStudioCreativeCopy()[$locale][$topic][1];
 $caption=$name.($description!==''?"\n\n".$description:'')."\n\n".$slogan."\n".$link;
 $keywords=nodenoStudioKeywords($p,$locale);$hashtags=nodenoStudioHashtags($keywords,$platform);
 if($platform!=='x'&&$hashtags)$caption.="\n\n".implode(' ',$hashtags);
 if($platform==='x'){
  // Prefer a complete factual sentence, never a headline chopped in mid-word.
  $first=preg_split('/(?<=[.!?])\s+/u',$description)[0]??'';$caption=$name."\n".$link;
  if($first!==''&&nodenoStudioLength($first."\n".$link)<=280)$caption=$first."\n".$link;
  if(nodenoStudioLength($caption)>280)$caption=$link;
  foreach($hashtags as $tag)if(nodenoStudioLength($caption."\n".$tag)<=280)$caption.="\n".$tag;
 }
 $frames=$profile['frames']??[];$storyboard=['creativeVersion'=>NODENO_SOCIAL_CREATIVE_VERSION,'status'=>'storyboard_only','aspectRatio'=>'9:16','photoFit'=>'contain','audio'=>'none_without_verified_licence','frames'=>[]];
 foreach($frames as $index=>$frame)$storyboard['frames'][]=['sourceIndex'=>$frame['index'],'sourceSha256'=>$frame['sha256'],'crop'=>$frame['crop'],'role'=>$index===0?'whole-product':'closer-view','seconds'=>4,'transition'=>'fade','motion'=>'none','logo'=>'wordmark_only'];
 return ['title'=>nodenoStudioSlice($name,$platform==='youtube'?90:100),'caption'=>$caption,'keywords'=>$keywords,'hashtags'=>$hashtags,'altText'=>$name,'generatedCaption'=>$caption,'copyEdited'=>false,'productName'=>$name,'productUrl'=>$link,'image'=>$p['images'][$frames[0]['index']??$p['coverIndex']??0]??$p['images'][0],'musicId'=>null,'origin'=>'catalogue','angle'=>$angle%3,'segment'=>$segment,'theme'=>$topic,'creativeVersion'=>NODENO_SOCIAL_CREATIVE_VERSION,'creativeFingerprint'=>$profile['factsSha256']??null,'storyboard'=>$storyboard];
}

function nodenoStudioSavePost(array $ctx,array $body,array $catalog,?string $id=null):array {
 $db=$ctx['db'];$p=nodenoStudioProduct($catalog,nodenoStudioText($body['productId']??'',120));$platform=nodenoStudioPlatform($body['platform']??'');$locale=$body['locale']??'tr';
 if(!in_array($locale,NODENO_SOCIAL_LOCALES,true))throw new NodenoControlHttpError(422,'social_locale_invalid');
 $format=$body['format']??'image';if(!in_array($format,['image','carousel','video'],true)||in_array($platform,['youtube','tiktok'],true)&&$format!=='video')throw new NodenoControlHttpError(422,'social_format_invalid');
 $scheduled=$body['scheduledAt']??time()+3600;if(!is_int($scheduled)||$scheduled<time()-60||$scheduled>time()+90*86400)throw new NodenoControlHttpError(422,'social_schedule_invalid');
 $payload=nodenoStudioCaption($p,$locale,$platform);$payload['caption']=nodenoStudioText($body['caption']??$payload['caption'],$platform==='x'?280:2200);$payload['copyEdited']=$payload['caption']!==$payload['generatedCaption'];$payload['title']=nodenoStudioText($body['title']??$payload['title'],100);$payload['musicId']=empty($body['musicId'])?null:nodenoStudioText($body['musicId'],80);
 return nodenoControlTransaction($db,static function()use($ctx,$db,$id,$body,$platform,$locale,$p,$format,$payload,$scheduled):array {
  $now=time();$postId=$id?:nodenoControlId('sp_');
  if($id){$old=nodenoStudioRead($db,$id);if((int)($body['version']??0)!==(int)$old['version'])throw new NodenoControlHttpError(409,'version_conflict');if(!in_array($old['status'],['draft','ready','scheduled','blocked','cancelled'],true))throw new NodenoControlHttpError(409,'social_post_locked');
   $db->prepare("UPDATE social_posts SET platform=?,locale=?,product_id=?,format=?,payload_json=?,status='draft',reason='',scheduled_at=?,version=version+1,updated_at=? WHERE id=?")->execute([$platform,$locale,$p['id'],$format,json_encode($payload,JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR),$scheduled,$now,$id]);
  }else{$db->prepare("INSERT INTO social_posts(id,platform,locale,product_id,format,payload_json,status,scheduled_at,created_at,updated_at) VALUES(?,?,?,?,?,?,'draft',?,?,?)")->execute([$postId,$platform,$locale,$p['id'],$format,json_encode($payload,JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR),$scheduled,$now,$now]);}
  nodenoStudioEvent($db,'post_saved',$postId);nodenoControlAudit($db,$ctx['root'],$ctx['user']['id'],'save','social',$postId);return nodenoStudioPost(nodenoStudioRead($db,$postId));
 });
}

function nodenoStudioPolicy(array $post,array $settings,array $channels,array $catalog,int $now):?string {
 if(!$settings['enabled'])return 'engine_paused';if(!$settings['autoPublish'])return 'publishing_paused';
 if(empty($channels[$post['platform']]['verified'])||($channels[$post['platform']]['checkedAt']??0)<$now-86400)return 'account_connection_required';
 $p=nodenoStudioProduct($catalog,$post['product_id']);$payload=json_decode($post['payload_json'],true);
 if(($payload['creativeVersion']??'')!==NODENO_SOCIAL_CREATIVE_VERSION)return 'creative_review_required';
 $profile=nodenoStudioCreativeProfile($p);if(!$profile||!hash_equals($profile['factsSha256'],(string)($payload['creativeFingerprint']??'')))return 'creative_review_required';
 if(str_starts_with($post['id'],'auto_')&&nodenoStudioSegment($p)!=='finished')return 'audience_review_required';
 if(nodenoStudioName($p,$post['locale'])!==($payload['productName']??nodenoStudioName($p,$post['locale'])))return 'product_changed';
 if(empty($payload['assetHashes'])&&empty($payload['videoUrl']))return 'media_required';
 if($post['format']==='video'&&empty($payload['videoUrl']))return 'video_render_required';
 if(nodenoStudioLength($payload['caption']??'')>($post['platform']==='x'?280:2200))return 'caption_too_long';
 return null;
}

function nodenoStudioQueue(array $ctx,string $id,array $body):array {
 return nodenoControlTransaction($ctx['db'],static function()use($ctx,$id,$body):array {
  $db=$ctx['db'];$row=nodenoStudioRead($db,$id);if((int)($body['version']??0)!==(int)$row['version'])throw new NodenoControlHttpError(409,'version_conflict');
  if(!in_array($row['status'],['draft','ready','blocked'],true))throw new NodenoControlHttpError(409,'social_post_locked');
  $db->prepare("UPDATE social_posts SET status='scheduled',reason='',version=version+1,updated_at=? WHERE id=?")->execute([time(),$id]);nodenoStudioEvent($db,'post_scheduled',$id);nodenoControlAudit($db,$ctx['root'],$ctx['user']['id'],'schedule','social',$id);return nodenoStudioPost(nodenoStudioRead($db,$id));
 });
}

function nodenoStudioClaim(PDO $db,int $now):?array {
 return nodenoControlTransaction($db,static function()use($db,$now):?array {
  // A crashed sender might already have published. Never blindly send it again.
  $db->prepare("UPDATE social_posts SET status='uncertain',reason='delivery_confirmation_required',version=version+1,updated_at=? WHERE status='publishing' AND lease_until<?")->execute([$now,$now]);
  $q=$db->prepare("SELECT * FROM social_posts WHERE status='scheduled' AND scheduled_at<=? ORDER BY scheduled_at,id LIMIT 1");$q->execute([$now]);$row=$q->fetch();if(!$row)return null;
  $lease=bin2hex(random_bytes(16));$db->prepare("UPDATE social_posts SET status='publishing',lease_token=?,lease_until=?,attempts=attempts+1,updated_at=? WHERE id=? AND status='scheduled'")->execute([$lease,$now+180,$now,$row['id']]);
  $row['lease_token']=$lease;return $row;
 });
}

function nodenoStudioExpire(PDO $db,int $now):int {
 $q=$db->prepare("UPDATE social_posts SET status='cancelled',reason='missed_window',version=version+1,updated_at=? WHERE scheduled_at<? AND status IN ('draft','ready','blocked','scheduled')");
 $q->execute([$now,$now-86400]);return $q->rowCount();
}

function nodenoStudioFinish(PDO $db,array $post,string $status,string $reason='',?string $remoteId=null,?string $remoteUrl=null,?int $nextAt=null):void {
 $q=$db->prepare('UPDATE social_posts SET status=?,reason=?,remote_id=COALESCE(?,remote_id),remote_url=COALESCE(?,remote_url),scheduled_at=COALESCE(?,scheduled_at),lease_token=NULL,lease_until=NULL,version=version+1,updated_at=? WHERE id=? AND lease_token=?');
 $q->execute([$status,$reason,$remoteId,$remoteUrl,$nextAt,time(),$post['id'],$post['lease_token']]);if($q->rowCount()!==1)throw new RuntimeException('Social lease lost');nodenoStudioEvent($db,'post_'.$status,$post['id'],['reason'=>$reason]);
}

function nodenoStudioReserve(PDO $db,array $settings,string $kind,string $key,int $now):bool {
 if(!$settings['paidEnabled']||$settings['monthlyBudgetMinor']<=0)return false;
 return nodenoControlTransaction($db,static function()use($db,$settings,$kind,$key,$now):bool {
  $month=gmdate('Y-m',$now);$q=$db->prepare('SELECT COALESCE(SUM(reserved_minor),0) FROM social_budget WHERE month=?');$q->execute([$month]);$amount=$settings[$kind==='video'?'videoReservationMinor':'textReservationMinor'];
  if((int)$q->fetchColumn()+$amount>$settings['monthlyBudgetMinor'])return false;
  $q=$db->prepare('INSERT OR IGNORE INTO social_budget(id,month,kind,reserved_minor,created_at) VALUES(?,?,?,?,?)');$q->execute([$key,$month,$kind,$amount,$now]);return $q->rowCount()===1;
 });
}

function nodenoStudioRelevant(string $title):int {
 if(preg_match('/deprem|vefat|savaş|ölüm|earthquake|death|war\b|disaster|террор|войн|زلزال|حرب/iu',$title))return 0;
 $words=['mobilya','dekorasyon','dolap','ahşap','tasarım','furniture','interior','storage','wardrobe','wood','design','мебел','интерьер','дизайн','أثاث','ديكور','خزانة'];$score=0;
 foreach($words as $word)if(preg_match('~'.preg_quote($word,'~').'~iu',$title))$score+=20;return min(100,$score);
}

function nodenoStudioMusicAllowed(array $music,string $platform,string $country,int $now):bool {
 return ($music['rightsConfirmed']??false)===true&&!empty($music['evidence'])&&($music['expiresAt']??0)>$now&&in_array($platform,$music['platforms']??[],true)&&(in_array('*',$music['countries']??[],true)||in_array($country,$music['countries']??[],true));
}

function nodenoStudioReplyDecision(array $message,array $settings,array $catalog,int $now):array {
 if(empty($message['verified'])||$message['received_at']>$now+60||$message['received_at']<$now-23*3600)return ['safe'=>false,'reason'=>'inbound_verification_or_window','reply'=>''];
 if($message['platform']==='x'&&!$settings['xAiApproval'])return ['safe'=>false,'reason'=>'x_written_approval_required','reply'=>''];
 if(preg_match('/iade|iptal|ödeme|ödeme|sipariş|şikayet|avukat|refund|cancel|payment|order|complaint|возврат|оплат|заказ|استرجاع|طلب|دفع|iban|password|şifre|parola|ignore|system prompt|talimatları/iu',$message['text']))return ['safe'=>false,'reason'=>'human_review_required','reply'=>''];
 $p=null;if(!empty($message['product_id'])){try{$p=nodenoStudioProduct($catalog,$message['product_id']);}catch(Throwable $e){}}
 if(!$p)return ['safe'=>false,'reason'=>'product_context_required','reply'=>''];
 $locale=preg_match('/[\x{0600}-\x{06ff}]/u',$message['text'])?'ar':(preg_match('/[\x{0400}-\x{04ff}]/u',$message['text'])?'ru':(preg_match('/price|colour|color|size|dimension|material/i',$message['text'])?'en':'tr'));
 if(!preg_match('/fiyat|renk|ölçü|ebat|boyut|price|colour|color|size|dimension|цвет|размер|цен|سعر|لون|مقاس/iu',$message['text']))return ['safe'=>false,'reason'=>'ai_draft_required','reply'=>''];
 $copy=['tr'=>'Merhaba, %s için güncel bilgileri, ölçüleri ve renk seçeneklerini bu sayfada bulabilirsiniz: %s','en'=>'Hello, you can find the current details, dimensions and colour options for %s here: %s','ru'=>'Здравствуйте! Актуальные сведения, размеры и варианты цвета для %s доступны здесь: %s','ar'=>'مرحباً، يمكنك الاطلاع على تفاصيل %s والأبعاد والألوان المتاحة هنا: %s'];
 return ['safe'=>true,'reason'=>'verified_product_information','reply'=>sprintf($copy[$locale],nodenoStudioName($p,$locale),nodenoStudioLink($p['id'],$locale,$message['platform']))];
}
