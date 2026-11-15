<?php
declare(strict_types=1);
if(PHP_SAPI!=='cli')exit(1);
ini_set('display_errors','0');ini_set('log_errors','0');ini_set('zend.exception_ignore_args','1');
$home=dirname(__DIR__);$heartbeat=__DIR__.'/heartbeat.json';
try{
 $runtimePath=$home.'/nodeno-runtime.php';if(is_link($runtimePath))throw new RuntimeException('search_runtime_unsafe');$runtime=require $runtimePath;$private=$runtime['privateRoot']??'';$storage=$runtime['storageRoot']??'';
 foreach([$private,$storage]as $path)if(!is_string($path)||str_contains($path,'..')||!str_starts_with($path,$home.'/')||str_starts_with($path,$home.'/public_html')||is_link($path))throw new RuntimeException('search_runtime_unsafe');
 if(!str_starts_with($private,$home.'/nodeno-releases/'))throw new RuntimeException('search_runtime_unsafe');
 $bootstrap=json_decode(file_get_contents(__DIR__.'/configuration.json'),true,64,JSON_THROW_ON_ERROR);
 $blog=null;if(is_file($private.'/blog-worker.php')){require_once $private.'/blog-worker.php';$blog=nodenoBlogTick($storage,$private,$home.'/public_html');}
 require_once $private.'/search-notifications.php';
 if(($blog['published']??0)>0){require_once $private.'/control-indexnow.php';$db=nodenoControlDatabase(nodenoAccountStorage($storage));nodenoSearchSchema($db);nodenoSearchSet($db,'scanRequested',true);}
 $result=nodenoSearchTick($storage,$private,$bootstrap,time());$result['blog']=$blog;
}catch(Throwable $e){$result=['status'=>'failed','checkedAt'=>time(),'reason'=>preg_match('/^[a-z_]+$/D',$e->getMessage())?$e->getMessage():'search_worker_failed'];}
$tmp=$heartbeat.'.'.bin2hex(random_bytes(8)).'.tmp';file_put_contents($tmp,json_encode($result,JSON_THROW_ON_ERROR),LOCK_EX);chmod($tmp,0600);rename($tmp,$heartbeat);
exit(($result['status']??'')==='failed'?1:0);
