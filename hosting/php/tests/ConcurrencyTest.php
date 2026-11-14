<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/ConcurrencyTest.php
 * Açıklama   : İki bağımsız PHP bağlantısıyla son-adet ve yinelenen ödeme yarışını sınar.
 */
declare(strict_types=1);
require_once __DIR__.'/TestDatabase.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{Config,Database,Fixtures,Principal,Catalog,Inventory,Cart,Commerce};
final class ConcurrencyTest extends TestCase
{
    private function race(TestDatabase $f,array $inputs):array
    {
        $barrier=dirname(__DIR__,3).'/.local/php-race-'.bin2hex(random_bytes(12));$processes=[];
        $config=[];foreach(['env','secret','payment_provider','base_path','app_url','db_dsn','db_user','db_password'] as $key)$config[$key]=$f->config->get($key);
        try{foreach($inputs as $data){$pipes=[];$p=proc_open([PHP_BINARY,'tests/race-worker.php'],[0=>['pipe','r'],1=>['pipe','w'],2=>['pipe','w']],$pipes,null,array_merge(getenv(),['SEXOGATE_RACE'=>json_encode($data+['barrier'=>$barrier,'config'=>$config],JSON_THROW_ON_ERROR)]),['bypass_shell'=>true]);if(!is_resource($p))throw new RuntimeException('WORKER_START_FAILED');fclose($pipes[0]);$processes[]=[$p,$pipes];}file_put_contents($barrier,'go');$results=[];foreach($processes as [$p,$pipes]){$raw=stream_get_contents($pipes[1]);fclose($pipes[1]);$stderr=stream_get_contents($pipes[2]);fclose($pipes[2]);file_put_contents(dirname(__DIR__,3).'/.local/php-race-stderr.txt',$stderr);self::assertSame(0,proc_close($p),$raw);$results[]=json_decode($raw,true,32,JSON_THROW_ON_ERROR);}return $results;}finally{if(is_file($barrier))unlink($barrier);}
    }
    public function testTwoProcessesCannotSellTheLastUnitTwice():void
    {
        $f=new TestDatabase();$fixtures=new Fixtures($f->db,$f->config);$fixtures->policies();$a=new Principal('fixture-admin','admin',true);$catalog=new Catalog($f->db,$f->config);$p=$catalog->create(['name'=>'Son adet','nameEn'=>'Last unit','slug'=>'last-unit','category'=>'ic-giyim','sku'=>'LAST','variantName'=>'Bordo','priceMinor'=>10000,'image'=>'/media/atelier-01.svg','fixture'=>true],$a);(new Inventory($f->db,$f->config))->receive($p['variantId'],1,'Test kabulü',bin2hex(random_bytes(16)),$a);$catalog->approve($p['id'],'TR',$a);
        $c=new Commerce($f->db,$f->config);$inputs=[];foreach([1,2] as $n){$token=bin2hex(random_bytes(32));(new Cart($f->db,$f->config))->set($token,$p['variantId'],1);$input=['email'=>'race@example.invalid','fullName'=>'Hamza ÖZBALKAN','phone'=>'05000000000','line1'=>'Şişli Çeşme adresi','city'=>'İstanbul','postalCode'=>'34000','country'=>'TR','currency'=>'TRY','locale'=>'tr','privacyAccepted'=>true,'termsAccepted'=>true,'idempotencyKey'=>bin2hex(random_bytes(16)),'couponCode'=>''];$input['quoteToken']=$c->quote($token,$input)['quoteToken'];$inputs[]=['mode'=>'checkout','token'=>$token,'input'=>$input];}
        $r=$this->race($f,$inputs);self::assertCount(1,array_filter($r,fn($r)=>$r['ok']));self::assertSame(1,(int)$f->db->one("SELECT COALESCE(SUM(quantity),0) n FROM reservations WHERE status='active'")['n']);self::assertSame(1,(int)$f->db->one('SELECT COUNT(*) n FROM orders')['n']);
    }
    public function testTwoProcessesConsumeOneSignedPaymentOnlyOnce():void
    {
        $f=new TestDatabase();$fixtures=new Fixtures($f->db,$f->config);$fixtures->policies();$a=new Principal('fixture-admin','admin',true);$fixtures->catalog($a);$v=$f->db->one("SELECT id FROM variants WHERE sku='TEST-01'")['id'];$token=bin2hex(random_bytes(32));(new Cart($f->db,$f->config))->set($token,$v,1);$input=['email'=>'race@example.invalid','fullName'=>'Hamza ÖZBALKAN','phone'=>'05000000000','line1'=>'Şişli Çeşme adresi','city'=>'İstanbul','postalCode'=>'34000','privacyAccepted'=>true,'termsAccepted'=>true,'idempotencyKey'=>bin2hex(random_bytes(16))];$c=new Commerce($f->db,$f->config);$input['quoteToken']=$c->quote($token,$input)['quoteToken'];$o=$c->checkout($token,$input);$event=$c->testEvent($o['orderId'],$o['trackingToken'],'succeeded');$e=['mode'=>'payment']+$event;$r=$this->race($f,[$e,$e]);self::assertCount(2,array_filter($r,fn($r)=>$r['ok']));self::assertCount(1,array_filter($r,fn($r)=>$r['duplicate']===true));self::assertSame(1,(int)$f->db->one("SELECT COUNT(*) n FROM inventory_movements WHERE type='sale'")['n']);self::assertSame(9,(int)$f->db->one('SELECT on_hand FROM inventory_balance WHERE variant_id=?',[$v])['on_hand']);
    }
}
