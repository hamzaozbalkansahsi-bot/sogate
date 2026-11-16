<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/test-native-return-ordering.php
 * Açıklama   : Sağlayıcı gözlem sırası, kalıcı gönderim niyeti ve lease sahipliğini izole SQLite üzerinde sınar.
 */
declare(strict_types=1);
$repo=dirname(__DIR__);
$private=in_array('--source',$argv,true)?$repo.'/native-store/upstream/hosting':json_decode(file_get_contents($repo.'/.local/native-stage-package.json'),true)['bundle'].'/private';
require $private.'/control-indexnow.php';require $private.'/payment-store.php';require $repo.'/native-store/returns/core.php';require $repo.'/native-store/returns/jobs.php';
$state=sys_get_temp_dir().'/sexogate-return-ordering-'.bin2hex(random_bytes(8));mkdir($state,0700);$db=nodenoControlDatabase($state);sgReturnSchema($db);$checks=[];$now=time();
function orderingCheck(bool $valid,string $name):void{global $checks;if(!$valid)throw new RuntimeException('FAILED_'.$name);$checks[]=$name;}
function orderingReject(callable $action,string $code):void{try{$action();}catch(NodenoControlHttpError $e){orderingCheck($e->errorCode===$code,$code);return;}throw new RuntimeException('NOT_REJECTED_'.$code);}
function orderingFixture(PDO $db,string $state,string $name,int $now):array{
 $quote=['lines'=>[['id'=>$name,'code'=>'TEST-ORDERING','quantity'=>1,'name'=>['tr'=>'İzole sıralama kontrolü'],'netMinor'=>1000,'vatMinor'=>200,'totalMinor'=>1200]],'netMinor'=>1000,'vatMinor'=>200,'totalMinor'=>1200,'currency'=>'TRY','country'=>'TR'];
 $order=nodenoPaymentBegin($db,$state,'isolated-ordering-actor','ordering_order_'.$name,$quote,[],'tr',['accountId'=>'acct_ordering_fixture','mode'=>'test','seller'=>['name'=>'İzole test']]);
 $db->prepare("UPDATE payment_orders SET status='paid',paid_at=?,payment_intent=?WHERE id=?")->execute([$now,'pi_ordering_'.$name,$order['id']]);$order=nodenoPaymentOrder($db,$order['id']);$line=array_key_first(sgReturnOrderLines($order));
 $case=sgReturnCreate($db,$state,$order,'isolated-ordering-actor',['key'=>'ordering_return_'.$name,'reason'=>'withdrawal','note'=>'','locale'=>'tr','lines'=>[$line=>1],'sealOpened'=>false],['approved'=>false,'country'=>'TR'],$now);
 foreach([['action'=>'shipping','carrier'=>'TEST','handoffCode'=>'TEST','evidenceRef'=>'fixture-only','expiresAt'=>$now+86400],['action'=>'receive'],['action'=>'inspect','inspectionComplete'=>true,'disposition'=>'quarantine','evidenceRef'=>'fixture-only'],['action'=>'approve']]as $command)$case=sgReturnCommand($db,$case['code'],'isolated-operator',['version'=>(int)$case['version']]+$command,$now);
 $db->prepare("UPDATE sg_return_jobs SET status='blocked',next_at=?WHERE case_code=?AND kind='fiscal'")->execute([$now+864000,$case['code']]);
 $q=$db->prepare("SELECT * FROM sg_return_jobs WHERE case_code=?AND kind='refund'");$q->execute([$case['code']]);return ['order'=>$order,'case'=>$case,'job'=>$q->fetch()];
}
function orderingResult(array $fixture,string $status,int $created):array{
 $order=$fixture['order'];$job=$fixture['job'];$suffix=substr(hash('sha256',$job['id']),0,16);
 return ['accountId'=>$order['stripe_account_id'],'live'=>false,'refund'=>['id'=>'re_ordering_'.$suffix,'object'=>'refund','charge'=>'ch_ordering_'.$suffix,'payment_intent'=>$order['payment_intent'],'currency'=>strtolower($order['currency']),'amount'=>(int)$job['amount_minor'],'status'=>$status,'created'=>$created,'metadata'=>['sexogate_return'=>$job['case_code'],'sexogate_order'=>$order['id']]]];
}
function orderingDigest(PDO $db):string{$data=[];foreach(['sg_return_cases','sg_return_jobs','sg_return_events','sg_return_journal','payment_refund_items','payment_events']as $table)$data[$table]=$db->query('SELECT * FROM '.$table.' ORDER BY rowid')->fetchAll();return hash('sha256',sgReturnJson($data));}
$fixture=orderingFixture($db,$state,'webhook',$now);$pending=orderingResult($fixture,'pending',$now-7200);
nodenoPaymentApply($db,['id'=>'evt_ordering_pending','created'=>$now-60,'type'=>'refund.updated','account'=>$pending['accountId'],'livemode'=>false,'data'=>['object'=>$pending['refund']]]);
orderingCheck((int)nodenoPaymentOrder($db,$fixture['order']['id'])['refund_pending_minor']===1200,'newer_pending_webhook_recorded');
$db->prepare("UPDATE sg_return_jobs SET status='running',lease_token='current-owner',lease_until=?WHERE id=?")->execute([$now+120,$fixture['job']['id']]);
$success=orderingResult($fixture,'succeeded',$now-7200);$applied=sgReturnApplyProviderResult($db,$fixture['job']['id'],$success,$now,'current-owner');
orderingCheck($applied['status']==='succeeded'&&(int)nodenoPaymentOrder($db,$fixture['order']['id'])['refunded_minor']===1200,'api_observation_follows_newer_pending_webhook');
$replay=sgReturnApplyProviderResult($db,$fixture['job']['id'],$pending,$now+1);
orderingCheck($replay['duplicate']===true&&$replay['status']==='succeeded','late_api_pending_keeps_success');
nodenoPaymentApply($db,['id'=>'evt_ordering_late_pending','created'=>$now+2,'type'=>'refund.updated','account'=>$pending['accountId'],'livemode'=>false,'data'=>['object'=>$pending['refund']]]);
orderingCheck((int)nodenoPaymentOrder($db,$fixture['order']['id'])['refunded_minor']===1200&&(int)$db->query("SELECT COUNT(*)FROM sg_return_journal WHERE kind='refund_payment'")->fetchColumn()===1,'late_pending_keeps_one_cash_post');
$lease=orderingFixture($db,$state,'lease',$now);$leaseResult=orderingResult($lease,'succeeded',$now-7200);
$db->prepare("UPDATE sg_return_jobs SET status='running',lease_token='new-owner',lease_until=?WHERE id=?")->execute([$now+120,$lease['job']['id']]);$before=orderingDigest($db);
orderingReject(fn()=>sgReturnApplyProviderResult($db,$lease['job']['id'],$leaseResult,$now,'old-owner'),'refund_lease_lost');orderingCheck(orderingDigest($db)===$before,'stolen_lease_has_no_mutation');
$db->prepare('UPDATE sg_return_jobs SET lease_until=?WHERE id=?')->execute([$now,$lease['job']['id']]);$before=orderingDigest($db);
orderingReject(fn()=>sgReturnApplyProviderResult($db,$lease['job']['id'],$leaseResult,$now,'new-owner'),'refund_lease_lost');orderingCheck(orderingDigest($db)===$before,'expired_lease_has_no_mutation');
$db->prepare("UPDATE sg_return_jobs SET status='blocked',next_at=?WHERE id=?")->execute([$now+864000,$lease['job']['id']]);
final class OrderingProvider implements SgReturnPaymentProvider{
 public int $calls=0;public bool $intentBeforeCall=false;public array $callsByCase=[];
 public function __construct(private PDO $db){}
 public function refund(array $order,array $job):array{
  $this->calls++;$this->callsByCase[]=$job['case_code'];$q=$this->db->prepare('SELECT request_json FROM sg_return_jobs WHERE id=?');$q->execute([$job['id']]);$request=json_decode($q->fetchColumn(),true);$this->intentBeforeCall=is_int($request['firstDispatchAt']??null);
  sgReturnError(503,'refund_provider_unavailable');
 }
}
$dispatch=orderingFixture($db,$state,'dispatch',$now);$provider=new OrderingProvider($db);$first=sgReturnRunJobs($db,$provider,$now,1);
orderingCheck($first['failed']===1&&$provider->calls===1&&$provider->intentBeforeCall,'first_dispatch_intent_committed_before_provider_call');
$q=$db->prepare('SELECT request_json FROM sg_return_jobs WHERE id=?');$q->execute([$dispatch['job']['id']]);$intent=json_decode($q->fetchColumn(),true);orderingCheck($intent['firstDispatchAt']===$now,'logical_clock_preserved_for_fast_run');
sgReturnRunJobs($db,$provider,$now+3600,1);$q->execute([$dispatch['job']['id']]);orderingCheck($provider->calls===2&&json_decode($q->fetchColumn(),true)['firstDispatchAt']===$now,'retry_preserves_first_dispatch_time');
$blocked=sgReturnRunJobs($db,$provider,$now+72000,1);$q=$db->prepare('SELECT status,error_code FROM sg_return_jobs WHERE id=?');$q->execute([$dispatch['job']['id']]);$job=$q->fetch();
orderingCheck($blocked['blocked']===1&&$provider->calls===2&&$job['status']==='blocked'&&$job['error_code']==='refund_dispatch_reconciliation_required','unknown_dispatch_after_twenty_hours_does_not_create_again');
$known=orderingFixture($db,$state,'known',$now);$knownResult=orderingResult($known,'pending',$now-7200);$knownRequest=json_decode($known['job']['request_json'],true);$knownRequest['firstDispatchAt']=$now-90000;
$db->prepare('UPDATE sg_return_jobs SET provider_ref=?,request_json=?WHERE id=?')->execute([$knownResult['refund']['id'],sgReturnJson($knownRequest),$known['job']['id']]);$beforeCalls=$provider->calls;sgReturnRunJobs($db,$provider,$now,1);
orderingCheck($provider->calls===$beforeCalls+1&&end($provider->callsByCase)===$known['case']['code'],'known_reference_can_be_polled_after_dispatch_window');
$null=orderingFixture($db,$state,'nullprovider',$now);$nullRun=sgReturnRunJobs($db,null,$now,1);$q=$db->prepare('SELECT request_json FROM sg_return_jobs WHERE id=?');$q->execute([$null['job']['id']]);orderingCheck($nullRun['blocked']===1&&!array_key_exists('firstDispatchAt',json_decode($q->fetchColumn(),true)),'null_provider_never_records_dispatch_intent');
$slowOne=orderingFixture($db,$state,'slowone',$now);$slowTwo=orderingFixture($db,$state,'slowtwo',$now);
$slowProvider=new class($db,$now) implements SgReturnPaymentProvider{
 public array $claims=[];
 public function __construct(private PDO $db,private int $now){}
 public function refund(array $order,array $job):array{
  $q=$this->db->prepare('SELECT lease_until,updated_at FROM sg_return_jobs WHERE id=?');$q->execute([$job['id']]);$this->claims[]=$q->fetch();if(count($this->claims)===1)usleep(1100000);
  return orderingResult(['order'=>$order,'job'=>$job],'succeeded',$this->now-7200);
 }
};
$slowRun=sgReturnRunJobs($db,$slowProvider,$now,2);orderingCheck($slowRun['succeeded']===2&&(int)$slowProvider->claims[0]['lease_until']===$now+120&&(int)$slowProvider->claims[1]['lease_until']>=$now+121,'each_batch_claim_refreshes_elapsed_time');
$q=$db->prepare('SELECT updated_at,next_at FROM sg_return_jobs WHERE id=?');$q->execute([$slowOne['job']['id']]);$slowApplied=$q->fetch();orderingCheck((int)$slowApplied['updated_at']>=$now+1&&(int)$slowApplied['next_at']>=$now+61,'provider_result_uses_elapsed_observation_time');
orderingCheck(!$db->query('PRAGMA foreign_key_check')->fetchAll(),'foreign_keys_valid');
echo sgReturnJson(['passed'=>count($checks),'checks'=>$checks,'testSha256'=>hash_file('sha256',__FILE__),'isolatedDatabase'=>true,'realPaymentOrFiscalApiCalled'=>false]);
