<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/seed-native-returns-local.php
 * Açıklama   : Yalnız izole loopback kabul alanında gerçek API testleri için özel siparişler oluşturur.
 */
declare(strict_types=1);
if(PHP_SAPI!=='cli')exit(1);
$repo=dirname(__DIR__);$local=json_decode(file_get_contents($repo.'/.local/native-stage-local.json'),true);
if($local['url']!=='https://127.0.0.1:3188/test'||!str_contains(str_replace('\\','/',$local['home']),'/private-installs/native-mount-local-'))throw new RuntimeException('LOCAL_FIXTURE_SCOPE');
$private=$local['home'].'/releases/'.$local['release'].'/private';$state=$local['home'].'/state';require $private.'/control-http.php';require $private.'/payment-store.php';$db=nodenoControlDatabase($state);sgReturnSchema($db);$result=[];
foreach(['chromium','webkit']as $engine){
 $pass=bin2hex(random_bytes(16));$secret=nodenoControlBase32(random_bytes(20));$email='return-'.bin2hex(random_bytes(6)).'@example.invalid';$operator=nodenoControlId('fixture_ops_');$now=time();
 $db->prepare('INSERT INTO control_users(id,email,display_name,role,password_hash,totp_secret,created_at,updated_at)VALUES(?,?,?,?,?,?,?,?)')->execute([$operator,$email,'İzole depo test kullanıcısı','operations',password_hash($pass,PASSWORD_BCRYPT),nodenoControlEncrypt($state,$secret,$operator),$now,$now]);
 $customer=bin2hex(random_bytes(16));$customerMail='customer-'.bin2hex(random_bytes(6)).'@example.invalid';$db->prepare('INSERT INTO users(id,email,name,password_hash,created_at,updated_at)VALUES(?,?,?,?,?,?)')->execute([$customer,$customerMail,'İzole İstanbul test kullanıcısı',password_hash($pass,PASSWORD_BCRYPT),$now,$now]);
 $orders=[];
 foreach(['one','two']as $suffix){
  $quote=['lines'=>[['id'=>'fixture_'.$suffix,'code'=>'seo-LOCAL-ONLY-XL','quantity'=>3,'name'=>['tr'=>'İç Giyim Şişli','en'=>'Şişli Lingerie'],'netMinor'=>10002,'vatMinor'=>2001,'totalMinor'=>12003,'selectionSnapshot'=>['summary'=>'Beden: XL · Renk: Siyah']]],'netMinor'=>10002,'vatMinor'=>2001,'totalMinor'=>12003,'currency'=>'TRY','country'=>'TR'];
  $order=nodenoPaymentBegin($db,$state,'local-http-return-fixture',bin2hex(random_bytes(16)),$quote,['name'=>'İzole test'],'tr',['accountId'=>'acct_local_return_fixture','mode'=>'test','seller'=>['name'=>'İzole test']],$suffix==='one'?$customer:null);
  $db->prepare("UPDATE payment_orders SET status='paid',paid_at=?,payment_intent=?WHERE id=?")->execute([$now,'pi_local_fixture_'.bin2hex(random_bytes(10)),$order['id']]);$orders[$suffix]=['id'=>$order['id'],'token'=>$order['returnToken']];
 }
 $result[$engine]=['orders'=>$orders,'operator'=>['email'=>$email,'password'=>$pass,'totpSecret'=>$secret],'customer'=>['email'=>$customerMail,'password'=>$pass,'id'=>$customer]];
}
file_put_contents($repo.'/.local/returns-local-fixtures.json',sgReturnJson($result));echo '{"localFixturesPrepared":true,"publicCatalogChanged":false,"realPayments":false}';
