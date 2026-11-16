<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/returns/jobs.php
 * Açıklama   : İade ödeme işlerini kalıcı kuyruk, sağlayıcı teyidi ve mükerrerlik korumasıyla yürütür.
 */
declare(strict_types=1);
interface SgReturnPaymentProvider{public function refund(array $order,array $job):array;}
final class SgReturnStripeProvider implements SgReturnPaymentProvider{
 private \Stripe\StripeClient $client;private string $account;
 public function __construct(array $configuration,array $acceptance,bool $runtimeApproved){
  if(!$runtimeApproved||($configuration['mode']??'')!=='live'||!nodenoPaymentReady($configuration)||($acceptance['approved']??false)!==true||($acceptance['accountId']??'')!==($configuration['accountId']??'')||empty($acceptance['evidenceRef']))sgReturnError(409,'refund_live_acceptance_required');
  require_once __DIR__.'/returns-vendor/autoload.php';$this->client=new \Stripe\StripeClient(['api_key'=>$configuration['credentials']['secretKey'],'stripe_version'=>'2026-10-28.endive']);$this->account=$configuration['accountId'];
 }
 public function refund(array $order,array $job):array{
  if((int)$order['live']!==1||$order['stripe_account_id']!==$this->account)sgReturnError(409,'refund_provider_account_mismatch');
  try{
   $account=$this->client->accounts->retrieve();if($account->id!==$this->account)sgReturnError(409,'refund_provider_account_mismatch');
   $object=$job['provider_ref']?$this->client->refunds->retrieve($job['provider_ref'],[]):$this->client->refunds->create(['payment_intent'=>$order['payment_intent'],'amount'=>(int)$job['amount_minor'],'metadata'=>['sexogate_return'=>$job['case_code'],'sexogate_order'=>$order['id']]],['idempotency_key'=>$job['id']]);
   return ['accountId'=>$this->account,'live'=>true,'refund'=>$object->toArray()];
  }catch(\Stripe\Exception\ApiErrorException $e){sgReturnError(503,'refund_provider_unavailable');}
 }
}
function sgReturnApplyProviderResult(PDO $db,string $jobId,array $result,int $now):array{
 return nodenoControlTransaction($db,static function()use($db,$jobId,$result,$now):array{
  $q=$db->prepare('SELECT * FROM sg_return_jobs WHERE id=?');$q->execute([$jobId]);$job=$q->fetch();if(!$job||$job['kind']!=='refund')sgReturnError(404,'refund_job_unknown');$c=sgReturnCase($db,$job['case_code']);$order=nodenoPaymentOrder($db,$c['order_id']);$r=$result['refund']??[];
  if(($result['accountId']??'')!==$order['stripe_account_id']||($result['live']??null)!==(bool)$order['live']||($r['object']??'')!=='refund'||!preg_match('/^re_[A-Za-z0-9_]+$/D',$r['id']??'')||($r['payment_intent']??'')!==$order['payment_intent']||!preg_match('/^ch_[A-Za-z0-9_]+$/D',$r['charge']??'')||($r['amount']??null)!==(int)$job['amount_minor']||strtoupper($r['currency']??'')!==$job['currency']||($r['metadata']['sexogate_return']??'')!==$c['code']||($r['metadata']['sexogate_order']??'')!==$order['id']||!in_array($r['status']??'',['pending','requires_action','succeeded','failed','canceled'],true))sgReturnError(409,'refund_provider_result_mismatch');
  if($job['provider_ref']!==null&&$job['provider_ref']!==$r['id'])sgReturnError(409,'refund_provider_reference_changed');
  if($job['status']==='succeeded')return ['duplicate'=>true,'status'=>'succeeded'];
  $event=['id'=>'evt_sg_api_'.hash('sha256',$r['id'].':'.$r['status']),'created'=>(int)($r['created']??$now),'type'=>'refund.updated','account'=>$result['accountId'],'livemode'=>$result['live'],'data'=>['object'=>$r]];
  nodenoPaymentApply($db,$event);$q=$db->prepare('SELECT * FROM payment_refund_items WHERE id=?');$q->execute([$r['id']]);$verified=$q->fetch();if(!$verified||$verified['status']!==$r['status'])sgReturnError(409,'refund_native_reconciliation_required');
  $status=match($r['status']){'succeeded'=>'succeeded','failed','canceled'=>'failed',default=>'pending'};
  if($status==='succeeded')sgReturnPost($db,'return-cash-'.$c['code'],$c['code'],$order['id'],$c['currency'],'refund_payment',[['account'=>'refunds_payable','debit'=>(int)$job['amount_minor']],['account'=>'cash','credit'=>(int)$job['amount_minor']]],$r['id'],$now);
  $db->prepare('UPDATE sg_return_jobs SET provider_ref=?,status=?,lease_token=NULL,lease_until=0,next_at=?,updated_at=?,error_code=?WHERE id=?')->execute([$r['id'],$status,$now+60,$now,$status==='failed'?'refund_provider_failed':null,$jobId]);
  $db->prepare("UPDATE sg_return_cases SET refund_state=?,status=CASE WHEN ?='succeeded'AND fiscal_state='confirmed' THEN 'closed' ELSE status END,version=version+1,updated_at=?WHERE code=?")->execute([$status,$status,$now,$c['code']]);sgReturnEvent($db,$c['code'],'refund_'.$status,'provider-api',['reference'=>$r['id'],'providerVerified'=>true],$now);return ['status'=>$status,'duplicate'=>false];
 });
}
function sgReturnRunJobs(PDO $db,?SgReturnPaymentProvider $provider,int $now,int $limit=10):array{
 $counts=['processed'=>0,'blocked'=>0,'failed'=>0,'pending'=>0,'succeeded'=>0];
 for($i=0;$i<max(0,min(50,$limit));$i++){
  $job=nodenoControlTransaction($db,static function()use($db,$now):?array{
   $q=$db->prepare("SELECT * FROM sg_return_jobs WHERE status IN('queued','retry','pending','blocked','running')AND next_at<=?AND lease_until<=?ORDER BY created_at,id LIMIT 1");$q->execute([$now,$now]);$j=$q->fetch();if(!$j)return null;$j['lease_token']=bin2hex(random_bytes(16));$db->prepare("UPDATE sg_return_jobs SET status='running',lease_token=?,lease_until=?,attempts=attempts+1,updated_at=?WHERE id=?")->execute([$j['lease_token'],$now+120,$now,$j['id']]);return $j;
  });if(!$job)break;$counts['processed']++;
  try{
   if($job['kind']==='fiscal')sgReturnError(409,'fiscal_provider_confirmation_required');if($provider===null)sgReturnError(409,'refund_provider_not_approved');$c=sgReturnCase($db,$job['case_code']);$order=nodenoPaymentOrder($db,$c['order_id']);$result=$provider->refund($order,$job);
   $q=$db->prepare("SELECT COUNT(*)FROM sg_return_jobs WHERE id=?AND lease_token=?AND status='running'");$q->execute([$job['id'],$job['lease_token']]);if(!(int)$q->fetchColumn())continue;
   $out=sgReturnApplyProviderResult($db,$job['id'],$result,$now);$counts[$out['status']]++;
  }catch(Throwable $error){
   $code=$error instanceof NodenoControlHttpError?$error->errorCode:'refund_worker_unavailable';$blocked=in_array($code,['fiscal_provider_confirmation_required','refund_provider_not_approved','refund_live_acceptance_required'],true);$state=$blocked?'blocked':'retry';$delay=$blocked?3600:min(3600,30*(2**min(7,(int)$job['attempts'])));
   nodenoControlTransaction($db,static function()use($db,$job,$state,$code,$now,$delay):void{$q=$db->prepare("UPDATE sg_return_jobs SET status=?,error_code=?,next_at=?,lease_until=0,lease_token=NULL,updated_at=?WHERE id=?AND lease_token=?AND status='running'");$q->execute([$state,$code,$now+$delay,$now,$job['id'],$job['lease_token']]);if($q->rowCount()&&$job['kind']==='refund')$db->prepare('UPDATE sg_return_cases SET refund_state=?WHERE code=?')->execute([$state==='blocked'?'blocked':'pending',$job['case_code']]);});$counts[$blocked?'blocked':'failed']++;
  }
 }
 return $counts;
}
function sgReturnFinancialReport(PDO $db,bool $live=true):array{
 $rows=[];$q=$db->prepare('SELECT * FROM payment_orders WHERE live=?AND paid_at IS NOT NULL');$q->execute([(int)$live]);
 foreach($q->fetchAll()as $order){$currency=$order['currency'];$rows[$currency]??=['currency'=>$currency,'paidGrossMinor'=>0,'paidNetMinor'=>0,'salesReturnsNetMinor'=>0,'refundCashMinor'=>0,'vatPendingMinor'=>0,'vatCorrectedMinor'=>0,'actualExpensesMinor'=>0,'costRecoveryMinor'=>0,'unallocatedProviderRefundMinor'=>0,'orders'=>0];$row=&$rows[$currency];$snapshot=json_decode($order['snapshot_json'],true);$row['paidGrossMinor']+=(int)$order['total_minor'];$row['paidNetMinor']+=(int)($snapshot['netMinor']??0);$row['orders']++;
  $journals=$db->prepare('SELECT kind,entries_json FROM sg_return_journal WHERE order_id=?');$journals->execute([$order['id']]);$mapped=0;
  foreach($journals->fetchAll()as $j)foreach(json_decode($j['entries_json'],true)as $e){$d=$e['debit'];$c=$e['credit'];switch($e['account']){case'sales_returns':$row['salesReturnsNetMinor']+=$d-$c;break;case'cash':if($j['kind']==='refund_payment'){$row['refundCashMinor']+=$c;$mapped+=$c;}else $row['actualExpensesMinor']+=$c;break;case'vat_pending_correction':$row['vatPendingMinor']+=$d-$c;break;case'vat_payable':$row['vatCorrectedMinor']+=$d-$c;break;case'cost_of_sales':$row['costRecoveryMinor']+=$c-$d;break;}}
  $known=nodenoPaymentOrder($db,$order['id']);$row['unallocatedProviderRefundMinor']+=max(0,(int)$known['refunded_minor']-$mapped);unset($row);
 }
 foreach($rows as &$r){$r['netSalesMinor']=$r['paidNetMinor']-$r['salesReturnsNetMinor'];$r['reconciliationRequired']=$r['unallocatedProviderRefundMinor']>0;}$q=$db->query("SELECT status,COUNT(*)AS count FROM sg_return_jobs GROUP BY status");return ['mode'=>$live?'live':'test','currencies'=>array_values($rows),'jobs'=>$q->fetchAll(),'definition'=>'Net satış: tahsil edilmiş siparişlerin vergi hariç bedeli eksi kabul edilmiş iadeler. Nakit iadesi yalnız sağlayıcı teyidiyle. Gerçek giderler silinmez. Resmî defter veya net işletme kârı değildir.'];
}
