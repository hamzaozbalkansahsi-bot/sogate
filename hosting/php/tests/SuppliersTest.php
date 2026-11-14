<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/SuppliersTest.php
 * Açıklama   : Manuel tedarikçi onayı/sevki, tahsis mutabakatı ve depo artmayan iade kabulü.
 */
declare(strict_types=1);
require_once __DIR__.'/TestShop.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{Suppliers,Principal,Inventory,Returns,RuleViolation};
final class SuppliersTest extends TestCase
{
    private function key():string{return bin2hex(random_bytes(16));}
    private function shop():TestShop
    {
        self::assertTrue(class_exists(Suppliers::class),'PHP tedarikçi operasyonu eksik.');
        return new TestShop(2,true,function($f,$a){
            $s=new Suppliers($f->db,$f->config);$id=$s->save(['name'=>'İzole tedarikçi','leadDays'=>3],$a)['id'];
            $s->profile(['supplierId'=>$id,'enabled'=>true,'contractReference'=>'TEST sözleşme belgesi','privacyReference'=>'TEST veri aktarım belgesi','packagingReference'=>'TEST ambalaj belgesi','returnReference'=>'TEST iade belgesi'],$a);
            $s->route(['supplierId'=>$id,'country'=>'TR','currency'=>'TRY','shippingMinor'=>1200,'handlingMinor'=>100,'minDays'=>2,'maxDays'=>5,'carrier'=>'Kabul taşıyıcısı','reference'=>'TEST rota belgesi','approved'=>true],$a);
            $v=$f->db->one("SELECT id FROM variants WHERE sku='TEST-01'")['id'];
            $s->offer(['supplierId'=>$id,'variantId'=>$v,'supplierSku'=>'REAL-EXTERNAL-TEST','currency'=>'TRY','costMinor'=>5000,'quantity'=>5,'safetyStock'=>1,'validUntil'=>gmdate('c',time()+3600),'reference'=>'TEST stok teyidi','approved'=>true],$a);
            $s->mode($v,'dropship',$a);return $v;
        });
    }
    public function testSupplierDispatchRequiresAcknowledgementAndDoesNotTouchWarehouseStock():void
    {
        $s=$this->shop();$service=new Suppliers($s->f->db,$s->f->config);$group=$s->f->db->one("SELECT id FROM order_fulfillment_groups WHERE source='supplier'")['id'];
        $items=[['variantId'=>$s->variant,'quantity'=>1]];
        try{$service->ship($group,$items,'Kabul taşıyıcısı','TEST-TRACK-1',$this->key(),$s->admin);self::fail('Teyitsiz sevk açıldı.');}catch(RuleViolation){}
        $service->accept($group,'TEST gerçek dış sipariş teyidi',$this->key(),$s->admin);
        try{$service->ship($group,$items,'Başka taşıyıcı','TEST-TRACK-1',$this->key(),$s->admin);self::fail('Snapshot taşıyıcısı değiştirildi.');}catch(RuleViolation){}
        $key=$this->key();$one=$service->ship($group,$items,'Kabul taşıyıcısı','TEST-TRACK-1',$key,$s->admin);
        self::assertEquals($one,$service->ship($group,$items,'Kabul taşıyıcısı','TEST-TRACK-1',$key,$s->admin));self::assertSame('partially_shipped',$one['status']);
        self::assertSame('shipped',$service->ship($group,$items,'Kabul taşıyıcısı','TEST-TRACK-2',$this->key(),$s->admin)['status']);
        self::assertSame(10,(int)$s->f->db->one('SELECT on_hand FROM inventory_balance WHERE variant_id=?',[$s->variant])['on_hand']);
        self::assertSame(2,(int)$s->f->db->one('SELECT COUNT(*) n FROM shipments')['n']);
    }
    public function testSupplierReturnEvidenceNeverCreatesWarehouseOrQuarantineStock():void
    {
        $s=$this->shop();$service=new Suppliers($s->f->db,$s->f->config);$group=$s->f->db->one("SELECT id FROM order_fulfillment_groups WHERE source='supplier'")['id'];$service->accept($group,'TEST tedarikçi teyidi',$this->key(),$s->admin);$service->ship($group,[['variantId'=>$s->variant,'quantity'=>2]],'Kabul taşıyıcısı','TEST-TRACK-RETURN',$this->key(),$s->admin);
        $returns=new Returns($s->f->db,$s->f->config);$r=$returns->request($s->order['orderId'],$s->order['trackingToken'],$s->variant,1,'İnceleme için iade','opened',$this->key());$returns->decide($r['id'],true,'İade kabul edildi',$this->key(),$s->admin);
        $service->returnReceived($r['id'],'TEST dış teslim belgesi',$this->key(),$s->admin);
        try{$returns->inspect($r['id'],'restock','Satışa dönüş denemesi',$this->key(),$s->admin);self::fail('Tedarikçi iadesi depo QC yoluna girdi.');}catch(RuleViolation){}
        $service->returnInspected($r['id'],'TEST tedarikçi kalite inceleme belgesi',$this->key(),$s->admin);$returns->refund($r['id'],$this->key(),$s->admin);
        $b=$s->f->db->one('SELECT on_hand,quarantine FROM inventory_balance WHERE variant_id=?',[$s->variant]);self::assertSame([10,0],[(int)$b['on_hand'],(int)$b['quarantine']]);
        self::assertSame(0,(int)$s->f->db->one('SELECT COUNT(*) n FROM return_stock_lines')['n']);
    }
    public function testOnlySelectedAcknowledgedAllocationIsReconciledAndWarehouseCannotAccessSupplierDetails():void
    {
        $s=$this->shop();$service=new Suppliers($s->f->db,$s->f->config);$group=$s->f->db->one("SELECT id FROM order_fulfillment_groups WHERE source='supplier'")['id'];$service->accept($group,'TEST teyit referansı',$this->key(),$s->admin);
        $allocation=$s->f->db->one('SELECT id,offer_id FROM supplier_reservations');self::assertSame(2,(new Inventory($s->f->db,$s->f->config))->available($s->variant));
        try{$service->reconcile($allocation['offer_id'],[$allocation['id']],'Eski bildirim ile deneme',$this->key(),$s->admin);self::fail('Yeni stok teyidi olmadan tahsis kapandı.');}catch(RuleViolation){}
        $supplier=$s->f->db->one('SELECT supplier_id FROM supplier_offers')['supplier_id'];
        $service->offer(['supplierId'=>$supplier,'variantId'=>$s->variant,'supplierSku'=>'REAL-EXTERNAL-TEST','currency'=>'TRY','costMinor'=>5000,'quantity'=>3,'safetyStock'=>1,'validUntil'=>gmdate('c',time()+3600),'reference'=>'TEST yeni stok teyidi','approved'=>true],$s->admin);
        self::assertSame('allocated',$s->f->db->one('SELECT status FROM supplier_reservations')['status']);
        $service->reconcile($allocation['offer_id'],[$allocation['id']],'TEST sonraki stokta düşüm teyidi',$this->key(),$s->admin);self::assertSame('reconciled',$s->f->db->one('SELECT status FROM supplier_reservations')['status']);
        $this->expectException(RuleViolation::class);$service->detail($group,new Principal('warehouse','warehouse',true));
    }
}
