<?php
declare(strict_types=1);
// Install outside public_html in /home/nodenoho/nodeno-blog; invoke with PHP CLI.
if(PHP_SAPI!=='cli')exit(1);
ini_set('display_errors','0');ini_set('log_errors','0');ini_set('zend.exception_ignore_args','1');
$home=dirname(__DIR__);$heartbeat=__DIR__.'/heartbeat.json';
try{
 $runtimeFile=$home.'/nodeno-runtime.php';if(is_link($runtimeFile)||!is_file($runtimeFile))throw new RuntimeException('runtime_unavailable');
 $runtime=require $runtimeFile;$private=$runtime['privateRoot']??'';$storage=$runtime['storageRoot']??'';$public=$home.'/public_html';
 foreach([$private,$storage] as $path)if(!is_string($path)||str_contains($path,'..')||!str_starts_with($path,$home.'/')||str_starts_with($path,$public.'/')||is_link($path))throw new RuntimeException('runtime_unsafe');
 if(!str_starts_with($private,$home.'/nodeno-releases/'))throw new RuntimeException('release_root_invalid');
 $source=$private.'/blog-worker.php';if(!is_file($source))throw new RuntimeException('blog_release_unavailable');
 require_once $source;$result=nodenoBlogTick($storage,$private,$public);
 $manifest=json_decode(file_get_contents($private.'/release.json'),true,64,JSON_THROW_ON_ERROR);
 $record=['checkedAt'=>time(),'releaseHash'=>$manifest['releaseHash']??null,'result'=>$result,'dependsOnLocalComputer'=>false,'paidRequests'=>0];
 $temporary=$heartbeat.'.'.bin2hex(random_bytes(6)).'.tmp';if(file_put_contents($temporary,json_encode($record,JSON_THROW_ON_ERROR),LOCK_EX)===false)throw new RuntimeException('heartbeat_write_failed');chmod($temporary,0600);if(!rename($temporary,$heartbeat))throw new RuntimeException('heartbeat_write_failed');
}catch(Throwable $e){
 $code=preg_match('/^[a-z_]+$/D',$e->getMessage())?$e->getMessage():'runner_action_failed';
 file_put_contents($heartbeat,json_encode(['checkedAt'=>time(),'status'=>'failed','reason'=>$code]),LOCK_EX);chmod($heartbeat,0600);exit(1);
}
