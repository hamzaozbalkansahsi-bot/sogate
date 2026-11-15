<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/CatalogExperienceTest.php
 * Açıklama   : Türkçe toleranslı arama, gerçek kategori ağacı ve toplu stok eşleşmesi.
 */
declare(strict_types=1);
require_once __DIR__.'/TestDatabase.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{CatalogSearch,Fixtures,Principal,Catalog,Inventory,Availability,CatalogPresentation,RuleViolation};
final class CatalogExperienceTest extends TestCase
{
    public function testTurkishNormalizationAndControlledOneEditMatching():void
    {self::assertTrue(class_exists(CatalogSearch::class));self::assertSame('igdir sisli cesme',CatalogSearch::normalize('IĞDIR ŞİŞLİ ÇEŞME'));self::assertTrue(CatalogSearch::oneEdit('saten','sateen'));self::assertTrue(CatalogSearch::oneEdit('saten','saten'));self::assertTrue(CatalogSearch::oneEdit('saten','staen'));self::assertFalse(CatalogSearch::oneEdit('saten','satenli'));}
    public function testServerSearchRanksTypoAndCodeWithoutChangingOriginalName():void
    {$f=new TestDatabase();$x=new Fixtures($f->db,$f->config);$x->policies();$x->catalog(new Principal('admin','admin',true));$c=new Catalog($f->db,$f->config);self::assertSame('saten-bag-detayi',$c->search(['q'=>'sateen'])['rows'][0]['slug']??null);self::assertSame(1,$c->search(['q'=>'TEST01'])['total']);self::assertSame('Saten Bağ Detayı',$c->search(['q'=>'saten'])['rows'][0]['name']);}
    public function testCategoryTreeIncludesDescendantsAndRejectsCycles():void
    {self::assertTrue(class_exists(CatalogPresentation::class));$f=new TestDatabase();$x=new Fixtures($f->db,$f->config);$x->policies();$x->catalog(new Principal('admin','admin',true));$a=new Principal('admin','admin',true);$p=new CatalogPresentation($f->db,$f->config);$p->category(['slug'=>'koleksiyon','name'=>'Koleksiyon','nameEn'=>'Collection','parent'=>null,'sortOrder'=>1],$a);$p->category(['slug'=>'ic-giyim','name'=>'İç Giyim','nameEn'=>'Lingerie','parent'=>'koleksiyon','sortOrder'=>2],$a);$c=new Catalog($f->db,$f->config);self::assertSame(3,$c->search(['category'=>'koleksiyon'])['total']);try{$p->category(['slug'=>'koleksiyon','name'=>'Koleksiyon','nameEn'=>'Collection','parent'=>'ic-giyim','sortOrder'=>1],$a);self::fail('Cycle accepted');}catch(RuleViolation $e){self::assertSame('CATEGORY_CYCLE',$e->rule);}}
    public function testBulkAvailabilityUsesCanonicalWarehouseAndSameMatchingVariant():void
    {self::assertTrue(class_exists(Availability::class));$f=new TestDatabase();$x=new Fixtures($f->db,$f->config);$x->policies();$x->catalog(new Principal('admin','admin',true));$ids=array_column($f->db->all('SELECT id FROM variants'),'id');$bulk=(new Availability($f->db,$f->config))->many($ids);$inventory=new Inventory($f->db,$f->config);foreach($ids as $id)self::assertSame($inventory->warehouse($id),$bulk[$id]);$v=$f->db->one("SELECT id,product_id FROM variants WHERE sku='TEST-01'");$f->db->execute('UPDATE inventory_balance SET on_hand=0 WHERE variant_id=?',[$v['id']]);$f->db->execute("UPDATE variants SET color='Bordo' WHERE id=?",[$v['id']]);$other='other-'.bin2hex(random_bytes(4));$f->db->execute("INSERT INTO variants(id,product_id,sku,name,price_minor,color) VALUES(?,?,?,'Alternatif',14900,'Krem')",[$other,$v['product_id'],$other]);$f->db->execute("INSERT INTO inventory_balance(variant_id,warehouse_id,on_hand) VALUES(?,'main',5)",[$other]);self::assertSame(0,(new Catalog($f->db,$f->config))->search(['color'=>'Bordo','available'=>'1'])['total']);}
}
