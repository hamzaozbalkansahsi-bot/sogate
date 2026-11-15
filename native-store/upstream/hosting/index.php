<?php
declare(strict_types=1);

// This file is the only PHP entry point shipped inside the public document root.
const NODENO_IMAGE_LIMIT = 20000000;
const NODENO_RASTER_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/avif', 'image/gif'];

function nodenoSecurityHeaders(?string $nonce = null): array
{
    $script = "script-src 'self'" . ($nonce === null ? '' : " 'nonce-" . $nonce . "'");
    return [
        'X-Content-Type-Options' => 'nosniff',
        'Referrer-Policy' => 'strict-origin-when-cross-origin',
        'Permissions-Policy' => 'camera=(), microphone=(), geolocation=()',
        'X-Frame-Options' => 'DENY',
        'Content-Security-Policy' => "default-src 'self'; " . $script . "; style-src 'self'; font-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; object-src 'none'",
    ];
}

function nodenoRespond(string $body, int $status = 200, string $type = 'application/json; charset=utf-8', array $extra = []): void
{
    http_response_code($status);
    foreach (array_merge(nodenoSecurityHeaders(), ['Content-Type' => $type], $extra) as $key => $value) {
        header($key . ': ' . $value);
    }
    if (($_SERVER['REQUEST_METHOD'] ?? 'GET') !== 'HEAD') {
        echo $body;
    }
}

function nodenoError(int $status, string $code): void
{
    nodenoRespond(json_encode(['error' => $code], JSON_THROW_ON_ERROR), $status, 'application/json; charset=utf-8', ['Cache-Control' => 'no-store']);
}

function nodenoIsWithin(string $candidate, string $directory): bool
{
    $candidate = str_replace('\\', '/', $candidate);
    $directory = rtrim(str_replace('\\', '/', $directory), '/');
    if (DIRECTORY_SEPARATOR === '\\') {
        $candidate = strtolower($candidate);
        $directory = strtolower($directory);
    }
    return $candidate === $directory || strpos($candidate, $directory . '/') === 0;
}

function nodenoRuntimeConfiguration(): array
{
    $path=dirname(__DIR__).'/nodeno-runtime.php';
    clearstatcache(true,$path);
    if(!is_file($path))return [];
    // The release pointer changes independently of PHP bytecode revalidation.
    if(function_exists('opcache_invalidate'))@opcache_invalidate($path,true);
    $configuration=require $path;
    if(!is_array($configuration))throw new RuntimeException('Invalid runtime configuration');
    return $configuration;
}

function nodenoPrivateRoot(): string
{
    clearstatcache(true);
    $public = realpath(__DIR__);
    $configuration = nodenoRuntimeConfiguration();
    $private = realpath($configuration['privateRoot'] ?? dirname(__DIR__) . '/private');
    $documentRoot = realpath($_SERVER['DOCUMENT_ROOT'] ?? __DIR__);
    if ($public === false || $private === false || !is_dir($private)
        || nodenoIsWithin($private, $public)
        || ($documentRoot !== false && nodenoIsWithin($private, $documentRoot))) {
        throw new RuntimeException('Private storage must be outside the document root');
    }
    return $private;
}

function nodenoPrivateFile(string $private, string $name): string
{
    $file = realpath($private . '/' . $name);
    if ($file === false || !is_file($file) || !nodenoIsWithin($file, $private)) {
        throw new RuntimeException('Unavailable release data');
    }
    $body = file_get_contents($file);
    if ($body === false) {
        throw new RuntimeException('Unavailable release data');
    }
    return $body;
}

function nodenoSafeMediaUrl(string $value): bool
{
    if (preg_match('/[\x00-\x20\x7f\\\\]/', $value)) {
        return false;
    }
    $url = parse_url($value);
    return is_array($url) && ($url['scheme'] ?? '') === 'https'
        && strtolower($url['host'] ?? '') === 'witcdn.adoremobilya.com'
        && !isset($url['user']) && !isset($url['pass']) && !isset($url['fragment'])
        && (!isset($url['port']) || $url['port'] === 443);
}

function nodenoRedirectUrl(string $location, string $base): ?string
{
    $location = trim($location);
    if ($location === '' || preg_match('/[\x00-\x20\x7f\\\\]/', $location)) {
        return null;
    }
    if (preg_match('~^[a-z][a-z0-9+.-]*:~i', $location)) {
        return nodenoSafeMediaUrl($location) ? $location : null;
    }
    if (strpos($location, '//') === 0) {
        $resolved = 'https:' . $location;
        return nodenoSafeMediaUrl($resolved) ? $resolved : null;
    }
    $parts = parse_url($base);
    if ($parts === false) {
        return null;
    }
    $origin = 'https://' . $parts['host'];
    if ($location[0] === '/') {
        $resolved = $origin . $location;
    } elseif ($location[0] === '?') {
        $resolved = $origin . ($parts['path'] ?? '/') . $location;
    } else {
        $basePath = $parts['path'] ?? '/';
        $resolved = $origin . substr($basePath, 0, (int) strrpos($basePath, '/') + 1) . $location;
    }
    return nodenoSafeMediaUrl($resolved) ? $resolved : null;
}

function nodenoRasterType(string $file): ?string
{
    if (!is_file($file) || filesize($file) === 0 || filesize($file) > NODENO_IMAGE_LIMIT) {
        return null;
    }
    $mime = (new finfo(FILEINFO_MIME_TYPE))->file($file);
    $image = @getimagesize($file);
    return in_array($mime, NODENO_RASTER_TYPES, true) && is_array($image) && ($image['mime'] ?? null) === $mime ? $mime : null;
}

function nodenoValidateMediaApproval(array $entry): void
{
    $extensions = ['image/jpeg' => 'jpg', 'image/png' => 'png', 'image/webp' => 'webp', 'image/gif' => 'gif', 'image/avif' => 'avif'];
    if (!in_array($entry['state'] ?? null, ['approved_unmodified', 'approved_cleaned'], true)
        || !preg_match('/^[a-f0-9]{64}$/D', (string) ($entry['sourceSha'] ?? ''))
        || !preg_match('/^[a-f0-9]{64}$/D', (string) ($entry['outputSha'] ?? ''))
        || !isset($extensions[$entry['mime'] ?? ''])
        || !is_int($entry['bytes'] ?? null) || $entry['bytes'] < 1 || $entry['bytes'] > NODENO_IMAGE_LIMIT
        || !is_int($entry['width'] ?? null) || $entry['width'] < 1 || $entry['width'] > 100000
        || !is_int($entry['height'] ?? null) || $entry['height'] < 1 || $entry['height'] > 100000) {
        throw new RuntimeException('Image approval is invalid');
    }
    if ($entry['state'] === 'approved_unmodified') {
        if (!hash_equals($entry['sourceSha'], $entry['outputSha']) || ($entry['file'] ?? null) !== null) {
            throw new RuntimeException('Original image approval is invalid');
        }
    } elseif (($entry['file'] ?? null) !== $entry['outputSha'] . '.' . $extensions[$entry['mime']]) {
        throw new RuntimeException('Cleaned image filename is invalid');
    }
}

function nodenoApprovedMediaManifest(string $private, array $media): array
{
    $body = nodenoPrivateFile($private, 'media-approved.json');
    $release = json_decode(nodenoPrivateFile($private, 'release.json'), true, 512, JSON_THROW_ON_ERROR);
    if (!is_string($release['mediaVersion'] ?? null) || !hash_equals($release['mediaVersion'], hash('sha256', $body))) {
        throw new RuntimeException('Image approvals do not match this release');
    }
    $approved = json_decode($body, true, 512, JSON_THROW_ON_ERROR);
    if (($approved['schema'] ?? null) !== 1 || ($approved['policy'] ?? null) !== 'approved-only-v1'
        || !is_array($approved['references'] ?? null) || !is_array($approved['images'] ?? null)) {
        throw new RuntimeException('Image approvals unavailable');
    }
    $references = 0;
    $unique = [];
    foreach ($media as $id => $urls) {
        foreach ($urls as $index => $url) {
            $references++;
            $key = hash('sha256', $url);
            if (!nodenoSafeMediaUrl($url) || ($approved['references'][$id . ':' . $index] ?? null) !== $key || !is_array($approved['images'][$key] ?? null)) {
                throw new RuntimeException('Image approval reference is missing');
            }
            $unique[$key] = true;
        }
    }
    if ($references < 1 || ($approved['referenceCount'] ?? null) !== $references
        || count($approved['references']) !== $references || count($approved['images']) !== count($unique)
        || ($approved['uniqueCount'] ?? null) !== count($unique)) {
        throw new RuntimeException('Image approval coverage is incomplete');
    }
    $counts = ['approved_unmodified' => 0, 'approved_cleaned' => 0];
    foreach ($approved['images'] as $entry) {
        nodenoValidateMediaApproval($entry);
        $counts[$entry['state']]++;
    }
    if (($approved['counts'] ?? null) !== $counts) {
        throw new RuntimeException('Image approval counts are invalid');
    }
    return $approved;
}

function nodenoMediaRoot(string $private): string
{
    $configuration = nodenoRuntimeConfiguration();
    $configured = $configuration['mediaRoot'] ?? null;
    $root = is_string($configured) ? realpath($configured) : false;
    $public = realpath(__DIR__);
    $documentRoot = realpath($_SERVER['DOCUMENT_ROOT'] ?? __DIR__);
    if ($root === false || !is_dir($root) || is_link($configured) || $public === false
        || nodenoIsWithin($root, $public) || nodenoIsWithin($root, dirname($private))
        || ($documentRoot !== false && nodenoIsWithin($root, $documentRoot))) {
        throw new RuntimeException('Approved media vault is unavailable');
    }
    return $root;
}

function nodenoVerifyApprovedImage(string $file, array $approval): array
{
    nodenoValidateMediaApproval($approval);
    clearstatcache(true, $file);
    $dimensions = is_file($file) ? @getimagesize($file) : false;
    if (is_link($file) || !is_file($file) || filesize($file) !== $approval['bytes']
        || nodenoRasterType($file) !== $approval['mime'] || !is_array($dimensions)
        || $dimensions[0] !== $approval['width'] || $dimensions[1] !== $approval['height']
        || !hash_equals($approval['outputSha'], hash_file('sha256', $file))) {
        throw new RuntimeException('Approved image bytes changed');
    }
    return ['file' => $file, 'type' => $approval['mime'], 'sha256' => $approval['outputSha']];
}

function nodenoApprovedVaultImage(string $root, array $approval): array
{
    nodenoValidateMediaApproval($approval);
    $extensions = ['image/jpeg' => 'jpg', 'image/png' => 'png', 'image/webp' => 'webp', 'image/gif' => 'gif', 'image/avif' => 'avif'];
    $canonicalRoot = realpath($root);
    if ($canonicalRoot === false || !is_dir($canonicalRoot) || is_link($root)) {
        throw new RuntimeException('Approved image vault is unavailable');
    }
    $candidate = $canonicalRoot . '/' . $approval['outputSha'] . '.' . $extensions[$approval['mime']];
    $file = realpath($candidate);
    if ($file === false || is_link($candidate) || !nodenoIsWithin($file, $canonicalRoot)) {
        throw new RuntimeException('Approved image is missing');
    }
    return nodenoVerifyApprovedImage($file, $approval);
}

function nodenoVerifyMediaVault(string $root, array $approved, string $releaseHash, string $mediaVersion): void
{
    if (!preg_match('/^[a-f0-9]{64}$/D', $mediaVersion) || !preg_match('/^[a-f0-9]{64}$/D', $releaseHash)) {
        throw new RuntimeException('Invalid media verification identity');
    }
    $extensions = ['image/jpeg' => 'jpg', 'image/png' => 'png', 'image/webp' => 'webp', 'image/gif' => 'gif', 'image/avif' => 'avif'];
    $unique = [];
    foreach ($approved['images'] as $entry) {
        $unique[$entry['outputSha'] . '.' . $extensions[$entry['mime']]] = $entry;
    }
    ksort($unique, SORT_STRING);
    $snapshot = static function () use ($root, $unique): string {
        $context = hash_init('sha256');
        foreach ($unique as $name => $entry) {
            $path = $root . '/' . $name;
            clearstatcache(true, $path);
            $stat = @lstat($path);
            if ($stat === false || is_link($path) || !is_file($path) || $stat['size'] !== $entry['bytes']) {
                throw new RuntimeException('Approved media set is incomplete');
            }
            hash_update($context, $name . ':' . implode(':', [$stat['size'], $stat['mtime'], $stat['ctime'], $stat['ino'], $stat['dev']]) . "\n");
        }
        return hash_final($context);
    };
    $identity = $releaseHash . '-' . $mediaVersion;
    $receiptPath = $root . '/.nodeno-verified-' . $identity . '.json';
    $lockPath = $root . '/.nodeno-verify-' . $identity . '.lock';
    $validReceipt = static function (string $fingerprint) use ($root, $receiptPath, $releaseHash, $mediaVersion, $unique): bool {
        if (is_link($receiptPath) || !is_file($receiptPath) || filesize($receiptPath) > 2048) {
            return false;
        }
        $receipt = json_decode((string) file_get_contents($receiptPath), true);
        return is_array($receipt) && ($receipt['schema'] ?? null) === 1
            && ($receipt['releaseHash'] ?? null) === $releaseHash
            && ($receipt['mediaVersion'] ?? null) === $mediaVersion
            && ($receipt['vaultRoot'] ?? null) === $root
            && ($receipt['verifiedFiles'] ?? null) === count($unique)
            && ($receipt['snapshotHash'] ?? null) === $fingerprint;
    };
    $fingerprint = $snapshot();
    if ($validReceipt($fingerprint)) {
        return;
    }
    if (is_link($lockPath)) {
        throw new RuntimeException('Invalid media verification lock');
    }
    $lock = fopen($lockPath, 'c+');
    if ($lock === false) {
        throw new RuntimeException('Media verification unavailable');
    }
    try {
        if (!flock($lock, LOCK_EX | LOCK_NB)) {
            throw new RuntimeException('Media verification is in progress');
        }
        $fingerprint = $snapshot();
        if ($validReceipt($fingerprint)) {
            return;
        }
        foreach ($unique as $entry) {
            nodenoApprovedVaultImage($root, $entry);
        }
        if (!hash_equals($fingerprint, $snapshot())) {
            throw new RuntimeException('Media changed during verification');
        }
        if (is_link($receiptPath)) {
            throw new RuntimeException('Invalid media verification receipt');
        }
        $temporary = $root . '/.nodeno-verification-' . bin2hex(random_bytes(16)) . '.tmp';
        $body = json_encode(['schema' => 1, 'releaseHash' => $releaseHash, 'mediaVersion' => $mediaVersion,
            'vaultRoot' => $root, 'snapshotHash' => $fingerprint, 'verifiedFiles' => count($unique), 'verifiedAt' => gmdate('c')], JSON_THROW_ON_ERROR);
        if (file_put_contents($temporary, $body, LOCK_EX) !== strlen($body)) {
            throw new RuntimeException('Media verification receipt unavailable');
        }
        chmod($temporary, 0600);
        if (!rename($temporary, $receiptPath)) {
            @unlink($temporary);
            throw new RuntimeException('Media verification receipt unavailable');
        }
    } finally {
        flock($lock, LOCK_UN);
        fclose($lock);
    }
}

/** One HTTPS hop. Redirects are handled and validated by the caller. */
function nodenoDownload(string $url, string $file): array
{
    if (!nodenoSafeMediaUrl($url) || !function_exists('curl_init')) {
        throw new RuntimeException('Image transport unavailable');
    }
    $stream = fopen($file, 'wb');
    if ($stream === false) {
        throw new RuntimeException('Image cache unavailable');
    }
    $headers = [];
    $received = 0;
    $curl = curl_init($url);
    if ($curl === false) {
        fclose($stream);
        throw new RuntimeException('Image transport unavailable');
    }
    try {
        $options = [
            CURLOPT_FOLLOWLOCATION => false,
            CURLOPT_MAXREDIRS => 0,
            CURLOPT_SSL_VERIFYPEER => true,
            CURLOPT_SSL_VERIFYHOST => 2,
            CURLOPT_CONNECTTIMEOUT => 5,
            CURLOPT_TIMEOUT => 20,
            CURLOPT_LOW_SPEED_LIMIT => 1024,
            CURLOPT_LOW_SPEED_TIME => 10,
            CURLOPT_USERAGENT => 'NODENO-Catalog/1.0',
            CURLOPT_HTTPHEADER => ['Accept: image/jpeg, image/png, image/webp, image/avif, image/gif'],
            CURLOPT_HEADERFUNCTION => static function ($handle, string $line) use (&$headers): int {
                if (preg_match('~^HTTP/~i', $line)) {
                    $headers = [];
                } elseif (strpos($line, ':') !== false) {
                    [$name, $value] = explode(':', $line, 2);
                    $headers[strtolower(trim($name))] = trim($value);
                }
                return strlen($line);
            },
            CURLOPT_WRITEFUNCTION => static function ($handle, string $chunk) use ($stream, &$received): int {
                $length = strlen($chunk);
                if ($received + $length > NODENO_IMAGE_LIMIT) {
                    return 0;
                }
                $written = fwrite($stream, $chunk);
                if ($written === false) {
                    return 0;
                }
                $received += $written;
                return $written;
            },
        ];
        $options[defined('CURLOPT_PROTOCOLS_STR') ? constant('CURLOPT_PROTOCOLS_STR') : CURLOPT_PROTOCOLS] = defined('CURLOPT_PROTOCOLS_STR') ? 'https' : CURLPROTO_HTTPS;
        $options[defined('CURLOPT_REDIR_PROTOCOLS_STR') ? constant('CURLOPT_REDIR_PROTOCOLS_STR') : CURLOPT_REDIR_PROTOCOLS] = defined('CURLOPT_REDIR_PROTOCOLS_STR') ? 'https' : CURLPROTO_HTTPS;
        curl_setopt_array($curl, $options);
        $success = curl_exec($curl);
        $status = (int) curl_getinfo($curl, CURLINFO_RESPONSE_CODE);
        if ($success === false || (isset($headers['content-length']) && (float) $headers['content-length'] > NODENO_IMAGE_LIMIT)) {
            throw new RuntimeException('Image download failed');
        }
        return ['status' => $status, 'headers' => $headers];
    } finally {
        $curl = null;
        fclose($stream);
    }
}

/** The optional transport is an internal test seam; HTTP requests cannot select it. */
function nodenoFetchImage(string $url, string $cacheRoot, ?callable $transport = null, ?array $approval = null): array
{
    if (!nodenoSafeMediaUrl($url) || !is_dir($cacheRoot) || is_link($cacheRoot)) {
        throw new RuntimeException('Image unavailable');
    }
    if ($approval !== null) {
        nodenoValidateMediaApproval($approval);
        if ($approval['state'] !== 'approved_unmodified') {
            throw new RuntimeException('Source image is not approved');
        }
    }
    $cacheFile = $cacheRoot . '/' . ($approval === null ? hash('sha256', $url) : 'approved-' . $approval['outputSha']) . '.bin';
    if (!is_link($cacheFile) && is_file($cacheFile) && ($approval !== null || filemtime($cacheFile) > time() - 86400)) {
        if ($approval !== null) {
            try { return nodenoVerifyApprovedImage($cacheFile, $approval); } catch (Throwable $error) { /* Revalidate newly downloaded bytes below. */ }
        }
        $type = nodenoRasterType($cacheFile);
        if ($approval === null && $type !== null) {
            return ['file' => $cacheFile, 'type' => $type];
        }
    }
    $download = $transport ?? 'nodenoDownload';
    $target = $url;
    for ($hops = 0; $hops <= 3; $hops++) {
        if (!nodenoSafeMediaUrl($target)) {
            throw new RuntimeException('Image unavailable');
        }
        $temporary = tempnam($cacheRoot, '.download-');
        if ($temporary === false) {
            throw new RuntimeException('Image unavailable');
        }
        @chmod($temporary, 0600);
        try {
            $response = $download($target, $temporary);
            $status = $response['status'] ?? 0;
            $headers = $response['headers'] ?? [];
            if (in_array($status, [301, 302, 303, 307, 308], true)) {
                $next = nodenoRedirectUrl((string) ($headers['location'] ?? ''), $target);
                if ($next === null || $hops === 3) {
                    throw new RuntimeException('Image redirect rejected');
                }
                $target = $next;
                continue;
            }
            $type = strtolower(trim(explode(';', (string) ($headers['content-type'] ?? ''))[0]));
            if ($status !== 200 || !in_array($type, NODENO_RASTER_TYPES, true)
                || (isset($headers['content-length']) && (float) $headers['content-length'] > NODENO_IMAGE_LIMIT)
                || nodenoRasterType($temporary) !== $type) {
                throw new RuntimeException('Image response rejected');
            }
            if ($approval !== null) {
                nodenoVerifyApprovedImage($temporary, $approval);
            }
            if (is_link($cacheFile) || !rename($temporary, $cacheFile)) {
                throw new RuntimeException('Image cache unavailable');
            }
            return ['file' => $cacheFile, 'type' => $type, 'sha256' => $approval['outputSha'] ?? null];
        } finally {
            if (is_file($temporary)) {
                unlink($temporary);
            }
        }
    }
    throw new RuntimeException('Image unavailable');
}

function nodenoHealth(string $private): array
{
    $cache = realpath($private . '/cache');
    if (!function_exists('curl_init') || !class_exists('finfo') || $cache === false
        || !nodenoIsWithin($cache, $private) || is_link($private . '/cache') || !is_writable($cache)) {
        throw new RuntimeException('Required runtime capability unavailable');
    }
    if (!class_exists('PDO') || !in_array('sqlite', PDO::getAvailableDrivers(), true)) {
        throw new RuntimeException('Account database capability unavailable');
    }
    $release = json_decode(nodenoPrivateFile($private, 'release.json'), true, 512, JSON_THROW_ON_ERROR);
    if (($release['runtime'] ?? null) !== 'php' || !is_array($release['files'] ?? null)) {
        throw new RuntimeException('Invalid release');
    }
    $files = $release['files'];
    ksort($files, SORT_STRING);
    $fingerprint = hash_init('sha256');
    foreach ($files as $file => $expected) {
        if (!preg_match('~^(public|private)/([A-Za-z0-9_./-]+)$~D', $file, $parts)
            || strpos($parts[2], '..') !== false || strpos($parts[2], '//') !== false) {
            throw new RuntimeException('Invalid release');
        }
        $directory = $parts[1] === 'public' ? __DIR__ : $private;
        $filename = realpath($directory . '/' . $parts[2]);
        if ($filename === false || !nodenoIsWithin($filename, (string) realpath($directory)) || !is_file($filename)) {
            throw new RuntimeException('Incomplete release');
        }
        $actual = hash_file('sha256', $filename);
        if (!is_string($expected) || !hash_equals($expected, $actual)) {
            throw new RuntimeException('Release integrity mismatch');
        }
        hash_update($fingerprint, $file . "\0" . $actual . "\0");
    }
    $hash = hash_final($fingerprint);
    if (!is_string($release['releaseHash'] ?? null) || !hash_equals($release['releaseHash'], $hash)) {
        throw new RuntimeException('Release integrity mismatch');
    }
    $media = json_decode(nodenoPrivateFile($private, 'media.json'), true, 512, JSON_THROW_ON_ERROR);
    $approved = nodenoApprovedMediaManifest($private, $media);
    if (($release['mediaApproved'] ?? null) !== $approved['referenceCount']
        || !hash_equals((string) ($release['mediaVersion'] ?? ''), hash('sha256', nodenoPrivateFile($private, 'media-approved.json')))) {
        throw new RuntimeException('Image approval release identity mismatch');
    }
    $vault = nodenoMediaRoot($private);
    nodenoVerifyMediaVault($vault, $approved, $hash, $release['mediaVersion']);
    $blogHealth=[];if(is_file($private.'/blog-bank.json')){require_once $private.'/blog-worker.php';$storage=nodenoRuntimeConfiguration()['storageRoot']??dirname(__DIR__).'/nodeno-data';if(!is_string($storage))throw new RuntimeException('Invalid blog storage');$blogHealth=nodenoBlogMediaHealth($storage,$private,__DIR__);}
    $supplierHealth=[];if(is_file($private.'/supplier-products.php')){require_once $private.'/supplier-products.php';$supplierHealth=nodenoSupplierMediaHealth($private,json_decode(nodenoPrivateFile($private,'catalog.json'),true,512,JSON_THROW_ON_ERROR),$files);}
    return [
        'status' => 'ok', 'brand' => 'NODENO', 'runtime' => 'php', 'phpVersion' => PHP_VERSION,
        'products' => $release['products'], 'categories' => $release['categories'],
        'checkoutEnabled' => nodenoStoreContext($private)['config']['checkoutEnabled']??false, 'driveConnected' => false, 'accountsEnabled' => true,
        'mediaReady' => true, 'mediaApproved' => $approved['referenceCount'], 'mediaCounts' => $approved['counts'], 'mediaVersion' => $release['mediaVersion'],
        'releaseHash' => $hash,
        ...$supplierHealth,
        ...$blogHealth,
    ];
}

function nodenoProductMetadata(string $html,string $private):string
{
    require_once $private . '/seo.php';
    $catalog=json_decode(nodenoPrivateFile($private,'catalog.json'),true,512,JSON_THROW_ON_ERROR);
    $config=json_decode(nodenoPrivateFile($private,'config.json'),true,512,JSON_THROW_ON_ERROR);
    require_once $private.'/door-commerce.php';$catalog=nodenoShippingCatalog($catalog);return nodenoSeoDocument($html,nodenoSeoPage($catalog,$config,$_GET));
}

function nodenoStoreContext(string $private):array
{
    if(is_file($private.'/door-commerce.php'))require_once $private.'/door-commerce.php';
    $runtime=nodenoRuntimeConfiguration();
    $catalog=json_decode(nodenoPrivateFile($private,'catalog.json'),true,512,JSON_THROW_ON_ERROR);
    $config=json_decode(nodenoPrivateFile($private,'config.json'),true,512,JSON_THROW_ON_ERROR);
    $storage=$runtime['storageRoot']??null;
    if(is_string($storage)){
        require_once $private.'/control-analytics.php';
        $root=nodenoAccountStorage($storage);
        $db=nodenoControlDatabase($root);$projection=nodenoControlPublicState($db,$catalog,$config);
        if(is_file($private.'/payment-admin.php')){
            require_once $private.'/payment-admin.php';$payment=nodenoPaymentConfiguration($db,$root);
            $projection['paymentsReady']=nodenoPaymentReady($payment);
            if($projection['paymentsReady']){$projection['config']['checkoutEnabled']=true;$projection['config']['paymentSeller']=$payment['seller'];}
        }
        return $projection+['storage'=>$root,'sourceCatalog'=>$catalog];
    }
    return ['catalog'=>$catalog,'config'=>$config,'sourceCatalog'=>$catalog,'storage'=>null,'revision'=>0];
}

function nodenoRun(): void
{
    $method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
    $path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH);
    if (!is_string($path)) {
        nodenoError(404, 'not_found');
        return;
    }
    try {
        $private = nodenoPrivateRoot();
        if(is_file($private.'/blog-http.php')){require_once $private.'/blog-http.php';if(nodenoBlogHttp($path,$method,$private,__DIR__))return;}
        if(preg_match('~^/social-media/([a-f0-9]{64})\.(png|mp3)$~D',$path,$socialAsset)){
            if(!in_array($method,['GET','HEAD'],true)){nodenoError(405,'method_not_allowed');return;}
            require_once $private.'/social-media.php';$socialState=nodenoStoreContext($private);
            if(!is_string($socialState['storage'])||!nodenoStudioServeAsset($socialAsset[1],$socialAsset[2],$socialState['storage']))nodenoError(404,'not_found');return;
        }
        if($path==='/legal'||str_starts_with($path,'/legal/')){require_once $private.'/legal.php';nodenoLegalHandle($path,$method,$private);return;}
        if(in_array($path,['/api/exchange-rates','/api/commerce/status','/api/commerce/quote','/api/door-inquiries'],true)){
            require_once $private.'/control-http.php';$state=nodenoStoreContext($private);
            if(!is_string($state['storage']))throw new RuntimeException('Persistent commerce storage required');
            if(nodenoCommerceHandle($path,$method,$state))return;
        }
        if ($path === '/api/visitor-context') {
            if (!in_array($method, ['GET','HEAD'], true)) { nodenoError(405,'method_not_allowed'); return; }
            require_once $private.'/visitor-market.php';
            $visitor=nodenoVisitorMarket($_SERVER,$private);
            $visitor['suggestedLocale']=nodenoInitialLocale(null,null,$visitor['country']);
            nodenoRespond(json_encode($visitor,JSON_THROW_ON_ERROR),200,'application/json; charset=utf-8',['Cache-Control'=>'private, no-store','X-Robots-Tag'=>'noindex,nofollow']);
            return;
        }
        if(preg_match('~^/([a-f0-9]{32})\.txt$~D',$path,$keyMatch)&&in_array($method,['GET','HEAD'],true)){
            $state=nodenoStoreContext($private);$key=null;
            if(is_string($state['storage']))$key=nodenoControlSetting(nodenoControlDatabase($state['storage']),'indexnow:key');
            if(is_string($key)&&hash_equals($key,$keyMatch[1]))nodenoRespond($key,200,'text/plain; charset=utf-8',['Cache-Control'=>'no-store','X-Robots-Tag'=>'noindex,nofollow']);else nodenoError(404,'not_found');return;
        }
        if(in_array($path,['/admin','/admin/'],true)){nodenoRespond('',302,'text/html; charset=utf-8',['Location'=>'/yonetim','Cache-Control'=>'no-store','X-Robots-Tag'=>'noindex,nofollow']);return;}
        if(in_array($path,['/yonetim','/yonetim/','/admin.html'],true)){
            if(!in_array($method,['GET','HEAD'],true)){nodenoError(405,'method_not_allowed');return;}
            nodenoRespond((string)file_get_contents(__DIR__.'/admin.html'),200,'text/html; charset=utf-8',['Cache-Control'=>'no-store','X-Robots-Tag'=>'noindex,nofollow']);return;
        }
        if(str_starts_with($path,'/api/admin/')||str_starts_with($path,'/api/insights/')||str_starts_with($path,'/api/wholesale')||in_array($path,['/api/recommendations','/api/support','/api/shipping-quote'],true)){
            require_once $private.'/control-http.php';$state=nodenoStoreContext($private);
            if(!is_string($state['storage']))throw new RuntimeException('Persistent management storage required');
            if(nodenoControlHandle($path,$method,$state['sourceCatalog'],$state['config'],$state['storage'])||nodenoWholesaleHandle($path,$method,$state['catalog'],$state['storage'])||nodenoControlPublicHandle($path,$method,$state['catalog'],$state['storage']))return;
        }
        if(str_starts_with($path,'/api/payments/')){
            require_once $private.'/payments.php';$state=nodenoStoreContext($private);
            if(!is_string($state['storage']))throw new RuntimeException('Persistent payment storage required');
            nodenoPaymentsHandle($path,$method,$state['catalog'],$state['storage']);return;
        }
        if ($path === '/api/account' || strpos($path, '/api/account/') === 0) {
            require_once $private . '/account.php';
            $configuration = nodenoRuntimeConfiguration();
            $storage = $configuration['storageRoot'] ?? dirname(__DIR__) . '/nodeno-data';
            if (!is_string($storage)) {
                throw new RuntimeException('Invalid account storage');
            }
            $catalog = nodenoStoreContext($private)['catalog'];
            if (nodenoHandleAccountRequest($path, $method, $catalog, $storage)) {
                return;
            }
            nodenoError(404, 'not_found');
            return;
        }
        if (!in_array($method, ['GET', 'HEAD'], true)) {
            nodenoRespond('{"error":"method_not_allowed"}', 405, 'application/json; charset=utf-8', ['Allow' => 'GET, HEAD', 'Cache-Control' => 'no-store']);
            return;
        }
        $categoryAliases = ['adore-gaming' => 'oyuncu-mobilyalari', 'adoregaming-tgif' => 'tgif-serisi'];
        $category = $_GET['category'] ?? null;
        if (in_array($path, ['/', '/index.html', '/index.php'], true) && is_string($category) && isset($categoryAliases[$category])) {
            $query = $_GET;
            $query['category'] = $categoryAliases[$category];
            nodenoRespond('', 301, 'text/html; charset=utf-8', ['Location' => $path . '?' . http_build_query($query, '', '&', PHP_QUERY_RFC3986), 'Cache-Control' => 'no-store']);
            return;
        }
        if(preg_match('~^/api/supplier-products/([A-Za-z0-9_-]{1,80})$~D',$path,$supplierMatch)){
            if(!in_array($method,['GET','HEAD'],true)){nodenoError(405,'method_not_allowed');return;}
            if(!is_file($private.'/supplier-products.php')){nodenoError(404,'not_found');return;}
            require_once $private.'/supplier-products.php';$state=nodenoStoreContext($private);$details=nodenoSupplierDetails($private,$supplierMatch[1],$state['catalog']);
            if(!$details){nodenoError(404,'not_found');return;}
            nodenoRespond(json_encode($details,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES),200,'application/json; charset=utf-8',['Cache-Control'=>'public, max-age=300','ETag'=>'"'.$details['sha256'].'"','X-Robots-Tag'=>'noindex,nofollow']);return;
        }
        if ($path === '/api/catalog' || $path === '/api/config') {
            $filename = $path === '/api/catalog' ? 'catalog.json' : 'config.json';
            $state=nodenoStoreContext($private);
            $bytes=($state['revision']>0||($path==='/api/config'&&($state['paymentsReady']??false)))?json_encode($path==='/api/catalog'?$state['catalog']:$state['config'],JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES):nodenoPrivateFile($private,$filename);
            nodenoRespond($bytes,200,'application/json; charset=utf-8',['Cache-Control'=>'no-cache','ETag'=>'"'.hash('sha256',$bytes).'"','X-Robots-Tag'=>'noindex']);
        } elseif ($path === '/api/health') {
            nodenoRespond(json_encode(nodenoHealth($private), JSON_THROW_ON_ERROR), 200, 'application/json; charset=utf-8', ['Cache-Control' => 'no-store']);
        } elseif ($path === '/' || $path === '/index.html' || $path === '/index.php') {
            require_once $private . '/seo.php';
            $state=nodenoStoreContext($private);$catalog=$state['catalog'];$config=$state['config'];
            require_once $private.'/visitor-market.php';
            $visitor=nodenoVisitorMarket($_SERVER,$private);
            $query=$_GET;
            $query['lang']=nodenoInitialLocale($query['lang']??null,$_COOKIE['nodeno_language']??null,$visitor['country']);
            if(is_file($private.'/supplier-products.php')){require_once $private.'/supplier-products.php';$catalog=nodenoSupplierSeoDetails($private,$catalog,$query);}
            $page=nodenoSeoPage($catalog,$config,$query);
            $nonce=bin2hex(random_bytes(16));
            $html=preg_replace('/<script\b/', '<script nonce="'.$nonce.'"', nodenoSeoDocument(nodenoPrivateFile($private,'index.html'),$page));
            $html=str_replace('<html lang=', '<html data-visitor-country="'.($visitor['country']??'').'" data-market="'.($visitor['international']?'international':($visitor['country']==='TR'?'domestic':'unknown')).'" lang=', $html);
            nodenoRespond($html,$page['status'],'text/html; charset=utf-8',array_merge(nodenoSecurityHeaders($nonce),['Cache-Control'=>'no-store','X-Robots-Tag'=>$page['indexable']?'index,follow':'noindex,follow']));
        } elseif ($path === '/robots.txt') {
            require_once $private . '/seo.php';
            nodenoRespond(nodenoSeoRobots(),200,'text/plain; charset=utf-8');
        } elseif ($path==='/sitemap.xml'||preg_match('~^/sitemap-(products|pages)-(tr|en|ru|ar|de|az|kk|tk|uz|ky|fa)\.xml$~D',$path,$map)) {
            require_once $private . '/seo.php';
            $state=nodenoStoreContext($private);$catalog=$state['catalog'];$config=$state['config'];
            nodenoRespond(nodenoSeoSitemap($catalog,$config,$map[1]??'index',$map[2]??'tr'),200,'application/xml; charset=utf-8',['Cache-Control'=>'public, max-age=300']);
        } elseif (strpos($path, '/media/') === 0) {
            if (!preg_match('~^/media/([A-Za-z0-9_-]+)/(0|[1-9][0-9]{0,3})$~D', $path, $match)) {
                nodenoError(404, 'image_not_found');
                return;
            }
            if(str_starts_with($match[1],'door-')||str_starts_with($match[1],'front-')){
                require_once $private.'/door-commerce.php';
                try{$image=nodenoDoorMedia($private,$match[1],(int)$match[2]);nodenoRespond('',200,$image['mime'],['Cache-Control'=>'public, max-age=86400','ETag'=>'"sha256-'.$image['sha256'].'"','X-Content-SHA256'=>$image['sha256'],'Content-Disposition'=>'inline','Content-Length'=>(string)filesize($image['file']),'Cross-Origin-Resource-Policy'=>'same-origin']);if($method!=='HEAD')readfile($image['file']);}catch(Throwable $e){nodenoError(404,'door_image_unavailable');}return;
            }
            $media = json_decode(nodenoPrivateFile($private, 'media.json'), true, 512, JSON_THROW_ON_ERROR);
            $url = $media[$match[1]][(int) $match[2]] ?? null;
            if (!is_string($url) || !nodenoSafeMediaUrl($url)) {
                nodenoError(404, 'image_not_found');
                return;
            }
            try {
                $approved = nodenoApprovedMediaManifest($private, $media);
                $key = $approved['references'][$match[1] . ':' . $match[2]];
                $entry = $approved['images'][$key];
                $image = nodenoApprovedVaultImage(nodenoMediaRoot($private), $entry);
                nodenoRespond('', 200, $image['type'], ['Cache-Control' => 'public, max-age=86400', 'ETag' => '"sha256-' . $entry['outputSha'] . '"', 'X-Content-SHA256' => $entry['outputSha'], 'Content-Disposition' => 'inline', 'Cross-Origin-Resource-Policy' => 'same-origin', 'Content-Length' => (string) filesize($image['file'])]);
                if ($method !== 'HEAD') {
                    readfile($image['file']);
                }
            } catch (Throwable $exception) {
                nodenoError(502, 'image_unavailable');
            }
        } else {
            nodenoError(404, 'not_found');
        }
    } catch (Throwable $exception) {
        nodenoError(503, 'temporarily_unavailable');
    }
}

if (!defined('NODENO_RUNTIME_LIBRARY')) {
    ini_set('display_errors', '0');
    set_error_handler(static function (int $severity, string $message, string $file, int $line): bool {
        // Suppressed probing calls are expected, and never reach the response body.
        if (!(error_reporting() & $severity)) {
            return false;
        }
        throw new ErrorException($message, 0, $severity, $file, $line);
    });
    nodenoRun();
}
