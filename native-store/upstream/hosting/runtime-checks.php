<?php
declare(strict_types=1);

// Executed only by tests/cpanel-runtime.test.mjs, never copied to the public release.
define('NODENO_RUNTIME_LIBRARY', true);
require __DIR__ . '/index.php';
function check(bool $condition, string $message): void {
    if (!$condition) { throw new RuntimeException($message); }
}
function rejects(callable $operation, string $message): void {
    $failed = false;
    try { $operation(); } catch (Throwable $error) { $failed = true; }
    check($failed, $message);
}
$cache = $argv[1];
$png = base64_decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=');
foreach (['http://witcdn.adoremobilya.com/a.jpg', 'https://witcdn.adoremobilya.com.evil.test/a.jpg', 'https://user:pass@witcdn.adoremobilya.com/a.jpg', 'https://127.0.0.1/a.jpg', 'https://witcdn.adoremobilya.com:8080/a.jpg', "https://witcdn.adoremobilya.com/a\n.jpg", 'https://witcdn.adoremobilya.com/a.jpg#fragment'] as $url) {
    check(!nodenoSafeMediaUrl($url), 'Unsafe URL accepted: ' . $url);
}
check(nodenoSafeMediaUrl('https://witcdn.adoremobilya.com/a.jpg'), 'CDN URL rejected');
$calls = 0;
$image = nodenoFetchImage('https://witcdn.adoremobilya.com/cache-test.png', $cache, function ($url, $file) use (&$calls, $png) {
    $calls++; file_put_contents($file, $png); return ['status' => 200, 'headers' => ['content-type' => 'image/png']];
});
check($image['type'] === 'image/png' && file_get_contents($image['file']) === $png, 'Valid image changed');
nodenoFetchImage('https://witcdn.adoremobilya.com/cache-test.png', $cache, function () { throw new RuntimeException('Fresh cache missed'); });
check($calls === 1, 'Cache did not avoid second network request');
rejects(function () use ($cache) {
    nodenoFetchImage('https://witcdn.adoremobilya.com/redirect-test.png', $cache, function ($url, $file) {
        return ['status' => 302, 'headers' => ['location' => 'https://127.0.0.1/private']];
    });
}, 'Redirect escaped allowlist');
$hops = 0;
rejects(function () use ($cache, &$hops) {
    nodenoFetchImage('https://witcdn.adoremobilya.com/loop-test.png', $cache, function ($url, $file) use (&$hops) {
        $hops++; return ['status' => 302, 'headers' => ['location' => '/loop-test.png']];
    });
}, 'Redirect loop accepted');
check($hops === 4, 'Redirect limit differs from three redirects');
rejects(function () use ($cache) {
    nodenoFetchImage('https://witcdn.adoremobilya.com/html-test.png', $cache, function ($url, $file) {
        file_put_contents($file, '<script>alert(1)</script>'); return ['status' => 200, 'headers' => ['content-type' => 'image/png']];
    });
}, 'Raster MIME spoof accepted');
rejects(function () use ($cache) {
    nodenoFetchImage('https://witcdn.adoremobilya.com/large-test.png', $cache, function ($url, $file) {
        $stream = fopen($file, 'wb'); ftruncate($stream, NODENO_IMAGE_LIMIT + 1); fclose($stream);
        return ['status' => 200, 'headers' => ['content-type' => 'image/png']];
    });
}, 'Oversized image accepted');
rejects(function () use ($cache, $png) {
    nodenoFetchImage('https://witcdn.adoremobilya.com/declared-large-test.png', $cache, function ($url, $file) use ($png) {
        file_put_contents($file, $png); return ['status' => 200, 'headers' => ['content-type' => 'image/png', 'content-length' => (string) (NODENO_IMAGE_LIMIT + 1)]];
    });
}, 'Oversized declared length accepted');
$redirectCalls = 0;
$redirected = nodenoFetchImage('https://witcdn.adoremobilya.com/relative/source.png', $cache, function ($url, $file) use (&$redirectCalls, $png) {
    $redirectCalls++;
    if ($redirectCalls === 1) { return ['status' => 302, 'headers' => ['location' => '/relative/target.png']]; }
    check($url === 'https://witcdn.adoremobilya.com/relative/target.png', 'Relative redirect resolved incorrectly');
    file_put_contents($file, $png); return ['status' => 200, 'headers' => ['content-type' => 'image/png']];
});
check($redirected['type'] === 'image/png' && $redirectCalls === 2, 'Valid CDN redirect failed');
check(count(glob($cache . '/.download-*')) === 0, 'Temporary download files leaked');
echo json_encode(['checks' => 'passed', 'transportMock' => true, 'phpVersion' => PHP_VERSION]);
