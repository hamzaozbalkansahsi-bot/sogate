<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/AuthTest.php
 * Açıklama   : Gerçek DB parola, rol, MFA ve oturum iptalini sınar.
 */
declare(strict_types=1);
require_once __DIR__.'/TestDatabase.php';
use PHPUnit\Framework\TestCase;
use Symfony\Component\HttpFoundation\Session\Session;
use Symfony\Component\HttpFoundation\Session\Storage\MockArraySessionStorage;
use Sexogate\{Auth,Principal,RuleViolation};
use OTPHP\TOTP;
final class AuthTest extends TestCase
{
    public function testCustomerSessionPreservesTurkishAndRevokesLogout():void
    {$f=new TestDatabase();$s=new Session(new MockArraySessionStorage());$a=new Auth($f->db,$f->config);$u=$a->register('Hamza ÖZBALKAN','hamza@example.invalid','güvenli-parola-123',$s,'127.0.0.1');self::assertSame('Hamza ÖZBALKAN',$u['user']['name']);self::assertSame('customer',$a->principal($s)->role);$row=$f->db->one('SELECT password_hash FROM `user` WHERE id=?',[$u['user']['id']]);self::assertStringStartsWith('$argon2id$',$row['password_hash']);$a->logout($s);self::assertNull($a->principal($s));}
    public function testAdminMfaIsBoundToSessionAndOldSessionsAreRevoked():void
    {
        $f=new TestDatabase();$a=new Auth($f->db,$f->config);$a->setupAdmin('Yönetici','admin@example.invalid','test-password-123456');$old=new Session(new MockArraySessionStorage());$s=new Session(new MockArraySessionStorage());$a->login('admin@example.invalid','test-password-123456',$old,'127.0.0.1');$a->login('admin@example.invalid','test-password-123456',$s,'127.0.0.1');self::assertFalse($a->principal($s)->mfa);
        try{$a->principal($s)->require('settings');self::fail('password-only admin accepted');}catch(RuleViolation){}
        $setup=$a->beginMfa($s,'test-password-123456');$backup=$a->confirmMfa($s,TOTP::createFromSecret($setup['secret'])->now());self::assertTrue($a->principal($s)->mfa);self::assertCount(8,$backup['recoveryCodes']);self::assertNull($a->principal($old));
        $next=new Session(new MockArraySessionStorage());self::assertTrue($a->login('admin@example.invalid','test-password-123456',$next,'127.0.0.1')['mfaRequired']);self::assertNull($a->principal($next));$a->verifyLoginMfa($next,TOTP::createFromSecret($setup['secret'])->now(),'127.0.0.1');self::assertTrue($a->principal($next)->mfa);
    }
    public function testFiveWrongAttemptsArePersistentlyRateLimited():void
    {$f=new TestDatabase();$a=new Auth($f->db,$f->config);$s=new Session(new MockArraySessionStorage());for($i=0;$i<5;$i++)try{$a->login('absent@example.invalid','wrong',$s,'192.0.2.1');}catch(RuleViolation $e){self::assertSame(401,$e->status);}$this->expectExceptionMessage('Çok fazla deneme');$a->login('absent@example.invalid','wrong',$s,'192.0.2.1');}
    public function testTotpCannotBeReplayedForAnotherLogin():void
    {
        $f=new TestDatabase();$a=new Auth($f->db,$f->config);$id=$a->setupAdmin('Yönetici','admin@example.invalid','test-password-123456');$s=new Session(new MockArraySessionStorage());$a->login('admin@example.invalid','test-password-123456',$s,'127.0.0.1');$setup=$a->beginMfa($s,'test-password-123456');$code=TOTP::createFromSecret($setup['secret'])->now();$a->confirmMfa($s,$code);
        $stored=$f->db->one('SELECT php_totp_secret FROM `user` WHERE id=?',[$id]);self::assertStringNotContainsString($setup['secret'],$stored['php_totp_secret']);
        $next=new Session(new MockArraySessionStorage());$a->login('admin@example.invalid','test-password-123456',$next,'127.0.0.1');$a->verifyLoginMfa($next,$code,'127.0.0.1');$again=new Session(new MockArraySessionStorage());$a->login('admin@example.invalid','test-password-123456',$again,'127.0.0.1');$this->expectException(RuleViolation::class);$a->verifyLoginMfa($again,$code,'127.0.0.1');
    }
}
