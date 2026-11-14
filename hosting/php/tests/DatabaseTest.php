<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/DatabaseTest.php
 * Açıklama   : PDO transaction, gerçek migration ve bozuk geçmiş engelini sınar.
 */
declare(strict_types=1);
require_once __DIR__.'/TestDatabase.php';
use PHPUnit\Framework\TestCase;
use Sexogate\Migrations;
final class DatabaseTest extends TestCase
{
    public function testCompoundSqlParserPreservesQuotesAndRejectsUnfinishedSql():void
    {
        $sql="-- kaynak\nCREATE TABLE x(id TEXT);\nDELIMITER $$\nCREATE TRIGGER t BEFORE INSERT ON x FOR EACH ROW BEGIN SET NEW.id='a;b'; END$$\nDELIMITER ;\n";
        self::assertCount(2,Migrations::split($sql));
        $this->expectException(RuntimeException::class);Migrations::split("SELECT 'unfinished");
    }
    public function testRealSchemaMigratesIdempotentlyAndRollbackPreservesUnicode():void
    {
        $f=new TestDatabase();$dir=dirname(__DIR__,3).'/migrations/mysql';$before=$f->db->all('SELECT name,checksum FROM schema_migrations ORDER BY name');
        (new Migrations($f->db))->apply($dir);self::assertSame($before,$f->db->all('SELECT name,checksum FROM schema_migrations ORDER BY name'));
        try{$f->db->transaction(function($db){$db->execute("INSERT INTO settings(`key`,value) VALUES('rollback',?)",[json_encode('Hamza ÖZBALKAN İstanbul Iğdır Şişli')]);throw new LogicException('expected rollback');});}catch(LogicException){}
        self::assertNull($f->db->one("SELECT value FROM settings WHERE `key`='rollback'"));
        $this->expectException(PDOException::class);$f->db->transaction(fn($db)=>$db->execute("INSERT INTO settings(`key`,value) VALUES('readonly','true')"),true);
    }
    public function testChangedMigrationHistoryBlocksInsteadOfRepairingSilently():void
    {
        $f=new TestDatabase();$f->db->execute("UPDATE schema_migrations SET checksum=REPEAT('0',64) WHERE name='001_auth.sql'");
        $this->expectExceptionMessage('MIGRATION_HISTORY_CHANGED');(new Migrations($f->db))->apply(dirname(__DIR__,3).'/migrations/mysql');
    }
}
