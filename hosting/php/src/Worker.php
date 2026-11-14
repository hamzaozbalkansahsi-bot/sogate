<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/Worker.php
 * Açıklama   : cPanel cron için kalıcı, kiralı ve tekrar denemeli kısa PHP işçi turu.
 */
declare(strict_types=1);
namespace Sexogate;
use Symfony\Component\Mailer\{Mailer,Transport};
use Symfony\Component\Mime\Email;
final class Worker
{
    public function __construct(private Database $db,private Config $config){}
    public function tick(int $limit=5):array
    {
        $expired=(new Commerce($this->db,$this->config))->expire();$done=0;$failed=0;$exhausted=0;$deadline=microtime(true)+45;
        for($i=0;$i<min(20,max(1,$limit))&&microtime(true)<$deadline;$i++){
            $job=$this->db->transaction(function(){
                $r=$this->db->one("SELECT * FROM jobs WHERE (status='pending' AND available_at<=CURRENT_TIMESTAMP(3)) OR(status='running' AND lease_until<CURRENT_TIMESTAMP(3)) ORDER BY available_at,id LIMIT 1 FOR UPDATE SKIP LOCKED");if(!$r)return null;
                if((int)$r['attempts']>=(int)$r['max_attempts']){$this->db->execute("UPDATE jobs SET status='failed',lease_until=NULL,last_error='RETRY_EXHAUSTED' WHERE id=?",[$r['id']]);return ['exhausted'=>true];}
                $attempt=(int)$r['attempts']+1;$this->db->execute("UPDATE jobs SET status='running',attempts=?,lease_until=DATE_ADD(CURRENT_TIMESTAMP(3),INTERVAL 120 SECOND) WHERE id=?",[$attempt,$r['id']]);$r['attempts']=$attempt;return $r;
            });if(!$job)break;if($job['exhausted']??false){$exhausted++;continue;}
            try{$this->dispatch($job);$done+=$this->db->execute("UPDATE jobs SET status='completed',completed_at=CURRENT_TIMESTAMP(3),lease_until=NULL,last_error=NULL WHERE id=? AND status='running' AND attempts=? AND generation=? AND lease_until>CURRENT_TIMESTAMP(3)",[$job['id'],$job['attempts'],$job['generation']]);}
            catch(\Throwable $e){$failed++;$code=$e instanceof RuleViolation?$e->rule:'PROVIDER_UNAVAILABLE';$delay=min(3600,30*(2**min(6,$job['attempts'])));$this->db->execute("UPDATE jobs SET status=?,available_at=DATE_ADD(CURRENT_TIMESTAMP(3),INTERVAL $delay SECOND),lease_until=NULL,last_error=? WHERE id=? AND status='running' AND attempts=? AND generation=?",[$job['attempts']>=(int)$job['max_attempts']?'failed':'pending',$code,$job['id'],$job['attempts'],$job['generation']]);}
        }return ['expired'=>$expired,'completed'=>$done,'deferred'=>$failed,'exhausted'=>$exhausted];
    }
    private function dispatch(array $job):void
    {
        $payload=json_decode($job['payload'],true,32,JSON_THROW_ON_ERROR);
        if(in_array($job['type'],['stripe.event','stripe.session','stripe.reconcile','payment.refund'],true)){$p=new Payments($this->db,$this->config);match($job['type']){'stripe.event'=>$p->process($payload['eventId']),'stripe.session'=>$p->createForOrder($payload['orderId']),'payment.refund'=>$p->refund($payload['refundId']),'stripe.reconcile'=>$p->reconcile()};return;}
        if($job['type']==='reservation.expire'){(new Commerce($this->db,$this->config))->expire();return;}
        RuleViolation::ensure(in_array($job['type'],['order.confirmation','email.auth'],true),'JOB_HANDLER_NOT_CONFIGURED','Bu iş için operasyon bağlantısı yapılandırılmadı.',503);
        RuleViolation::ensure($this->config->get('smtp_dsn')!==''&&filter_var($this->config->get('mail_from'),FILTER_VALIDATE_EMAIL),'SMTP_NOT_CONFIGURED','E-posta bağlantısı yapılandırılmadı.',503);
        if($job['type']==='email.auth'){$message=(new Crypto($this->config))->open($payload['envelope'],'email.auth');$email=$message['email'];$body="SEXOGATE hesap işleminize aşağıdaki güvenli bağlantıdan devam edebilirsiniz.\n".$message['url'];}
        else{$order=$this->db->one('SELECT email,number FROM orders WHERE id=?',[$payload['orderId']]);RuleViolation::ensure($order,'ORDER_NOT_FOUND','Sipariş bulunamadı.',404);$email=$order['email'];$body='Siparişiniz kaydedildi. Sipariş numaranız: '.$order['number'].'. Ayrıntıları hesabınızdan veya size verilen özel sipariş bağlantısından inceleyebilirsiniz.';}
        $mail=(new Email())->from($this->config->get('mail_from'))->to($email)->subject('Hesap ve sipariş bilgilendirmesi')->text($body);$mail->getHeaders()->addIdHeader('Message-ID','sg-'.$job['id'].'@sexogate.com');
        (new Mailer(Transport::fromDsn($this->config->get('smtp_dsn').(str_contains($this->config->get('smtp_dsn'),'?')?'&':'?').'timeout=15')))->send($mail);
    }
}
