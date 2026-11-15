<?php
declare(strict_types=1);
if(PHP_SAPI!=='cli-server'||!in_array($_SERVER['REMOTE_ADDR']??'',['127.0.0.1','::1'],true)||getenv('NODENO_CONTROL_TEST')!=='isolated-only'){http_response_code(404);exit;}
ini_set('display_errors','0');
set_error_handler(static function(int $severity,string $message,string $file,int $line):bool {if(!(error_reporting()&$severity))return false;throw new ErrorException($message,0,$severity,$file,$line);});
function nodenoRespond(string $body,int $status=200,string $type='application/json; charset=utf-8',array $extra=[]):void {http_response_code($status);header('Content-Type: '.$type);foreach($extra as $key=>$value)header($key.': '.$value);if($_SERVER['REQUEST_METHOD']!=='HEAD')echo $body;}
require dirname(__DIR__,2).'/hosting/control-http.php';
$root=getenv('NODENO_CONTROL_TEST_ROOT');$path=parse_url($_SERVER['REQUEST_URI'],PHP_URL_PATH);
$catalog=['products'=>[['id'=>'p1','code'=>'TEST-P1','salePriceMinor'=>10000,'currency'=>'TRY','name'=>['tr'=>'Test ürün'],'categoryIds'=>[]]],'categories'=>[],'meta'=>[]];
if(str_starts_with($path,'/api/account')){nodenoHandleAccountRequest($path,$_SERVER['REQUEST_METHOD'],$catalog,$root);return;}
if(!nodenoControlHandle($path,$_SERVER['REQUEST_METHOD'],$catalog,['checkoutEnabled'=>false],$root))nodenoRespond('{"error":"not_found"}',404);
