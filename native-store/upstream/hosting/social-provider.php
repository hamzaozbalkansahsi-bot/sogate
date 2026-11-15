<?php
declare(strict_types=1);

/** Provider URLs are constants: configuration and HTTP input cannot redirect credentials. */
function nodenoSocialProviderJson(string $url, ?array $fields = null): array
{
    $allowed = ['https://oauth2.googleapis.com/token', 'https://www.googleapis.com/oauth2/v3/certs',
        'https://appleid.apple.com/auth/token', 'https://appleid.apple.com/auth/keys'];
    if (!in_array($url, $allowed, true) || !extension_loaded('curl')) {
        throw new NodenoAccountHttpError(503, 'social_provider_unavailable');
    }
    $body = '';$handle = curl_init($url);
    if ($handle === false) {
        throw new NodenoAccountHttpError(503, 'social_provider_unavailable');
    }
    try {
        curl_setopt_array($handle, [CURLOPT_SSL_VERIFYPEER => true, CURLOPT_SSL_VERIFYHOST => 2,
            CURLOPT_FOLLOWLOCATION => false, CURLOPT_CONNECTTIMEOUT => 5,
            CURLOPT_TIMEOUT => 15, CURLOPT_ENCODING => '', CURLOPT_USERAGENT => 'NODENO-Account/1.0',
            CURLOPT_HTTPHEADER => ['Accept: application/json'],
            CURLOPT_WRITEFUNCTION => static function ($handle, string $chunk) use (&$body): int {
                if (strlen($body) + strlen($chunk) > 131072) {return 0;}
                $body .= $chunk;return strlen($chunk);
            }]);
        if (defined('CURLOPT_PROTOCOLS_STR')) {
            curl_setopt($handle, constant('CURLOPT_PROTOCOLS_STR'), 'https');
        } else {
            curl_setopt($handle, CURLOPT_PROTOCOLS, CURLPROTO_HTTPS);
        }
        if ($fields !== null) {
            curl_setopt_array($handle, [CURLOPT_POST => true, CURLOPT_POSTFIELDS => http_build_query($fields, '', '&', PHP_QUERY_RFC3986)]);
        }
        if (curl_exec($handle) === false || (int) curl_getinfo($handle, CURLINFO_RESPONSE_CODE) !== 200) {
            throw new NodenoAccountHttpError(503, 'social_provider_unavailable');
        }
        $value = json_decode($body, true, 32, JSON_THROW_ON_ERROR);
        if (!is_array($value)) {throw new UnexpectedValueException();}
        return $value;
    } catch (Throwable $exception) {
        throw new NodenoAccountHttpError(503, 'social_provider_unavailable');
    } finally {
        unset($handle);
    }
}

function nodenoSocialJwks(string $root, string $provider, string $kid): array
{
    if (!in_array($provider, ['google', 'apple'], true)) {
        throw new NodenoAccountHttpError(400, 'invalid_social_request');
    }
    $file = $root . '/oauth-' . $provider . '-jwks.json';
    if (is_link($file)) {throw new RuntimeException('Unsafe identity key cache');}
    if (is_file($file) && filesize($file) <= 131072) {
        try {
            $cache = json_decode(file_get_contents($file), true, 32, JSON_THROW_ON_ERROR);
            if (is_int($cache['fetchedAt'] ?? null) && $cache['fetchedAt'] > time() - 3600
                && is_array($cache['keys'] ?? null) && in_array($kid, array_column($cache['keys'], 'kid'), true)) {
                return ['keys' => $cache['keys']];
            }
        } catch (JsonException $exception) {
            // Corrupt/old public key cache is refreshed from the pinned HTTPS endpoint.
        }
    }
    $keys = nodenoSocialProviderJson($provider === 'google' ? 'https://www.googleapis.com/oauth2/v3/certs' : 'https://appleid.apple.com/auth/keys');
    if (!is_array($keys['keys'] ?? null) || count($keys['keys']) < 1 || count($keys['keys']) > 32) {
        throw new NodenoAccountHttpError(503, 'social_provider_unavailable');
    }
    $temporary = $file . '.' . bin2hex(random_bytes(8)) . '.tmp';
    try {
        if (file_put_contents($temporary, json_encode(['fetchedAt' => time(), 'keys' => $keys['keys']], JSON_THROW_ON_ERROR), LOCK_EX) === false
            || !chmod($temporary, 0600) || !rename($temporary, $file)) {
            throw new RuntimeException('Identity key cache unavailable');
        }
    } finally {
        if (is_file($temporary) && !is_link($temporary)) {unlink($temporary);}
    }
    return ['keys' => $keys['keys']];
}

function nodenoSocialAppleSecret(array $configuration): string
{
    $key = file_get_contents($configuration['privateKeyFile']);
    if (!is_string($key) || $key === '') {throw new NodenoAccountHttpError(503, 'social_not_configured');}
    return Firebase\JWT\JWT::encode(['iss' => $configuration['teamId'], 'iat' => time(), 'exp' => time() + 300,
        'aud' => 'https://appleid.apple.com', 'sub' => $configuration['clientId']], $key, 'ES256', $configuration['keyId']);
}

function nodenoSocialExchange(string $root, string $provider, array $configuration, array $flow, string $code): array
{
    $fields = ['client_id' => $configuration['clientId'], 'grant_type' => 'authorization_code',
        'code' => $code, 'redirect_uri' => $flow['callback']];
    if ($provider === 'google') {
        $fields['client_secret'] = $configuration['clientSecret'];$fields['code_verifier'] = $flow['verifier'];
    } else {
        $fields['client_secret'] = nodenoSocialAppleSecret($configuration);
    }
    $result = nodenoSocialProviderJson($provider === 'google' ? 'https://oauth2.googleapis.com/token' : 'https://appleid.apple.com/auth/token', $fields);
    unset($fields);
    $token = $result['id_token'] ?? null;
    if (!is_string($token) || strlen($token) > 16384 || substr_count($token, '.') !== 2) {
        throw new NodenoAccountHttpError(401, 'social_verification_failed');
    }
    $header = json_decode(Firebase\JWT\JWT::urlsafeB64Decode(explode('.', $token)[0]), true, 8, JSON_THROW_ON_ERROR);
    $kid = $header['kid'] ?? null;
    if (!is_string($kid) || strlen($kid) > 200) {throw new NodenoAccountHttpError(401, 'social_verification_failed');}
    $identity = nodenoSocialVerify($provider, $token, $configuration['clientId'], $flow['nonce'], nodenoSocialJwks($root, $provider, $kid));
    unset($token, $result);
    return $identity;
}
