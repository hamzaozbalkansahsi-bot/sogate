<?php
declare(strict_types=1);
if(PHP_SAPI==='cli-server'&&getenv('NODENO_TEST_HTTPS')==='loopback-tls-only'&&in_array($_SERVER['REMOTE_ADDR']??'',['127.0.0.1','::1'],true))$_SERVER['HTTPS']='on';

// Local integration tests only. Apache production routing lives in .htaccess.
$public = realpath($argv[1] ?? getenv('NODENO_TEST_PUBLIC') ?: dirname(__DIR__) . '/artifacts/cpanel-release/public');
$requestPath = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH);
if ($public !== false && is_string($requestPath) && in_array($_SERVER['REQUEST_METHOD'], ['GET', 'HEAD'], true)
    && !str_starts_with($requestPath, '/assets/blog/')
    && !preg_match('~(?:^|/)\.|^/(?:private|cache|hosting|data|lib|scripts|tests|artifacts|dist)(?:/|$)~i', $requestPath)
    && (preg_match('~\.(?:css|js|svg|png|jpe?g|webp|gif|avif|ico|woff2?|ttf|webmanifest|txt)$~i', $requestPath)
        || preg_match('~^/locales/(?:de|az|kk|tk|uz|ky|fa)(?:\.catalogue)?\.json$~D', $requestPath))) {
    $file = realpath($public . $requestPath);
    if ($file !== false && strpos(str_replace('\\', '/', $file), rtrim(str_replace('\\', '/', $public), '/') . '/') === 0 && is_file($file)) {
        return false;
    }
}
require $public . '/index.php';
