<?php
declare(strict_types=1);
if(PHP_SAPI!=='cli')exit(1);
ini_set('display_errors','0');umask(0077);
$lock=fopen(__DIR__.'/paint-price-watch.lock','c');if(!$lock||!flock($lock,LOCK_EX|LOCK_NB))exit(0);
try{
 $runtime=require '/home/nodenoho/nodeno-runtime.php';$private=$runtime['privateRoot'];$storage=$runtime['storageRoot'];require_once $private.'/control-http.php';
 $result=nodenoPaintWatchTick(nodenoControlDatabase($storage),nodenoSupplierSeed());
 $result['releaseHash']=json_decode(file_get_contents($private.'/release.json'),true)['releaseHash'];$result['at']=time();$tmp=__DIR__.'/paint-price-watch-heartbeat.tmp';file_put_contents($tmp,json_encode($result,JSON_THROW_ON_ERROR),LOCK_EX);rename($tmp,__DIR__.'/paint-price-watch-heartbeat.json');
}catch(Throwable $e){file_put_contents(__DIR__.'/paint-price-watch-heartbeat.json',json_encode(['at'=>time(),'status'=>'failed','reason'=>'worker_failed']),LOCK_EX);exit(1);}
