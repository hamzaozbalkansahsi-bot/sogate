<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/Payments.php
 * Açıklama   : Ödeme oturumu, kalıcı imzalı inbox, mutabakat ve sağlayıcı iadesi koordinasyonu.
 */
declare(strict_types=1);
namespace Sexogate;
use Sexogate\Providers\{PaymentProvider,StripeProvider};
final class Payments
{
    public function __construct(private Database $db,private Config $config){}
    private function provider():PaymentProvider{return new StripeProvider($this->config);}
    public function start(string $id,?string $tracking,?string $user):array
    {
        $provider=$this->provider();$order=(new Commerce($this->db,$this->config))->order($id,$tracking,$user);RuleViolation::ensure($order,'ORDER_NOT_FOUND','Sipariş bulunamadı.',404);
        $this->db->transaction(function()use($id,$tracking,$order){$o=$this->db->one('SELECT status,expires_at FROM orders WHERE id=? FOR UPDATE',[$id]);RuleViolation::ensure($o['status']==='awaiting_payment'&&strtotime($o['expires_at'].' UTC')>time(),'PAYMENT_EXPIRED','Ödeme süresi dolmuş.');$p=$this->db->one('SELECT provider FROM payments WHERE order_id=? FOR UPDATE',[$id]);RuleViolation::ensure($p['provider']==='stripe','PROVIDER_MISMATCH','Ödeme sağlayıcısı eşleşmiyor.');$attempt=$this->db->one('SELECT order_id FROM payment_attempts WHERE order_id=?',[$id]);if(!$attempt){$path='/siparis/'.$id.($tracking!==null?'?token='.rawurlencode($tracking):'');$envelope=(new Crypto($this->config))->seal(['order'=>['id'=>$id,'number'=>$order['number'],'totalMinor'=>$order['total_minor'],'currency'=>$order['currency']],'success'=>$this->config->url($path),'cancel'=>$this->config->url($path)],'stripe-session');$this->db->execute('INSERT INTO payment_attempts(order_id,idempotency_key,envelope) VALUES(?,?,?)',[$id,'stripe-session:'.$id,$envelope]);(new Commerce($this->db,$this->config))->enqueue('stripe.session',['orderId'=>$id],'stripe-session:'.$id);}});
        return $this->createForOrder($id,$provider);
    }
    public function createForOrder(string $id,?PaymentProvider $provider=null):array
    {
        $provider??=$this->provider();$attempt=$this->db->one('SELECT * FROM payment_attempts WHERE order_id=?',[$id]);RuleViolation::ensure($attempt,'PAYMENT_ATTEMPT_REQUIRED','Ödeme hazırlığı bulunamadı.');if($attempt['status']==='created')return ['url'=>$attempt['session_url']];$payload=(new Crypto($this->config))->open($attempt['envelope'],'stripe-session');$response=$provider->createSession($payload['order'],$payload['success'],$payload['cancel'],$attempt['idempotency_key']);RuleViolation::ensure($response['orderId']===$id&&$response['amountMinor']===$payload['order']['totalMinor']&&$response['currency']===$payload['order']['currency']&&$response['url']!==null,'PAYMENT_RESPONSE_MISMATCH','Ödeme oturumu eşleşmiyor.',503);
        $this->db->transaction(function()use($id,$response){$p=$this->db->one('SELECT id,provider_reference FROM payments WHERE order_id=? FOR UPDATE',[$id]);RuleViolation::ensure($p['provider_reference']===null||$p['provider_reference']===$response['id'],'PAYMENT_REFERENCE_MISMATCH','Ödeme oturumu eşleşmiyor.');$this->db->execute('UPDATE payments SET provider_reference=?,payment_intent=COALESCE(?,payment_intent),updated_at=CURRENT_TIMESTAMP(3) WHERE id=?',[$response['id'],$response['paymentIntent'],$p['id']]);$this->db->execute("UPDATE payment_attempts SET status='created',session_url=?,updated_at=CURRENT_TIMESTAMP(3) WHERE order_id=?",[$response['url'],$id]);});return ['url'=>$response['url']];
    }
    public function receive(string $raw,string $signature):array
    {
        $event=$this->provider()->verify($raw,$signature);$hash=hash('sha256',$raw);return $this->db->transaction(function()use($event,$hash){$this->db->execute('INSERT INTO provider_events(id,payload_hash,payload) VALUES(?,?,?) ON DUPLICATE KEY UPDATE id=id',[$event['id'],$hash,$this->config->json($event)]);$old=$this->db->one('SELECT payload_hash FROM provider_events WHERE id=? FOR UPDATE',[$event['id']]);RuleViolation::ensure(hash_equals($old['payload_hash'],$hash),'EVENT_CONFLICT','Aynı olay farklı içerikle alındı.');(new Commerce($this->db,$this->config))->enqueue('stripe.event',['eventId'=>$event['id']],'stripe-event:'.$event['id']);return ['received'=>true];});
    }
    public function process(string $id):array
    {
        $row=$this->db->one('SELECT * FROM provider_events WHERE id=?',[$id]);RuleViolation::ensure($row,'EVENT_NOT_FOUND','Olay bulunamadı.',404);if($row['status']==='processed')return ['duplicate'=>true];$event=json_decode($row['payload'],true);
        if($event['kind']==='payment'&&$event['status']!=='pending'){$p=$this->db->one('SELECT provider_reference FROM payments WHERE order_id=?',[$event['orderId']]);RuleViolation::ensure($p&&!empty($p['provider_reference'])&&$p['provider_reference']===$event['providerReference'],'PAYMENT_REFERENCE_MISMATCH','Ödeme oturumu henüz eşleşmedi.');$this->bindIntent($event);(new Commerce($this->db,$this->config))->settle($event,'stripe',$row['payload_hash']);}
        elseif($event['kind']==='refund'){$refund=$this->db->one('SELECT id FROM refunds WHERE provider_reference=?',[$event['reference']]);RuleViolation::ensure($refund,'REFUND_REFERENCE_PENDING','İade referansı henüz eşleşmedi.');$this->finalizeRefund($refund['id'],$event);}
        elseif($event['kind']==='dispute'){$this->db->transaction(function()use($event){$p=$this->db->one('SELECT id,currency FROM payments WHERE payment_intent=? FOR UPDATE',[$event['paymentIntent']]);RuleViolation::ensure($p&&$p['currency']===$event['currency'],'DISPUTE_REFERENCE_PENDING','İtiraz ödemesi henüz eşleşmedi.');$this->db->execute('INSERT INTO payment_disputes(id,payment_id,status,amount_minor,currency) VALUES(?,?,?,?,?) ON DUPLICATE KEY UPDATE status=?,updated_at=CURRENT_TIMESTAMP(3)',[$event['reference'],$p['id'],$event['status'],$event['amountMinor'],$event['currency'],$event['status']]);});}
        $this->db->execute("UPDATE provider_events SET status='processed',processed_at=CURRENT_TIMESTAMP(3),last_error=NULL WHERE id=?",[$id]);return ['duplicate'=>false];
    }
    private function bindIntent(array $event):void
    {if(empty($event['paymentIntent']))return;$this->db->transaction(function()use($event){$this->db->one('SELECT id FROM orders WHERE id=? FOR UPDATE',[$event['orderId']]);$p=$this->db->one('SELECT provider,provider_reference,payment_intent,amount_minor,currency FROM payments WHERE order_id=? FOR UPDATE',[$event['orderId']]);RuleViolation::ensure($p&&$p['provider']==='stripe'&&$p['provider_reference']===$event['providerReference']&&(int)$p['amount_minor']===$event['amountMinor']&&$p['currency']===$event['currency']&&($p['payment_intent']===null||$p['payment_intent']===$event['paymentIntent']),'PAYMENT_INTENT_MISMATCH','Tahsilat referansı siparişle eşleşmiyor.');$this->db->execute('UPDATE payments SET payment_intent=COALESCE(payment_intent,?) WHERE order_id=?',[$event['paymentIntent'],$event['orderId']]);});}
    public function refund(string $id):array
    {$r=$this->db->one('SELECT f.*,p.payment_intent,p.currency FROM refunds f JOIN payments p ON p.id=f.payment_id WHERE f.id=?',[$id]);RuleViolation::ensure($r&&$r['payment_intent'],'REFUND_REFERENCE_PENDING','Tahsilat referansı henüz doğrulanmadı.');if($r['status']==='succeeded')return ['duplicate'=>true];$response=$this->provider()->refund($r['payment_intent'],(int)$r['amount_minor'],'stripe-refund:'.$id);return $this->finalizeRefund($id,$response+['reference'=>$response['id']]);}
    private function finalizeRefund(string $id,array $response):array
    {return $this->db->transaction(function()use($id,$response){$link=$this->db->one('SELECT r.order_id FROM refunds f JOIN returns r ON r.id=f.return_id WHERE f.id=?',[$id]);RuleViolation::ensure($link,'REFUND_NOT_FOUND','İade bulunamadı.',404);$this->db->one('SELECT id FROM orders WHERE id=? FOR UPDATE',[$link['order_id']]);$p=$this->db->one('SELECT * FROM payments WHERE order_id=? FOR UPDATE',[$link['order_id']]);$r=$this->db->one('SELECT * FROM refunds WHERE id=? FOR UPDATE',[$id]);RuleViolation::ensure($r&&(int)$r['amount_minor']===$response['amountMinor']&&$p['currency']===$response['currency']&&($r['provider_reference']===null||$r['provider_reference']===$response['reference']),'REFUND_MISMATCH','İade yanıtı tutar/para/referansla eşleşmiyor.');if($r['status']==='succeeded')return ['duplicate'=>true];$status=$response['status']==='succeeded'?'succeeded':(in_array($response['status'],['failed','canceled'],true)?'failed':'pending');if($r['status']==='failed'&&$status==='pending')return ['duplicate'=>true,'status'=>'failed'];$this->db->execute('UPDATE refunds SET provider_reference=?,status=? WHERE id=?',[$response['reference'],$status,$id]);$state=$status==='succeeded'?'refunded':($status==='failed'?'refund_failed':'refund_pending');$this->db->execute('UPDATE returns SET status=?,updated_at=CURRENT_TIMESTAMP(3) WHERE id=?',[$state,$r['return_id']]);if($status==='succeeded'){$total=Money::sum([(int)$p['refunded_minor'],(int)$r['amount_minor']]);RuleViolation::ensure($total<=(int)$p['amount_minor'],'REFUND_AMOUNT','İade tahsilatı aşıyor.');$paymentStatus=$total===(int)$p['amount_minor']?'refunded':'partially_refunded';$this->db->execute('UPDATE payments SET refunded_minor=?,status=?,updated_at=CURRENT_TIMESTAMP(3) WHERE id=?',[$total,$paymentStatus,$p['id']]);$this->db->execute('UPDATE orders SET payment_status=?,updated_at=CURRENT_TIMESTAMP(3) WHERE id=?',[$paymentStatus,$link['order_id']]);}return ['duplicate'=>false,'status'=>$status];});}
    public function reconcile(int $limit=2):array
    {
        $provider=$this->provider();$limit=max(1,min(2,$limit));
        $candidates=$this->db->all("SELECT p.order_id FROM payments p JOIN orders o ON o.id=p.order_id WHERE p.provider='stripe' AND p.provider_reference IS NOT NULL AND(p.status IN('pending','failed') OR(p.payment_intent IS NULL AND p.status IN('succeeded','partially_refunded','refunded'))) AND p.reconcile_after<=CURRENT_TIMESTAMP(3) AND o.created_at>DATE_SUB(CURRENT_TIMESTAMP(3),INTERVAL 7 DAY) ORDER BY(p.reconciled_at IS NOT NULL),p.reconciled_at,o.created_at,p.order_id LIMIT ".$limit);
        $checked=0;$failed=0;
        foreach($candidates as $candidate){
            $p=$this->db->transaction(function()use($candidate){$this->db->one('SELECT id FROM orders WHERE id=? FOR UPDATE',[$candidate['order_id']]);$p=$this->db->one('SELECT order_id,provider_reference,status FROM payments WHERE order_id=? AND reconcile_after<=CURRENT_TIMESTAMP(3) FOR UPDATE',[$candidate['order_id']]);if(!$p)return null;$this->db->execute('UPDATE payments SET reconcile_after=DATE_ADD(CURRENT_TIMESTAMP(3),INTERVAL 3 MINUTE) WHERE order_id=?',[$p['order_id']]);return $p;});
            if(!$p)continue;$error=null;
            try{$session=$provider->query($p['provider_reference']);
                if($session['paymentStatus']==='paid'||$session['status']==='expired'){
                    $event=['id'=>'reconcile:'.hash('sha256',$session['id'].':'.$session['paymentStatus'].':'.$session['status']),'orderId'=>$session['orderId'],'providerReference'=>$session['id'],'amountMinor'=>$session['amountMinor'],'currency'=>$session['currency'],'status'=>$session['paymentStatus']==='paid'?'succeeded':'failed','paymentIntent'=>$session['paymentIntent']];
                    RuleViolation::ensure($event['orderId']===$p['order_id']&&$event['providerReference']===$p['provider_reference'],'PAYMENT_REFERENCE_MISMATCH','Mutabakat siparişi eşleşmiyor.');$this->bindIntent($event);
                    if(in_array($p['status'],['pending','failed'],true))(new Commerce($this->db,$this->config))->settle($event,'stripe');
                }$checked++;
            }catch(\Throwable $e){$failed++;$error=$e instanceof RuleViolation?$e->rule:'PROVIDER_UNAVAILABLE';}
            finally{$this->db->execute('UPDATE payments SET reconciled_at=CURRENT_TIMESTAMP(3),reconcile_after=DATE_ADD(CURRENT_TIMESTAMP(3),INTERVAL 1 MINUTE),reconcile_error=? WHERE order_id=?',[$error,$p['order_id']]);}
        }return ['checked'=>$checked,'deferred'=>$failed];
    }
}
