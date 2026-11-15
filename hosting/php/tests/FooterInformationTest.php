<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/FooterInformationTest.php
 * Açıklama   : Gerçek footer hedefleri, ayrı hukuk taslakları ve iletişim veri minimizasyonu.
 */
declare(strict_types=1);
require_once __DIR__.'/TestDatabase.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{Fixtures,Kernel,Config};
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Session\{Session,Storage\MockArraySessionStorage};
final class FooterInformationTest extends TestCase
{
    private function kernel(TestDatabase $f):Kernel
    {(new Fixtures($f->db,$f->config))->policies();return new Kernel($f->db,$f->config,new Session(new MockArraySessionStorage()));}
    public function testFooterTargetsOpenAndLegalDraftsDoNotPretendToBeApproved():void
    {$f=new TestDatabase();$k=$this->kernel($f);$home=$k->handle(Request::create('/test/'))->getContent();foreach(['/site-haritasi','/blog','/iletisim','/yasal/kvkk','/yasal/gizlilik','/yasal/mesafeli-satis','/yasal/iade','/yasal/cerez','/yasal/teslimat'] as $path){self::assertStringContainsString('/test'.$path,$home);$r=$k->handle(Request::create('/test'.$path));self::assertSame(200,$r->getStatusCode(),$path);if(str_starts_with($path,'/yasal/'))self::assertStringContainsString('İnceleme taslağı',$r->getContent());}self::assertStringContainsString('61596759171927',$home);self::assertStringContainsString('mailto:info@sexogate.com',$home);self::assertStringNotContainsString('PTYS Technoligess',$home);}
    public function testReturnPolicyPreservesDefectiveGoodsRightsAndNoSellerIsInvented():void
    {$f=new TestDatabase();$k=$this->kernel($f);$html=$k->handle(Request::create('/test/yasal/iade'))->getContent();self::assertStringContainsString('mührü açılmış',$html);self::assertStringContainsString('Ayıplı',$html);self::assertStringNotContainsString('hiçbir şekilde iade',$html);$contact=$k->handle(Request::create('/test/iletisim'))->getContent();self::assertStringNotContainsString('05000000000',$contact);$f->db->execute("INSERT INTO settings(`key`,value) VALUES('seller.bankAccount',?)",[json_encode('PRIVATE-BANK-REFERENCE')]);self::assertStringNotContainsString('PRIVATE-BANK-REFERENCE',$k->handle(Request::create('/test/'))->getContent());}
    public function testEnglishInformationAndPublishedBlogAreReadable():void
    {$f=new TestDatabase();$k=$this->kernel($f);foreach(['/en/site-haritasi','/en/blog','/en/yasal/kvkk','/en/yasal/iade'] as $path)self::assertSame(200,$k->handle(Request::create('/test'.$path))->getStatusCode());$a=new \Sexogate\Principal('admin','admin',true);$c=new \Sexogate\Content($f->db,$f->config);$e=$c->save(['kind'=>'guide','locale'=>'tr','slug'=>'bakim-rehberi','title'=>'Ürün bakım rehberi','body'=>'Üreticinin bakım talimatlarını izleyin.'],$a);$c->publish($e['id'],$a);self::assertStringContainsString('Ürün bakım rehberi',$k->handle(Request::create('/test/blog'))->getContent());}
    public function testFooterNoticeUsesTheSameDocumentKindAsCheckoutAndPrivacyPolicyStaysSeparate():void
    {$f=new TestDatabase();$k=$this->kernel($f);foreach(['privacy'=>'Yürürlükte aydınlatma','privacy-policy'=>'Yürürlükte gizlilik'] as $kind=>$title){$body='Bu metin yalnız izole otomatik test içindir.';$f->db->execute("INSERT INTO legal_documents(kind,locale,version,title,body,body_hash,status,fixture,effective_at) VALUES(?,'tr',2,?,?,?,'effective',false,'2020-01-01')",[$kind,$title,$body,hash('sha256',$body)]);}self::assertStringContainsString('Yürürlükte aydınlatma',$k->handle(Request::create('/test/yasal/kvkk'))->getContent());self::assertStringContainsString('Yürürlükte gizlilik',$k->handle(Request::create('/test/yasal/gizlilik'))->getContent());}
}
