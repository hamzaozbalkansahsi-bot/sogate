<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/public/index.php
 * Açıklama   : PHP ön denetleyicisini özel yapılandırmayla başlatır.
 */
declare(strict_types=1);
ini_set('display_errors','0');
require dirname(__DIR__).'/vendor/autoload.php';
try {
    $config=Sexogate\Config::load(defined('SEXOGATE_CONFIG')?SEXOGATE_CONFIG:dirname(__DIR__).'/config.local.json');
    (new Sexogate\Kernel(new Sexogate\Database($config),$config))->handle(Symfony\Component\HttpFoundation\Request::createFromGlobals())->send();
} catch (Throwable $e) {
    error_log('SEXOGATE_BOOT '.get_class($e));
    http_response_code(503);header('Content-Type: text/plain; charset=utf-8');header('Cache-Control: no-store');header('X-Robots-Tag: noindex, nofollow');
    echo 'Uygulama şu anda kullanılamıyor. Lütfen daha sonra yeniden deneyin.';
}
