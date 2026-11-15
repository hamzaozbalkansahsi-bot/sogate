<?php
declare(strict_types=1);
if(PHP_SAPI!=='cli-server'||!in_array($_SERVER['REMOTE_ADDR']??'',['127.0.0.1','::1'],true)||getenv('NODENO_PAYMENT_TEST')!=='isolated-only'){http_response_code(404);exit;}
ini_set('display_errors','0');
set_error_handler(static function(int $severity,string $message,string $file,int $line):bool{if(!(error_reporting()&$severity))return false;throw new ErrorException($message,0,$severity,$file,$line);});
function nodenoRespond(string $body,int $status=200,string $type='application/json; charset=utf-8',array $headers=[]):void{http_response_code($status);header('Content-Type: '.$type);foreach($headers as $key=>$value)header($key.': '.$value);echo $body;}
require dirname(__DIR__,2).'/hosting/payments.php';
$catalog=['products'=>[['id'=>'p1','code'=>'FIXTURE','currency'=>'TRY','salePriceMinor'=>10001,'name'=>['tr'=>'Test dolap']]],'meta'=>[]];
nodenoPaymentsHandle(parse_url($_SERVER['REQUEST_URI'],PHP_URL_PATH),$_SERVER['REQUEST_METHOD'],$catalog,getenv('NODENO_PAYMENT_TEST_ROOT'),static fn()=>json_decode(file_get_contents(getenv('NODENO_PAYMENT_TEST_ROOT').'/fixture-provider-event.json'),true,64,JSON_THROW_ON_ERROR));
