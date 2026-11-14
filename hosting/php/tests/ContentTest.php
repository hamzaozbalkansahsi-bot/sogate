<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/ContentTest.php
 * Açıklama   : Taslak/yayın sürümleri, çeviri ve değişmez hukuk onay akışı.
 */
declare(strict_types=1);
require_once __DIR__.'/TestDatabase.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{Content,Fixtures,Principal,RuleViolation};
final class ContentTest extends TestCase
{
    public function testPublishedDetailRemainsReachableAfterTheFirstHundredItems():void
    {$f=new TestDatabase();$content=new Content($f->db,$f->config);$actor=new Principal('admin','admin',true);for($i=0;$i<101;$i++){$row=$content->save(['kind'=>'guide','slug'=>'rehber-'.$i,'locale'=>'tr','title'=>'Rehber '.$i,'body'=>'Ölçü ve Özellikler'],$actor);$content->publish($row['id'],$actor);}$f->db->execute("UPDATE content_publications p JOIN content_entries e ON e.id=p.entry_id SET p.publish_at='2020-01-01' WHERE e.slug='rehber-0'");self::assertSame('Rehber 0',$content->find('guide','rehber-0','tr')['title']??null);}
    public function testDraftNeverReplacesPublishedContentUntilExplicitPublication():void
    {$f=new TestDatabase();self::assertTrue(class_exists(Content::class),'PHP içerik yönetimi eksik.');$c=new Content($f->db,$f->config);$a=new Principal('admin','admin',true);$first=$c->save(['kind'=>'guide','slug'=>'bakim-rehberi','locale'=>'tr','title'=>'Bakım rehberi','summary'=>'Ölçü ve Özellikler','body'=>'Şişli Çeşme Iğdır ıİiIşŞğĞüÜöÖçÇ'],$a);self::assertNull($c->find('guide','bakim-rehberi','tr'));$c->publish($first['id'],$a);self::assertSame('Bakım rehberi',$c->find('guide','bakim-rehberi','tr')['title']);$c->save(['id'=>$first['id'],'kind'=>'guide','slug'=>'bakim-rehberi','locale'=>'tr','title'=>'Yeni taslak','summary'=>'','body'=>'Taslak metin'],$a);self::assertSame('Bakım rehberi',$c->find('guide','bakim-rehberi','tr')['title']);$c->publish($first['id'],$a);self::assertSame('Yeni taslak',$c->find('guide','bakim-rehberi','tr')['title']);self::assertNull($c->find('guide','bakim-rehberi','en'));}
    public function testPastContentRevisionCannotBeOverwritten():void
    {$f=new TestDatabase();self::assertTrue(class_exists(Content::class),'PHP içerik yönetimi eksik.');$c=new Content($f->db,$f->config);$a=new Principal('admin','admin',true);$r=$c->save(['kind'=>'faq','slug'=>'kargo','locale'=>'tr','title'=>'Kargo','summary'=>'','body'=>'Teslimat ülkesi ve taşıyıcı kabulüne bağlıdır.'],$a);$c->publish($r['id'],$a);$this->expectException(PDOException::class);$f->db->execute('UPDATE content_revisions SET body=? WHERE entry_id=?',['değişti',$r['id']]);}
    public function testLegalApprovalCannotUseMissingSellerOrMarketingRole():void
    {$f=new TestDatabase();self::assertTrue(class_exists(Content::class),'PHP içerik yönetimi eksik.');$c=new Content($f->db,$f->config);$a=new Principal('admin','admin',true);$r=$c->legalDraft('privacy','tr','Aydınlatma taslağı','Gerçek işletme bilgileri tamamlanmalıdır.',$a);try{$c->approveLegal($r['id'],'Hukuk inceleme referansı2026',$a);self::fail('Satıcısız onay verildi.');}catch(RuleViolation){}$this->expectException(RuleViolation::class);$c->legalDraft('privacy','tr','Başlık','Metin',new Principal('pazarlama','marketing',true));}
    public function testVerifiedSellerDraftCanBeApprovedAndPublishedWithItsExactVersion():void
    {$f=new TestDatabase();$c=new Content($f->db,$f->config);$a=new Principal('admin','admin',true);foreach(['seller.name','seller.taxNumber','seller.address','seller.supportEmail','seller.phone','seller.bankAccount'] as $key)$f->db->execute('INSERT INTO settings(`key`,value) VALUES(?,?)',[$key,json_encode('İzole test alanı '.$key)]);$r=$c->legalDraft('privacy','tr','KVKK taslağı','Bu metin yalnız test onay akışını doğrular.',$a);$c->approveLegal($r['id'],'TEST hukuk inceleme referansı2026',$a);$result=$c->publishLegal($r['id'],$a);self::assertSame('effective',$result['status']);self::assertSame(1,(int)$f->db->one("SELECT COUNT(*) n FROM legal_documents WHERE kind='privacy' AND locale='tr' AND status='effective'")['n']);}
}
