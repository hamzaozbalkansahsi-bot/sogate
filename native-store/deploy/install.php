<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/deploy/install.php
 * Açıklama   : Yalnız doğrulanmış test paketi için süreli kurucu; özel alan ve MFA yöneticisini hazırlar.
 */
declare(strict_types=1);
ini_set('display_errors','0');header('Content-Type: application/json; charset=utf-8');header('Cache-Control: no-store');header('X-Robots-Tag: noindex,nofollow');
try{
 $request=json_decode((string)file_get_contents(__DIR__.'/app/native-request.json'),true);
 if($_SERVER['REQUEST_METHOD']!=='POST'||!is_array($request)||time()>($request['expires']??0)||!hash_equals($request['tokenHash']??'',hash('sha256',$_SERVER['HTTP_X_NATIVE_DEPLOY']??'')))throw new RuntimeException('request_rejected');
 $id=$request['release']??'';if(!preg_match('/^[a-f0-9]{24}$/D',$id))throw new RuntimeException('release_invalid');
 $body=json_decode((string)file_get_contents('php://input',false,null,0,100001),true,32,JSON_THROW_ON_ERROR);
 if(!is_array($body)||!filter_var($body['email']??'',FILTER_VALIDATE_EMAIL)||!preg_match('/^\$2y\$/', $body['passwordHash']??'')||!preg_match('/^[A-Z2-7]{16,256}$/D',$body['totpSecret']??''))throw new RuntimeException('owner_input_invalid');
 $doc=realpath($_SERVER['DOCUMENT_ROOT']);if($doc===false)throw new RuntimeException('document_root_invalid');$parent=realpath(dirname($doc));$home=$parent.'/.sexogate-native-test';
 if(is_link($home))throw new RuntimeException('private_symlink');
 if(!is_dir($home)){if(!mkdir($home,0700))throw new RuntimeException('private_create_failed');file_put_contents($home.'/owner.json',json_encode(['owner'=>$request['owner'],'purpose'=>'sexogate-native-test-v1'],JSON_THROW_ON_ERROR));}
 $owner=json_decode((string)file_get_contents($home.'/owner.json'),true);if(($owner['owner']??null)!==$request['owner']||($owner['purpose']??null)!=='sexogate-native-test-v1')throw new RuntimeException('private_owner_mismatch');
 $real=realpath($home);if($real===false||str_starts_with($real.'/',rtrim($doc,'/').'/'))throw new RuntimeException('private_inside_webroot');
 foreach(['releases','state']as $name){if(is_link($home.'/'.$name))throw new RuntimeException('private_symlink');if(!is_dir($home.'/'.$name)&&!mkdir($home.'/'.$name,0700))throw new RuntimeException('private_create_failed');}
 $archive=__DIR__.'/app/native-payload-'.$id.'.zip';if(!hash_equals($request['sha256'],hash_file('sha256',$archive)))throw new RuntimeException('archive_hash_mismatch');
 $zip=new ZipArchive();if($zip->open($archive)!==true||$zip->numFiles>2000)throw new RuntimeException('archive_unavailable');
 $manifest=json_decode($zip->getFromName('deployment-manifest.json'),true,512,JSON_THROW_ON_ERROR);if(($manifest['release']??null)!==$id||($manifest['checkoutEnabled']??null)!==false||!in_array($manifest['products']??null,[0,2194],true)||($manifest['previewOnly']??null)!==true)throw new RuntimeException('manifest_invalid');
 $release=$home.'/releases/'.$id;if(is_link($release))throw new RuntimeException('release_symlink');$fresh=!is_dir($release);if($fresh&&!mkdir($release,0700))throw new RuntimeException('release_create_failed');$total=0;$seen=[];
 for($i=0;$i<$zip->numFiles;$i++){
  $item=$zip->statIndex($i);$name=$item['name'];$zip->getExternalAttributesIndex($i,$system,$attributes);
  if(!preg_match('~^(?:(?:public|private|deploy)/[A-Za-z0-9_./-]+|deployment-manifest\.json)$~D',$name)||str_contains($name,'..')||in_array('.',explode('/',$name),true)||str_contains($name,'//')||isset($seen[$name])||(($attributes>>16)&0170000)===0120000)throw new RuntimeException('archive_path_invalid');
  $seen[$name]=true;$total+=$item['size'];if($item['size']>25000000||$total>80000000)throw new RuntimeException('archive_too_large');
  $bytes=$zip->getFromIndex($i);if(!is_string($bytes))throw new RuntimeException('archive_read_failed');
  if($name!=='deployment-manifest.json'&&(!isset($manifest['files'][$name])||!hash_equals($manifest['files'][$name],hash('sha256',$bytes))))throw new RuntimeException('file_hash_mismatch');
  $target=$release.'/'.$name;if($fresh){$directory=dirname($target);if(!is_dir($directory)&&!mkdir($directory,0700,true))throw new RuntimeException('release_create_failed');if(file_put_contents($target,$bytes,LOCK_EX)!==strlen($bytes))throw new RuntimeException('file_write_failed');chmod($target,0600);}
  if(is_link($target)||!str_starts_with(str_replace('\\','/',(string)realpath($target)),str_replace('\\','/',(string)realpath($release)).'/')||!hash_equals(hash('sha256',$bytes),hash_file('sha256',$target)))throw new RuntimeException('existing_release_changed');
 }
 $zip->close();if(count($seen)!==count($manifest['files'])+1)throw new RuntimeException('archive_incomplete');
 $catalog=json_decode((string)file_get_contents($release.'/private/catalog.json'),true,512,JSON_THROW_ON_ERROR);
 if(($catalog['brand']['name']??null)!=='SEXOGATE'||count($catalog['products']??[])!==$manifest['products'])throw new RuntimeException('unexpected_catalog_data');
 if($manifest['products']===0){if($catalog['categories']!==[])throw new RuntimeException('unexpected_catalog_data');}
 else{
  if(($catalog['catalogOrigin']??null)!=='sexogate-suppliers-v1'||($catalog['dataset']??null)!==($manifest['dataset']??null)||!preg_match('/^[a-f0-9]{32}$/D',$manifest['dataset']??'')||count($catalog['categories'])!==6)throw new RuntimeException('catalog_provenance_invalid');$ids=[];$skus=[];
  foreach($catalog['products']as $product){if(!preg_match('/^sg_(?:xsh|lio|sis)_[a-f0-9]{16}$/D',$product['id']??'')||isset($ids[$product['id']])||isset($skus[$product['code']])||($product['catalogOrigin']??'')!=='sexogate-suppliers-v1'||!in_array($product['sourceVendor']??'',['xshopum','liona','sistina'],true)||($product['published']??true)!==false||($product['hidden']??false)!==true||($product['stockKnown']??true)!==false||($product['stockQuantity']??null)!==null)throw new RuntimeException('catalog_provenance_invalid');$ids[$product['id']]=true;$skus[$product['code']]=true;}
 }
 $bank=json_decode((string)file_get_contents($release.'/private/blog-bank.json'),true,512,JSON_THROW_ON_ERROR);
 foreach($bank['articles']??[]as $article)if(!str_starts_with($article['id']??'','sexogate-'))throw new RuntimeException('unexpected_article_data');
 $runtime=['privateRoot'=>$release.'/private','storageRoot'=>$home.'/state','mediaRoot'=>$home.'/media'];
 file_put_contents($release.'/nodeno-runtime.php','<?php return '.var_export($runtime,true).';',LOCK_EX);chmod($release.'/nodeno-runtime.php',0600);
 foreach([$release.'/private/cache',$home.'/media']as $directory)if(!is_dir($directory))mkdir($directory,0700);
 require $release.'/private/control-auth.php';$db=nodenoControlDatabase($home.'/state');
 if(!(int)$db->query("SELECT COUNT(*) FROM control_users WHERE role='owner'")->fetchColumn()){
  $uid=nodenoControlId('owner_');$db->prepare('INSERT INTO control_users(id,email,display_name,role,password_hash,totp_secret,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)')->execute([$uid,$body['email'],'Mağaza yöneticisi','owner',$body['passwordHash'],nodenoControlEncrypt($home.'/state',$body['totpSecret'],$uid),time(),time()]);nodenoControlAudit($db,$home.'/state',$uid,'setup','team',$uid);
 }
 if($db->query('PRAGMA quick_check')->fetchColumn()!=='ok')throw new RuntimeException('database_integrity_failed');
 $php=null;foreach(['/opt/alt/php83/usr/bin/php','/opt/cpanel/ea-php83/root/usr/bin/php','/usr/local/bin/php']as $candidate)if(is_file($candidate)&&is_executable($candidate)){$php=$candidate;break;}
 file_put_contents($home.'/active.json.tmp',json_encode(['release'=>$id],JSON_THROW_ON_ERROR),LOCK_EX);chmod($home.'/active.json.tmp',0600);rename($home.'/active.json.tmp',$home.'/active.json');
 if(!copy($release.'/deploy/worker.php',$home.'/worker.php'))throw new RuntimeException('worker_install_failed');chmod($home.'/worker.php',0600);
 unlink(__DIR__.'/app/native-request.json');echo json_encode(['installed'=>true,'release'=>$id,'privateRoot'=>$home,'phpCli'=>$php,'products'=>$manifest['products'],'checkoutEnabled'=>false,'ownerCount'=>(int)$db->query("SELECT COUNT(*) FROM control_users WHERE role='owner'")->fetchColumn()],JSON_THROW_ON_ERROR);
}catch(Throwable $error){http_response_code(400);$code=preg_match('/^[a-z_]+$/D',$error->getMessage())?$error->getMessage():'native_install_failed';echo json_encode(['installed'=>false,'code'=>$code]);}
