<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/WorkerTest.php
 * Açıklama   : Kalıcı işte başarı, görünür bağlantı eksiği ve mükerrerlik kontrolü.
 */
declare(strict_types=1);
require_once __DIR__.'/TestDatabase.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{Commerce,Worker,Config,RuleViolation};
final class WorkerTest extends TestCase
{
    public function testDurableExpiryJobCompletesOnlyOnceAndUnconfiguredEmailDefers():void
    {$f=new TestDatabase();$c=new Commerce($f->db,$f->config);$c->enqueue('reservation.expire',[],'expire-one');$c->enqueue('reservation.expire',[],'expire-one');$c->enqueue('order.confirmation',['orderId'=>'unknown'],'email-one');$w=new Worker($f->db,$f->config);$r=$w->tick();self::assertSame(1,$r['completed']);self::assertSame(1,$r['deferred']);self::assertSame('SMTP_NOT_CONFIGURED',$f->db->one("SELECT last_error FROM jobs WHERE dedupe_key='email-one'")['last_error']);self::assertSame(0,$w->tick()['completed']);self::assertSame(1,(int)$f->db->one("SELECT COUNT(*) n FROM jobs WHERE status='completed'")['n']);}
    public function testProductionRejectsTestProvider():void
    {$this->expectException(RuleViolation::class);new Config(['env'=>'production','secret'=>str_repeat('a',64),'base_path'=>'/test','app_url'=>'https://sexogate.com/test','payment_provider'=>'test']);}
    public function testCredentialBearingApplicationUrlIsRejected():void
    {$this->expectException(RuleViolation::class);new Config(['env'=>'production','secret'=>str_repeat('a',64),'base_path'=>'/test','app_url'=>'https://user@sexogate.com/test','payment_provider'=>'stripe']);}
    public function testExhaustedLeaseDoesNotBlockAnotherReadyJobInTheSameTick():void
    {$f=new TestDatabase();$c=new Commerce($f->db,$f->config);$c->enqueue('reservation.expire',[],'exhausted');$c->enqueue('reservation.expire',[],'ready');$f->db->execute("UPDATE jobs SET attempts=max_attempts,status='running',lease_until=DATE_SUB(CURRENT_TIMESTAMP(3),INTERVAL 1 MINUTE),available_at=DATE_SUB(CURRENT_TIMESTAMP(3),INTERVAL 2 MINUTE) WHERE dedupe_key='exhausted'");$result=(new Worker($f->db,$f->config))->tick(5);self::assertSame(1,$result['completed']);self::assertSame('failed',$f->db->one("SELECT status FROM jobs WHERE dedupe_key='exhausted'")['status']);}
}
