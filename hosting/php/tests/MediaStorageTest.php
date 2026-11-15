<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/MediaStorageTest.php
 * Açıklama   : Görsel yükleme, özel önizleme, yayın bağlantısı ve etkin içerik reddi.
 */
declare(strict_types=1);
require_once __DIR__.'/TestDatabase.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{MediaStorage,Fixtures,Principal,RuleViolation,Config,CatalogPresentation};
final class MediaStorageTest extends TestCase
{
    public function testActiveSvgUploadIsRejected():void
    {self::assertTrue(class_exists(MediaStorage::class));$f=new TestDatabase();$this->expectException(RuleViolation::class);(new MediaStorage($f->db,$f->config))->upload('<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>','Owned test image',new Principal('admin','admin',true));}
    public function testPrivateStorageBecomesReadableOnlyThroughPublishedProduct():void
    {self::assertTrue(class_exists(MediaStorage::class));$f=new TestDatabase();$x=new Fixtures($f->db,$f->config);$x->policies();$x->catalog(new Principal('admin','admin',true));$root=sys_get_temp_dir().'/sexogate-media-'.bin2hex(random_bytes(8));$c=new Config(['env'=>'test','secret'=>str_repeat('m',40),'payment_provider'=>'test','app_url'=>'http://127.0.0.1:3183/test','base_path'=>'/test','media_root'=>$root]);$m=new MediaStorage($f->db,$c);$image=imagecreatetruecolor(20,30);ob_start();imagepng($image);$raw=ob_get_clean();$a=new Principal('admin','admin',true);$result=$m->upload($raw,'Original synthetic test fixture',$a);try{self::assertSame(20,$result['width']);self::assertSame(30,$result['height']);try{$m->response(basename($result['path']),null);self::fail('Unpublished media leaked');}catch(RuleViolation $e){self::assertSame(404,$e->getCode()?:$e->status);} $p=$f->db->one("SELECT id FROM products WHERE slug='saten-bag-detayi'");(new CatalogPresentation($f->db,$c))->media(['productId'=>$p['id'],'path'=>$result['path'],'altTr'=>'Ölçü ve Özellikler','altEn'=>'Measurements and details','rightsReference'=>'Owned test fixture','key'=>bin2hex(random_bytes(16))],$a);self::assertSame(200,$m->response(basename($result['path']),null)->getStatusCode());self::assertStringStartsWith('RIFF',file_get_contents($root.'/'.basename($result['path'])));}finally{foreach(glob($root.'/*')?:[] as $file)unlink($file);if(is_dir($root))rmdir($root);}}
}
