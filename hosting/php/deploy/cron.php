<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/deploy/cron.php
 * Açıklama   : Sabit özel test uygulamasının PHP CLI cron girişidir.
 */
declare(strict_types=1);
if(PHP_SAPI!=='cli'){http_response_code(404);exit;}
ini_set('display_errors','0');$app=__DIR__;$lock=fopen($app.'/cron.lock','c');if(!$lock||!flock($lock,LOCK_EX|LOCK_NB))exit;
try{$id=require $app.'/active.php';if(!is_string($id)||!preg_match('/\A[a-f0-9]{24}\z/',$id))throw new RuntimeException('INVALID_RELEASE');require $app.'/releases/'.$id.'/vendor/autoload.php';$config=Sexogate\Config::load($app.'/config.local.json');$db=new Sexogate\Database($config);if($config->get('payment_provider')==='stripe')(new Sexogate\Commerce($db,$config))->enqueue('stripe.reconcile',[],'stripe-reconcile:'.gmdate('YmdHi'));$result=(new Sexogate\Worker($db,$config))->tick();file_put_contents($app.'/worker-health.json',json_encode(['checkedAt'=>gmdate('c'),'runtime'=>PHP_VERSION,'ok'=>true,'result'=>$result]));}
catch(Throwable $e){file_put_contents($app.'/worker-health.json',json_encode(['checkedAt'=>gmdate('c'),'runtime'=>PHP_VERSION,'ok'=>false,'error'=>get_class($e)]));exit(1);}
finally{flock($lock,LOCK_UN);fclose($lock);}
