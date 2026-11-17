#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/native_marketplace_import_guard.py
# Açıklama   : Dondurulmuş 51 inceleme taslağını tam alan, tür, fiyat ve API sürüm kanıtıyla korumalı yükseltir.
import copy
import hashlib
import json
import subprocess
from pathlib import Path

FROZEN_DATASET = 'e9cecfa1c6c675fdf6886b58bb85e451'
FROZEN_SHA256 = 'd6828498854e6763207b134da811cfbdd6c9d9b82166b96d644624ddf36f4263'
FROZEN_FILE = Path('D:/sexogate-local-artifacts-20261114/private-installs/marketplace-catalog-20261116/prepared/catalog-data.json')
GENERIC_BRANDS = {'genel markalar', 'markasız', 'markasiz', 'diğer', 'diger'}
PHP_TRIM = ' \t\n\r\x00\x0b'


def canonical_data(data):
    """Match the flat API validation's PHP trim, preserving NBSP and scalar types."""
    if not isinstance(data, dict) or any(not isinstance(key, str) for key in data):
        raise ValueError('GUARD_DATA_INVALID')
    if any(value is not None and type(value) not in (str, int, bool) for value in data.values()):
        raise ValueError('GUARD_DATA_INVALID')
    return {key: value.strip(PHP_TRIM) if isinstance(value, str) else value for key, value in data.items()}


def fingerprint(data):
    # JSON distinguishes true from 1, unlike Python dictionary equality.
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode('utf8')).hexdigest()


def normalize_generic_brand(data):
    result = copy.deepcopy(data)
    brand = result.get('brand', '')
    if isinstance(brand, str) and brand.casefold() in GENERIC_BRANDS:
        result['brand'] = ''
        for key, value in list(result.items()):
            if isinstance(value, str) and key.startswith(('title_', 'seoTitle_', 'seoDescription_')):
                result[key] = value.removeprefix(brand + ' ')
    return result


def frozen_baseline():
    raw = FROZEN_FILE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FROZEN_SHA256:
        raise ValueError('GUARD_FROZEN_BASELINE_HASH_MISMATCH')
    data = json.loads(raw)
    products = data['products'][2194:]
    held = {p['id'] for p in products if not p['visualApprovedIndices'] or p['eligibilityHold']}
    if data.get('dataset') != FROZEN_DATASET or len(products) != 131 or len(held) != 51:
        raise ValueError('GUARD_FROZEN_BASELINE_SCOPE_MISMATCH')
    return products, held, {'dataset': FROZEN_DATASET, 'sha256': FROZEN_SHA256}


def project_initials(php_binary, private, products):
    """Execute actual packaged projection functions without initializing a database."""
    private = Path(private)
    program = r'''declare(strict_types=1);
ini_set('display_errors','stderr');error_reporting(E_ALL);
$private=$argv[1];require $private.'/localization.php';require $private.'/sexogate-catalog.php';
$products=json_decode(stream_get_contents(STDIN),true,512,JSON_THROW_ON_ERROR);$out=[];
foreach($products as $product){$id=$product['id'];if(isset($out[$id]))throw new RuntimeException('duplicate_product');$out[$id]=sexogateCatalogInitial($product,$private);}
echo json_encode($out,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR);'''
    completed = subprocess.run([str(php_binary), '-r', program, str(private)],
        input=json.dumps(products, ensure_ascii=False).encode('utf8'), capture_output=True, timeout=90)
    if completed.returncode or completed.stderr:
        raise ValueError('GUARD_PHP_INITIAL_PROJECTION_FAILED')
    try:
        result = json.loads(completed.stdout)
    except (ValueError, UnicodeError):
        raise ValueError('GUARD_PHP_INITIAL_PROJECTION_FAILED') from None
    if not isinstance(result, dict) or set(result) != {p['id'] for p in products}:
        raise ValueError('GUARD_PHP_INITIAL_PROJECTION_FAILED')
    return {key: canonical_data(value) for key, value in result.items()}


def plan_upgrade(identity, record, baseline, target, dataset, journal, *, eligible=False, scope=''):
    preserve = lambda reason: {'action': 'preserve', 'reason': reason}
    if eligible is not True or baseline.get('visible') is not False or target.get('visible') is not True:
        return preserve('not_approved_old_hold')
    if not isinstance(record, dict) or record.get('id') != identity:
        return preserve('record_missing_or_wrong_id')
    try:
        previous = canonical_data(baseline)
        wanted = normalize_generic_brand(canonical_data(target))
        current = canonical_data(record['data'])
    except (KeyError, ValueError):
        return preserve('invalid_record_data')
    if previous.get('sku') != wanted.get('sku') or normalize_generic_brand(previous).get('brand') != wanted.get('brand'):
        return preserve('target_identity_changed')
    if type(previous.get('priceMinor')) is not int or previous['priceMinor'] < 1 or type(wanted.get('priceMinor')) is not int or previous['priceMinor'] != wanted['priceMinor']:
        return preserve('target_price_changed')
    version, published = record.get('version'), record.get('publishedVersion')
    if type(version) is not int or type(published) is not int or version < 1 or published < 0:
        return preserve('invalid_record_version')
    binding = {'id': identity, 'dataset': dataset, 'scope': scope,
        'baselineSha256': fingerprint(previous), 'targetSha256': fingerprint(wanted)}
    if published == version and fingerprint(current) == binding['targetSha256']:
        return {'action': 'already_current', 'reason': 'exact_published_target', 'data': wanted, **binding}
    if published != 0:
        return preserve('published_or_concurrent_draft')
    prior = journal.get(identity, {})
    if (isinstance(prior, dict) and all(prior.get(key) == value for key, value in binding.items())
            and prior.get('phase') == 'saved' and type(prior.get('savedVersion')) is int
            and prior['savedVersion'] == version and type(prior.get('fromVersion')) is int
            and prior['fromVersion'] in (1, 2)
            and version == prior['fromVersion'] + 1 and fingerprint(current) == binding['targetSha256']):
        return {'action': 'resume', 'reason': 'own_saved_intent', 'data': wanted, **binding}
    exact_initial = version == 1 and fingerprint(current) == fingerprint(previous)
    normalized = normalize_generic_brand(previous)
    exact_known_normalization = (version == 2 and previous.get('brand', '').casefold() in GENERIC_BRANDS
        and fingerprint(current) == fingerprint(normalized))
    if not exact_initial and not exact_known_normalization:
        return preserve('manual_or_unknown_draft')
    return {'action': 'upgrade', 'reason': 'untouched_initial_or_known_normalization',
            'data': wanted, 'fromVersion': version, **binding}


def guarded_upgrade(api, identity, baseline, target, dataset, journal, checkpoint, *, eligible=False, scope=''):
    """Use existing MFA API; never retry a PUT or bypass its expected-version check."""
    record = api('products/' + identity + '/editor')['record']
    plan = plan_upgrade(identity, record, baseline, target, dataset, journal, eligible=eligible, scope=scope)
    action = plan['action']
    if action in ('preserve', 'already_current'):
        return {'id': identity, 'action': action, 'reason': plan['reason']}
    if action == 'upgrade':
        journal[identity] = {key: value for key, value in plan.items() if key not in ('data', 'action', 'reason')}
        journal[identity]['phase'] = 'prepared'
        checkpoint()
        response = api('products/' + identity, {'version': record['version'], 'data': plan['data']}, 'PUT')
        saved = response['data']
        if (saved.get('id') != identity or saved.get('version') != record['version'] + 1
                or saved.get('publishedVersion') != 0
                or fingerprint(canonical_data(saved.get('data'))) != plan['targetSha256']):
            raise ValueError('GUARD_PUT_RESPONSE_MISMATCH')
        journal[identity].update(phase='saved', savedVersion=saved['version'])
        checkpoint()
    intent = journal[identity]
    fresh = api('products/' + identity + '/editor')['record']
    if (fresh.get('id') != identity or fresh.get('version') != intent['savedVersion']
            or fresh.get('publishedVersion') != 0
            or fingerprint(canonical_data(fresh.get('data'))) != intent['targetSha256']):
        raise ValueError('GUARD_CONCURRENT_DRAFT_BEFORE_PUBLISH')
    response = api('products/' + identity + '/publish', {'version': fresh['version']})
    published = response['data']
    if (published.get('id') != identity or published.get('version') != fresh['version'] + 1
            or published.get('publishedVersion') != published.get('version')
            or fingerprint(canonical_data(published.get('data'))) != intent['targetSha256']):
        raise ValueError('GUARD_PUBLISH_RESPONSE_MISMATCH')
    journal[identity].update(phase='published', publishedVersion=published['version'])
    checkpoint()
    return {'id': identity, 'action': 'resumed' if action == 'resume' else 'upgraded',
            'fromVersion': intent['fromVersion'], 'publishedVersion': published['version']}
