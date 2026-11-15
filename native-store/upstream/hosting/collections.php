<?php
declare(strict_types=1);

function nodenoCollectionsSchema(PDO $database): void
{
    $database->exec("CREATE TABLE IF NOT EXISTS collection_state (
        user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
        data_json TEXT NOT NULL DEFAULT '[]', version INTEGER NOT NULL DEFAULT 0, updated_at INTEGER NOT NULL
    )");
}

function nodenoCollectionsValidate($value, array $catalog, bool $strict = true): array
{
    if (!is_array($value) || !array_is_list($value) || count($value) > 20) {
        throw new NodenoAccountHttpError(422, 'collections_limit');
    }
    $known = array_fill_keys(array_column($catalog['products'] ?? [], 'id'), true);
    $result = []; $seen = []; $total = 0;
    foreach ($value as $row) {
        if (!is_array($row) || !is_string($row['id'] ?? null) || !preg_match('/^[a-f0-9]{32}$/D', $row['id'])
            || isset($seen[$row['id']]) || !is_array($row['items'] ?? null) || !array_is_list($row['items'])) {
            throw new NodenoAccountHttpError(422, 'invalid_collection');
        }
        $seen[$row['id']] = true;
        $name = nodenoAccountText($row['name'] ?? null, 1, 60, 'invalid_collection_name');
        if (count($row['items']) > 100) { throw new NodenoAccountHttpError(422, 'collections_limit'); }
        $items = [];
        foreach ($row['items'] as $id) {
            if (!is_string($id) || !isset($known[$id])) {
                if ($strict) { throw new NodenoAccountHttpError(422, 'invalid_product'); }
                continue;
            }
            if (!in_array($id, $items, true)) { $items[] = $id; }
        }
        $total += count($items);
        if ($total > 1000) { throw new NodenoAccountHttpError(422, 'collections_limit'); }
        $result[] = ['id' => $row['id'], 'name' => $name, 'items' => $items];
    }
    return $result;
}

function nodenoCollectionsRead(PDO $database, string $userId, array $catalog): array
{
    $read = $database->prepare('SELECT data_json,version FROM collection_state WHERE user_id=?');
    $read->execute([$userId]); $row = $read->fetch();
    return $row ? ['version' => (int) $row['version'], 'collections' => nodenoCollectionsValidate(json_decode($row['data_json'], true, 16, JSON_THROW_ON_ERROR), $catalog, false)]
        : ['version' => 0, 'collections' => []];
}

function nodenoCollectionsMerge(array $target, array $incoming, array $catalog): array
{
    $result = nodenoCollectionsValidate($target, $catalog);
    foreach (nodenoCollectionsValidate($incoming, $catalog) as $row) {
        $found = false;
        foreach ($result as &$current) {
            if ($current['id'] === $row['id']) {
                $current['items'] = array_values(array_unique(array_merge($current['items'], $row['items'])));
                $found = true; break;
            }
        }
        unset($current);
        if (!$found) { $result[] = $row; }
    }
    return nodenoCollectionsValidate($result, $catalog);
}

/** Call inside the owner's write transaction, also used by atomic social account merging. */
function nodenoCollectionsStore(PDO $database, string $userId, array $collections, int $version): array
{
    $write = $database->prepare('INSERT INTO collection_state(user_id,data_json,version,updated_at) VALUES(?,?,?,?)
        ON CONFLICT(user_id) DO UPDATE SET data_json=excluded.data_json,version=excluded.version,updated_at=excluded.updated_at');
    $write->execute([$userId, json_encode($collections, JSON_THROW_ON_ERROR), $version, time()]);
    return ['version' => $version, 'collections' => $collections];
}

function nodenoCollectionsWrite(PDO $database, array $user, array $body, array $catalog, bool $merge): array
{
    $incoming = nodenoCollectionsValidate($body['collections'] ?? null, $catalog);
    if (!$merge && (!is_int($body['version'] ?? null) || $body['version'] < 0 || $body['version'] > 2147483647)) {
        throw new NodenoAccountHttpError(422, 'invalid_collection_version');
    }
    return nodenoAccountTransaction($database, static function () use ($database, $user, $body, $catalog, $incoming, $merge): array {
        $owner = $database->prepare('SELECT auth_version FROM users WHERE id=?'); $owner->execute([$user['id']]);
        if ((int) $owner->fetchColumn() !== (int) $user['auth_version']) { throw new NodenoAccountHttpError(409, 'account_changed'); }
        $current = nodenoCollectionsRead($database, $user['id'], $catalog);
        if (!$merge && $body['version'] !== $current['version']) { throw new NodenoAccountHttpError(409, 'collections_changed'); }
        $next = $merge ? nodenoCollectionsMerge($current['collections'], $incoming, $catalog) : $incoming;
        return $next === $current['collections'] ? $current : nodenoCollectionsStore($database, $user['id'], $next, $current['version'] + 1);
    });
}
