<?php
declare(strict_types=1);
if(PHP_SAPI!=='cli'||getenv('NODENO_STRIPE_SANDBOX_QA')!=='isolated-only')exit(2);
require getenv('NODENO_STRIPE_SANDBOX_CODE_ROOT').'/hosting/payments.php';
$root=$argv[1]??'';$input=json_decode(file_get_contents($argv[2]??''),true,16,JSON_THROW_ON_ERROR);
if(($input['mode']??'')!=='test'||!nodenoPaymentSecretKeyValid($input['secretKey']??null,'test'))exit(3);
$db=nodenoControlDatabase($root);nodenoPaymentSchema($db);
if((int)$db->query('SELECT COUNT(*) FROM payment_orders')->fetchColumn()!==0)exit(4);
$languages=['tr','en','ru','ar'];$seller=['name'=>'NODENO QA seller — TEST ONLY','address'=>'Sandbox address, no goods dispatched','email'=>'qa@example.test','termsVersion'=>'sandbox-qa-1','terms'=>array_fill_keys($languages,'Isolated test conditions. No real purchase or delivery.'),'returns'=>array_fill_keys($languages,'Isolated refund test. No real funds move.'),'taxConfirmed'=>true,'authorityConfirmed'=>true];
// The anonymous test account ID is attested by the official CLI provisioning result.
// Its restricted key cannot read /v1/account; production account verification is not bypassed.
nodenoControlSetSetting($db,'payment:stripe',['version'=>1,'enabled'=>true,'mode'=>'test','accountId'=>$input['accountId'],'seller'=>$seller,'verifiedAt'=>time(),'webhookVerifiedAt'=>null,'credentials'=>nodenoControlEncrypt($root,json_encode(['secretKey'=>$input['secretKey'],'webhookSecret'=>$input['webhookSecret']],JSON_THROW_ON_ERROR),'stripe-credentials')]);
echo json_encode(['seeded'=>true,'mode'=>'test','orders'=>0]);
