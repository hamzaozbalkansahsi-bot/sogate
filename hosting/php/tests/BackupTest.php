<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/BackupTest.php
 * Açıklama   : Gerçek DB yedeği, UTF-8, şifreli bütünlük ve yeni DB'ye geri yükleme testi.
 */
declare(strict_types=1);
require_once __DIR__.'/TestDatabase.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{Backup,Fixtures,Auth,Principal,RuleViolation};
final class BackupTest extends TestCase
{
    public function testEncryptedSnapshotRestoresCatalogStockUnicodeAndSchema():void
    {$source=new TestDatabase();$fixtures=new Fixtures($source->db,$source->config);$fixtures->policies();$id=(new Auth($source->db,$source->config))->setupAdmin('Hamza ÖZBALKAN','backup@example.invalid','Backup-pass-ıİşŞğĞ2026');$fixtures->catalog(new Principal($id,'admin',true));$snapshot=(new Backup($source->db,$source->config))->snapshot();$key=random_bytes(32);$archive=Backup::encrypt($snapshot,$key);self::assertStringNotContainsString('ÖZBALKAN',$archive);$target=new TestDatabase();$r=(new Backup($target->db,$target->config))->restoreLocal(Backup::decrypt($archive,$key));self::assertTrue($r['hashesVerified']);self::assertGreaterThan(50,$r['tables']);self::assertGreaterThan(20,$r['foreignKeys']);self::assertSame('Hamza ÖZBALKAN',$target->db->one('SELECT name FROM `user`')['name']);}
    public function testTamperedBackupIsRejectedBeforeRestore():void
    {$key=random_bytes(32);$archive=Backup::encrypt(['version'=>1],$key);$archive[strlen($archive)-1]=chr(ord($archive[strlen($archive)-1])^1);$this->expectException(RuleViolation::class);Backup::decrypt($archive,$key);}
    public function testHistoricalSchemaBackupCanBeRestoredAndUpgradedWithoutLosingRows():void
    {$root=dirname(__DIR__,3);$folder=$root.'/.local/php-history-test-'.bin2hex(random_bytes(10));mkdir($folder,0700);$archive=$folder.'/snapshot.aesgcm';try{foreach(glob($root.'/migrations/mysql/*.sql') as $file)if((int)basename($file)<=13)copy($file,$folder.'/'.basename($file));$source=new TestDatabase($folder);(new Fixtures($source->db,$source->config))->policies();$snapshot=(new Backup($source->db,$source->config))->snapshot();$key=random_bytes(32);file_put_contents($archive,Backup::encrypt($snapshot,$key));$env=array_merge(getenv(),['SEXOGATE_BACKUP_KEY'=>bin2hex($key),'SEXOGATE_BACKUP_FILE_B64'=>base64_encode($archive)]);$pipes=[];$p=proc_open([PHP_BINARY,'bin/verify-restore.php'],[0=>['pipe','r'],1=>['pipe','w'],2=>['pipe','w']],$pipes,null,$env,['bypass_shell'=>true]);fclose($pipes[0]);$out=stream_get_contents($pipes[1]);$error=stream_get_contents($pipes[2]);fclose($pipes[1]);fclose($pipes[2]);self::assertSame(0,proc_close($p),$error);$result=json_decode($out,true,32,JSON_THROW_ON_ERROR);self::assertSame(13,$result['sourceMigrations']);self::assertTrue($result['hashesVerified']);self::assertTrue($result['forwardMigrationVerified']);self::assertSame(count(glob($root.'/migrations/mysql/*.sql')),$result['currentMigrations']);}finally{foreach(glob($folder.'/*') as $file)unlink($file);rmdir($folder);}}
}
