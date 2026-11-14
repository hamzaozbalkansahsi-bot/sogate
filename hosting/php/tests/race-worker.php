<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/race-worker.php
 * Açıklama   : Yalnız yerel kabul testinde ayrı PHP sürecinden aynı stok/ödeme yarışını yürütür.
 */
declare(strict_types=1);
if(PHP_SAPI!=='cli')exit(1);
require dirname(__DIR__).'/vendor/autoload.php';
$v=json_decode(getenv('SEXOGATE_RACE')?:'',true,64,JSON_THROW_ON_ERROR);
if(!str_starts_with($v['config']['db_dsn'],'mysql:host=127.0.0.1;port=55433;dbname=sexogate_php_')||!str_ends_with(explode(';charset',$v['config']['db_dsn'])[0],'_test'))exit(1);
$until=microtime(true)+10;while(!is_file($v['barrier'])&&microtime(true)<$until)usleep(1000);
try{$c=new Sexogate\Commerce(new Sexogate\Database(new Sexogate\Config($v['config'])),new Sexogate\Config($v['config']));$r=$v['mode']==='checkout'?$c->checkout($v['token'],$v['input']):$c->handleTest($v['raw'],$v['signature']);echo json_encode(['ok'=>true,'duplicate'=>$r['duplicate']??null]);}
catch(Sexogate\RuleViolation $e){echo json_encode(['ok'=>false,'code'=>$e->rule]);}
catch(Throwable $e){echo json_encode(['ok'=>false,'code'=>'UNEXPECTED_'.get_class($e),'location'=>basename($e->getFile()).':'.$e->getLine(),'errno'=>$e instanceof PDOException?($e->errorInfo[1]??0):0]);exit(1);}
