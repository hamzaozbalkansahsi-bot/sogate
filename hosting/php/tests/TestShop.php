<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/TestShop.php
 * Açıklama   : Operasyon kabulü için gerçek satın alma akışından izole ödenmiş sipariş hazırlar.
 */
declare(strict_types=1);
require_once __DIR__.'/TestDatabase.php';
use Sexogate\{Fixtures,Principal,Cart,Commerce};
final class TestShop
{
    public readonly TestDatabase $f;public readonly Principal $admin;public readonly array $order;public readonly string $variant;
    public function __construct(int $quantity=2,bool $paid=true,?callable $configure=null)
    {
        $this->f=new TestDatabase();$this->admin=new Principal('fixture-admin','admin',true);$fixtures=new Fixtures($this->f->db,$this->f->config);$fixtures->policies();$fixtures->catalog($this->admin);$this->variant=$configure?$configure($this->f,$this->admin):$this->f->db->one("SELECT id FROM variants WHERE sku='TEST-01'")['id'];$token=bin2hex(random_bytes(32));(new Cart($this->f->db,$this->f->config))->set($token,$this->variant,$quantity);
        $input=['email'=>'operations@example.invalid','fullName'=>'Hamza ÖZBALKAN','phone'=>'05000000000','line1'=>'Şişli Çeşme adresi','city'=>'İstanbul','postalCode'=>'34000','privacyAccepted'=>true,'termsAccepted'=>true,'idempotencyKey'=>bin2hex(random_bytes(16))];$c=new Commerce($this->f->db,$this->f->config);$input['quoteToken']=$c->quote($token,$input)['quoteToken'];$this->order=$c->checkout($token,$input);if($paid){$event=$c->testEvent($this->order['orderId'],$this->order['trackingToken'],'succeeded');$c->handleTest($event['raw'],$event['signature']);}
    }
}
