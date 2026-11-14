<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/TestDatabase.php
 * Açıklama   : Yalnız projenin yerel MySQL'inde rastgele izole test DB'si oluşturur ve temizler.
 */
declare(strict_types=1);
use Sexogate\Config;
use Sexogate\Database;
use Sexogate\Migrations;
final class TestDatabase
{
    public readonly Database $db;public readonly Config $config;private readonly PDO $control;private readonly string $name;
    public function __construct(?string $migrationDirectory=null)
    {
        $parts=parse_url(getenv('MYSQL_TEST_ADMIN_URL')?:'');
        if(($parts['host']??'')!=='127.0.0.1'||($parts['port']??0)!==55433)throw new RuntimeException('LOCAL_MYSQL_TEST_ONLY');
        $this->name='sexogate_php_'.bin2hex(random_bytes(8)).'_test';$dsn='mysql:host=127.0.0.1;port=55433;dbname=';$user=rawurldecode($parts['user']);$password=rawurldecode($parts['pass']);
        $this->control=new PDO($dsn.'mysql;charset=utf8mb4',$user,$password,[PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION]);
        $this->control->exec('CREATE DATABASE `'.$this->name.'` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci');
        $this->config=new Config(['env'=>'test','secret'=>bin2hex(random_bytes(32)),'payment_provider'=>'test','base_path'=>'/test','app_url'=>'http://127.0.0.1:3183/test','db_dsn'=>$dsn.$this->name.';charset=utf8mb4','db_user'=>$user,'db_password'=>$password]);
        $this->db=new Database($this->config);(new Migrations($this->db))->apply($migrationDirectory??dirname(__DIR__,3).'/migrations/mysql');
    }
    public function __destruct()
    {
        if(!isset($this->control,$this->name))return;
        if(isset($this->db)&&$this->db->pdo->inTransaction())$this->db->pdo->rollBack();
        if(!preg_match('/\Asexogate_php_[a-f0-9]{16}_test\z/',$this->name))return;
        $this->control->exec('DROP DATABASE IF EXISTS `'.$this->name.'`');
    }
}
