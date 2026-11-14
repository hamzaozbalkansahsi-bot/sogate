<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/bin/setup-local.php
 * Açıklama   : Ayrı yerel PHP önizleme DB'sini sırları yazdırmadan kurar.
 */
declare(strict_types=1);
if(PHP_SAPI!=='cli')exit(1);
require dirname(__DIR__).'/vendor/autoload.php';
use Sexogate\{Config,Database,Migrations,Fixtures,Auth,Principal};
$root=dirname(__DIR__,3);$file=dirname(__DIR__).'/config.local.json';
try{
    if(!is_file($file)){
        $u=parse_url(getenv('MYSQL_TEST_ADMIN_URL')?:'');if(($u['host']??'')!=='127.0.0.1'||($u['port']??0)!==55433)throw new RuntimeException('LOCAL_ONLY');
        $pdo=new PDO('mysql:host=127.0.0.1;port=55433;charset=utf8mb4',rawurldecode($u['user']),rawurldecode($u['pass']),[PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION]);
        $name='sexogate_php_preview_test';if($pdo->query("SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='$name'")->fetch())throw new RuntimeException('UNOWNED_DATABASE');
        $password=bin2hex(random_bytes(32));$pdo->exec("CREATE DATABASE `$name` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci");$pdo->exec("CREATE USER 'sg_php_preview'@'127.0.0.1' IDENTIFIED BY ".$pdo->quote($password));$pdo->exec("GRANT ALL ON `$name`.* TO 'sg_php_preview'@'127.0.0.1'");
        $values=['env'=>'test','secret'=>bin2hex(random_bytes(32)),'payment_provider'=>'test','base_path'=>'/test','app_url'=>'http://127.0.0.1:3183/test','db_dsn'=>'mysql:host=127.0.0.1;port=55433;dbname='.$name.';charset=utf8mb4','db_user'=>'sg_php_preview','db_password'=>$password];
        file_put_contents($file,json_encode($values,JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES));
    }
    $config=Config::load($file);$db=new Database($config);(new Migrations($db))->apply($root.'/migrations/mysql');$fixtures=new Fixtures($db,$config);$fixtures->policies();$admin=$db->one("SELECT id FROM `user` WHERE role='admin'");
    if(!$admin){$password=bin2hex(random_bytes(20));$email='php-admin@example.invalid';$id=(new Auth($db,$config))->setupAdmin('Hamza ÖZBALKAN',$email,$password);file_put_contents($root.'/.local/php-access.json',json_encode(['email'=>$email,'password'=>$password],JSON_PRETTY_PRINT));$admin=['id'=>$id];}
    $fixtures->catalog(new Principal($admin['id'],'admin',true));echo "PHP local preview ready; credentials in ignored .local/php-access.json\n";
}catch(Throwable $e){fwrite(STDERR,'SETUP_FAILED '.get_class($e).' '.($e instanceof PDOException?($e->errorInfo[1]??''):($e instanceof RuntimeException?$e->getMessage():''))."\n");exit(1);}
