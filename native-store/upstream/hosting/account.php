<?php
declare(strict_types=1);

/** Durable account storage is explicitly supplied by the deployment, never by HTTP input. */
final class NodenoAccountHttpError extends RuntimeException
{
    public int $status;
    public string $errorCode;
    public array $headers;

    public function __construct(int $status, string $errorCode, array $headers = [])
    {
        parent::__construct($errorCode);
        $this->status = $status;
        $this->errorCode = $errorCode;
        $this->headers = $headers;
    }
}

require_once __DIR__ . '/social-auth.php';
require_once __DIR__ . '/social-provider.php';
require_once __DIR__ . '/social-http.php';
require_once __DIR__ . '/collections.php';
require_once __DIR__ . '/membership-legal.php';

function nodenoAccountJson(array $value, int $status = 200, array $headers = []): void
{
    nodenoRespond(json_encode($value, JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE), $status,
        'application/json; charset=utf-8', array_merge(['Cache-Control' => 'no-store', 'Vary' => 'Cookie', 'X-Content-Type-Options' => 'nosniff'], $headers));
}

function nodenoAccountWithin(string $candidate, string $directory): bool
{
    $candidate = str_replace('\\', '/', $candidate);
    $directory = rtrim(str_replace('\\', '/', $directory), '/');
    if (DIRECTORY_SEPARATOR === '\\') {
        $candidate = strtolower($candidate);
        $directory = strtolower($directory);
    }
    return $candidate === $directory || strpos($candidate, $directory . '/') === 0;
}

function nodenoAccountStorage(string $storageRoot): string
{
    if ($storageRoot === '' || strpos($storageRoot, "\0") !== false
        || !preg_match('~^(?:[A-Za-z]:[\\\\/]|/)~', $storageRoot) || is_link($storageRoot)) {
        throw new RuntimeException('Invalid account storage');
    }
    $requested = rtrim($storageRoot, '/\\');
    $parent = realpath(dirname($requested));
    $basename = basename($requested);
    if ($parent === false || $basename === '.' || $basename === '..' || $basename === '') {
        throw new RuntimeException('Invalid account storage');
    }
    $candidate = realpath($requested);
    if ($candidate === false) {
        $candidate = $parent . DIRECTORY_SEPARATOR . $basename;
    }
    if (preg_match('~(?:^|/)(?:public_html|public_ftp|www|htdocs|httpdocs|nodeno-releases|\\.nodeno-releases)(?:/|$)~i', str_replace('\\', '/', $candidate))) {
        throw new RuntimeException('Account storage cannot be in a public or versioned release tree');
    }
    // dirname(__DIR__) is the checkout/release root; account data must survive its replacement.
    $forbidden = [realpath(dirname(__DIR__)), realpath(__DIR__)];
    foreach (['DOCUMENT_ROOT', 'CONTEXT_DOCUMENT_ROOT'] as $key) {
        if (isset($_SERVER[$key]) && $_SERVER[$key] !== '') {
            $documentRoot = realpath($_SERVER[$key]);
            if ($documentRoot === false) {
                throw new RuntimeException('Invalid document root');
            }
            $forbidden[] = $documentRoot;
        }
    }
    foreach ($forbidden as $directory) {
        if ($directory !== false && nodenoAccountWithin($candidate, $directory)) {
            throw new RuntimeException('Account storage must be outside public and release roots');
        }
    }
    if (!is_dir($candidate) && !mkdir($candidate, 0700)) {
        throw new RuntimeException('Account storage unavailable');
    }
    $root = realpath($candidate);
    if ($root === false || !is_writable($root) || is_link($requested)) {
        throw new RuntimeException('Account storage unavailable');
    }
    foreach ($forbidden as $directory) {
        if ($directory !== false && nodenoAccountWithin($root, $directory)) {
            throw new RuntimeException('Unsafe account storage');
        }
    }
    chmod($root, 0700);
    return $root;
}

function nodenoAccountDatabase(string $root): PDO
{
    $filename = $root . '/accounts.sqlite';
    if (is_link($filename) || (file_exists($filename) && !is_file($filename))) {
        throw new RuntimeException('Unsafe account database');
    }
    $database = new PDO('sqlite:' . $filename, null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC, PDO::ATTR_EMULATE_PREPARES => false]);
    chmod($filename, 0600);
    $database->exec('PRAGMA busy_timeout = 5000; PRAGMA foreign_keys = ON; PRAGMA journal_mode = WAL; PRAGMA synchronous = FULL;');
    $database->exec("CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE COLLATE NOCASE, name TEXT NOT NULL,
        password_hash TEXT NOT NULL, auth_version INTEGER NOT NULL DEFAULT 1,
        created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS account_state (
        user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
        cart_json TEXT NOT NULL DEFAULT '[]', favorites_json TEXT NOT NULL DEFAULT '[]', updated_at INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS addresses (
        id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        data_json TEXT NOT NULL, is_default INTEGER NOT NULL DEFAULT 0, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL
    );
    CREATE UNIQUE INDEX IF NOT EXISTS one_default_address ON addresses(user_id) WHERE is_default = 1;
    CREATE INDEX IF NOT EXISTS addresses_user ON addresses(user_id);
    CREATE TABLE IF NOT EXISTS orders (
        id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), status TEXT NOT NULL,
        currency TEXT NOT NULL, total_minor INTEGER NOT NULL, items_json TEXT NOT NULL, created_at INTEGER NOT NULL
    );
    CREATE INDEX IF NOT EXISTS orders_user ON orders(user_id);
    CREATE TABLE IF NOT EXISTS shipments (
        id TEXT PRIMARY KEY, order_id TEXT NOT NULL REFERENCES orders(id), carrier TEXT NOT NULL DEFAULT '',
        tracking_number TEXT NOT NULL DEFAULT '', tracking_url TEXT NOT NULL DEFAULT '', status TEXT NOT NULL, updated_at INTEGER NOT NULL
    );
    CREATE INDEX IF NOT EXISTS shipments_order ON shipments(order_id);
    CREATE TABLE IF NOT EXISTS rate_limits (key_hash TEXT PRIMARY KEY, window_start INTEGER NOT NULL, count INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS account_settings (name TEXT PRIMARY KEY, value TEXT NOT NULL);");
    $statement = $database->prepare('INSERT OR IGNORE INTO account_settings(name, value) VALUES (?, ?)');
    $statement->execute(['rate_key', bin2hex(random_bytes(32))]);
    nodenoSocialSchema($database);
    nodenoCollectionsSchema($database);
    nodenoMembershipSchema($database);
    return $database;
}

/** SQLite write transactions acquire the lock before reading counters/ownership/defaults. */
function nodenoAccountTransaction(PDO $database, callable $operation)
{
    $database->exec('BEGIN IMMEDIATE');
    try {
        $result = $operation();
        $database->exec('COMMIT');
        return $result;
    } catch (Throwable $exception) {
        $database->exec('ROLLBACK');
        throw $exception;
    }
}

function nodenoAccountRateLimit(PDO $database, string $scope, int $limit, int $window, string $subject = ''): void
{
    $secret = $database->query("SELECT value FROM account_settings WHERE name = 'rate_key'")->fetchColumn();
    $ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown'; // Never trust client supplied proxy headers.
    $key = hash_hmac('sha256', $scope . "\0" . $ip . "\0" . $subject, (string) $secret);
    $now = time();
    $count = nodenoAccountTransaction($database, static function () use ($database, $key, $now, $window): int {
        $read = $database->prepare('SELECT window_start, count FROM rate_limits WHERE key_hash = ?');
        $read->execute([$key]);
        $row = $read->fetch();
        $active = $row && (int) $row['window_start'] > $now - $window;
        $start = $active ? (int) $row['window_start'] : $now;
        $count = $active ? (int) $row['count'] + 1 : 1;
        $write = $database->prepare('INSERT INTO rate_limits(key_hash, window_start, count) VALUES (?, ?, ?)
            ON CONFLICT(key_hash) DO UPDATE SET window_start = excluded.window_start, count = excluded.count');
        $write->execute([$key, $start, $count]);
        $cleanup = $database->prepare('DELETE FROM rate_limits WHERE window_start < ?');
        $cleanup->execute([$now - 86400]);
        return $count;
    });
    if ($count > $limit) {
        throw new NodenoAccountHttpError(429, 'rate_limited', ['Retry-After' => (string) $window]);
    }
}

function nodenoAccountRotate(?array $user = null): void
{
    $_SESSION = ['csrf' => bin2hex(random_bytes(32)), 'createdAt' => time(), 'lastActivity' => time()];
    if ($user !== null) {
        $_SESSION['userId'] = $user['id'];
        $_SESSION['authVersion'] = (int) $user['auth_version'];
    }
    if (!session_regenerate_id(true)) {
        throw new RuntimeException('Account session unavailable');
    }
}

function nodenoAccountSession(string $root, PDO $database): ?array
{
    if (session_status() !== PHP_SESSION_NONE) {
        throw new RuntimeException('Account requires an isolated session');
    }
    $directory = $root . '/sessions';
    if (is_link($directory) || (!is_dir($directory) && !mkdir($directory, 0700))) {
        throw new RuntimeException('Unsafe session storage');
    }
    $sessions = realpath($directory);
    if ($sessions === false || !nodenoAccountWithin($sessions, $root)) {
        throw new RuntimeException('Unsafe session storage');
    }
    chmod($sessions, 0700);
    ini_set('session.save_handler', 'files');
    ini_set('session.use_strict_mode', '1');
    ini_set('session.use_only_cookies', '1');
    ini_set('session.use_trans_sid', '0');
    ini_set('session.gc_maxlifetime', '43200');
    session_save_path($sessions);
    session_name('NODENOSESSID');
    session_set_cookie_params(['lifetime' => 0, 'path' => '/', 'secure' => true, 'httponly' => true, 'samesite' => 'Lax']);
    if (!session_start()) {
        throw new RuntimeException('Account session unavailable');
    }
    $now = time();
    if (!isset($_SESSION['csrf'], $_SESSION['createdAt'], $_SESSION['lastActivity'])
        || $now - (int) $_SESSION['createdAt'] > 43200 || $now - (int) $_SESSION['lastActivity'] > 1800) {
        nodenoAccountRotate();
    }
    $_SESSION['lastActivity'] = $now;
    if (!isset($_SESSION['userId'], $_SESSION['authVersion'])) {
        return null;
    }
    $statement = $database->prepare('SELECT * FROM users WHERE id = ?');
    $statement->execute([$_SESSION['userId']]);
    $user = $statement->fetch();
    if (!$user || (int) $user['auth_version'] !== (int) $_SESSION['authVersion']) {
        nodenoAccountRotate();
        return null;
    }
    return $user;
}

function nodenoAccountView(?array $user): array
{
    return ['user' => $user === null ? null : ['id' => $user['id'], 'email' => $user['email'], 'name' => $user['name'],
        'emailVerified' => (bool) ($user['email_verified'] ?? 0), 'hasPassword' => (bool) ($user['password_configured'] ?? 1)],
        'csrfToken' => $_SESSION['csrf'], 'capabilities' => ['registration' => true, 'passwordReset' => false, 'checkout' => false]];
}

function nodenoAccountBody(): array
{
    $scheme = (!empty($_SERVER['HTTPS']) && strtolower((string) $_SERVER['HTTPS']) !== 'off') || (int) ($_SERVER['SERVER_PORT'] ?? 0) === 443 ? 'https' : 'http';
    $host = $_SERVER['HTTP_HOST'] ?? '';
    $origin = $_SERVER['HTTP_ORIGIN'] ?? '';
    if ($host === '' || !preg_match('~^[a-z0-9.\-\[\]:]+$~iD', $host)
        || !hash_equals(strtolower($scheme . '://' . $host), strtolower($origin))) {
        throw new NodenoAccountHttpError(403, 'origin_rejected');
    }
    $token = $_SERVER['HTTP_X_CSRF_TOKEN'] ?? '';
    if (!is_string($token) || !hash_equals($_SESSION['csrf'], $token)) {
        throw new NodenoAccountHttpError(403, 'csrf_rejected');
    }
    if (!preg_match('~^application/json(?:\s*;\s*charset=utf-8)?$~iD', trim($_SERVER['CONTENT_TYPE'] ?? ''))) {
        throw new NodenoAccountHttpError(415, 'json_required');
    }
    if ((int) ($_SERVER['CONTENT_LENGTH'] ?? 0) > 32768) {
        throw new NodenoAccountHttpError(413, 'body_too_large');
    }
    $stream = fopen('php://input', 'rb');
    if ($stream === false) {
        throw new NodenoAccountHttpError(400, 'invalid_json');
    }
    try {
        $body = stream_get_contents($stream, 32769);
    } finally {
        fclose($stream);
    }
    if ($body === false || strlen($body) > 32768) {
        throw new NodenoAccountHttpError(413, 'body_too_large');
    }
    try {
        $value = json_decode($body, true, 16, JSON_THROW_ON_ERROR);
    } catch (JsonException $exception) {
        throw new NodenoAccountHttpError(400, 'invalid_json');
    }
    if (!is_array($value) || substr(ltrim($body), 0, 1) !== '{') {
        throw new NodenoAccountHttpError(400, 'invalid_json');
    }
    return $value;
}

function nodenoAccountText($value, int $minimum, int $maximum, string $error): string
{
    if (!is_string($value) || !preg_match('//u', $value) || preg_match('/[\x00-\x1f\x7f]/u', $value)) {
        throw new NodenoAccountHttpError(422, $error);
    }
    $value = trim($value);
    $length = preg_match_all('/./us', $value);
    if ($length < $minimum || $length > $maximum) {
        throw new NodenoAccountHttpError(422, $error);
    }
    return $value;
}

function nodenoAccountEmail($value): string
{
    if (!is_string($value) || strlen($value) > 254 || !filter_var($value, FILTER_VALIDATE_EMAIL)) {
        throw new NodenoAccountHttpError(422, 'invalid_email');
    }
    return strtolower($value);
}

function nodenoAccountPassword($value): string
{
    // Count Unicode code points for the minimum; bcrypt's byte ceiling must never truncate input.
    if (!is_string($value) || strlen($value) > 72 || strpos($value, "\0") !== false
        || !preg_match('//u', $value) || preg_match_all('/./us', $value) < 12) {
        throw new NodenoAccountHttpError(422, 'invalid_password');
    }
    return $value;
}

function nodenoAccountRequireUser(?array $user): array
{
    if ($user === null) {
        throw new NodenoAccountHttpError(401, 'authentication_required');
    }
    return $user;
}

function nodenoAccountState(array $value, array $catalog, bool $strict = true): array
{
    $known = [];
    foreach ($catalog['products'] ?? [] as $product) {
        if (is_array($product) && isset($product['id'])) {
            $known[(string) $product['id']] = $product;
        }
    }
    $cart = $value['cart'] ?? null;
    $favorites = $value['favorites'] ?? null;
    if (!is_array($cart) || !array_is_list($cart) || count($cart) > 100
        || !is_array($favorites) || !array_is_list($favorites) || count($favorites) > max(667,count($known))) {
        throw new NodenoAccountHttpError(422, 'invalid_state');
    }
    $cleanCart = [];
    $seen = [];
    foreach ($cart as $item) {
        if (!is_array($item) || !is_string($item['id'] ?? null) || !is_int($item['quantity'] ?? null)
            || $item['quantity'] < 1 || $item['quantity'] > (in_array($known[$item['id']]['productType']??'',['door','cabinet-front'],true)?10000:99)) {
            throw new NodenoAccountHttpError(422, 'invalid_state');
        }
        if (!isset($known[$item['id']])) {
            if ($strict) {
                throw new NodenoAccountHttpError(422, 'invalid_product');
            }
            continue;
        }
        if(($known[$item['id']]['productType']??'')==='supplier-item'){
            if($known[$item['id']]['variationSelectionRequired']??false){if(!$strict)continue;throw new NodenoAccountHttpError(422,'invalid_state');}
            $q=$known[$item['id']]['quantityPolicy'];$min=$q['minimum'];$step=$q['step'];
            if($item['quantity']<$min||($item['quantity']-$min)%$step!==0){if(!$strict)continue;throw new NodenoAccountHttpError(422,'invalid_state');}
        }
        $line=['id'=>$item['id'],'quantity'=>$item['quantity']];
        if(in_array($known[$item['id']]['productType']??'',['door','cabinet-front'],true)){
            if(!function_exists('nodenoDoorCartLine'))require_once __DIR__.'/door-commerce.php';
            try{$line=($known[$item['id']]['productType']??'')==='door'?nodenoDoorCartLine($item,$known[$item['id']]):nodenoFrontCartLine($item,$known[$item['id']]);}catch(InvalidArgumentException $e){if(!$strict)continue;throw new NodenoAccountHttpError(422,'invalid_state');}
        }
        $key=$line['key']??$line['id'];if(isset($seen[$key]))throw new NodenoAccountHttpError(422,'invalid_state');$seen[$key]=true;$cleanCart[]=$line;
    }
    $cleanFavorites = [];
    foreach ($favorites as $id) {
        if (!is_string($id) || !isset($known[$id])) {
            if ($strict) {
                throw new NodenoAccountHttpError(422, 'invalid_product');
            }
            continue;
        }
        if (!in_array($id, $cleanFavorites, true)) {
            $cleanFavorites[] = $id;
        }
    }
    return ['cart' => $cleanCart, 'favorites' => $cleanFavorites];
}

function nodenoAccountAddress(array $value): array
{
    $result = [];
    foreach (['label' => [1, 60], 'name' => [2, 100], 'phone' => [7, 25], 'country' => [2, 80],
        'city' => [1, 80], 'district' => [1, 80], 'postalCode' => [0, 20], 'line1' => [5, 250], 'line2' => [0, 250]] as $key => $bounds) {
        $result[$key] = nodenoAccountText($value[$key] ?? (in_array($key, ['postalCode', 'line2'], true) ? '' : null), $bounds[0], $bounds[1], 'invalid_address');
    }
    $digits = preg_replace('/[^0-9]/', '', $result['phone']);
    if (!preg_match('/^\+?[0-9 ()\-.]+$/D', $result['phone']) || strlen($digits) < 7 || strlen($digits) > 15
        || (isset($value['isDefault']) && !is_bool($value['isDefault']))) {
        throw new NodenoAccountHttpError(422, 'invalid_address');
    }
    $result['isDefault'] = $value['isDefault'] ?? false;
    return $result;
}

function nodenoAccountAddresses(PDO $database, string $userId): array
{
    $read = $database->prepare('SELECT id, data_json, is_default FROM addresses WHERE user_id = ? ORDER BY created_at, id');
    $read->execute([$userId]);
    $result = [];
    foreach ($read->fetchAll() as $row) {
        $value = json_decode($row['data_json'], true, 16, JSON_THROW_ON_ERROR);
        $result[] = array_merge($value, ['id' => $row['id'], 'isDefault' => (bool) $row['is_default']]);
    }
    return $result;
}

/** Returns false outside /api/account; recognized requests always emit one JSON response. */
function nodenoHandleAccountRequest(string $path, string $method, array $catalog, string $storageRoot): bool
{
    if ($path !== '/api/account' && strpos($path, '/api/account/') !== 0) {
        return false;
    }
    $previousMask = umask(0077);
    try {
        if (nodenoHandleSocialRequest($path, $method, $catalog, $storageRoot)) {
            return true;
        }
        $routes = ['/api/account' => ['GET', 'HEAD', 'DELETE'], '/api/account/register' => ['POST'], '/api/account/login' => ['POST'],
            '/api/account/logout' => ['POST'], '/api/account/profile' => ['PATCH'], '/api/account/password' => ['POST'],
            '/api/account/password-reset' => ['POST'], '/api/account/state' => ['GET', 'HEAD', 'PUT'],
            '/api/account/collections' => ['GET', 'HEAD', 'PUT'], '/api/account/collections/merge' => ['POST'],
            '/api/account/addresses' => ['GET', 'HEAD', 'POST'], '/api/account/orders' => ['GET', 'HEAD', 'POST'],
            '/api/account/membership-terms' => ['GET', 'HEAD']];
        $addressId = null;
        if (preg_match('~^/api/account/addresses/([a-f0-9]{32})$~D', $path, $match)) {
            $addressId = $match[1];
            $allowed = ['PATCH', 'DELETE'];
        } else {
            $allowed = $routes[$path] ?? null;
        }
        if ($allowed === null) {
            throw new NodenoAccountHttpError(404, 'not_found');
        }
        if (!in_array($method, $allowed, true)) {
            throw new NodenoAccountHttpError(405, 'method_not_allowed', ['Allow' => implode(', ', $allowed)]);
        }
        $root = nodenoAccountStorage($storageRoot);
        $database = nodenoAccountDatabase($root);
        $user = nodenoAccountSession($root, $database);
        $mutation = !in_array($method, ['GET', 'HEAD'], true);
        $body = $mutation ? nodenoAccountBody() : [];
        if ($mutation) {
            nodenoAccountRateLimit($database, 'mutations', 120, 600);
        }
        if ($path === '/api/account' && $method === 'DELETE') {
            $user = nodenoAccountRequireUser($user);
            $password = nodenoAccountPassword($body['password'] ?? null);
            nodenoAccountRateLimit($database, 'account-delete', 8, 900, $user['id']);
            nodenoAccountTransaction($database, static function () use ($database, $user, $password): void {
                $read = $database->prepare('SELECT password_hash, auth_version FROM users WHERE id = ?');
                $read->execute([$user['id']]);
                $current = $read->fetch();
                if (!$current || (int) $current['auth_version'] !== (int) $user['auth_version']) {
                    throw new NodenoAccountHttpError(409, 'account_changed');
                }
                if (!password_verify($password, $current['password_hash'])) {
                    throw new NodenoAccountHttpError(401, 'invalid_credentials');
                }
                $orders = $database->prepare('SELECT COUNT(*) FROM orders WHERE user_id = ?');
                $orders->execute([$user['id']]);
                if ((int) $orders->fetchColumn() > 0) {
                    throw new NodenoAccountHttpError(409, 'account_has_orders');
                }
                $delete = $database->prepare('DELETE FROM users WHERE id = ?');
                $delete->execute([$user['id']]);
            });
            nodenoAccountRotate();
            nodenoAccountJson(nodenoAccountView(null));
        } elseif ($path === '/api/account') {
            nodenoAccountJson(nodenoAccountView($user));
        } elseif ($path === '/api/account/membership-terms') {
            $terms = nodenoMembershipTerms($_GET['lang'] ?? 'tr');
            nodenoAccountJson(array_intersect_key($terms, array_flip(['version', 'hash', 'locale', 'url'])));
        } elseif ($path === '/api/account/register') {
            $name = nodenoAccountText($body['name'] ?? null, 2, 100, 'invalid_name');
            $email = nodenoAccountEmail($body['email'] ?? null);
            $password = nodenoAccountPassword($body['password'] ?? null);
            $membership = nodenoMembershipValidate($body);
            nodenoAccountRateLimit($database, 'registration', 5, 3600);
            $hash = password_hash($password, PASSWORD_DEFAULT);
            $id = bin2hex(random_bytes(16));
            $created = time();
            try {
                nodenoAccountTransaction($database, static function () use ($database, $id, $email, $name, $hash, $created, $membership): void {
                    $insert = $database->prepare('INSERT INTO users(id,email,name,password_hash,created_at,updated_at) VALUES (?,?,?,?,?,?)');
                    $insert->execute([$id, $email, $name, $hash, $created, $created]);
                    nodenoMembershipRecord($database, $id, $membership, $created);
                });
            } catch (PDOException $exception) {
                if ((string) $exception->getCode() === '23000') {
                    $duplicate = $database->prepare('SELECT COUNT(*) FROM users WHERE email = ?');
                    $duplicate->execute([$email]);
                    if ((int) $duplicate->fetchColumn() > 0) throw new NodenoAccountHttpError(409, 'email_already_registered');
                }
                throw $exception;
            }
            $user = ['id' => $id, 'email' => $email, 'name' => $name, 'auth_version' => 1];
            nodenoAccountRotate($user);
            nodenoAccountJson(nodenoAccountView($user), 201);
        } elseif ($path === '/api/account/login') {
            $email = nodenoAccountEmail($body['email'] ?? null);
            $password = nodenoAccountPassword($body['password'] ?? null);
            nodenoAccountRateLimit($database, 'login-ip', 30, 900);
            nodenoAccountRateLimit($database, 'login-account-ip', 8, 900, $email);
            $read = $database->prepare('SELECT * FROM users WHERE email = ?');
            $read->execute([$email]);
            $user = $read->fetch();
            // Constant work for nonexistent users; this hash is not an account or a secret.
            $dummy = '$2y$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2uheWG/igi.';
            if (!password_verify($password, $user ? $user['password_hash'] : $dummy) || !$user) {
                throw new NodenoAccountHttpError(401, 'invalid_credentials');
            }
            if (password_needs_rehash($user['password_hash'], PASSWORD_DEFAULT)) {
                $update = $database->prepare('UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ? AND password_hash = ?');
                $update->execute([password_hash($password, PASSWORD_DEFAULT), time(), $user['id'], $user['password_hash']]);
            }
            nodenoAccountRotate($user);
            nodenoAccountJson(nodenoAccountView($user));
        } elseif ($path === '/api/account/logout') {
            nodenoAccountRotate();
            nodenoAccountJson(nodenoAccountView(null));
        } elseif ($path === '/api/account/password-reset') {
            throw new NodenoAccountHttpError(503, 'email_delivery_unavailable');
        } else {
            $user = nodenoAccountRequireUser($user);
            $userId = $user['id'];
            if ($path === '/api/account/profile') {
                $name = nodenoAccountText($body['name'] ?? null, 2, 100, 'invalid_name');
                $update = $database->prepare('UPDATE users SET name = ?, updated_at = ? WHERE id = ?');
                $update->execute([$name, time(), $userId]);
                $user['name'] = $name;
                nodenoAccountJson(nodenoAccountView($user));
            } elseif ($path === '/api/account/password') {
                $password = nodenoAccountPassword($body['password'] ?? null);
                nodenoAccountRateLimit($database, 'password-change', 8, 900, $userId);
                if ((bool) $user['password_configured']) {
                    $current = nodenoAccountPassword($body['currentPassword'] ?? null);
                    if (!password_verify($current, $user['password_hash'])) {throw new NodenoAccountHttpError(401, 'invalid_credentials');}
                } elseif (($_SESSION['socialAuthenticatedAt'] ?? 0) < time() - 600) {
                    throw new NodenoAccountHttpError(409, 'social_reauthentication_required');
                }
                $update = $database->prepare('UPDATE users SET password_hash = ?, password_configured = 1, auth_version = auth_version + 1, updated_at = ? WHERE id = ? AND auth_version = ?');
                $update->execute([password_hash($password, PASSWORD_DEFAULT), time(), $userId, $user['auth_version']]);
                if ($update->rowCount() !== 1) {
                    throw new NodenoAccountHttpError(409, 'account_changed');
                }
                $user['auth_version'] = (int) $user['auth_version'] + 1;
                $user['password_configured'] = 1;
                nodenoAccountRotate($user);
                nodenoAccountJson(nodenoAccountView($user));
            } elseif ($path === '/api/account/collections' || $path === '/api/account/collections/merge') {
                $result = in_array($method, ['GET', 'HEAD'], true) ? nodenoCollectionsRead($database, $userId, $catalog)
                    : nodenoCollectionsWrite($database, $user, $body, $catalog, $path === '/api/account/collections/merge');
                nodenoAccountJson($result);
            } elseif ($path === '/api/account/state') {
                if ($method === 'PUT') {
                    $state = nodenoAccountState($body, $catalog);
                    $write = $database->prepare('INSERT INTO account_state(user_id, cart_json, favorites_json, updated_at) VALUES (?, ?, ?, ?)
                        ON CONFLICT(user_id) DO UPDATE SET cart_json = excluded.cart_json, favorites_json = excluded.favorites_json, updated_at = excluded.updated_at');
                    $write->execute([$userId, json_encode($state['cart'], JSON_THROW_ON_ERROR), json_encode($state['favorites'], JSON_THROW_ON_ERROR), time()]);
                } else {
                    $read = $database->prepare('SELECT cart_json, favorites_json FROM account_state WHERE user_id = ?');
                    $read->execute([$userId]);
                    $row = $read->fetch();
                    $state = $row ? nodenoAccountState(['cart' => json_decode($row['cart_json'], true, 16, JSON_THROW_ON_ERROR),
                        'favorites' => json_decode($row['favorites_json'], true, 16, JSON_THROW_ON_ERROR)], $catalog, false) : ['cart' => [], 'favorites' => []];
                }
                nodenoAccountJson($state);
            } elseif ($path === '/api/account/orders') {
                if ($method === 'POST') {
                    throw new NodenoAccountHttpError(409, 'commerce_not_configured');
                }
                $read = $database->prepare('SELECT id, status, currency, total_minor, items_json, created_at FROM orders WHERE user_id = ? ORDER BY created_at DESC');
                $read->execute([$userId]);
                $shipments = $database->prepare('SELECT id, carrier, tracking_number, tracking_url, status, updated_at FROM shipments WHERE order_id = ? ORDER BY updated_at');
                $orders = [];
                foreach ($read->fetchAll() as $row) {
                    $shipments->execute([$row['id']]);
                    $tracking = array_map(static function (array $shipment): array {
                        return ['id' => $shipment['id'], 'carrier' => $shipment['carrier'], 'trackingNumber' => $shipment['tracking_number'],
                            'trackingUrl' => $shipment['tracking_url'], 'status' => $shipment['status'], 'updatedAt' => (int) $shipment['updated_at']];
                    }, $shipments->fetchAll());
                    $orders[] = ['id' => $row['id'], 'status' => $row['status'], 'currency' => $row['currency'], 'totalMinor' => (int) $row['total_minor'],
                        'items' => json_decode($row['items_json'], true, 32, JSON_THROW_ON_ERROR), 'createdAt' => (int) $row['created_at'], 'shipments' => $tracking];
                }
                if(is_file(__DIR__.'/payment-store.php')){require_once __DIR__.'/payment-store.php';nodenoPaymentSchema($database);$orders=array_merge($orders,nodenoPaymentUserOrders($database,$userId));usort($orders,static fn($a,$b)=>$b['createdAt']<=>$a['createdAt']);}
                nodenoAccountJson(['orders' => $orders]);
            } else {
                if ($method === 'GET' || $method === 'HEAD') {
                    nodenoAccountJson(['addresses' => nodenoAccountAddresses($database, $userId)]);
                } else {
                    $result = nodenoAccountTransaction($database, static function () use ($database, $userId, $addressId, $method, $body): array {
                        $addresses = nodenoAccountAddresses($database, $userId);
                        $existing = null;
                        foreach ($addresses as $address) {
                            if ($address['id'] === $addressId) {
                                $existing = $address;
                            }
                        }
                        if ($addressId !== null && $existing === null) {
                            throw new NodenoAccountHttpError(404, 'address_not_found');
                        }
                        if ($method === 'DELETE') {
                            $delete = $database->prepare('DELETE FROM addresses WHERE id = ? AND user_id = ?');
                            $delete->execute([$addressId, $userId]);
                            if ($existing['isDefault']) {
                                $next = $database->prepare('UPDATE addresses SET is_default = 1 WHERE id = (SELECT id FROM addresses WHERE user_id = ? ORDER BY created_at, id LIMIT 1)');
                                $next->execute([$userId]);
                            }
                            return ['addresses' => nodenoAccountAddresses($database, $userId)];
                        }
                        if ($method === 'POST' && count($addresses) >= 20) {
                            throw new NodenoAccountHttpError(422, 'address_limit');
                        }
                        $value = nodenoAccountAddress(array_merge($existing ?? [], $body));
                        $id = $addressId ?? bin2hex(random_bytes(16));
                        if (count($addresses) === 0 || ($existing !== null && $existing['isDefault'])) {
                            $value['isDefault'] = true;
                        }
                        if ($value['isDefault']) {
                            $clear = $database->prepare('UPDATE addresses SET is_default = 0 WHERE user_id = ?');
                            $clear->execute([$userId]);
                        }
                        $write = $database->prepare('INSERT INTO addresses(id, user_id, data_json, is_default, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)
                            ON CONFLICT(id) DO UPDATE SET data_json = excluded.data_json, is_default = excluded.is_default, updated_at = excluded.updated_at');
                        $now = time();
                        $write->execute([$id, $userId, json_encode($value, JSON_THROW_ON_ERROR), (int) $value['isDefault'], $now, $now]);
                        return ['address' => array_merge($value, ['id' => $id])];
                    });
                    nodenoAccountJson($result, $method === 'POST' ? 201 : 200);
                }
            }
        }
    } catch (NodenoAccountHttpError $exception) {
        nodenoAccountJson(['error' => $exception->errorCode], $exception->status, $exception->headers);
    } catch (Throwable $exception) {
        // Never expose or log passwords, email addresses, physical addresses, SQL or filesystem paths.
        nodenoAccountJson(['error' => 'account_unavailable'], 503);
    } finally {
        if (session_status() === PHP_SESSION_ACTIVE) {
            session_write_close();
        }
        umask($previousMask);
    }
    return true;
}
