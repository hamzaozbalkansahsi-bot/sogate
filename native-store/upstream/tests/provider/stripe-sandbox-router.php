<?php
declare(strict_types=1);
if(PHP_SAPI!=='cli-server'||getenv('NODENO_STRIPE_SANDBOX_QA')!=='isolated-only'||!in_array($_SERVER['REMOTE_ADDR']??'',['127.0.0.1','::1'],true)){http_response_code(404);exit;}
ini_set('display_errors','0');
require getenv('NODENO_STRIPE_SANDBOX_CODE_ROOT').'/hosting/payments.php';
function nodenoRespond(string $body,int $status=200,string $type='application/json; charset=utf-8',array $headers=[]):void{http_response_code($status);header('Content-Type: '.$type);foreach($headers as $key=>$value)header($key.': '.$value);echo $body;}
$path=parse_url($_SERVER['REQUEST_URI'],PHP_URL_PATH);
if($path==='/payments.js'){nodenoRespond(file_get_contents(getenv('NODENO_STRIPE_SANDBOX_CODE_ROOT').'/web/payments.js'),200,'application/javascript; charset=utf-8');exit;}
if($path==='/styles.css'){nodenoRespond(file_get_contents(getenv('NODENO_STRIPE_SANDBOX_CODE_ROOT').'/web/styles.css'),200,'text/css; charset=utf-8');exit;}
if(preg_match('~^/assets/fonts/(NODENOSans-(?:Regular|Bold)\.woff)$~D',$path,$font)){nodenoRespond(file_get_contents(dirname(__DIR__,2).'/web/assets/fonts/'.$font[1]),200,'font/woff');exit;}
if($path==='/receipt'){
 nodenoRespond(<<<'HTML'
<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="/styles.css"><title>NODENO sandbox receipt</title></head><body><main class="wrap payment-result" data-payment-result></main><script type="module">
import {createPayments} from '/payments.js';const lang=new URLSearchParams(location.search).get('lang')||'en';document.documentElement.lang=lang;document.documentElement.dir=lang==='ar'?'rtl':'ltr';const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));createPayments({state:()=>({locale:lang,items:[],page:'checkout'}),esc,href:()=>'/'}).mount();
</script></body></html>
HTML,200,'text/html; charset=utf-8');exit;
}
if(!str_starts_with($path,'/api/payments/')){http_response_code(404);exit;}
$catalog=['products'=>[['id'=>'sandbox-dolap','code'=>'TEST-ONLY','currency'=>'TRY','salePriceMinor'=>10001,'name'=>['tr'=>'NODENO test dolap','en'=>'NODENO sandbox cabinet']]],'meta'=>['testOnly'=>true]];
nodenoPaymentsHandle($path,$_SERVER['REQUEST_METHOD'],$catalog,getenv('NODENO_STRIPE_SANDBOX_ROOT'));
exit;
