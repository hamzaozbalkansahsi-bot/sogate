<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/deploy/install.php
 * Açıklama   : Yalnız doğrulanmış test paketi için süreli kurucu; özel alan ve MFA yöneticisini hazırlar.
 */
declare(strict_types=1);
function sexogateNativeProductProvenance(array $product,string $catalogOrigin):bool{
 $origin=$product['catalogOrigin']??'';$vendor=$product['sourceVendor']??'';$id=$product['id']??'';
 if(!in_array($catalogOrigin,['sexogate-suppliers-v1','sexogate-catalog-v2'],true)||!is_string($origin)||!is_string($vendor)||!is_string($id))return false;
 if($origin==='sexogate-suppliers-v1'){$prefix=['xshopum'=>'xsh','liona'=>'lio','sistina'=>'sis'][$vendor]??null;return $prefix!==null&&preg_match('/^sg_'.$prefix.'_[a-f0-9]{16}$/D',$id)===1;}
 return $catalogOrigin==='sexogate-catalog-v2'&&$origin==='sexogate-marketplaces-v1'&&$vendor==='trendyol'&&preg_match('/^sg_ty_[a-f0-9]{16}$/D',$id)===1&&is_string($product['code']??null)&&str_starts_with($product['code'],'seo-')&&strlen($product['code'])>4;
}
function sexogateNativeCategoryTree(array $categories,array $products):bool{
 $roots=['sg_toys','sg_lingerie','sg_couples','sg_accessories','sg_care','sg_gifts'];$locales=['tr','en','ru','ar','de','az','kk','tk','uz','ky','fa'];$seen=[];$rootCount=0;
 if(count($categories)<6||count($categories)>200)return false;
 foreach($categories as $category){$id=$category['id']??'';$parent=$category['parentId']??null;if(!is_string($id)||array_key_exists($id,$seen))return false;
  if($parent===null){if(!in_array($id,$roots,true))return false;$rootCount++;}
  elseif(!in_array($parent,$roots,true)||!preg_match('/^'.preg_quote($parent,'/').'_[a-z0-9_]+$/D',$id))return false;
  foreach($locales as $locale){$label=$category['name'][$locale]??null;if(!is_string($label)||trim($label)===''||strlen($label)>240||preg_match('//u',$label)!==1)return false;}
  $seen[$id]=$parent;
 }
 if($rootCount!==6)return false;
 foreach($products as $product){$ids=$product['categoryIds']??null;if(!is_array($ids)||!$ids)return false;
  foreach($ids as $id)if(!is_string($id)||!array_key_exists($id,$seen)||($seen[$id]!==null&&!in_array($seen[$id],$ids,true)))return false;
 }
 return true;
}
function sexogateNativeManifestValid(array $manifest,string $release,int $archiveFiles):bool{
 if(($manifest['schema']??null)!==1||!preg_match('/^[a-f0-9]{24}$/D',$release)||($manifest['release']??null)!==$release||($manifest['checkoutEnabled']??null)!==false||($manifest['previewOnly']??null)!==true||($manifest['domain']??null)!=='sexogate.com'||($manifest['mount']??null)!=='/test')return false;
 $count=$manifest['products']??null;$files=$manifest['files']??null;$dataset=$manifest['dataset']??null;
 if(!is_int($count)||$count<0||$count>20000||!is_array($files)||!$files||$archiveFiles<2||$archiveFiles>5000||count($files)+1!==$archiveFiles)return false;
 if($count===0?$dataset!==null:(!is_string($dataset)||preg_match('/^[a-f0-9]{32}$/D',$dataset)!==1))return false;
 foreach($files as $name=>$hash)if(!is_string($name)||!preg_match('~^(?:public|private|deploy)/[A-Za-z0-9_./-]+$~D',$name)||str_contains($name,'..')||in_array('.',explode('/',$name),true)||str_contains($name,'//')||!is_string($hash)||preg_match('/^[a-f0-9]{64}$/D',$hash)!==1)return false;
 ksort($files,SORT_STRING);$payload='';foreach($files as $name=>$hash)$payload.=$name."\0".$hash."\0";
 $fingerprint=hash('sha256',$payload);
 return is_string($manifest['fingerprint']??null)&&hash_equals($fingerprint,$manifest['fingerprint'])&&substr($fingerprint,0,24)===$release;
}
function sexogateNativeCatalogValid(array $catalog,array $manifest):bool{
 try{
  $products=$catalog['products']??null;$categories=$catalog['categories']??null;$count=$manifest['products']??null;
  if(!is_int($count)||$count<0||$count>20000||($catalog['brand']['name']??null)!=='SEXOGATE'||!is_array($products)||!array_is_list($products)||count($products)!==$count||!is_array($categories)||!array_is_list($categories))return false;
  if($count===0)return $categories===[];
  $origin=$catalog['catalogOrigin']??null;
  if(!in_array($origin,['sexogate-suppliers-v1','sexogate-catalog-v2'],true)||($origin==='sexogate-suppliers-v1'&&$count!==2194)||($catalog['dataset']??null)!==($manifest['dataset']??null)||!is_string($manifest['dataset']??null)||preg_match('/^[a-f0-9]{32}$/D',$manifest['dataset'])!==1||!sexogateNativeCategoryTree($categories,$products))return false;
  $ids=[];$skus=[];
  foreach($products as $product){
   if(!is_array($product)||!is_string($product['id']??null)||!is_string($product['code']??null)||$product['code']===''||!sexogateNativeProductProvenance($product,$origin)||isset($ids[$product['id']])||isset($skus[$product['code']])||($product['published']??null)!==false||($product['hidden']??null)!==true||($product['stockKnown']??null)!==false||!array_key_exists('stockQuantity',$product)||$product['stockQuantity']!==null)return false;
   $ids[$product['id']]=true;$skus[$product['code']]=true;
  }
  return true;
 }catch(Throwable $error){return false;}
}
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
 // Yalnız kimliği doğrulanmış bakım isteği; kilitli SDK dosyaları da tek tek hash ile denetlenir.
 if(function_exists('set_time_limit'))set_time_limit(90);
 $real=realpath($home);if($real===false||str_starts_with($real.'/',rtrim($doc,'/').'/'))throw new RuntimeException('private_inside_webroot');
 foreach(['releases','state']as $name){if(is_link($home.'/'.$name))throw new RuntimeException('private_symlink');if(!is_dir($home.'/'.$name)&&!mkdir($home.'/'.$name,0700))throw new RuntimeException('private_create_failed');}
 $archive=__DIR__.'/app/native-payload-'.$id.'.zip';if(!hash_equals($request['sha256'],hash_file('sha256',$archive)))throw new RuntimeException('archive_hash_mismatch');
 $zip=new ZipArchive();if($zip->open($archive)!==true||$zip->numFiles>5000)throw new RuntimeException('archive_unavailable');
 $manifest=json_decode($zip->getFromName('deployment-manifest.json'),true,512,JSON_THROW_ON_ERROR);if(!is_array($manifest)||!sexogateNativeManifestValid($manifest,$id,$zip->numFiles))throw new RuntimeException('manifest_invalid');
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
 if(!is_array($catalog)||!sexogateNativeCatalogValid($catalog,$manifest))throw new RuntimeException('catalog_provenance_invalid');
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
