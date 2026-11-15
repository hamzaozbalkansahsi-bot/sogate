<?php
declare(strict_types=1);
require_once __DIR__.'/control-store.php';

function nodenoControlBase32(string $bytes):string {
 $alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';$bits='';foreach(unpack('C*',$bytes) as $n)$bits.=str_pad(decbin($n),8,'0',STR_PAD_LEFT);$out='';foreach(str_split($bits,5) as $part)$out.=$alphabet[bindec(str_pad($part,5,'0'))];return $out;
}
function nodenoControlTotp(string $secret,int $time,int $digits=6):string {
 if(!preg_match('/^[A-Z2-7]+$/D',$secret)||!in_array($digits,[6,8],true))throw new RuntimeException('Invalid TOTP input');$bits='';foreach(str_split($secret) as $c)$bits.=str_pad(decbin(strpos('ABCDEFGHIJKLMNOPQRSTUVWXYZ234567',$c)),5,'0',STR_PAD_LEFT);$key='';foreach(str_split($bits,8) as $part)if(strlen($part)===8)$key.=chr(bindec($part));$counter=intdiv($time,30);$hash=hash_hmac('sha1',pack('N2',intdiv($counter,4294967296),$counter%4294967296),$key,true);$offset=ord($hash[19])&15;$number=unpack('N',substr($hash,$offset,4))[1]&0x7fffffff;return str_pad((string)($number%(10**$digits)),$digits,'0',STR_PAD_LEFT);
}
function nodenoControlTotpCounter(string $secret,string $code,int $time,int $last):?int {
 if(!preg_match('/^[0-9]{6}$/D',$code))return null;$current=intdiv($time,30);for($i=-1;$i<=1;$i++){ $counter=$current+$i;if($counter>$last&&$counter>=0&&hash_equals(nodenoControlTotp($secret,$counter*30),$code))return $counter;}return null;
}
function nodenoControlPermissions(string $role):array {
 $map=['owner'=>['*'],'manager'=>['dashboard.read','catalog.read','catalog.write','operations.read','operations.write','marketing.read','marketing.write','analytics.read','settings.read','settings.write','audit.read'], 'catalog'=>['dashboard.read','catalog.read','catalog.write'], 'operations'=>['dashboard.read','operations.read','operations.write'], 'marketing'=>['dashboard.read','marketing.read','marketing.write','analytics.read','catalog.read'], 'analyst'=>['dashboard.read','analytics.read']];return $map[$role]??[];
}
function nodenoControlSafeUser(?array $user):?array {return $user?['id'=>$user['id'],'email'=>$user['email'],'name'=>$user['display_name'],'role'=>$user['role'],'active'=>(bool)$user['active'],'version'=>(int)$user['version']]:null;}
function nodenoControlRotate(?array $user=null):void {
 $_SESSION=['csrf'=>bin2hex(random_bytes(32)),'createdAt'=>time(),'lastActivity'=>time()];if($user){$_SESSION['userId']=$user['id'];$_SESSION['authVersion']=(int)$user['auth_version'];$_SESSION['elevatedAt']=time();}session_regenerate_id(true);
}
function nodenoControlSession(PDO $db,string $root):array {
 if(session_status()!==PHP_SESSION_NONE)throw new RuntimeException('Conflicting session');$sessions=$root.'/admin-sessions';if(is_link($sessions))throw new RuntimeException('Unsafe session path');if(!is_dir($sessions)&&!mkdir($sessions,0700))throw new RuntimeException('Session storage unavailable');chmod($sessions,0700);
 ini_set('session.use_strict_mode','1');ini_set('session.use_only_cookies','1');session_name('__Host-NODENOADMIN');session_save_path($sessions);session_set_cookie_params(['lifetime'=>0,'path'=>'/','secure'=>true,'httponly'=>true,'samesite'=>'Strict']);session_start();$host=strtolower($_SERVER['HTTP_HOST']??'');
 if(!isset($_SESSION['csrf'],$_SESSION['createdAt'],$_SESSION['lastActivity'])||($_SESSION['host']??$host)!==$host||time()-(int)$_SESSION['createdAt']>28800||time()-(int)$_SESSION['lastActivity']>900)nodenoControlRotate();$_SESSION['host']=$host;$_SESSION['lastActivity']=time();$user=null;
 if(isset($_SESSION['userId'],$_SESSION['authVersion'])){$q=$db->prepare('SELECT * FROM control_users WHERE id=?');$q->execute([$_SESSION['userId']]);$user=$q->fetch();if(!$user||!(bool)$user['active']||(int)$user['auth_version']!==(int)$_SESSION['authVersion']||!nodenoControlPermissions($user['role'])){$user=null;nodenoControlRotate();$_SESSION['host']=$host;}}
 return ['db'=>$db,'root'=>$root,'user'=>$user?:null,'permissions'=>$user?nodenoControlPermissions($user['role']):[]];
}
function nodenoControlRequire(array $ctx,string $permission,bool $elevated=false):array {
 if(!$ctx['user'])throw new NodenoControlHttpError(401,'authentication_required');if(!in_array('*',$ctx['permissions'],true)&&!in_array($permission,$ctx['permissions'],true))throw new NodenoControlHttpError(403,'permission_denied');if($elevated&&($_SESSION['elevatedAt']??0)<time()-300)throw new NodenoControlHttpError(403,'reauthentication_required');return $ctx['user'];
}
function nodenoControlBootstrap(PDO $db,string $root):?array {
 if((int)$db->query("SELECT COUNT(*) FROM control_users WHERE role='owner'")->fetchColumn()>0)return null;$file=$root.'/admin-bootstrap.json';if(is_link($file)||!is_file($file)||filesize($file)>4096)return null;$seed=json_decode(file_get_contents($file),true);if(($seed['schema']??0)!==1||!filter_var($seed['email']??'',FILTER_VALIDATE_EMAIL)||!preg_match('/^[a-f0-9]{64}$/D',$seed['tokenHash']??'')||($seed['expiresAt']??0)<time())return null;return $seed;
}
function nodenoControlView(array $ctx):array {return ['user'=>nodenoControlSafeUser($ctx['user']),'csrfToken'=>$_SESSION['csrf'],'permissions'=>$ctx['permissions'],'setupRequired'=>(int)$ctx['db']->query("SELECT COUNT(*) FROM control_users WHERE role='owner'")->fetchColumn()===0,'bootstrapAvailable'=>nodenoControlBootstrap($ctx['db'],$ctx['root'])!==null,'authStage'=>isset($_SESSION['mfa'])?'mfa':'password'];}
function nodenoControlPassword($value):string {if(!is_string($value)||strlen($value)>72||preg_match_all('/./us',$value)<14)throw new NodenoControlHttpError(422,'password_minimum_14_characters');return $value;}
function nodenoControlEmail($value):string {$value=is_string($value)?strtolower(trim($value)):'';if(strlen($value)>254||!filter_var($value,FILTER_VALIDATE_EMAIL))throw new NodenoControlHttpError(422,'email_invalid');return $value;}
function nodenoControlProof(PDO $db,string $root,array $row,array $body):bool {
 $counter=null;$hashes=json_decode($row['recovery_json'],true);$recovery=$body['recoveryCode']??'';$used=false;
 if(is_string($recovery)&&$recovery!==''){$hash=hash_hmac('sha256',strtoupper(trim($recovery)),nodenoControlKey($root));$index=array_search($hash,$hashes,true);if($index!==false){array_splice($hashes,$index,1);$used=true;}}
 else {$secret=nodenoControlDecrypt($root,$row['totp_secret'],$row['id']);$counter=nodenoControlTotpCounter($secret,(string)($body['code']??''),time(),(int)$row['last_totp_counter']);if($counter===null)return false;}
 if(!$used&&$counter===null)return false;$db->prepare('UPDATE control_users SET last_totp_counter=?,recovery_json=?,auth_version=auth_version+?,updated_at=? WHERE id=?')->execute([$counter??$row['last_totp_counter'],json_encode($hashes),$used?1:0,time(),$row['id']]);return true;
}
function nodenoControlAuth(array &$ctx,string $route,string $method,array $body):?array {
 $db=$ctx['db'];$root=$ctx['root'];if($route==='session'&&$method==='GET')return nodenoControlView($ctx);
 if($route==='logout'&&$method==='POST'){nodenoControlRotate();$ctx['user']=null;$ctx['permissions']=[];return nodenoControlView($ctx);}
 if(in_array($route,['bootstrap/start','invite/start'],true)&&$method==='POST'){
  nodenoControlRate($db,$root,'setup',$_SERVER['REMOTE_ADDR']??'',15,3600);$email=nodenoControlEmail($body['email']??null);$password=nodenoControlPassword($body['password']??null);$token=is_string($body['token']??null)?$body['token']:'';$hash=hash('sha256',$token);$invite=null;
  if($route==='bootstrap/start'){$seed=nodenoControlBootstrap($db,$root);if(!$seed||!hash_equals(strtolower($seed['email']),$email)||!hash_equals($seed['tokenHash'],$hash))throw new NodenoControlHttpError(403,'setup_rejected');$role='owner';$expires=$seed['expiresAt'];}
  else {$q=$db->prepare('SELECT * FROM control_invites WHERE token_hash=? AND email=? AND consumed_at IS NULL AND expires_at>?');$q->execute([$hash,$email,time()]);$invite=$q->fetch();if(!$invite)throw new NodenoControlHttpError(403,'setup_rejected');$role=$invite['role'];$expires=$invite['expires_at'];}
  nodenoControlRotate();$secret=nodenoControlBase32(random_bytes(20));$_SESSION['setup']=['email'=>$email,'passwordHash'=>password_hash($password,PASSWORD_BCRYPT),'secret'=>nodenoControlEncrypt($root,$secret,'setup:'.session_id()),'proof'=>$hash,'expiresAt'=>min($expires,time()+600),'role'=>$role,'inviteId'=>$invite['id']??null];return ['totpSecret'=>$secret,'otpauthUri'=>'otpauth://totp/'.rawurlencode('NODENO:'.$email).'?secret='.$secret.'&issuer=NODENO&algorithm=SHA1&digits=6&period=30','csrfToken'=>$_SESSION['csrf']];
 }
 if(in_array($route,['bootstrap/complete','invite/complete'],true)&&$method==='POST'){
  nodenoControlRate($db,$root,'setup-otp',session_id(),8,300);$pending=$_SESSION['setup']??null;if(!$pending||$pending['expiresAt']<time())throw new NodenoControlHttpError(403,'setup_expired');$secret=nodenoControlDecrypt($root,$pending['secret'],'setup:'.session_id());
  return nodenoControlTransaction($db,static function()use(&$ctx,$db,$root,$pending,$secret,$body):array{
   if($pending['inviteId']){$q=$db->prepare('SELECT * FROM control_invites WHERE id=? AND consumed_at IS NULL AND expires_at>?');$q->execute([$pending['inviteId'],time()]);$invite=$q->fetch();if(!$invite||!hash_equals($invite['token_hash'],$pending['proof']))throw new NodenoControlHttpError(409,'setup_consumed');}
   else {$seed=nodenoControlBootstrap($db,$root);if(!$seed||!hash_equals($seed['tokenHash'],$pending['proof']))throw new NodenoControlHttpError(409,'setup_consumed');}
   $counter=nodenoControlTotpCounter($secret,(string)($body['code']??''),time(),-1);if($counter===null)throw new NodenoControlHttpError(401,'verification_failed');$id=nodenoControlId('u_');$codes=[];$hashes=[];for($i=0;$i<10;$i++){$code=strtoupper(bin2hex(random_bytes(8)));$codes[]=$code;$hashes[]=hash_hmac('sha256',$code,nodenoControlKey($root));}
   $db->prepare('INSERT INTO control_users(id,email,role,password_hash,totp_secret,last_totp_counter,recovery_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)')->execute([$id,$pending['email'],$pending['role'],$pending['passwordHash'],nodenoControlEncrypt($root,$secret,$id),$counter,json_encode($hashes),time(),time()]);if($pending['inviteId'])$db->prepare('UPDATE control_invites SET consumed_at=? WHERE id=?')->execute([time(),$pending['inviteId']]);$q=$db->prepare('SELECT * FROM control_users WHERE id=?');$q->execute([$id]);$ctx['user']=$q->fetch();$ctx['permissions']=nodenoControlPermissions($ctx['user']['role']);nodenoControlAudit($db,$root,$id,'setup','team',$id);nodenoControlRotate($ctx['user']);return array_merge(nodenoControlView($ctx),['recoveryCodes'=>$codes,'_status'=>201]);
  });
 }
 if($route==='login'&&$method==='POST'){
  nodenoControlRate($db,$root,'login-ip',$_SERVER['REMOTE_ADDR']??'',30,3600);$email=strtolower(trim((string)($body['email']??'')));nodenoControlRate($db,$root,'login-email',$email,10,900);$password=(string)($body['password']??'');$q=$db->prepare('SELECT * FROM control_users WHERE email=?');$q->execute([$email]);$row=$q->fetch();$valid=password_verify(substr($password,0,73),$row['password_hash']??'$2y$12$9DD.p5FMyZ8gBLJgYO5hWu9aHbBUzO6utJm2NKGnkFRV9lHfjOLCa');if(!$row||!$row['active']||!$valid||strlen($password)>72)throw new NodenoControlHttpError(401,'credentials_invalid');nodenoControlRotate();$_SESSION['mfa']=['id'=>$row['id'],'version'=>$row['auth_version'],'expiresAt'=>time()+180];return nodenoControlView($ctx);
 }
 if(in_array($route,['login/verify','reauthenticate'],true)&&$method==='POST'){
  nodenoControlRate($db,$root,'otp',session_id(),8,300);$pending=$_SESSION['mfa']??null;if($route==='reauthenticate'){$row=nodenoControlRequire($ctx,'dashboard.read');if(!password_verify((string)($body['password']??''),$row['password_hash']))throw new NodenoControlHttpError(401,'credentials_invalid');$pending=['id'=>$row['id'],'version'=>$row['auth_version'],'expiresAt'=>time()+60];}
  if(!$pending||$pending['expiresAt']<time())throw new NodenoControlHttpError(401,'verification_expired');return nodenoControlTransaction($db,static function()use(&$ctx,$db,$root,$pending,$body):array{$q=$db->prepare('SELECT * FROM control_users WHERE id=?');$q->execute([$pending['id']]);$row=$q->fetch();if(!$row||!$row['active']||(int)$row['auth_version']!==(int)$pending['version']||!nodenoControlProof($db,$root,$row,$body))throw new NodenoControlHttpError(401,'verification_failed');$q->execute([$pending['id']]);$ctx['user']=$q->fetch();$ctx['permissions']=nodenoControlPermissions($ctx['user']['role']);nodenoControlRotate($ctx['user']);nodenoControlAudit($db,$root,$ctx['user']['id'],'login','session','');return nodenoControlView($ctx);});
 }
 return null;
}
