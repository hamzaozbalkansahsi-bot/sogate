<?php
declare(strict_types=1);

// Loopback-only account UI fixture. Never part of the production release.
if (PHP_SAPI !== 'cli-server' || getenv('NODENO_SOCIAL_UI_TEST') !== 'isolated-test-only'
    || !in_array($_SERVER['REMOTE_ADDR'] ?? '', ['127.0.0.1', '::1'], true)) {
    http_response_code(404);exit;
}
$_SERVER['HTTPS'] = 'on'; // The owned loopback HTTPS proxy terminates test TLS.
$workspace = dirname(__DIR__, 2);$web = realpath($workspace . '/web');
$path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH);
function nodenoRespond(string $body, int $status = 200, string $type = 'application/json; charset=utf-8', array $headers = []): void
{
    http_response_code($status);header('Content-Type: ' . $type);header('Cache-Control: no-store');
    header('X-Nodeno-Test-Only: social-auth-ui');header('X-Content-Type-Options: nosniff');
    foreach ($headers as $key => $value) {header($key . ': ' . $value);}
    if ($_SERVER['REQUEST_METHOD'] !== 'HEAD') {echo $body;}
}
if ($path === '/api/catalog' || $path === '/api/config') {
    $filename = getenv($path === '/api/catalog' ? 'NODENO_SOCIAL_TEST_CATALOG' : 'NODENO_SOCIAL_TEST_CONFIG');
    nodenoRespond(file_get_contents($filename));return;
}
if ($path === '/api/health') {
    nodenoRespond(json_encode(['testOnly' => true, 'purpose' => 'isolated account UI; not a deployable catalogue',
        'appSha256' => hash_file('sha256', $web . '/app.js')], JSON_THROW_ON_ERROR));return;
}
if (is_string($path) && ($path === '/api/account' || str_starts_with($path, '/api/account/'))) {
    $storage = getenv('NODENO_SOCIAL_TEST_STORAGE');
    if (!is_string($storage) || !str_starts_with(basename($storage), 'nodeno-auth-browser-') || is_link($storage)) {
        nodenoRespond('{"error":"test_fixture_unavailable"}', 503);return;
    }
    $scenario = $_SERVER['HTTP_X_NODENO_TEST_SCENARIO'] ?? 'default';
    if (!preg_match('/^(?:default|(?:chromium|webkit)-(?:tr|en|ru|ar))$/D', $scenario)) {
        nodenoRespond('{"error":"invalid_test_scenario"}', 400);return;
    }
    $storage .= '/' . $scenario;
    if (!is_dir($storage)) {mkdir($storage, 0700);}
    require $workspace . '/hosting/account.php';
    $catalog = json_decode(file_get_contents(getenv('NODENO_SOCIAL_TEST_CATALOG')), true, 512, JSON_THROW_ON_ERROR);
    nodenoHandleAccountRequest($path, $_SERVER['REQUEST_METHOD'], $catalog, $storage);return;
}
if ($path === '/') {nodenoRespond(file_get_contents($web . '/index.html'), 200, 'text/html; charset=utf-8');return;}
if (is_string($path) && !preg_match('~(?:^|/)\.|\.\.|\\\\~', $path)
    && preg_match('/\.(?:js|css|svg|png|ico|woff2?|ttf|webmanifest)$/iD', $path)) {
    $file = realpath($web . $path);
    if ($file !== false && str_starts_with(str_replace('\\', '/', $file), str_replace('\\', '/', $web) . '/') && is_file($file)) {return false;}
}
nodenoRespond('{"error":"not_found"}', 404);
