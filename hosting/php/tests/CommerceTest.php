<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/CommerceTest.php
 * Açıklama   : PHP katalog/stok/sepet/teklif/ödeme/sipariş zincirinin gerçek DB kabulü.
 */
declare(strict_types=1);
require_once __DIR__.'/TestDatabase.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{Database,Principal,Catalog,Inventory,Cart,Commerce,Fixtures,RuleViolation};
final class CommerceTest extends TestCase
{
    private TestDatabase $f;private Principal $admin;
    protected function setUp():void{$this->f=new TestDatabase();$this->admin=new Principal('fixture-admin','admin',true);(new Fixtures($this->f->db,$this->f->config))->policies();}
    private function product(int $stock=3):array
    {
        $catalog=new Catalog($this->f->db,$this->f->config);$p=$catalog->create(['name'=>'Ölçü ve Özellikler','nameEn'=>'Measurements','slug'=>'olcu-'.bin2hex(random_bytes(5)),'category'=>'ic-giyim','sku'=>'PHP-'.bin2hex(random_bytes(6)),'variantName'=>'Bordo','priceMinor'=>12501,'costMinor'=>4000,'image'=>'/media/atelier-02.svg','fixture'=>true],$this->admin);
        (new Inventory($this->f->db,$this->f->config))->receive($p['variantId'],$stock,'İzole mal kabulü',bin2hex(random_bytes(16)),$this->admin);$catalog->approve($p['id'],'TR',$this->admin);return $p;
    }
    private function input():array{return ['fullName'=>'Hamza ÖZBALKAN','phone'=>'05000000000','line1'=>'Şişli Çeşme Güvenli Alışveriş','city'=>'İstanbul','postalCode'=>'34000','country'=>'TR','currency'=>'TRY','locale'=>'tr','email'=>'fixture@example.invalid','privacyAccepted'=>true,'termsAccepted'=>true,'idempotencyKey'=>bin2hex(random_bytes(16))];}
    private function place(array $p,string $token,array $input=[]):array
    {$cart=new Cart($this->f->db,$this->f->config);$cart->set($token,$p['variantId'],1);$c=new Commerce($this->f->db,$this->f->config);$i=$input?:$this->input();$i['quoteToken']=$c->quote($token,$i)['quoteToken'];return $c->checkout($token,$i);}
    public function testProductReceiptStorefrontGuestOrderAndSignedPayment():void
    {
        $p=$this->product();$catalog=new Catalog($this->f->db,$this->f->config);self::assertCount(1,$catalog->search(['q'=>'ölçü'])['rows']);
        $token=bin2hex(random_bytes(32));$order=$this->place($p,$token);self::assertSame(12501+500,$order['totalMinor']);$c=new Commerce($this->f->db,$this->f->config);
        $signed=$c->testEvent($order['orderId'],$order['trackingToken'],'succeeded');self::assertFalse($c->handleTest($signed['raw'],$signed['signature'])['duplicate']);self::assertTrue($c->handleTest($signed['raw'],$signed['signature'])['duplicate']);
        self::assertSame(2,(int)$this->f->db->one('SELECT on_hand FROM inventory_balance WHERE variant_id=?',[$p['variantId']])['on_hand']);
        $view=$c->order($order['orderId'],$order['trackingToken']);self::assertSame('confirmed',$view['status']);self::assertSame('Ölçü ve Özellikler',$view['items'][0]['name']);self::assertNull($c->order($order['orderId'],'wrong'));
        self::assertSame(1,(int)$this->f->db->one("SELECT COUNT(*) n FROM inventory_movements WHERE type='sale'")['n']);
    }
    public function testLastStockAndIdempotentCheckout():void
    {
        $p=$this->product(1);$a=bin2hex(random_bytes(32));$b=bin2hex(random_bytes(32));$cart=new Cart($this->f->db,$this->f->config);$cart->set($a,$p['variantId'],1);$cart->set($b,$p['variantId'],1);$c=new Commerce($this->f->db,$this->f->config);$ia=$this->input();$ia['quoteToken']=$c->quote($a,$ia)['quoteToken'];$ib=$this->input();$ib['quoteToken']=$c->quote($b,$ib)['quoteToken'];
        $one=$c->checkout($a,$ia);self::assertSame($one,$c->checkout($a,$ia));$this->expectException(RuleViolation::class);$c->checkout($b,$ib);
    }
    public function testForgedAmountAndUnsignedPaymentNeverBecomePaid():void
    {
        $p=$this->product();$order=$this->place($p,bin2hex(random_bytes(32)));$c=new Commerce($this->f->db,$this->f->config);$signed=$c->testEvent($order['orderId'],$order['trackingToken'],'succeeded');
        try{$c->handleTest($signed['raw'],'');self::fail('unsigned accepted');}catch(RuleViolation){}
        $event=json_decode($signed['raw'],true);$event['amountMinor']=1;$raw=json_encode($event);try{$c->handleTest($raw,hash_hmac('sha256',$raw,$this->f->config->get('secret')));self::fail('amount accepted');}catch(RuleViolation){}
        self::assertSame('pending',$this->f->db->one('SELECT status FROM payments WHERE order_id=?',[$order['orderId']])['status']);
    }
    public function testExpiredReservationLateSuccessIsAnException():void
    {
        $p=$this->product(1);$order=$this->place($p,bin2hex(random_bytes(32)));$c=new Commerce($this->f->db,$this->f->config);$this->f->db->execute('UPDATE orders SET expires_at=DATE_SUB(CURRENT_TIMESTAMP(3),INTERVAL 1 HOUR) WHERE id=?',[$order['orderId']]);$c->expire();
        $event=$c->testEvent($order['orderId'],$order['trackingToken'],'succeeded');$c->handleTest($event['raw'],$event['signature']);self::assertSame('payment_exception',$c->order($order['orderId'],$order['trackingToken'])['status']);self::assertSame(1,(int)$this->f->db->one('SELECT on_hand FROM inventory_balance WHERE variant_id=?',[$p['variantId']])['on_hand']);
    }
    public function testStaleQuoteCountryAndCartOwnershipFailClosed():void
    {
        $p=$this->product();$token=bin2hex(random_bytes(32));$cart=new Cart($this->f->db,$this->f->config);$cart->set($token,$p['variantId'],1);$c=new Commerce($this->f->db,$this->f->config);$i=$this->input();$i['quoteToken']=$c->quote($token,$i)['quoteToken'];$this->f->db->execute('UPDATE variant_prices SET amount_minor=25000 WHERE variant_id=?',[$p['variantId']]);
        try{$c->checkout($token,$i);self::fail('stale quote accepted');}catch(RuleViolation){}
        $i['country']='US';try{$c->quote($token,$i);self::fail('country accepted');}catch(RuleViolation){}
        $this->f->db->execute('UPDATE carts SET user_id=? WHERE token_hash=?',['owner-a',hash('sha256',$token)]);$this->expectException(RuleViolation::class);$cart->get($token,'TRY','owner-b');
    }
    public function testWarehouseCannotReadCostsAndOriginalAgreementsStayImmutable():void
    {
        $p=$this->product();$rows=(new Catalog($this->f->db,$this->f->config))->admin(new Principal('warehouse','warehouse',true));self::assertArrayNotHasKey('cost_minor',$rows[0]);
        $order=$this->place($p,bin2hex(random_bytes(32)));$agreements=$this->f->db->all('SELECT body,body_hash FROM order_agreements WHERE order_id=?',[$order['orderId']]);self::assertCount(2,$agreements);
        $this->expectException(PDOException::class);$this->f->db->execute('UPDATE order_agreements SET body=? WHERE order_id=?',['changed',$order['orderId']]);
    }
}
