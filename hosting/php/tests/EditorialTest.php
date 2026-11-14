<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/EditorialTest.php
 * Açıklama   : Yayımlanmış blog araması, konu/ilgili kayıtlar ve güvenli içindekiler.
 */
declare(strict_types=1);
require_once __DIR__.'/TestDatabase.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{Fixtures,Content,Editorial,Principal};
final class EditorialTest extends TestCase
{
    public function testBlogFiltersOnlyPublishedRevisionsAndPreservesTurkish():void
    {$f=new TestDatabase();(new Fixtures($f->db,$f->config))->policies();$c=new Content($f->db,$f->config);$a=new Principal('admin','admin',true);foreach(['bakim','beden','taslak'] as $slug){$r=$c->save(['kind'=>'guide','locale'=>'tr','slug'=>$slug,'title'=>$slug==='bakim'?'Ölçü ve bakım':$slug,'body'=>'İç Giyim ürün bilgileri','metadata'=>['topic'=>$slug==='bakim'?'Bakım':'Seçim']],$a);if($slug!=='taslak')$c->publish($r['id'],$a);}$e=new Editorial($f->db,$f->config);self::assertSame(2,$e->listing('tr')['total']);self::assertSame(1,$e->listing('tr',['q'=>'Ölçü','topic'=>'Bakım'])['total']);self::assertSame('bakim',$e->listing('tr',['topic'=>'Bakım'])['rows'][0]['slug']);}
    public function testArticleBuildsStableTocAndNeverTreatsHtmlAsTrusted():void
    {$f=new TestDatabase();(new Fixtures($f->db,$f->config))->policies();$c=new Content($f->db,$f->config);$a=new Principal('admin','admin',true);$r=$c->save(['kind'=>'guide','locale'=>'tr','slug'=>'olcu-rehberi','title'=>'Ölçü rehberi','body'=>"Giriş paragrafı.\n\n## Beden seçimi\n<script>alert(1)</script>\n\n## Üretici bilgisi\nGerçek ölçü tablosunu inceleyin."],$a);$c->publish($r['id'],$a);$e=new Editorial($f->db,$f->config);$p=$e->article('olcu-rehberi','tr');self::assertCount(3,$p['sections']);self::assertSame('Beden seçimi',$p['sections'][1]['title']);self::assertSame($p['sections'][1]['id'],$e->article('olcu-rehberi','tr')['sections'][1]['id']);self::assertStringContainsString('<script>',$p['sections'][1]['paragraphs'][0]);}
}
