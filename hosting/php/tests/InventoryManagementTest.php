<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/InventoryManagementTest.php
 * Açıklama   : Satın alma, lotlu kabul/geri çağırma ve bileşen setinin gerçek DB kabulü.
 */
declare(strict_types=1);
require_once __DIR__.'/TestShop.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{InventoryManagement,Purchasing,Inventory,Fixtures,Catalog,Principal,RuleViolation};
final class InventoryManagementTest extends TestCase
{
    private function fixture():array
    {$f=new TestDatabase();$a=new Principal('fixture-admin','admin',true);$x=new Fixtures($f->db,$f->config);$x->policies();$x->catalog($a);$f->db->execute("INSERT INTO suppliers(id,name) VALUES('supplier-test','İzole test tedarikçisi')");return [$f,$a];}
    private function key():string{return bin2hex(random_bytes(16));}
    public function testPurchaseReceiptIsIdempotentAndCannotExceedRemainingQuantity():void
    {[$f,$a]=$this->fixture();self::assertTrue(class_exists(Purchasing::class),'PHP satın alma modülü eksik.');$v=$f->db->one("SELECT id FROM variants WHERE sku='TEST-01'")['id'];$p=new Purchasing($f->db,$f->config);$po=$p->create('supplier-test','TRY',[['variantId'=>$v,'quantity'=>3,'unitCostMinor'=>7000]],'Tedarik belge referansı123',$this->key(),$a);$key=$this->key();$r=$p->receive($po['id'],[['variantId'=>$v,'quantity'=>2]],'Mal kabul belge referansı123',$key,$a);self::assertEquals($r,$p->receive($po['id'],[['variantId'=>$v,'quantity'=>2]],'Mal kabul belge referansı123',$key,$a));self::assertSame(12,(int)$f->db->one('SELECT on_hand FROM inventory_balance WHERE variant_id=?',[$v])['on_hand']);try{$p->receive($po['id'],[['variantId'=>$v,'quantity'=>2]],'Fazla kabul belgesi123',$this->key(),$a);self::fail('Fazla mal kabulü yapıldı.');}catch(RuleViolation){}self::assertSame(2,(int)$f->db->one('SELECT received FROM purchase_items')['received']);}
    public function testLotReceiptAndRecallMoveOnlyTheActualPhysicalQuantity():void
    {[$f,$a]=$this->fixture();self::assertTrue(class_exists(InventoryManagement::class),'PHP lot/depo yönetimi eksik.');$catalog=new Catalog($f->db,$f->config);$v=$catalog->create(['name'=>'Lotlu test ürünü','nameEn'=>'Lot item','slug'=>'lot-item','category'=>'ic-giyim','sku'=>'LOT-NEW','variantName'=>'Tek seçenek','priceMinor'=>10000,'image'=>'/media/atelier-01.svg','fixture'=>true],$a);$m=new InventoryManagement($f->db,$f->config);$m->tracking($v['variantId'],true,true,$a);$p=new Purchasing($f->db,$f->config);$po=$p->create('supplier-test','TRY',[['variantId'=>$v['variantId'],'quantity'=>5,'unitCostMinor'=>3000]],'Satın alma belgesi123',$this->key(),$a);$p->receive($po['id'],[['variantId'=>$v['variantId'],'quantity'=>5,'lotNumber'=>'LOT-ÖZ-2026','expiresAt'=>gmdate('Y-m-d',time()+31536000)]],'Lotlu mal kabul belgesi123',$this->key(),$a);$lot=$f->db->one('SELECT id FROM inventory_lots WHERE variant_id=?',[$v['variantId']])['id'];self::assertSame(5,(new Inventory($f->db,$f->config))->available($v['variantId']));$m->recall($lot,'Üretici geri çağırma referansı123',$this->key(),$a);self::assertSame(0,(new Inventory($f->db,$f->config))->available($v['variantId']));$b=$f->db->one('SELECT on_hand,quarantine FROM inventory_balance WHERE variant_id=?',[$v['variantId']]);self::assertSame([0,5],[(int)$b['on_hand'],(int)$b['quarantine']]);}
    public function testBundleDefinitionUsesComponentsAndCannotBecomePhysicalStock():void
    {[$f,$a]=$this->fixture();self::assertTrue(class_exists(InventoryManagement::class),'PHP set yönetimi eksik.');$v=$f->db->one("SELECT id FROM variants WHERE sku='TEST-01'")['id'];$p=(new Catalog($f->db,$f->config))->create(['name'=>'Test seti','nameEn'=>'Test set','slug'=>'test-set','category'=>'ic-giyim','sku'=>'BUNDLE-NEW','variantName'=>'Set','priceMinor'=>20000,'image'=>'/media/atelier-03.svg','fixture'=>true],$a);(new InventoryManagement($f->db,$f->config))->bundle($p['variantId'],0,[['variantId'=>$v,'quantity'=>2]],'Set tanımı inceleme referansı123',$a);self::assertSame(5,(new Inventory($f->db,$f->config))->available($p['variantId']));$this->expectException(RuleViolation::class);(new Inventory($f->db,$f->config))->receive($p['variantId'],1,'Yanlış fiziksel kabul',$this->key(),$a);}
}
