<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/ShoppingCartHttpTest.php
 * Açıklama   : Gerçek anonim API eklemesinin mevcut adedi koruması ve özel HTML sepet bölümü.
 */
declare(strict_types=1);
require_once __DIR__.'/TestDatabase.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{Fixtures,Principal,Kernel};
use Symfony\Component\HttpFoundation\{Request,Session\Session,Session\Storage\MockArraySessionStorage};
final class ShoppingCartHttpTest extends TestCase
{
    public function testRepeatedProductAddAccumulatesAndFragmentIsPrivate():void
    {$f=new TestDatabase();$x=new Fixtures($f->db,$f->config);$x->policies();$x->catalog(new Principal('admin','admin',true));$k=new Kernel($f->db,$f->config,new Session(new MockArraySessionStorage()));$r=$k->handle(Request::create('http://127.0.0.1:3183/test/api/session'));$csrf=json_decode($r->getContent(),true)['csrfToken'];$token=$r->headers->getCookies()[0]->getValue();$variant=$f->db->one("SELECT id FROM variants WHERE sku='TEST-01'")['id'];$post=fn($q)=>$k->handle(Request::create('http://127.0.0.1:3183/test/api/cart','POST',[],['sg_cart'=>$token],[],['CONTENT_TYPE'=>'application/json','HTTP_ORIGIN'=>'http://127.0.0.1:3183','HTTP_X_CSRF_TOKEN'=>$csrf],json_encode(['action'=>'add','variantId'=>$variant,'quantity'=>$q])));self::assertSame(200,$post(2)->getStatusCode());self::assertSame(3,json_decode($post(1)->getContent(),true)['items'][0]['quantity']);$r=$k->handle(Request::create('http://127.0.0.1:3183/test/api/cart-fragment','GET',[],['sg_cart'=>$token]));self::assertSame(200,$r->getStatusCode());self::assertStringContainsString('data-revision=',$r->getContent());self::assertStringContainsString('no-store',$r->headers->get('Cache-Control'));}
}
