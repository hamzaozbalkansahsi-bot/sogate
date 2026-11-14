<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/deploy/install.php
 * Açıklama   : Tek kullanımlık kimlikle sabit test paketini doğrular, kurar ve atomik etkinleştirir.
 */
declare(strict_types=1);
ini_set('display_errors','0');set_time_limit(180);
header('Content-Type: application/json; charset=utf-8');header('Cache-Control: no-store');header('X-Robots-Tag: noindex, nofollow');
$root=PHP_SAPI==='cli'?realpath($argv[1]??''):__DIR__;
$lock=null;
try{
    if(!$root||!is_file($root.'/app/deploy.json'))throw new RuntimeException('INSTALL_NOT_AVAILABLE');
    $deploy=json_decode(file_get_contents($root.'/app/deploy.json'),true,32,JSON_THROW_ON_ERROR);
    $token=PHP_SAPI==='cli'?(getenv('SEXOGATE_DEPLOY_TOKEN')?:''):($_SERVER['HTTP_X_DEPLOY_TOKEN']??'');
    if((PHP_SAPI!=='cli'&&($_SERVER['REQUEST_METHOD']??'')!=='POST')||!is_string($token)||strlen($token)!==64||!hash_equals($deploy['token_hash']??'',hash('sha256',$token))||(int)($deploy['expires']??0)<time())throw new RuntimeException('INSTALL_NOT_AVAILABLE');
    if(!preg_match('/\A[a-f0-9]{24}\z/',$deploy['release']??''))throw new RuntimeException('RELEASE_INVALID');
    $lock=fopen($root.'/app/install.lock','c');if(!$lock||!flock($lock,LOCK_EX|LOCK_NB))throw new RuntimeException('INSTALL_BUSY');
    $id=$deploy['release'];$zipfile=$root.'/app/payload-'.$id.'.zip';if(!is_file($zipfile)||!hash_equals($deploy['sha256'],hash_file('sha256',$zipfile)))throw new RuntimeException('PACKAGE_HASH_INVALID');
    $release=$root.'/app/releases/'.$id;if(is_dir($release))throw new RuntimeException('RELEASE_ALREADY_EXISTS');
    $zip=new ZipArchive();if($zip->open($zipfile)!==true)throw new RuntimeException('PACKAGE_INVALID');$bytes=0;
    for($i=0;$i<$zip->numFiles;$i++){$entry=$zip->statIndex($i);$path=$entry['name'];$opsys=0;$attr=0;$zip->getExternalAttributesIndex($i,$opsys,$attr);$type=($attr>>16)&0170000;
        if(!preg_match('~\A(?:src/|templates/|vendor/|public/|migrations/|bin/|composer\.(?:json|lock)$|manifest\.json$)~',$path)||str_contains($path,'\\')||str_contains($path,"\0")||preg_match('~(?:^|/)\.\.?(/|$)~',$path)||$type===0120000)throw new RuntimeException('PACKAGE_PATH_INVALID');
        $bytes+=(int)$entry['size'];if($bytes>200000000||$zip->numFiles>6000)throw new RuntimeException('PACKAGE_LIMIT');
    }
    if(!mkdir($release,0700,true)||!$zip->extractTo($release))throw new RuntimeException('EXTRACTION_FAILED');$zip->close();
    $manifest=json_decode(file_get_contents($release.'/manifest.json'),true,32,JSON_THROW_ON_ERROR);foreach($manifest as $path=>$hash){if(str_contains($path,'..')||str_contains($path,'\\')||str_starts_with($path,'/')||!hash_equals($hash,hash_file('sha256',$release.'/'.$path)))throw new RuntimeException('MANIFEST_HASH_INVALID');}
    require $release.'/vendor/autoload.php';
    $configFile=$root.'/app/config.local.json';$values=json_decode(file_get_contents($configFile),true,32,JSON_THROW_ON_ERROR);$config=new Sexogate\Config($values);
    if(!$config->local()||$config->get('base_path')!=='/test'||$config->get('payment_provider')!=='test'||$config->flag('live_sales'))throw new RuntimeException('TEST_INSTALL_ONLY');
    $db=new Sexogate\Database($config);if(!str_ends_with($db->one('SELECT DATABASE() name')['name'],'_test'))throw new RuntimeException('TEST_DATABASE_REQUIRED');
    (new Sexogate\Migrations($db))->apply($release.'/migrations');$fixtures=new Sexogate\Fixtures($db,$config);$fixtures->policies();$admin=$db->one("SELECT id FROM `user` WHERE role='admin'");
    if(!$admin){$b=$values['bootstrap_admin']??null;if(!is_array($b))throw new RuntimeException('ADMIN_SETUP_REQUIRED');$idAdmin=(new Sexogate\Auth($db,$config))->setupAdmin($b['name'],$b['email'],$b['password']);$admin=['id'=>$idAdmin];}
    $fixtures->catalog(new Sexogate\Principal($admin['id'],'admin',true));
    $assets=$root.'/assets/releases/'.$id;if(!is_dir($assets)&&!mkdir($assets,0755,true))throw new RuntimeException('ASSET_DIRECTORY_FAILED');
    $iterator=new RecursiveIteratorIterator(new RecursiveDirectoryIterator($release.'/public/assets',FilesystemIterator::SKIP_DOTS));foreach($iterator as $file){$relative=substr($file->getPathname(),strlen($release.'/public/assets/'));$destination=$assets.'/'.$relative;if(!is_dir(dirname($destination)))mkdir(dirname($destination),0755,true);if(!copy($file->getPathname(),$destination))throw new RuntimeException('ASSET_COPY_FAILED');}
    unset($values['bootstrap_admin']);$values['asset_prefix']='/test/assets/releases/'.$id;file_put_contents($configFile.'.new',json_encode($values,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR));chmod($configFile.'.new',0600);if(!rename($configFile.'.new',$configFile))throw new RuntimeException('CONFIG_ACTIVATION_FAILED');
    $active=$root.'/app/active.php';if(is_file($active))copy($active,$root.'/app/previous.php');$code='<?php return '.var_export($id,true).';';file_put_contents($active.'.new',$code);chmod($active.'.new',0600);if(!rename($active.'.new',$active))throw new RuntimeException('ACTIVATION_FAILED');if(function_exists('opcache_invalidate'))opcache_invalidate($active,true);
    $cli=null;foreach(['/opt/alt/php83/usr/bin/php','/opt/cpanel/ea-php83/root/usr/bin/php','/usr/local/bin/php'] as $candidate)if(is_executable($candidate)){$cli=$candidate;break;}
    unlink($root.'/app/deploy.json');unlink($zipfile);echo json_encode(['installed'=>true,'release'=>$id,'runtime'=>PHP_VERSION,'migrations'=>(int)$db->one("SELECT COUNT(*) n FROM schema_migrations WHERE state='applied'")['n'],'realCharges'=>false,'cronPath'=>$root.'/app/cron.php','phpCli'=>$cli]);
}catch(Throwable $e){http_response_code(503);$code=$e instanceof RuntimeException&&preg_match('/\A[A-Z_0-9]+\z/',$e->getMessage())?$e->getMessage():'INSTALL_FAILED';error_log('SEXOGATE_INSTALL '.get_class($e));echo json_encode(['installed'=>false,'code'=>$code]);if(PHP_SAPI==='cli')exit(1);}
finally{if(is_resource($lock)){flock($lock,LOCK_UN);fclose($lock);}}
