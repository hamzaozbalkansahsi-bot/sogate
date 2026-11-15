<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/SourceCatalogTest.php
 * Açıklama   : Gerçek kaynak inceleme aktarımının canlı katalog ve depo stoğundan ayrılması.
 */
declare(strict_types=1);
require_once __DIR__.'/TestDatabase.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{SourceCatalog,Principal,RuleViolation};
final class SourceCatalogTest extends TestCase
{
    public function testImportIsIdempotentAndNeverPublishesOrCreatesWarehouseStock():void
    {self::assertTrue(class_exists(SourceCatalog::class));$f=new TestDatabase();$s=new SourceCatalog($f->db,$f->config);$file=tempnam(sys_get_temp_dir(),'sx-source-');file_put_contents($file,json_encode(['vendor'=>'liona','kind'=>'product','sourceUrl'=>'https://www.liona.com.tr/olcu.html','title'=>'İç Giyim · Ölçü','sku'=>'GERÇEK-01','images'=>[],'metadataState'=>'parsed','quotedRetailMinor'=>19990,'quotedCurrency'=>'TRY','supplierQuantity'=>null],JSON_UNESCAPED_UNICODE)."\n");try{$a=new Principal('admin','admin',true);$key=bin2hex(random_bytes(16));$r=$s->import($file,'liona',$key,$a);self::assertSame(1,$r['productCount']);self::assertEquals($r,$s->import($file,'liona',$key,$a));self::assertSame(1,(int)$f->db->one('SELECT COUNT(*) n FROM source_catalog_batches')['n']);self::assertSame(0,(int)$f->db->one('SELECT COUNT(*) n FROM products')['n']);self::assertSame(0,(int)$f->db->one('SELECT COUNT(*) n FROM inventory_balance')['n']);self::assertSame('İç Giyim · Ölçü',$s->records($r['id'],[], $a)['rows'][0]['title']);$this->expectException(RuleViolation::class);$s->records($r['id'],[],new Principal('warehouse','warehouse',true));}finally{unlink($file);}}
    public function testExternalAndPrivateSourceUrlsAreRejected():void
    {self::assertTrue(class_exists(SourceCatalog::class));$f=new TestDatabase();$file=tempnam(sys_get_temp_dir(),'sx-source-');file_put_contents($file,json_encode(['vendor'=>'liona','kind'=>'product','sourceUrl'=>'http://127.0.0.1/private','title'=>'Yanlış','metadataState'=>'indexed'])."\n");try{$this->expectException(RuleViolation::class);(new SourceCatalog($f->db,$f->config))->import($file,'liona',bin2hex(random_bytes(16)),new Principal('admin','admin',true));}finally{unlink($file);}}
    public function testCompressedCategoryAndProductKeepUtf8AndRejectInventedSupplierStockAtomically():void
    {$f=new TestDatabase();$s=new SourceCatalog($f->db,$f->config);$a=new Principal('admin','admin',true);$category=['vendor'=>'sistina','kind'=>'category','sourceUrl'=>'https://sistinaicgiyim.com.tr/kadin','title'=>'Kadın · İç Giyim','images'=>[],'metadataState'=>'parsed','supplierQuantity'=>null];$product=$category+[];$product['kind']='product';$product['sourceUrl']='https://sistinaicgiyim.com.tr/olcu';$product['title']='Ölçü ve Özellikler';$file=tempnam(sys_get_temp_dir(),'sx-source-');try{file_put_contents($file,gzencode(json_encode($category,JSON_UNESCAPED_UNICODE)."\n".json_encode($product,JSON_UNESCAPED_UNICODE)."\n"));$r=$s->import($file,'sistina',bin2hex(random_bytes(16)),$a);self::assertSame(1,$r['categoryCount']);self::assertSame(1,$r['productCount']);self::assertSame(2,$r['parsedCount']);self::assertSame('Kadın · İç Giyim',$s->records($r['id'],['kind'=>'category'],$a)['rows'][0]['title']);$product['supplierQuantity']=999;file_put_contents($file,gzencode(json_encode($category)."\n".json_encode($product)."\n"));try{$s->import($file,'sistina',bin2hex(random_bytes(16)),$a);self::fail('Public availability became authoritative quantity');}catch(RuleViolation $e){self::assertSame('SOURCE_STOCK_NOT_CONFIRMED',$e->rule);}self::assertSame(1,(int)$f->db->one('SELECT COUNT(*) n FROM source_catalog_batches')['n']);self::assertSame(0,(int)$f->db->one('SELECT COUNT(*) n FROM categories')['n']);}finally{unlink($file);}}
}
