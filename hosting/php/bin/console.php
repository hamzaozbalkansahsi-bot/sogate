<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/bin/console.php
 * Açıklama   : PHP CLI için sabit migration, kurulum ve süre sonu komutları.
 */
declare(strict_types=1);
if(PHP_SAPI!=='cli'){http_response_code(404);exit;}
require dirname(__DIR__).'/vendor/autoload.php';
try {
    $config=Sexogate\Config::load(getenv('SEXOGATE_CONFIG')?:dirname(__DIR__).'/config.local.json');$db=new Sexogate\Database($config);
    switch($argv[1]??''){
        case 'migrate':$directory=is_dir(dirname(__DIR__).'/migrations')?dirname(__DIR__).'/migrations':dirname(__DIR__,3).'/migrations/mysql';(new Sexogate\Migrations($db))->apply($directory);echo "Migrations verified.\n";break;
        case 'fixtures':(new Sexogate\Fixtures($db,$config))->policies();echo "Isolated test rules prepared.\n";break;
        case 'expire':(new Sexogate\Commerce($db,$config))->expire();echo "Reservation expiry checked.\n";break;
        default:throw new RuntimeException('UNKNOWN_COMMAND');
    }
}catch(Throwable $e){fwrite(STDERR,'PHP command failed: '.get_class($e)."\n");exit(1);}
