<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/Providers/StripeProvider.php
 * Açıklama   : Resmî Stripe SDK ile idempotent Checkout, iade, sorgu ve ham imza doğrulama.
 */
declare(strict_types=1);
namespace Sexogate\Providers;
use Sexogate\{Config,Money,RuleViolation};
use Stripe\{StripeClient,Webhook};
final class StripeProvider implements PaymentProvider
{
    private StripeClient $client;private array $currencies;
    public function __construct(private Config $config)
    {
        $secret=$config->get('stripe_secret_key');RuleViolation::ensure($config->flag('stripe_business_approved')&&str_starts_with($secret,$config->local()?'sk_test_':'sk_live_')&&strlen($config->get('stripe_webhook_secret'))>=16,'STRIPE_NOT_APPROVED','Stripe işletme/kategori kabulü ve güvenli anahtar kurulumu gerekir.',503);$this->currencies=array_values(array_intersect(['TRY','EUR','USD','GBP'],explode(',',$config->get('stripe_enabled_currencies'))));RuleViolation::ensure($this->currencies,'STRIPE_CURRENCY_REQUIRED','Stripe hesabının tahsilat para birimleri yapılandırılmadı.',503);\Stripe\HttpClient\CurlClient::instance()->setTimeout(12);\Stripe\HttpClient\CurlClient::instance()->setConnectTimeout(5);$this->client=new StripeClient(['api_key'=>$secret,'max_network_retries'=>2]);
    }
    private function currency(string $currency):string{RuleViolation::ensure(in_array($currency,$this->currencies,true),'PAYMENT_CURRENCY_UNSUPPORTED','Bu para birimi ödeme hesabında açık değil.',400);return strtolower($currency);}
    private function session(array $s):array
    {$currency=strtoupper($s['currency']??'');$this->currency($currency);$url=$s['url']??null;if($url!==null){$u=parse_url($url);RuleViolation::ensure(is_array($u)&&($u['scheme']??'')==='https'&&($u['host']??'')==='checkout.stripe.com'&&!isset($u['user'])&&!isset($u['pass']),'PAYMENT_URL_INVALID','Ödeme adresi doğrulanamadı.',503);}RuleViolation::ensure(is_string($s['id']??null)&&is_int($s['amount_total']??null),'PROVIDER_RESPONSE_INVALID','Ödeme yanıtı doğrulanamadı.',503);return ['id'=>$s['id'],'url'=>$url,'orderId'=>$s['metadata']['orderId']??'','amountMinor'=>Money::amount($s['amount_total']),'currency'=>$currency,'paymentStatus'=>$s['payment_status']??'','status'=>$s['status']??'','paymentIntent'=>is_string($s['payment_intent']??null)?$s['payment_intent']:null];}
    public function createSession(array $order,string $successUrl,string $cancelUrl,string $key):array
    {$currency=$this->currency($order['currency']);$amount=Money::amount($order['totalMinor']);RuleViolation::ensure($amount>0,'INVALID_AMOUNT','Ödeme tutarı pozitif olmalıdır.',400);foreach([$successUrl,$cancelUrl] as $url)RuleViolation::ensure(str_starts_with($url,rtrim($this->config->get('app_url'),'/').'/'),'RETURN_URL_INVALID','Dönüş adresi geçersiz.',400);$s=$this->client->checkout->sessions->create(['mode'=>'payment','client_reference_id'=>$order['id'],'metadata'=>['orderId'=>$order['id']],'payment_intent_data'=>['metadata'=>['orderId'=>$order['id']]],'line_items'=>[['quantity'=>1,'price_data'=>['currency'=>$currency,'unit_amount'=>$amount,'product_data'=>['name'=>'SEXOGATE sipariş '.$order['number']]]]],'success_url'=>$successUrl,'cancel_url'=>$cancelUrl],['idempotency_key'=>$key]);return $this->session($s->toArray());}
    public function query(string $reference):array{return $this->session($this->client->checkout->sessions->retrieve($reference,[])->toArray());}
    public function refund(string $paymentIntent,int $amount,string $key):array
    {$r=$this->client->refunds->create(['payment_intent'=>$paymentIntent,'amount'=>Money::amount($amount)],['idempotency_key'=>$key])->toArray();RuleViolation::ensure(is_string($r['id']??null)&&($r['payment_intent']??null)===$paymentIntent&&($r['amount']??null)===$amount,'REFUND_RESPONSE_MISMATCH','Sağlayıcı iade yanıtı eşleşmiyor.',503);return ['id'=>$r['id'],'status'=>$r['status'],'amountMinor'=>$r['amount'],'currency'=>strtoupper($r['currency'])];}
    public function cancel(string $reference,string $key):array{return $this->session($this->client->checkout->sessions->expire($reference,[],['idempotency_key'=>$key])->toArray());}
    public function verify(string $raw,string $signature):array
    {
        RuleViolation::ensure(strlen($raw)<=1000000,'BODY_TOO_LARGE','Bildirim çok büyük.',413);try{$event=Webhook::constructEvent($raw,$signature,$this->config->get('stripe_webhook_secret'),300)->toArray();}catch(\Throwable){throw new RuleViolation('INVALID_SIGNATURE','Ödeme bildirimi doğrulanamadı.',401);}RuleViolation::ensure(($event['livemode']??null)===!$this->config->local()&&is_string($event['id']??null)&&strlen($event['id'])<=200,'EVENT_ENVIRONMENT_MISMATCH','Ödeme olayı ortamla eşleşmiyor.',400);$type=$event['type'];$o=$event['data']['object'];$base=['id'=>$event['id'],'type'=>$type,'created'=>$event['created']];
        if(in_array($type,['checkout.session.completed','checkout.session.async_payment_succeeded','checkout.session.async_payment_failed','checkout.session.expired'],true)){$s=$this->session($o);$status=in_array($type,['checkout.session.expired','checkout.session.async_payment_failed'],true)?'failed':($s['paymentStatus']==='paid'?'succeeded':'pending');RuleViolation::ensure($s['orderId']!=='','ORDER_REFERENCE_REQUIRED','Ödeme siparişi eşleşmiyor.',400);return $base+['kind'=>'payment','orderId'=>$s['orderId'],'providerReference'=>$s['id'],'amountMinor'=>$s['amountMinor'],'currency'=>$s['currency'],'status'=>$status,'paymentIntent'=>$s['paymentIntent']];}
        if(in_array($type,['refund.created','refund.updated','refund.failed'],true)){RuleViolation::ensure(is_string($o['id']??null)&&is_int($o['amount']??null),'REFUND_EVENT_INVALID','İade olayı geçersiz.',400);return $base+['kind'=>'refund','reference'=>$o['id'],'paymentIntent'=>$o['payment_intent']??null,'amountMinor'=>Money::amount($o['amount']),'currency'=>strtoupper($o['currency']??''),'status'=>$o['status']??'pending'];}
        if(str_starts_with($type,'charge.dispute.'))return $base+['kind'=>'dispute','reference'=>$o['id'],'paymentIntent'=>$o['payment_intent']??null,'amountMinor'=>Money::amount($o['amount']??null),'currency'=>strtoupper($o['currency']??''),'status'=>$o['status']??'needs_response'];
        return $base+['kind'=>'ignored'];
    }
}
