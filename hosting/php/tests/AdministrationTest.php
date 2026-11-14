<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/AdministrationTest.php
 * Açıklama   : Son yönetici, rol değişiminde oturum iptali ve atomik satıcı ayarları.
 */
declare(strict_types=1);
require_once __DIR__.'/TestDatabase.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{Administration,Principal,RuleViolation};
final class AdministrationTest extends TestCase
{
    public function testLastAdministratorCannotBeDemotedAndRoleChangesRevokeSessions():void
    {$f=new TestDatabase();self::assertTrue(class_exists(Administration::class),'PHP yönetim/rol modülü eksik.');$f->db->execute("INSERT INTO `user`(id,name,email,emailVerified,role,twoFactorEnabled) VALUES('admin-a','Yönetici','admin@example.invalid',true,'admin',true),('staff-b','Depo','staff@example.invalid',true,'warehouse',true)");$a=new Principal('admin-a','admin',true);$s=new Administration($f->db,$f->config);try{$s->role('admin-a','warehouse',$a);self::fail('Son yönetici yetkisi kaldırıldı.');}catch(RuleViolation){}$s->role('staff-b','support',$a);self::assertSame('support',$f->db->one("SELECT role FROM `user` WHERE id='staff-b'")['role']);self::assertSame(1,(int)$f->db->one("SELECT php_session_version FROM `user` WHERE id='staff-b'")['php_session_version']);}
    public function testInvalidSettingCannotLeaveOtherSellerChangesPartiallyWritten():void
    {$f=new TestDatabase();self::assertTrue(class_exists(Administration::class),'PHP yönetim/rol modülü eksik.');$a=new Principal('admin','admin',true);$s=new Administration($f->db,$f->config);try{$s->settings(['seller.name'=>'Hamza ÖZBALKAN','other.secret'=>'izin verilmez'],$a);self::fail('Bilinmeyen ayar kabul edildi.');}catch(RuleViolation){}self::assertSame(0,(int)$f->db->one('SELECT COUNT(*) n FROM settings')['n']);$s->settings(['seller.name'=>'Hamza ÖZBALKAN'],$a);self::assertSame(1,(int)$f->db->one('SELECT COUNT(*) n FROM audit_log')['n']);}
    public function testRetryOnlyAcceptsFailedJobsAndAdvancesGeneration():void
    {$f=new TestDatabase();$a=new Principal('admin','admin',true);(new Sexogate\Commerce($f->db,$f->config))->enqueue('unconfigured',[],'test-retry');$id=$f->db->one('SELECT id FROM jobs')['id'];$service=new Administration($f->db,$f->config);try{$service->retryJob($id,$a);self::fail('Bekleyen iş yeniden sıfırlandı.');}catch(RuleViolation){}$f->db->execute("UPDATE jobs SET status='failed',attempts=5 WHERE id=?",[$id]);$service->retryJob($id,$a);$row=$f->db->one('SELECT status,attempts,generation FROM jobs');self::assertSame(['pending',0,1],[$row['status'],(int)$row['attempts'],(int)$row['generation']]);}
}
