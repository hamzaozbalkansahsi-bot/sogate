<?php
declare(strict_types=1);
require_once __DIR__.'/localization.php';

function nodenoSocialRequestOrigin(): string
{
    $https = (!empty($_SERVER['HTTPS']) && strtolower((string) $_SERVER['HTTPS']) !== 'off') || (int) ($_SERVER['SERVER_PORT'] ?? 0) === 443;
    return ($https ? 'https://' : 'http://') . strtolower((string) ($_SERVER['HTTP_HOST'] ?? ''));
}

function nodenoSocialBrowserCookie(?string $value): void
{
    setcookie('__Secure-NODENOOAUTH', $value ?? '', ['expires' => $value === null ? time() - 3600 : time() + 600,
        'path' => '/api/account/oauth', 'secure' => true, 'httponly' => true, 'samesite' => 'None']);
}

function nodenoSocialRedirect(string $page, string $locale, string $result = ''): void
{
    $parameters = ['page' => in_array($page, ['login', 'account', 'checkout'], true) ? $page : 'login',
        'lang' => in_array($locale, NODENO_STORE_LOCALES, true) ? $locale : 'tr'];
    if ($result !== '') {$parameters['social'] = $result;}
    nodenoRespond('', 303, 'text/plain; charset=utf-8', ['Location' => '/?' . http_build_query($parameters, '', '&', PHP_QUERY_RFC3986),
        'Cache-Control' => 'no-store', 'Referrer-Policy' => 'no-referrer']);
}

function nodenoSocialRequireReauthentication(PDO $database, array $user, array $body): void
{
    nodenoAccountRateLimit($database, 'social-reauthentication', 8, 900, $user['id']);
    if ((bool) ($user['password_configured'] ?? 1)) {
        $password = nodenoAccountPassword($body['currentPassword'] ?? null);
        if (!password_verify($password, $user['password_hash'])) {throw new NodenoAccountHttpError(401, 'invalid_credentials');}
    } elseif (($_SESSION['socialAuthenticatedAt'] ?? 0) < time() - 600) {
        throw new NodenoAccountHttpError(409, 'social_reauthentication_required');
    }
}

function nodenoHandleSocialRequest(string $path, string $method, array $catalog, string $storageRoot): bool
{
    $callback = preg_match('~^/api/account/oauth/(google|apple)/callback$~D', $path, $callbackMatch) === 1;
    $start = preg_match('~^/api/account/oauth/(google|apple)/start$~D', $path, $startMatch) === 1;
    $complete = $path === '/api/account/oauth/complete';
    $normal = ['/api/account/social' => ['GET', 'HEAD'], '/api/account/social/merge' => ['POST'],
        '/api/account/social/merge-cancel' => ['POST'], '/api/account/social/unlink' => ['POST']];
    if (!$callback && !$start && !$complete && !isset($normal[$path])) {return false;}
    $flow = null;$claimed = false;$root = null;$database = null;$state = '';
    try {
        $allowed = $callback ? [$callbackMatch[1] === 'apple' ? 'POST' : 'GET'] : ($start ? ['POST'] : ($complete ? ['GET'] : $normal[$path]));
        if (!in_array($method, $allowed, true)) {
            nodenoAccountJson(['error' => 'method_not_allowed'], 405, ['Allow' => implode(', ', $allowed)]);return true;
        }
        $root = nodenoAccountStorage($storageRoot);$database = nodenoAccountDatabase($root);
        if ($callback) {
            // Apple's form_post does not send the ordinary Lax session cookie.
            // Do not start or replace that session until the first-party GET below.
            nodenoAccountRateLimit($database, 'social-callback', 30, 600);
            if ((int) ($_SERVER['CONTENT_LENGTH'] ?? 0) > 16384) {throw new NodenoAccountHttpError(413, 'body_too_large');}
            if ($method === 'POST' && !preg_match('~^application/x-www-form-urlencoded(?:\s*;.*)?$~iD', $_SERVER['CONTENT_TYPE'] ?? '')) {
                throw new NodenoAccountHttpError(415, 'invalid_social_request');
            }
            $parameters = $method === 'POST' ? $_POST : $_GET;
            $state = is_string($parameters['state'] ?? null) ? $parameters['state'] : '';
            $browser = is_string($_COOKIE['__Secure-NODENOOAUTH'] ?? null) ? $_COOKIE['__Secure-NODENOOAUTH'] : '';
            $provider = $callbackMatch[1];$flow = nodenoSocialClaimFlow($database, $state, $provider, $browser);$claimed = true;
            if (isset($parameters['error'])) {throw new NodenoAccountHttpError(400, 'social_cancelled');}
            $code = $parameters['code'] ?? null;
            if (!is_string($code) || $code === '' || strlen($code) > 4096 || preg_match('/[\x00-\x20\x7f]/', $code)) {
                throw new NodenoAccountHttpError(400, 'invalid_social_request');
            }
            $origin = substr($flow['callback'], 0, -strlen('/api/account/oauth/' . $provider . '/callback'));
            $configuration = nodenoSocialProvider(nodenoSocialConfiguration($root), $root, $provider, $origin);
            if ($configuration === null) {throw new NodenoAccountHttpError(503, 'social_not_configured');}
            $identity = nodenoSocialExchange($root, $provider, $configuration, $flow, $code);
            if ($provider === 'apple' && is_string($parameters['user'] ?? null) && strlen($parameters['user']) <= 4096) {
                try {
                    $apple = json_decode($parameters['user'], true, 8, JSON_THROW_ON_ERROR);
                    $parts = [$apple['name']['firstName'] ?? '', $apple['name']['lastName'] ?? ''];
                    if (is_string($parts[0]) && is_string($parts[1])) {
                        $identity['name'] = nodenoAccountText(trim(implode(' ', $parts)), 2, 100, 'invalid_name');
                    }
                } catch (Throwable $exception) { /* Display name is optional; email always comes from the verified token. */ }
            }
            nodenoSocialSaveVerified($database, $state, $flow, $identity);
            nodenoRespond('', 303, 'text/plain; charset=utf-8', ['Location' => '/api/account/oauth/complete?flow=' . rawurlencode($state),
                'Cache-Control' => 'no-store', 'Referrer-Policy' => 'no-referrer']);
            return true;
        }
        $user = nodenoAccountSession($root, $database);
        if ($complete) {
            $state = is_string($_GET['flow'] ?? null) ? $_GET['flow'] : '';
            $browser = is_string($_COOKIE['__Secure-NODENOOAUTH'] ?? null) ? $_COOKIE['__Secure-NODENOOAUTH'] : '';
            $flow = nodenoSocialCompleteFlow($database, $state, $browser, session_id());nodenoSocialBrowserCookie(null);
            if ($flow['intent'] !== 'login' && (!$user || $user['id'] !== $flow['targetId'] || (int) $user['auth_version'] !== (int) $flow['authVersion'])) {
                throw new NodenoAccountHttpError(409, 'account_changed');
            }
            $result = nodenoSocialResolveIdentity($database, $flow['identity'], $flow['intent'] === 'login' ? null : $user, $flow['intent']);
            if (isset($result['mergeUser'])) {
                $source = $result['mergeUser'];
                $_SESSION['socialMerge'] = ['targetId' => $user['id'], 'targetVersion' => (int) $user['auth_version'],
                    'sourceId' => $source['id'], 'sourceVersion' => (int) $source['auth_version'], 'provider' => $flow['identity']['provider'],
                    'email' => $source['email'], 'confirmation' => bin2hex(random_bytes(32)), 'expiresAt' => time() + 600];
                nodenoSocialRedirect('account', $flow['locale'], 'merge_ready');
            } else {
                nodenoAccountRotate($result['user']);$_SESSION['socialAuthenticatedAt'] = time();
                nodenoSocialRedirect($flow['intent'] === 'login' ? $flow['next'] : 'account', $flow['locale'], $flow['intent'] === 'link' ? 'linked' : '');
            }
            return true;
        }
        $body = !in_array($method, ['GET', 'HEAD'], true) ? nodenoAccountBody() : [];
        if ($method === 'POST') {nodenoAccountRateLimit($database, 'social-mutations', 30, 600);}
        if ($path === '/api/account/social') {
            nodenoAccountJson(nodenoSocialPublicStatus($database, $root, $user, nodenoSocialRequestOrigin()));
        } elseif ($start) {
            $provider = $startMatch[1];$configuration = nodenoSocialProvider(nodenoSocialConfiguration($root), $root, $provider, nodenoSocialRequestOrigin());
            if ($configuration === null) {throw new NodenoAccountHttpError(503, 'social_not_configured');}
            $intent = $body['intent'] ?? 'login';
            if (!in_array($intent, ['login', 'link', 'reauth'], true)) {throw new NodenoAccountHttpError(422, 'invalid_social_request');}
            if ($intent !== 'login') {
                $user = nodenoAccountRequireUser($user);
                if ($intent === 'link') {nodenoSocialRequireReauthentication($database, $user, $body);}
            }
            $browser = bin2hex(random_bytes(32));
            $created = nodenoSocialCreateFlow($database, $provider, $configuration, ['sessionId' => session_id(), 'browser' => $browser,
                'intent' => $intent, 'locale' => $body['locale'] ?? 'tr', 'next' => $body['next'] ?? 'account', 'user' => $user]);
            nodenoSocialBrowserCookie($browser);nodenoAccountJson(['url' => $created['url']]);
        } else {
            $user = nodenoAccountRequireUser($user);
            if ($path === '/api/account/social/merge-cancel') {
                unset($_SESSION['socialMerge']);nodenoAccountJson(nodenoSocialPublicStatus($database, $root, $user, nodenoSocialRequestOrigin()));
            } elseif ($path === '/api/account/social/merge') {
                $proposal = $_SESSION['socialMerge'] ?? null;
                if (!$proposal || ($body['confirm'] ?? false) !== true || ($proposal['expiresAt'] ?? 0) < time()
                    || $proposal['targetId'] !== $user['id'] || (int) $proposal['targetVersion'] !== (int) $user['auth_version']
                    || !is_string($body['confirmation'] ?? null) || !hash_equals($proposal['confirmation'], $body['confirmation'])) {
                    throw new NodenoAccountHttpError(409, 'social_merge_invalid');
                }
                $read = $database->prepare('SELECT * FROM users WHERE id=?');$read->execute([$proposal['sourceId']]);$source = $read->fetch();
                if (!$source || (int) $source['auth_version'] !== (int) $proposal['sourceVersion']) {throw new NodenoAccountHttpError(409, 'account_changed');}
                $user = nodenoSocialMerge($database, $user, $source, $catalog);nodenoAccountRotate($user);nodenoAccountJson(nodenoAccountView($user));
            } else {
                $provider = $body['provider'] ?? null;
                if (!in_array($provider, ['google', 'apple'], true)) {throw new NodenoAccountHttpError(422, 'invalid_social_request');}
                nodenoSocialRequireReauthentication($database, $user, $body);
                nodenoAccountTransaction($database, static function () use ($database, &$user, $provider): void {
                    $check = $database->prepare('SELECT auth_version FROM users WHERE id=?');$check->execute([$user['id']]);
                    if ((int) $check->fetchColumn() !== (int) $user['auth_version']) {throw new NodenoAccountHttpError(409, 'account_changed');}
                    $others = $database->prepare('SELECT COUNT(*) FROM provider_identities WHERE user_id=? AND provider<>?');$others->execute([$user['id'], $provider]);
                    if (!(bool) $user['password_configured'] && (int) $others->fetchColumn() === 0) {throw new NodenoAccountHttpError(409, 'social_last_login_method');}
                    $delete = $database->prepare('DELETE FROM provider_identities WHERE user_id=? AND provider=?');$delete->execute([$user['id'], $provider]);
                    if ($delete->rowCount() === 0) {throw new NodenoAccountHttpError(404, 'social_identity_not_found');}
                    $update = $database->prepare('UPDATE users SET auth_version=auth_version+1,updated_at=? WHERE id=?');$update->execute([time(), $user['id']]);$user['auth_version'] = (int) $user['auth_version'] + 1;
                });
                nodenoAccountRotate($user);nodenoAccountJson(nodenoAccountView($user));
            }
        }
    } catch (Throwable $exception) {
        if ($callback || $complete) {
            if ($claimed && $database instanceof PDO) {
                $delete = $database->prepare('DELETE FROM oauth_flows WHERE state_hash=?');$delete->execute([hash('sha256', $state)]);nodenoSocialBrowserCookie(null);
            }
            $error = $exception instanceof NodenoAccountHttpError ? $exception->errorCode : 'social_failed';
            nodenoSocialRedirect(is_array($flow) && ($flow['intent'] ?? 'login') !== 'login' ? 'account' : 'login', $flow['locale'] ?? 'tr', $error);
        } elseif ($exception instanceof NodenoAccountHttpError) {
            nodenoAccountJson(['error' => $exception->errorCode], $exception->status, $exception->headers);
        } else {
            nodenoAccountJson(['error' => 'social_unavailable'], 503);
        }
    } finally {
        if (session_status() === PHP_SESSION_ACTIVE) {session_write_close();}
    }
    return true;
}
