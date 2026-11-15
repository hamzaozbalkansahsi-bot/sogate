<?php
declare(strict_types=1);
require_once __DIR__.'/localization.php';

require_once __DIR__ . '/oauth-jwt.php';

function nodenoSocialSchema(PDO $database): void
{
    nodenoAccountTransaction($database, static function () use ($database): void {
        $columns = array_column($database->query('PRAGMA table_info(users)')->fetchAll(), 'name');
        foreach (['password_configured' => 1, 'email_verified' => 0] as $column => $default) {
            if (!in_array($column, $columns, true)) {
                $database->exec('ALTER TABLE users ADD COLUMN ' . $column . ' INTEGER NOT NULL DEFAULT ' . $default);
            }
        }
        $database->exec("CREATE TABLE IF NOT EXISTS provider_identities (
            provider TEXT NOT NULL, subject TEXT NOT NULL, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            email TEXT NOT NULL, created_at INTEGER NOT NULL, PRIMARY KEY(provider,subject));
            CREATE INDEX IF NOT EXISTS provider_identities_user ON provider_identities(user_id);
            CREATE TABLE IF NOT EXISTS oauth_flows (
            state_hash TEXT PRIMARY KEY, provider TEXT NOT NULL, session_hash TEXT NOT NULL, browser_hash TEXT NOT NULL,
            data_json TEXT NOT NULL, phase TEXT NOT NULL, expires_at INTEGER NOT NULL);
            CREATE INDEX IF NOT EXISTS oauth_flows_expiry ON oauth_flows(expires_at);");
    });
}

function nodenoSocialOriginAllowed(string $origin): bool
{
    return in_array($origin, ['https://nodenohome.com', 'https://www.nodenohome.com',
        'https://nodenohome.com.tr', 'https://www.nodenohome.com.tr'], true);
}

function nodenoSocialConfiguration(string $root): array
{
    $file = $root . '/social-auth.json';
    if (!file_exists($file)) {
        return [];
    }
    if (is_link($file) || !is_file($file) || filesize($file) > 32768) {
        throw new RuntimeException('Invalid social authentication configuration');
    }
    $configuration = json_decode(file_get_contents($file), true, 12, JSON_THROW_ON_ERROR);
    if (!is_array($configuration) || ($configuration['schema'] ?? null) !== 1) {
        throw new RuntimeException('Invalid social authentication configuration');
    }
    return $configuration;
}

function nodenoSocialProvider(array $configuration, string $root, string $provider, string $origin): ?array
{
    if (!in_array($provider, ['google', 'apple'], true) || !nodenoSocialOriginAllowed($origin)) {
        return null;
    }
    $value = $configuration[$provider] ?? [];
    $callback = $origin . '/api/account/oauth/' . $provider . '/callback';
    if (!is_array($value) || ($value['enabled'] ?? false) !== true || !extension_loaded('openssl') || !extension_loaded('curl')
        || !is_array($value['redirectUris'] ?? null) || !in_array($callback, $value['redirectUris'], true)) {
        return null;
    }
    foreach (['clientId', ...($provider === 'google' ? ['clientSecret'] : ['teamId', 'keyId'])] as $field) {
        if (!is_string($value[$field] ?? null) || $value[$field] === '' || strlen($value[$field]) > 512
            || preg_match('/[\x00-\x20\x7f]/', $value[$field])) {
            return null;
        }
    }
    if ($provider === 'google' && !preg_match('/^[A-Za-z0-9_.-]+\.apps\.googleusercontent\.com$/D', $value['clientId'])) {
        return null;
    }
    if ($provider === 'apple') {
        if (!preg_match('/^[A-Z0-9]{10}$/D', $value['teamId']) || !preg_match('/^[A-Z0-9]{10}$/D', $value['keyId'])) {
            return null;
        }
        $key = $root . '/apple-signin.p8';
        if (is_link($key) || !is_file($key) || filesize($key) > 16384 || !is_readable($key)) {
            return null;
        }
        $private = openssl_pkey_get_private(file_get_contents($key));
        $details = $private === false ? false : openssl_pkey_get_details($private);
        if ($details === false || ($details['type'] ?? null) !== OPENSSL_KEYTYPE_EC || ($details['ec']['curve_name'] ?? '') !== 'prime256v1') {
            return null;
        }
        $value['privateKeyFile'] = $key;
    }
    $value['callback'] = $callback;
    return $value;
}

function nodenoSocialPublicStatus(PDO $database, string $root, ?array $user, string $origin): array
{
    $configuration = nodenoSocialConfiguration($root);
    $providers = [];
    foreach (['google', 'apple'] as $provider) {
        $emails = [];
        if ($user !== null) {
            $query = $database->prepare('SELECT email FROM provider_identities WHERE user_id=? AND provider=? ORDER BY created_at');
            $query->execute([$user['id'], $provider]);
            $emails = array_column($query->fetchAll(), 'email');
        }
        $providers[$provider] = ['ready' => nodenoSocialProvider($configuration, $root, $provider, $origin) !== null,
            'linked' => count($emails) > 0, 'emails' => $emails];
    }
    $proposal = $_SESSION['socialMerge'] ?? null;
    if ($proposal !== null && ($user === null || ($proposal['targetId'] ?? '') !== $user['id'] || ($proposal['expiresAt'] ?? 0) < time())) {
        $proposal = null;
        unset($_SESSION['socialMerge']);
    }
    $merge = $proposal === null ? null : ['provider' => $proposal['provider'], 'email' => $proposal['email'],
        'confirmation' => $proposal['confirmation']];
    return ['providers' => $providers, 'hasPassword' => $user === null ? null : (bool) ($user['password_configured'] ?? 1), 'merge' => $merge];
}

function nodenoSocialVerify(string $provider, string $token, string $clientId, string $nonce, array $jwks): array
{
    try {
        if (!in_array($provider, ['google', 'apple'], true) || strlen($token) > 16384 || substr_count($token, '.') !== 2) {
            throw new UnexpectedValueException();
        }
        $header = json_decode(Firebase\JWT\JWT::urlsafeB64Decode(explode('.', $token)[0]), true, 8, JSON_THROW_ON_ERROR);
        if (($header['alg'] ?? '') !== 'RS256' || !is_string($header['kid'] ?? null) || strlen($header['kid']) > 200) {
            throw new UnexpectedValueException();
        }
        $jwks['keys'] = array_values(array_filter($jwks['keys'] ?? [], static function ($key): bool {
            return is_array($key) && ($key['kty'] ?? '') === 'RSA' && ($key['alg'] ?? 'RS256') === 'RS256'
                && ($key['use'] ?? 'sig') === 'sig';
        }));
        if (count($jwks['keys']) > 32) {
            throw new UnexpectedValueException();
        }
        Firebase\JWT\JWT::$leeway = 60;
        $claims = (array) Firebase\JWT\JWT::decode($token, Firebase\JWT\JWK::parseKeySet($jwks, 'RS256'));
        $issuers = $provider === 'google' ? ['https://accounts.google.com', 'accounts.google.com'] : ['https://appleid.apple.com'];
        $audience = $claims['aud'] ?? null;
        $audienceValid = is_string($audience) ? hash_equals($clientId, $audience) :
            (is_array($audience) && in_array($clientId, $audience, true) && ($claims['azp'] ?? '') === $clientId);
        if (!in_array($claims['iss'] ?? null, $issuers, true) || !$audienceValid
            || (isset($claims['azp']) && $claims['azp'] !== $clientId)
            || !is_string($claims['nonce'] ?? null) || !hash_equals($nonce, $claims['nonce'])
            || !is_int($claims['iat'] ?? null) || $claims['iat'] > time() + 60 || $claims['iat'] < time() - 7200
            || !is_int($claims['exp'] ?? null) || $claims['exp'] < time() - 60 || $claims['exp'] > time() + 86400
            || !in_array($claims['email_verified'] ?? false, [true, 'true'], true)) {
            throw new UnexpectedValueException();
        }
        $subject = nodenoAccountText($claims['sub'] ?? null, 1, 255, 'social_verification_failed');
        $email = nodenoAccountEmail($claims['email'] ?? null);
        $name = is_string($claims['name'] ?? null) ? trim($claims['name']) : explode('@', $email)[0];
        if (!preg_match('//u', $name) || preg_match('/[\x00-\x1f\x7f]/', $name) || strlen($name) > 300 || preg_match_all('/./us', $name) < 2) {
            $name = 'NODENO';
        }
        $name = preg_replace('/^(.{1,100}).*$/us', '$1', $name);
        return ['provider' => $provider, 'subject' => $subject, 'email' => $email, 'emailVerified' => true, 'name' => $name];
    } catch (Throwable $exception) {
        throw new NodenoAccountHttpError(401, 'social_verification_failed');
    }
}

function nodenoSocialResolveIdentity(PDO $database, array $identity, ?array $target, string $intent): array
{
    return nodenoAccountTransaction($database, static function () use ($database, $identity, $target, $intent): array {
        if (($identity['emailVerified'] ?? false) !== true || !in_array($identity['provider'] ?? null, ['google', 'apple'], true)) {
            throw new NodenoAccountHttpError(401, 'social_verification_failed');
        }
        if ($target !== null) {
            $version = $database->prepare('SELECT auth_version FROM users WHERE id=?');$version->execute([$target['id']]);
            if ((int) $version->fetchColumn() !== (int) $target['auth_version']) {throw new NodenoAccountHttpError(409, 'account_changed');}
        }
        $read = $database->prepare('SELECT users.* FROM provider_identities JOIN users ON users.id=provider_identities.user_id WHERE provider=? AND subject=?');
        $read->execute([$identity['provider'], $identity['subject']]);
        $owner = $read->fetch();
        if ($intent === 'reauth' && (!$target || !$owner || $target['id'] !== $owner['id'])) {
            throw new NodenoAccountHttpError(409, 'social_identity_mismatch');
        }
        if ($owner) {
            if ($target && $intent === 'link' && $target['id'] !== $owner['id']) {
                return ['user' => null, 'mergeUser' => $owner];
            }
            return ['user' => $owner];
        }
        if ($target === null) {
            $existing = $database->prepare('SELECT id FROM users WHERE email=?');
            $existing->execute([$identity['email']]);
            if ($existing->fetchColumn() !== false) {
                throw new NodenoAccountHttpError(409, 'social_existing_account');
            }
            $id = bin2hex(random_bytes(16));
            $insert = $database->prepare('INSERT INTO users(id,email,name,password_hash,password_configured,email_verified,created_at,updated_at) VALUES (?,?,?,?,0,1,?,?)');
            $insert->execute([$id, $identity['email'], $identity['name'], password_hash(bin2hex(random_bytes(32)), PASSWORD_DEFAULT), time(), time()]);
            $read = $database->prepare('SELECT * FROM users WHERE id=?');$read->execute([$id]);$target = $read->fetch();
        }
        $insert = $database->prepare('INSERT INTO provider_identities(provider,subject,user_id,email,created_at) VALUES (?,?,?,?,?)');
        $insert->execute([$identity['provider'], $identity['subject'], $target['id'], $identity['email'], time()]);
        if (strcasecmp($target['email'], $identity['email']) === 0) {
            $update = $database->prepare('UPDATE users SET email_verified=1 WHERE id=?');$update->execute([$target['id']]);$target['email_verified'] = 1;
        }
        return ['user' => $target];
    });
}

function nodenoSocialMerge(PDO $database, array $target, array $source, array $catalog): array
{
    return nodenoAccountTransaction($database, static function () use ($database, $target, $source, $catalog): array {
        if ($target['id'] === $source['id']) {
            throw new NodenoAccountHttpError(409, 'social_identity_mismatch');
        }
        foreach ([$target, $source] as $expected) {
            $check = $database->prepare('SELECT auth_version FROM users WHERE id=?');$check->execute([$expected['id']]);
            if ((int) $check->fetchColumn() !== (int) $expected['auth_version']) {
                throw new NodenoAccountHttpError(409, 'account_changed');
            }
        }
        $cart = [];$favorites = [];
        foreach ([$target, $source] as $user) {
            $read = $database->prepare('SELECT cart_json,favorites_json FROM account_state WHERE user_id=?');$read->execute([$user['id']]);$row = $read->fetch();
            $state = $row ? nodenoAccountState(['cart' => json_decode($row['cart_json'], true, 16, JSON_THROW_ON_ERROR),
                'favorites' => json_decode($row['favorites_json'], true, 16, JSON_THROW_ON_ERROR)], $catalog, false) : ['cart' => [], 'favorites' => []];
            foreach ($state['cart'] as $item) {
                $key=$item['key']??$item['id'];$quantity=($cart[$key]['quantity']??0)+$item['quantity'];$cart[$key]=$item;$cart[$key]['quantity']=$quantity;
                if ($quantity > (isset($item['options'])?10000:99) || count($cart) > 100) {
                    throw new NodenoAccountHttpError(409, 'social_merge_cart_limit');
                }
            }
            $favorites = array_values(array_unique(array_merge($favorites, $state['favorites'])));
        }
        $addresses = $database->prepare('SELECT COUNT(*) FROM addresses WHERE user_id IN (?,?)');$addresses->execute([$target['id'], $source['id']]);
        if ((int) $addresses->fetchColumn() > 20) {
            throw new NodenoAccountHttpError(409, 'social_merge_address_limit');
        }
        $targetCollections = nodenoCollectionsRead($database, $target['id'], $catalog);
        $sourceCollections = nodenoCollectionsRead($database, $source['id'], $catalog);
        try {
            $mergedCollections = nodenoCollectionsMerge($targetCollections['collections'], $sourceCollections['collections'], $catalog);
        } catch (NodenoAccountHttpError $exception) {
            if ($exception->errorCode === 'collections_limit') { throw new NodenoAccountHttpError(409, 'social_merge_collections_limit'); }
            throw $exception;
        }
        nodenoCollectionsStore($database, $target['id'], $mergedCollections, $targetCollections['version'] + 1);
        $write = $database->prepare('INSERT INTO account_state(user_id,cart_json,favorites_json,updated_at) VALUES (?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET cart_json=excluded.cart_json,favorites_json=excluded.favorites_json,updated_at=excluded.updated_at');
        $rows = array_values($cart);
        $write->execute([$target['id'], json_encode($rows, JSON_THROW_ON_ERROR), json_encode($favorites, JSON_THROW_ON_ERROR), time()]);
        $hasDefault = $database->prepare('SELECT COUNT(*) FROM addresses WHERE user_id=? AND is_default=1');$hasDefault->execute([$target['id']]);
        if ((int) $hasDefault->fetchColumn() > 0) {
            $reset = $database->prepare('UPDATE addresses SET is_default=0 WHERE user_id=?');$reset->execute([$source['id']]);
        }
        foreach (['addresses', 'orders', 'provider_identities'] as $table) {
            $move = $database->prepare('UPDATE ' . $table . ' SET user_id=? WHERE user_id=?');$move->execute([$target['id'], $source['id']]);
        }
        $delete = $database->prepare('DELETE FROM users WHERE id=?');$delete->execute([$source['id']]);
        $update = $database->prepare('UPDATE users SET auth_version=auth_version+1,updated_at=? WHERE id=?');$update->execute([time(), $target['id']]);
        $read = $database->prepare('SELECT * FROM users WHERE id=?');$read->execute([$target['id']]);return $read->fetch();
    });
}

function nodenoSocialCreateFlow(PDO $database, string $provider, array $configuration, array $context): array
{
    $suffix = '/api/account/oauth/' . $provider . '/callback';
    $callback = $configuration['callback'] ?? '';
    $origin = is_string($callback) && str_ends_with($callback, $suffix) ? substr($callback, 0, -strlen($suffix)) : '';
    $intent = $context['intent'] ?? 'login';
    if (!in_array($provider, ['google', 'apple'], true) || !nodenoSocialOriginAllowed($origin)
        || !in_array($intent, ['login', 'link', 'reauth'], true)) {
        throw new NodenoAccountHttpError(422, 'invalid_social_request');
    }
    $user = $context['user'] ?? null;
    if ($intent !== 'login' && $user === null) {
        throw new NodenoAccountHttpError(401, 'authentication_required');
    }
    $state = bin2hex(random_bytes(32));$nonce = bin2hex(random_bytes(32));$verifier = bin2hex(random_bytes(32));
    $data = ['intent' => $intent, 'targetId' => $user['id'] ?? null, 'authVersion' => $user['auth_version'] ?? null,
        'locale' => in_array($context['locale'] ?? '', NODENO_STORE_LOCALES, true) ? $context['locale'] : 'tr',
        'next' => ($context['next'] ?? '') === 'checkout' ? 'checkout' : 'account', 'nonce' => $nonce,
        'verifier' => $verifier, 'callback' => $callback];
    nodenoAccountTransaction($database, static function () use ($database, $state, $provider, $context, $data): void {
        $delete = $database->prepare('DELETE FROM oauth_flows WHERE expires_at < ?');$delete->execute([time()]);
        $insert = $database->prepare('INSERT INTO oauth_flows VALUES (?,?,?,?,?,?,?)');
        $insert->execute([hash('sha256', $state), $provider, hash('sha256', $context['sessionId']),
            hash('sha256', $context['browser']), json_encode($data, JSON_THROW_ON_ERROR), 'pending', time() + 600]);
    });
    $parameters = ['client_id' => $configuration['clientId'], 'redirect_uri' => $callback, 'response_type' => 'code',
        'scope' => $provider === 'google' ? 'openid email profile' : 'name email', 'state' => $state, 'nonce' => $nonce];
    if ($provider === 'google') {
        $parameters['code_challenge_method'] = 'S256';
        $parameters['code_challenge'] = rtrim(strtr(base64_encode(hash('sha256', $verifier, true)), '+/', '-_'), '=');
        $parameters['prompt'] = 'select_account';
    } else {
        $parameters['response_mode'] = 'form_post';
    }
    return ['state' => $state, 'url' => ($provider === 'google' ? 'https://accounts.google.com/o/oauth2/v2/auth' :
        'https://appleid.apple.com/auth/authorize') . '?' . http_build_query($parameters, '', '&', PHP_QUERY_RFC3986)];
}

function nodenoSocialClaimFlow(PDO $database, string $state, string $provider, string $browser): array
{
    return nodenoAccountTransaction($database, static function () use ($database, $state, $provider, $browser): array {
        if (!preg_match('/^[a-f0-9]{64}$/D', $state)) {
            throw new NodenoAccountHttpError(400, 'social_state_invalid');
        }
        $read = $database->prepare('SELECT * FROM oauth_flows WHERE state_hash=?');$read->execute([hash('sha256', $state)]);$flow = $read->fetch();
        if (!$flow || $flow['provider'] !== $provider || $flow['phase'] !== 'pending' || (int) $flow['expires_at'] < time()
            || !hash_equals($flow['browser_hash'], hash('sha256', $browser))) {
            throw new NodenoAccountHttpError(400, 'social_state_invalid');
        }
        $update = $database->prepare("UPDATE oauth_flows SET phase='processing' WHERE state_hash=?");$update->execute([hash('sha256', $state)]);
        return json_decode($flow['data_json'], true, 12, JSON_THROW_ON_ERROR);
    });
}

function nodenoSocialSaveVerified(PDO $database, string $state, array $data, array $identity): void
{
    unset($data['verifier']);$data['identity'] = $identity;
    $update = $database->prepare("UPDATE oauth_flows SET phase='verified',data_json=?,expires_at=? WHERE state_hash=? AND phase='processing'");
    $update->execute([json_encode($data, JSON_THROW_ON_ERROR), time() + 120, hash('sha256', $state)]);
    if ($update->rowCount() !== 1) {
        throw new NodenoAccountHttpError(400, 'social_state_invalid');
    }
}

function nodenoSocialCompleteFlow(PDO $database, string $state, string $browser, string $sessionId): array
{
    return nodenoAccountTransaction($database, static function () use ($database, $state, $browser, $sessionId): array {
        if (!preg_match('/^[a-f0-9]{64}$/D', $state)) {
            throw new NodenoAccountHttpError(400, 'social_state_invalid');
        }
        $read = $database->prepare('SELECT * FROM oauth_flows WHERE state_hash=?');$read->execute([hash('sha256', $state)]);$flow = $read->fetch();
        if (!$flow || $flow['phase'] !== 'verified' || (int) $flow['expires_at'] < time()
            || !hash_equals($flow['browser_hash'], hash('sha256', $browser)) || !hash_equals($flow['session_hash'], hash('sha256', $sessionId))) {
            throw new NodenoAccountHttpError(400, 'social_state_invalid');
        }
        $delete = $database->prepare('DELETE FROM oauth_flows WHERE state_hash=?');$delete->execute([hash('sha256', $state)]);
        return json_decode($flow['data_json'], true, 12, JSON_THROW_ON_ERROR);
    });
}
