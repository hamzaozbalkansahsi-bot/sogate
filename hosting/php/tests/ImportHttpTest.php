<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/ImportHttpTest.php
 * Açıklama   : Native dosya yükleme, CSRF ve önizleme sayfasının gerçek HTTP kabulü.
 */
declare(strict_types=1);
require_once __DIR__.'/TestDatabase.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{Fixtures,Kernel};
use Symfony\Component\HttpFoundation\{Request,File\UploadedFile};
use Symfony\Component\HttpFoundation\Session\Session;
use Symfony\Component\HttpFoundation\Session\Storage\MockArraySessionStorage;
final class ImportHttpTest extends TestCase
{
    public function testNativeUploadRequiresCsrfAndRendersAnOwnedPreview():void
    {
        $f=new TestDatabase();(new Fixtures($f->db,$f->config))->policies();$f->db->execute("INSERT INTO `user`(id,name,email,emailVerified,role,twoFactorEnabled) VALUES('catalog-user','Katalog','import@example.invalid',true,'catalog',true)");$session=new Session(new MockArraySessionStorage());foreach(['user_id'=>'catalog-user','epoch'=>0,'mfa'=>true,'auth_at'=>time(),'last_seen'=>time()] as $key=>$value)$session->set($key,$value);$k=new Kernel($f->db,$f->config,$session);
        $r=$k->handle(Request::create('http://127.0.0.1:3183/test/yonetim/ice-aktarim'));self::assertSame(200,$r->getStatusCode());self::assertStringContainsString('multipart/form-data',$r->getContent());
        $file=tempnam(sys_get_temp_dir(),'sg-upload-');file_put_contents($file,"sku;name;nameEn;slug;category;variantName;price;image\nUPLOAD-1;İç Giyim;Lingerie;upload-one;ic-giyim;Bordo;149,50;/media/atelier-01.svg\n");
        try{$request=fn($csrf)=>Request::create('http://127.0.0.1:3183/test/api/admin/import-upload','POST',['_csrf'=>$csrf],[],['file'=>new UploadedFile($file,'ürünler.csv','text/csv',null,true)],['HTTP_ORIGIN'=>'http://127.0.0.1:3183']);self::assertSame(403,$k->handle($request('bad'))->getStatusCode());$csrf=json_decode($k->handle(Request::create('http://127.0.0.1:3183/test/api/session'))->getContent(),true)['csrfToken'];$result=$k->handle($request($csrf));self::assertSame(303,$result->getStatusCode());$preview=$k->handle(Request::create('http://127.0.0.1:3183'.$result->headers->get('Location')));self::assertSame(200,$preview->getStatusCode());self::assertStringContainsString('UPLOAD-1',$preview->getContent());self::assertStringContainsString('Taslak ürünleri oluştur',$preview->getContent());}finally{unlink($file);}
    }
}
