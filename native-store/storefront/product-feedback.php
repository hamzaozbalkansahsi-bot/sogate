<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/product-feedback.php
 * Açıklama   : Yayındaki ürünler için mahremiyet korumalı geri bildirim ve yetkili inceleme akışını sağlar.
 */
declare(strict_types=1);

function sgProductFeedbackSchema(PDO $db):void{
 $sql=file_get_contents(__DIR__.'/product-feedback-001.sql');if($sql===false)throw new RuntimeException('feedback_schema_unavailable');
 nodenoControlTransaction($db,static function()use($db,$sql):void{
  $db->exec($sql);foreach(['sg_product_feedback'=>180*86400,'sg_product_feedback_commands'=>86400]as $table=>$duration){$columns=array_column($db->query('PRAGMA table_info('.$table.')')->fetchAll(),'name');if(!in_array('expires_at',$columns,true)){$db->exec('ALTER TABLE '.$table.' ADD COLUMN expires_at INTEGER NOT NULL DEFAULT 0');$db->exec('UPDATE '.$table.' SET expires_at=created_at+'.$duration.' WHERE expires_at=0');}}
  $db->exec('CREATE INDEX IF NOT EXISTS sg_product_feedback_expiry ON sg_product_feedback(expires_at);CREATE INDEX IF NOT EXISTS sg_product_feedback_command_expiry ON sg_product_feedback_commands(expires_at);CREATE INDEX IF NOT EXISTS sg_product_feedback_rate_expiry ON sg_product_feedback_rates(expires_at)');
 });
}
function sgProductFeedbackError(int $status,string $code):never{throw new NodenoControlHttpError($status,$code);}
function sgProductFeedbackJson(array $data):string{return json_encode($data,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES);}
function sgProductFeedbackText(mixed $value,int $max=1200):string{
 if(!is_string($value)||strlen($value)>$max*4||!preg_match('//u',$value)||preg_match('/[<>\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/u',$value)||preg_match_all('/./us',$value)>$max)sgProductFeedbackError(422,'feedback_request_invalid');return trim($value);
}
function sgProductFeedbackOwner(string $root,mixed $token):string{
 if(!is_string($token)||!preg_match('/^[a-f0-9]{64}$/D',$token))sgProductFeedbackError(403,'feedback_owner_required');return hash_hmac('sha256','product-feedback-owner:'.$token,nodenoControlKey($root));
}
function sgProductFeedbackCleanup(PDO $db,int $now,int $limit=100):array{
 $limit=max(1,min(200,$limit));return nodenoControlTransaction($db,static function()use($db,$now,$limit):array{
  $counts=[];foreach(['commands'=>'sg_product_feedback_commands','rates'=>'sg_product_feedback_rates']as $name=>$table){$q=$db->prepare('DELETE FROM '.$table.' WHERE key_hash IN(SELECT key_hash FROM '.$table.' WHERE expires_at<=?ORDER BY expires_at LIMIT '.$limit.')');$q->execute([$now]);$counts[$name]=$q->rowCount();}
  $q=$db->prepare("UPDATE sg_product_feedback SET owner_hash='',request_hash='' WHERE id IN(SELECT id FROM sg_product_feedback WHERE created_at<=?AND owner_hash<>''ORDER BY created_at,id LIMIT ".$limit.')');$q->execute([$now-86400]);$counts['ownerLinks']=$q->rowCount();
  $q=$db->prepare('SELECT id FROM sg_product_feedback WHERE expires_at<=?ORDER BY expires_at,id LIMIT '.$limit);$q->execute([$now]);$ids=$q->fetchAll(PDO::FETCH_COLUMN);foreach($ids as $id){$db->prepare('DELETE FROM sg_product_feedback_events WHERE feedback_id=?')->execute([$id]);$db->prepare('DELETE FROM sg_product_feedback_commands WHERE feedback_id=?')->execute([$id]);$db->prepare('DELETE FROM sg_product_feedback WHERE id=?')->execute([$id]);}$counts['feedback']=count($ids);return $counts;
 });
}
function sgProductFeedbackRate(PDO $db,string $root,string $purpose,string $owner,int $limit,int $window,int $now):void{
 $key=hash_hmac('sha256','product-feedback:'.$purpose.':'.$owner,nodenoControlKey($root));
 $allowed=nodenoControlTransaction($db,static function()use($db,$key,$limit,$window,$now):bool{
  $q=$db->prepare('SELECT window_start,count FROM sg_product_feedback_rates WHERE key_hash=?');$q->execute([$key]);$row=$q->fetch();if(!$row||(int)$row['window_start']<=$now-$window){$db->prepare('INSERT INTO sg_product_feedback_rates VALUES(?,?,1,?)ON CONFLICT(key_hash)DO UPDATE SET window_start=excluded.window_start,count=1,expires_at=excluded.expires_at')->execute([$key,$now,$now+86400]);return true;}if((int)$row['count']>=$limit)return false;$db->prepare('UPDATE sg_product_feedback_rates SET count=count+1 WHERE key_hash=?')->execute([$key]);return true;
 });if(!$allowed)throw new NodenoControlHttpError(429,'rate_limited',['Retry-After'=>(string)$window]);
}
function sgProductFeedbackProduct(array $catalog,mixed $id):array{
 $id=sgProductFeedbackText($id,180);if($id==='')sgProductFeedbackError(422,'feedback_request_invalid');
 foreach($catalog['products']??[]as $product)if(($product['id']??null)===$id&&empty($product['hidden'])&&($product['published']??true)!==false&&($product['visible']??true)!==false)return $product;
 sgProductFeedbackError(404,'feedback_product_unavailable');
}
function sgProductFeedbackSubmit(PDO $db,string $root,array $catalog,string $owner,array $body,int $now):array{
 if(!preg_match('/^[a-f0-9]{64}$/D',$owner)||array_diff(array_keys($body),['productId','reason','note','key'])||!is_string($body['key']??null)||!preg_match('/^[A-Za-z0-9_-]{16,100}$/D',$body['key'])||!in_array($body['reason']??null,['title','description','specification','price','category','image','image_mismatch','safety','variant','other'],true))sgProductFeedbackError(422,'feedback_request_invalid');
 $product=sgProductFeedbackProduct($catalog,$body['productId']??null);$note=sgProductFeedbackText($body['note']??'');$hash=hash('sha256',sgProductFeedbackJson([$product['id'],$body['reason'],$note]));$key=hash_hmac('sha256',$owner.':'.$body['key'],nodenoControlKey($root));sgProductFeedbackCleanup($db,$now);
 return nodenoControlTransaction($db,static function()use($db,$root,$owner,$body,$now,$product,$note,$hash,$key):array{
  $db->prepare('DELETE FROM sg_product_feedback_commands WHERE key_hash=?AND expires_at<=?')->execute([$key,$now]);
  $q=$db->prepare('SELECT request_hash,feedback_id FROM sg_product_feedback_commands WHERE key_hash=?');$q->execute([$key]);if($old=$q->fetch()){if(!hash_equals($old['request_hash'],$hash))sgProductFeedbackError(409,'feedback_request_changed');return ['reference'=>$old['feedback_id'],'status'=>'received','duplicate'=>true];}
  sgProductFeedbackRate($db,$root,'commands',$owner,60,600,$now);
  $q=$db->prepare('SELECT id FROM sg_product_feedback WHERE owner_hash=?AND request_hash=?AND created_at>?ORDER BY created_at DESC LIMIT 1');$q->execute([$owner,$hash,$now-86400]);$id=$q->fetchColumn();$duplicate=$id!==false;
  if(!$duplicate){
   sgProductFeedbackRate($db,$root,'submit',$owner,8,3600,$now);$id='SGF-'.gmdate('ymd',$now).'-'.strtoupper(bin2hex(random_bytes(6)));
   $db->prepare('INSERT INTO sg_product_feedback(id,product_id,reason,note_envelope,owner_hash,request_hash,created_at,updated_at,expires_at)VALUES(?,?,?,?,?,?,?,?,?)')->execute([$id,$product['id'],$body['reason'],nodenoControlEncrypt($root,$note,'product-feedback:'.$id),$owner,$hash,$now,$now,$now+180*86400]);
  }
  $db->prepare('INSERT INTO sg_product_feedback_commands VALUES(?,?,?,?,?)')->execute([$key,$hash,$id,$now,$now+86400]);return ['reference'=>$id,'status'=>'received','duplicate'=>$duplicate];
 });
}
function sgProductFeedbackHandle(string $private,string $method):void{
 try{
  require_once $private.'/control-http.php';$state=nodenoStoreContext($private);$root=nodenoAccountStorage($state['storage']);$db=nodenoControlDatabase($root);sgProductFeedbackSchema($db);sgProductFeedbackCleanup($db,time());nodenoAccountSession($root,$db);
  $cookie='__Host-SGFEEDBACK_'.substr(hash('sha256',$root),0,10);$token=$_COOKIE[$cookie]??null;
  if(!is_string($token)||!preg_match('/^[a-f0-9]{64}$/D',$token)){
   if($method!=='GET')sgProductFeedbackError(403,'feedback_owner_required');$token=bin2hex(random_bytes(32));setcookie($cookie,$token,['expires'=>time()+30*86400,'path'=>'/','secure'=>true,'httponly'=>true,'samesite'=>'Strict']);
  }
  $owner=sgProductFeedbackOwner($root,$token);
  if($method==='GET'){sgProductFeedbackRate($db,$root,'bootstrap',$owner,60,600,time());nodenoAccountJson(['csrfToken'=>$_SESSION['csrf'],'maxNoteLength'=>1200,'retentionDays'=>180]);}
  elseif($method==='POST'){$body=nodenoAccountBody();$result=sgProductFeedbackSubmit($db,$root,$state['catalog'],$owner,$body,time());nodenoAccountJson($result,$result['duplicate']?200:201);}
  else nodenoAccountJson(['error'=>'method_not_allowed'],405,['Allow'=>'GET, POST']);
 }catch(NodenoControlHttpError|NodenoAccountHttpError $error){nodenoAccountJson(['error'=>$error->errorCode],$error->status,$error->headers);}catch(Throwable $error){nodenoAccountJson(['error'=>'feedback_service_unavailable'],503);}finally{if(session_status()===PHP_SESSION_ACTIVE)session_write_close();}
}
function sgProductFeedbackRequire(array $ctx,bool $write=false):array{
 if(!$ctx['user'])sgProductFeedbackError(401,'authentication_required');$role=$ctx['user']['role']??'';
 if(!in_array($role,['owner','manager','catalog','support'],true))sgProductFeedbackError(403,'permission_denied');
 return nodenoControlRequire($ctx,$role==='support'?($write?'feedback.write':'feedback.read'):'catalog.write',$write);
}
function sgProductFeedbackView(string $root,array $row):array{
 return ['reference'=>$row['id'],'productId'=>$row['product_id'],'reason'=>$row['reason'],'note'=>nodenoControlDecrypt($root,$row['note_envelope'],'product-feedback:'.$row['id']),'status'=>$row['status'],'version'=>(int)$row['version'],'createdAt'=>(int)$row['created_at'],'updatedAt'=>(int)$row['updated_at'],'expiresAt'=>(int)$row['expires_at']];
}
function sgProductFeedbackDetail(PDO $db,string $root,string $id):array{
 $q=$db->prepare('SELECT * FROM sg_product_feedback WHERE id=?');$q->execute([$id]);$row=$q->fetch();if(!$row)sgProductFeedbackError(404,'feedback_not_found');$out=sgProductFeedbackView($root,$row);
 $q=$db->prepare('SELECT * FROM sg_product_feedback_events WHERE feedback_id=?ORDER BY id DESC LIMIT 100');$q->execute([$id]);$out['history']=array_map(static fn($event)=>['status'=>$event['status'],'note'=>nodenoControlDecrypt($root,$event['note_envelope'],'product-feedback-event:'.$id),'actorId'=>$event['actor_id'],'at'=>(int)$event['created_at']],$q->fetchAll());return $out;
}
function sgProductFeedbackAdmin(array $ctx,string $route,string $method,array $body):?array{
 if($route!=='product-feedback'&&!str_starts_with($route,'product-feedback/'))return null;$actor=sgProductFeedbackRequire($ctx,$method!=='GET');$db=$ctx['db'];$root=$ctx['root'];sgProductFeedbackSchema($db);sgProductFeedbackCleanup($db,time());
 if($route==='product-feedback'&&$method==='GET'){
  $rawPage=$_GET['page']??'1';if(!is_scalar($rawPage)||!preg_match('/^[0-9]{1,7}$/D',(string)$rawPage))sgProductFeedbackError(422,'feedback_request_invalid');$page=max(1,min(1000000,(int)$rawPage));$status=$_GET['status']??'';if(!is_string($status)||!in_array($status,['','new','reviewing','resolved','rejected'],true))sgProductFeedbackError(422,'feedback_request_invalid');
  $where=$status===''?'1=1':'status=?';$args=$status===''?[]:[$status];$q=$db->prepare('SELECT COUNT(*)FROM sg_product_feedback WHERE '.$where);$q->execute($args);$total=(int)$q->fetchColumn();$q=$db->prepare('SELECT * FROM sg_product_feedback WHERE '.$where.' ORDER BY created_at DESC,id LIMIT 25 OFFSET '.(($page-1)*25));$q->execute($args);return ['data'=>array_map(static fn($row)=>sgProductFeedbackView($root,$row),$q->fetchAll()),'page'=>$page,'pageSize'=>25,'total'=>$total];
 }
 if(!preg_match('~^product-feedback/(SGF-[0-9]{6}-[A-F0-9]{12})$~D',$route,$m))sgProductFeedbackError(404,'feedback_not_found');$id=$m[1];
 if($method==='GET')return sgProductFeedbackDetail($db,$root,$id);
 if($method!=='PATCH')sgProductFeedbackError(405,'method_not_allowed');
 if(array_diff(array_keys($body),['version','status','note'])||!is_int($body['version']??null)||!in_array($body['status']??null,['new','reviewing','resolved','rejected'],true))sgProductFeedbackError(422,'feedback_request_invalid');$note=sgProductFeedbackText($body['note']??'');
 return nodenoControlTransaction($db,static function()use($db,$root,$id,$body,$note,$actor):array{
  $current=sgProductFeedbackDetail($db,$root,$id);if($current['version']!==$body['version'])sgProductFeedbackError(409,'version_conflict');$now=time();
  $db->prepare('UPDATE sg_product_feedback SET status=?,version=version+1,updated_at=?WHERE id=?')->execute([$body['status'],$now,$id]);$db->prepare('INSERT INTO sg_product_feedback_events(feedback_id,status,note_envelope,actor_id,created_at)VALUES(?,?,?,?,?)')->execute([$id,$body['status'],nodenoControlEncrypt($root,$note,'product-feedback-event:'.$id),$actor['id'],$now]);
  nodenoControlAudit($db,$root,$actor['id'],'review','product-feedback',$id,['status'=>$body['status'],'version'=>$body['version']+1]);return sgProductFeedbackDetail($db,$root,$id);
 });
}
function sgProductFeedbackAdminPage(string $mount,string $version):never{
 foreach(nodenoSecurityHeaders()as $key=>$value)header($key.': '.$value);header('Cache-Control: private, no-store');header('X-Robots-Tag: noindex, nofollow');header('Content-Type: text/html; charset=utf-8');$e=static fn($v)=>htmlspecialchars($v,ENT_QUOTES|ENT_SUBSTITUTE,'UTF-8');
 echo '<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>Ürün geri bildirimleri | SEXOGATE</title><link rel="icon" type="image/svg+xml" href="'.$e($mount.'/favicon.svg').'"><link rel="stylesheet" href="'.$e($mount.'/admin.css?v='.$version).'"><link rel="stylesheet" href="'.$e($mount.'/sexogate.css?v='.$version).'"><link rel="stylesheet" href="'.$e($mount.'/sg-product-feedback.css?v='.$version).'"><script type="module" src="'.$e($mount.'/sg-product-feedback.js?v='.$version).'"></script></head><body class="sg-feedback-admin-page"><a class="sg-feedback-skip" href="#sg-product-feedback-admin">İçeriğe geç</a><div class="sg-feedback-admin-layout"><aside class="sg-feedback-admin-sidebar" aria-label="SEXOGATE yönetimi"><a class="sg-feedback-admin-brand" href="'.$e($mount.'/yonetim').'"><img src="'.$e($mount.'/assets/brand/logo-horizontal.svg').'" width="160" height="90" alt="SEXOGATE"><span>Mağaza yönetimi</span></a><nav aria-label="Yönetim gezinmesi"><a href="'.$e($mount.'/yonetim').'">Genel yönetim</a><a href="'.$e($mount.'/yonetim/urun-geri-bildirimleri').'" aria-current="page">Ürün geri bildirimleri</a></nav><a class="sg-feedback-admin-store" href="'.$e($mount.'/').'">Mağazayı görüntüle</a></aside><main id="sg-product-feedback-admin" class="sg-feedback-admin" tabindex="-1"><p role="status">Yönetim oturumu kontrol ediliyor.</p></main></div></body></html>';exit;
}
