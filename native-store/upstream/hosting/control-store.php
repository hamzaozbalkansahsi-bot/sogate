<?php
declare(strict_types=1);
require_once __DIR__.'/account.php';

final class NodenoControlHttpError extends RuntimeException {
 public int $status;public string $errorCode;public array $headers;
 public function __construct(int $status,string $code,array $headers=[]){parent::__construct($code);$this->status=$status;$this->errorCode=$code;$this->headers=$headers;}
}
function nodenoControlTransaction(PDO $db,callable $action){
 static $depth=[];$key=spl_object_id($db);if(($depth[$key]??0)>0)return $action();$db->exec('BEGIN IMMEDIATE');$depth[$key]=1;
 try{$result=$action();$db->exec('COMMIT');return $result;}catch(Throwable $e){$db->exec('ROLLBACK');throw $e;}finally{unset($depth[$key]);}
}
function nodenoControlDatabase(string $requested):PDO {
 $root=nodenoAccountStorage($requested);$db=nodenoAccountDatabase($root);
 $exists=$db->query("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='control_settings'")->fetchColumn();
 if($exists){$q=$db->prepare('SELECT value_json FROM control_settings WHERE name=?');$q->execute(['schema_version']);if($q->fetchColumn()==='1')return $db;}
 nodenoControlTransaction($db,static function()use($db):void{
  $db->exec("CREATE TABLE IF NOT EXISTS control_users(id TEXT PRIMARY KEY,email TEXT NOT NULL UNIQUE COLLATE NOCASE,display_name TEXT NOT NULL DEFAULT '',role TEXT NOT NULL,active INTEGER NOT NULL DEFAULT 1,password_hash TEXT NOT NULL,totp_secret TEXT NOT NULL,last_totp_counter INTEGER NOT NULL DEFAULT -1,recovery_json TEXT NOT NULL DEFAULT '[]',auth_version INTEGER NOT NULL DEFAULT 1,version INTEGER NOT NULL DEFAULT 1,created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL);
   CREATE TABLE IF NOT EXISTS control_invites(id TEXT PRIMARY KEY,email TEXT NOT NULL,role TEXT NOT NULL,token_hash TEXT NOT NULL UNIQUE,expires_at INTEGER NOT NULL,consumed_at INTEGER,created_by TEXT NOT NULL,created_at INTEGER NOT NULL);
   CREATE TABLE IF NOT EXISTS control_settings(name TEXT PRIMARY KEY,value_json TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1,updated_at INTEGER NOT NULL);
   CREATE TABLE IF NOT EXISTS control_audit(id INTEGER PRIMARY KEY AUTOINCREMENT,actor_id TEXT NOT NULL,action TEXT NOT NULL,resource TEXT NOT NULL,record_id TEXT NOT NULL,detail_json TEXT NOT NULL,occurred_at INTEGER NOT NULL,previous_hash TEXT NOT NULL,entry_hash TEXT NOT NULL);
   CREATE TABLE IF NOT EXISTS control_rate_limits(key_hash TEXT PRIMARY KEY,window_start INTEGER NOT NULL,count INTEGER NOT NULL);
   CREATE TABLE IF NOT EXISTS control_records(resource TEXT NOT NULL,id TEXT NOT NULL,data_json TEXT NOT NULL,published_json TEXT,version INTEGER NOT NULL DEFAULT 1,published_version INTEGER NOT NULL DEFAULT 0,created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL,published_at INTEGER,PRIMARY KEY(resource,id));
   CREATE INDEX IF NOT EXISTS control_records_public ON control_records(resource,published_version);
   CREATE TABLE IF NOT EXISTS control_record_versions(resource TEXT NOT NULL,record_id TEXT NOT NULL,version INTEGER NOT NULL,data_json TEXT NOT NULL,actor_id TEXT NOT NULL,created_at INTEGER NOT NULL,PRIMARY KEY(resource,record_id,version));
   CREATE TABLE IF NOT EXISTS control_commands(key_hash TEXT PRIMARY KEY,actor_id TEXT NOT NULL,request_hash TEXT NOT NULL,response_json TEXT NOT NULL,created_at INTEGER NOT NULL);
   CREATE TABLE IF NOT EXISTS control_jobs(id TEXT PRIMARY KEY,type TEXT NOT NULL,status TEXT NOT NULL,request_json TEXT NOT NULL,result_json TEXT,attempts INTEGER NOT NULL DEFAULT 0,next_attempt_at INTEGER NOT NULL,created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL,idempotency_key TEXT UNIQUE);");
  $db->prepare('INSERT OR IGNORE INTO control_settings(name,value_json,updated_at) VALUES(?,?,?)')->execute(['public_revision','0',time()]);
  $db->prepare('INSERT OR REPLACE INTO control_settings(name,value_json,updated_at) VALUES(?,?,?)')->execute(['schema_version','1',time()]);
 });return $db;
}
function nodenoControlKey(string $requested):string {
 $root=nodenoAccountStorage($requested);$file=$root.'/control-key.bin';if(is_link($file))throw new RuntimeException('Unsafe control key');$handle=fopen($file,'c+b');if($handle===false)throw new RuntimeException('Control key unavailable');
 try{if(!flock($handle,LOCK_EX))throw new RuntimeException('Control key lock unavailable');$stat=fstat($handle);if($stat['size']===0){$key=random_bytes(32);if(fwrite($handle,$key)!==32||!fflush($handle))throw new RuntimeException('Control key write failed');}else{rewind($handle);$key=stream_get_contents($handle,33);if(strlen($key)!==32)throw new RuntimeException('Invalid control key');}chmod($file,0600);flock($handle,LOCK_UN);return $key;}finally{fclose($handle);}
}
function nodenoControlEncrypt(string $root,string $plain,string $aad):string {
 $iv=random_bytes(12);$tag='';$encrypted=openssl_encrypt($plain,'aes-256-gcm',nodenoControlKey($root),OPENSSL_RAW_DATA,$iv,$tag,'NODENO-CONTROL:v1:'.$aad,16);if($encrypted===false)throw new RuntimeException('Control encryption failed');return json_encode(['v'=>1,'iv'=>base64_encode($iv),'tag'=>base64_encode($tag),'data'=>base64_encode($encrypted)],JSON_THROW_ON_ERROR);
}
function nodenoControlDecrypt(string $root,string $value,string $aad):string {
 $data=json_decode($value,true,8,JSON_THROW_ON_ERROR);if(($data['v']??null)!==1)throw new RuntimeException('Invalid encrypted value');$iv=base64_decode($data['iv']??'',true);$tag=base64_decode($data['tag']??'',true);$body=base64_decode($data['data']??'',true);if($iv===false||strlen($iv)!==12||$tag===false||strlen($tag)!==16||$body===false)throw new RuntimeException('Invalid encrypted value');$plain=openssl_decrypt($body,'aes-256-gcm',nodenoControlKey($root),OPENSSL_RAW_DATA,$iv,$tag,'NODENO-CONTROL:v1:'.$aad);if($plain===false)throw new RuntimeException('Control authentication failed');return $plain;
}
function nodenoControlRedact($value){
 if(!is_array($value))return is_string($value)?substr($value,0,2000):$value;$result=[];foreach($value as $key=>$item)$result[$key]=preg_match('/password|secret|token|otp|credential|api.?key|recovery|channel/i',(string)$key)?'[REDACTED]':nodenoControlRedact($item);return $result;
}
function nodenoControlAudit(PDO $db,string $root,string $actor,string $action,string $resource,string $id,array $detail=[]):void {
 nodenoControlTransaction($db,static function()use($db,$root,$actor,$action,$resource,$id,$detail):void{
  $previous=(string)($db->query('SELECT entry_hash FROM control_audit ORDER BY id DESC LIMIT 1')->fetchColumn()?:'');$now=time();$json=json_encode(nodenoControlRedact($detail),JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE);$hash=hash_hmac('sha256',json_encode([$previous,$actor,$action,$resource,$id,$json,$now],JSON_THROW_ON_ERROR),nodenoControlKey($root));$db->prepare('INSERT INTO control_audit(actor_id,action,resource,record_id,detail_json,occurred_at,previous_hash,entry_hash) VALUES(?,?,?,?,?,?,?,?)')->execute([$actor,$action,$resource,$id,$json,$now,$previous,$hash]);
 });
}
function nodenoControlSetting(PDO $db,string $name,$fallback=null){$q=$db->prepare('SELECT value_json FROM control_settings WHERE name=?');$q->execute([$name]);$value=$q->fetchColumn();return $value===false?$fallback:json_decode($value,true,512,JSON_THROW_ON_ERROR);}
function nodenoControlSetSetting(PDO $db,string $name,$value):void {$db->prepare('INSERT INTO control_settings(name,value_json,updated_at) VALUES(?,?,?) ON CONFLICT(name) DO UPDATE SET value_json=excluded.value_json,version=control_settings.version+1,updated_at=excluded.updated_at')->execute([$name,json_encode($value,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE),time()]);}
function nodenoControlRate(PDO $db,string $root,string $purpose,string $subject,int $limit,int $window):void {
 $key=hash_hmac('sha256',$purpose.'|'.$subject,nodenoControlKey($root));$now=time();$allowed=nodenoControlTransaction($db,static function()use($db,$key,$now,$window,$limit):bool{
  $q=$db->prepare('SELECT * FROM control_rate_limits WHERE key_hash=?');$q->execute([$key]);$row=$q->fetch();if(!$row||$row['window_start']<=$now-$window){$db->prepare('INSERT OR REPLACE INTO control_rate_limits(key_hash,window_start,count) VALUES(?,?,1)')->execute([$key,$now]);return true;}if($row['count']>=$limit)return false;$db->prepare('UPDATE control_rate_limits SET count=count+1 WHERE key_hash=?')->execute([$key]);return true;
 });if(!$allowed)throw new NodenoControlHttpError(429,'rate_limited',['Retry-After'=>(string)$window]);
}
function nodenoControlId(string $prefix=''):string { return $prefix.bin2hex(random_bytes(16)); }
