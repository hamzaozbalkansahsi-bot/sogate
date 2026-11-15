<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/deploy/maintenance.php
 * Açıklama   : Süreli token ile yalnız bu test uygulamasının CLI durumunu ve şifreli SQLite yedeğini sağlar.
 */
declare(strict_types=1);
ini_set('display_errors','0');header('Content-Type: application/json; charset=utf-8');header('Cache-Control: no-store');header('X-Robots-Tag: noindex,nofollow');
try{
 $request=json_decode((string)file_get_contents(__DIR__.'/app/native-maintenance-request.json'),true);
 if($_SERVER['REQUEST_METHOD']!=='POST'||!is_array($request)||time()>($request['expires']??0)||!hash_equals($request['tokenHash']??'',hash('sha256',$_SERVER['HTTP_X_NATIVE_MAINTENANCE']??'')))throw new RuntimeException('request_rejected');
 $home=dirname(realpath($_SERVER['DOCUMENT_ROOT'])).'/.sexogate-native-test';$owner=json_decode((string)file_get_contents($home.'/owner.json'),true);
 if(($owner['owner']??null)!==$request['owner']||($owner['purpose']??null)!=='sexogate-native-test-v1'||is_link($home))throw new RuntimeException('owner_mismatch');
 $input=json_decode((string)file_get_contents('php://input',false,null,0,10001),true,16,JSON_THROW_ON_ERROR);
 if(($input['action']??null)==='status'){$file=$home.'/worker-health.json';echo is_file($file)?file_get_contents($file):'{"ok":false,"pending":true}';exit;}
 if(($input['action']??null)!=='backup'||!preg_match('/^[a-f0-9]{24}$/D',$input['id']??'')||!preg_match('/^[a-f0-9]{64}$/D',$input['key']??''))throw new RuntimeException('backup_input_invalid');
 $id=$input['id'];$temp=$home.'/backup-'.$id;if(file_exists($temp)||!mkdir($temp,0700))throw new RuntimeException('backup_path_conflict');$zipPath=$temp.'/backup.zip';$zip=new ZipArchive();if($zip->open($zipPath,ZipArchive::CREATE|ZipArchive::EXCL)!==true)throw new RuntimeException('backup_zip_failed');
 $manifest=['schema'=>1,'at'=>time(),'release'=>json_decode((string)file_get_contents($home.'/active.json'),true)['release'],'databases'=>[],'files'=>[]];$temporary=[];
 foreach(glob($home.'/state/*.sqlite')as $file){
  $name=basename($file);if(is_link($file)||!preg_match('/^[a-z_-]+\.sqlite$/D',$name))throw new RuntimeException('database_path_invalid');$source=new PDO('sqlite:'.$file,null,null,[PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION]);$source->exec('PRAGMA busy_timeout=5000');$snapshot=$temp.'/'.$name;$source->exec('VACUUM INTO '.$source->quote($snapshot));$source=null;$temporary[]=$snapshot;
  $db=new PDO('sqlite:'.$snapshot,null,null,[PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION]);if($db->query('PRAGMA integrity_check')->fetchColumn()!=='ok'||$db->query('PRAGMA foreign_key_check')->fetchAll()!==[])throw new RuntimeException('backup_integrity_failed');
  $counts=[];foreach($db->query("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")->fetchAll(PDO::FETCH_COLUMN)as $table)$counts[$table]=(int)$db->query('SELECT COUNT(*) FROM "'.str_replace('"','""',$table).'"')->fetchColumn();$db=null;
  $manifest['databases'][$name]=$counts;$manifest['files'][$name]=hash_file('sha256',$snapshot);$zip->addFile($snapshot,$name);
 }
 foreach(glob($home.'/state/*.bin')as $file){$name=basename($file);if(is_link($file)||!preg_match('/^[a-z_-]+\.bin$/D',$name))throw new RuntimeException('key_path_invalid');$manifest['files'][$name]=hash_file('sha256',$file);$zip->addFile($file,$name);}
 $zip->addFromString('manifest.json',json_encode($manifest,JSON_THROW_ON_ERROR));$zip->close();$plain=file_get_contents($zipPath);if(!is_string($plain)||strlen($plain)>40000000)throw new RuntimeException('backup_size_invalid');$nonce=random_bytes(12);$tag='';$cipher=openssl_encrypt($plain,'aes-256-gcm',hex2bin($input['key']),OPENSSL_RAW_DATA,$nonce,$tag,'sexogate-native-backup-v1',16);if($cipher===false)throw new RuntimeException('backup_encryption_failed');
 $destination=__DIR__.'/app/native-backups';if(is_link($destination))throw new RuntimeException('backup_destination_invalid');if(!is_dir($destination))mkdir($destination,0700);$encrypted='SGNATIVE1'.$nonce.$tag.$cipher;$file=$destination.'/'.$id.'.aesgcm';if(file_put_contents($file,$encrypted,LOCK_EX)!==strlen($encrypted))throw new RuntimeException('backup_write_failed');chmod($file,0600);
 foreach($temporary as $file)unlink($file);unlink($zipPath);rmdir($temp);echo json_encode(['created'=>true,'id'=>$id,'sha256'=>hash('sha256',$encrypted),'databases'=>count($manifest['databases']),'tables'=>array_sum(array_map('count',$manifest['databases'])),'rows'=>array_sum(array_map('array_sum',$manifest['databases']))],JSON_THROW_ON_ERROR);
}catch(Throwable $error){http_response_code(400);echo json_encode(['created'=>false,'code'=>preg_match('/^[a-z_]+$/D',$error->getMessage())?$error->getMessage():'maintenance_failed']);}
