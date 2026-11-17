#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/clean-native-marketplace-copy.py
# Açıklama   : Yalnız mevcut test vitrininin kanıtlı reklam cümlelerini MFA API’siyle temizler ve kaynak/fiyat koruma raporu üretir.
import base64
import copy
import hashlib
import hmac
import json
import os
import re
import struct
import sys
import time
from pathlib import Path

import requests
from native_marketplace_copy import apply_copy, plan_copy, has_advertising, protected_data
from native_marketplace_import_guard import canonical_data, fingerprint, frozen_baseline, project_initials
from native_marketplace_paths import marketplace_paths

ROOT = Path(__file__).resolve().parent.parent
EXPECTED_RELEASE = 'e7f4feeb57497118bdaf4dd3'
EXPECTED_DATASET = '057fb50f7d5887fee341e3d5b4a3dd64'
EXPECTED_VISIBLE = 803


def target_base(value):
    if not isinstance(value, str) or not re.fullmatch(
        r'https://(?:127\.0\.0\.1:3188/test|sexogate\.com/test(?:/native-preview-[a-f0-9]{16})?)/?', value):
        raise ValueError('COPY_TARGET_REJECTED')
    return value.rstrip('/')


def atomic_json(path, value):
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True), encoding='utf8')
    temporary.replace(path)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def source_fingerprint(paths, private):
    source16 = paths.source.parent / 'marketplace-catalog-20261116'
    files = {
        'selection': ROOT / '.local/native-marketplace-selection.json',
        'packageMetadata': ROOT / '.local/native-stage-package.json',
    }
    for label, folder in [('frozen16', source16 / 'prepared'), ('current17', paths.prepared), ('package', private)]:
        for name in ['catalog-data.json', 'catalog.json', 'catalog-sources.json', 'catalog-spec-labels.json',
                     'catalog-selections.json', 'catalog-seo-copy.json']:
            if (folder / name).is_file():
                files[label + '/' + name] = folder / name
        for path in sorted((folder / 'catalog-workbench').glob('*.json')):
            files[label + '/catalog-workbench/' + path.name] = path
    for label, folder in [('source16', source16), ('source17', paths.source)]:
        for name in ['catalog-source.json', 'editorial-review.json', 'cover-review.json']:
            if (folder / name).is_file():
                files[label + '/' + name] = folder / name
    return {key: sha(path) for key, path in sorted(files.items())}


class AdminClient:
    def __init__(self, base):
        self.base = base
        self.remote = base.startswith('https://sexogate.com/test')
        self.session = requests.Session()
        self.session.trust_env = False
        if self.remote:
            self.session.verify = True
        else:
            local = json.loads((ROOT / '.local/native-stage-local.json').read_text('utf8'))
            certificate = Path(local['base']) / 'tls.pem'
            if not certificate.is_file():
                raise ValueError('COPY_LOCAL_CA_MISSING')
            self.session.verify = str(certificate)
        self.access = json.loads((ROOT / '.local' / ('php-stage-access.json' if self.remote else 'php-access.json')).read_text('utf8'))
        self.csrf = None
        self.requests = 0
        self.elevated = 0

    def request(self, route, body=None, method='GET'):
        headers = {'Accept': 'application/json', 'Cache-Control': 'no-cache'}
        if body is not None:
            headers.update({'Origin': self.base.split('/test')[0], 'X-CSRF-Token': self.csrf or ''})
        response = self.session.request(method, self.base + route, json=body if body is not None else None,
            headers=headers, timeout=(12, 60), allow_redirects=False)
        self.requests += 1
        if response.status_code != 200:
            raise ValueError('COPY_HTTP_' + str(response.status_code))
        try:
            result = response.json()
        except ValueError:
            raise ValueError('COPY_HTTP_JSON_INVALID') from None
        if not isinstance(result, dict):
            raise ValueError('COPY_HTTP_JSON_INVALID')
        return result

    def public(self, route):
        if route not in ('deployment-status', 'catalog'):
            raise ValueError('COPY_ROUTE_REJECTED')
        return self.request('/api/' + route)

    def otp(self):
        # Do not submit a code at the end of its validity window.
        remaining = 30 - time.time() % 30
        if remaining < 5:
            time.sleep(remaining + 0.2)
        secret = self.access['totpSecret']
        key = base64.b32decode(secret + '=' * ((8 - len(secret) % 8) % 8))
        digest = hmac.new(key, struct.pack('>Q', int(time.time()) // 30), hashlib.sha1).digest()
        offset = digest[-1] & 15
        return str((struct.unpack('>I', digest[offset:offset + 4])[0] & 0x7fffffff) % 1000000).zfill(6)

    def admin(self, route, body=None, method='POST'):
        allowed = route in ('session', 'login', 'login/verify', 'reauthenticate', 'catalog-source', 'products')
        allowed = allowed or bool(re.fullmatch(r'products/sg_ty_[a-f0-9]{16}(?:/editor|/publish)?', route))
        if not allowed:
            raise ValueError('COPY_ROUTE_REJECTED')
        if route.endswith('/publish') and time.monotonic() - self.elevated > 230:
            auth = self.request('/api/admin/reauthenticate',
                {'password': self.access['password'], 'code': self.otp()}, 'POST')
            self.csrf = auth['csrfToken']
            if auth.get('user', {}).get('role') != 'owner':
                raise ValueError('COPY_OWNER_MFA_REQUIRED')
            self.elevated = time.monotonic()
        return self.request('/api/admin/' + route, body, method if body is not None else 'GET')

    def login(self):
        self.csrf = self.admin('session')['csrfToken']
        self.csrf = self.admin('login', {'email': self.access['email'], 'password': self.access['password']})['csrfToken']
        # Another legitimate test may have used this account's current TOTP step.
        time.sleep(30.1 - time.time() % 30)
        auth = self.admin('login/verify', {'code': self.otp()})
        self.csrf = auth['csrfToken']
        if auth.get('user', {}).get('role') != 'owner':
            raise ValueError('COPY_OWNER_MFA_REQUIRED')
        self.elevated = time.monotonic()


def admin_rows(client):
    rows = client.admin('products')['data']
    if not isinstance(rows, list) or len({row['id'] for row in rows}) != len(rows):
        raise ValueError('COPY_ADMIN_SET_INVALID')
    return {row['id']: row for row in rows}


def protected_public(products, fields_by_id, timestamp_keys=None):
    result = {}
    for product in products:
        item = copy.deepcopy(product)
        for field in fields_by_id.get(item['id'], []):
            prefix, language = field.rsplit('_', 1)
            if isinstance(item.get(prefix), dict):
                item[prefix].pop(language, None)
        for key in (timestamp_keys or {}).get(item['id'], []):
            item.pop(key, None)
        result[item['id']] = item
    return fingerprint(result)


def runtime_time_changes(before, after, changed_ids):
    excluded = {}
    for identity in changed_ids:
        for key in ('publishedAt', 'updatedAt'):
            first, last = before[identity].get(key), after[identity].get(key)
            if first != last:
                if type(first) is not int or type(last) is not int or last < first:
                    raise ValueError('COPY_RUNTIME_TIMESTAMP_INVALID')
                excluded.setdefault(identity, []).append(key)
    return excluded


def execute(base, proof_path, proof):
    selection = json.loads((ROOT / '.local/native-marketplace-selection.json').read_text('utf8'))
    paths = marketplace_paths(selection)
    package = json.loads((ROOT / '.local/native-stage-package.json').read_text('utf8'))
    if package.get('release') != EXPECTED_RELEASE or selection.get('dataset') != EXPECTED_DATASET or package.get('dataset') != EXPECTED_DATASET:
        raise ValueError('COPY_RELEASE_SCOPE_MISMATCH')
    private = Path(package['bundle']) / 'private'
    catalog = json.loads((private / 'catalog.json').read_text('utf8'))
    prepared = json.loads((paths.prepared / 'catalog-data.json').read_text('utf8'))
    if catalog['products'] != prepared['products'] or catalog.get('dataset') != EXPECTED_DATASET:
        raise ValueError('COPY_SOURCE_PACKAGE_MISMATCH')
    current = catalog['products'][2194:]
    expected_ids = {p['id'] for p in current if p['images'] and p['visualApprovedIndices'] and not p['eligibilityHold'] and p['salePriceMinor']}
    if len(expected_ids) != EXPECTED_VISIBLE:
        raise ValueError('COPY_PUBLIC_SCOPE_MISMATCH')
    original16, _, _ = frozen_baseline()
    initial16 = project_initials(ROOT / '.local/php-runtime/php.exe', private, original16)
    initial17 = project_initials(ROOT / '.local/php-runtime/php.exe', private, current)
    known = {identity: [initial16.get(identity), initial17[identity]] for identity in expected_ids}
    sources_before = source_fingerprint(paths, private)
    client = AdminClient(base)
    proof['base'], proof['release'], proof['dataset'] = base, package['release'], selection['dataset']
    try:
        if client.public('deployment-status').get('release') != package['release']:
            raise ValueError('COPY_WRONG_DEPLOYED_RELEASE')
        client.login()
        source = client.admin('catalog-source')
        if source.get('dataset') != selection['dataset'] or source.get('products') != len(catalog['products']):
            raise ValueError('COPY_WRONG_DEPLOYED_DATASET')
        before = client.public('catalog')['products']
        public_ids = {p['id'] for p in before}
        if public_ids != expected_ids or len(before) != EXPECTED_VISIBLE:
            raise ValueError('COPY_EXISTING_PUBLIC_SET_MISMATCH')
        records_before = admin_rows(client)
        if not public_ids.issubset(records_before):
            raise ValueError('COPY_PUBLIC_ADMIN_RECORD_MISSING')
        context = {'base': base, 'release': package['release'], 'dataset': selection['dataset']}
        intent_file = ROOT / ('.local/native-marketplace-copy-intent-' + fingerprint(context)[:24] + '.json')
        journal = json.loads(intent_file.read_text('utf8')) if intent_file.is_file() else {}
        if not isinstance(journal, dict):
            raise ValueError('COPY_INTENT_INVALID')
        checkpoint = lambda: atomic_json(intent_file, journal)
        rows, fields = [], {}
        for index, identity in enumerate(sorted(public_ids), 1):
            result = apply_copy(client.admin, records_before[identity], known[identity], public_ids, context, journal, checkpoint)
            rows.append(result)
            fields[identity] = result.get('changedFields', [])
            if index % 50 == 0:
                print(json.dumps({'copyReviewed': index, 'of': len(public_ids),
                    'updated': sum(row['action'] in ('updated', 'resumed') for row in rows)}), flush=True)
        after = client.public('catalog')['products']
        records_after = admin_rows(client)
        after_ids = {p['id'] for p in after}
        expected_match = after_ids == public_ids == expected_ids and len(after) == EXPECTED_VISIBLE
        protected_cms = (set(records_after) == set(records_before) and all(
            fingerprint(protected_data(records_before[identity]['data'], fields.get(identity, []))) ==
            fingerprint(protected_data(records_after[identity]['data'], fields.get(identity, [])))
            for identity in records_before))
        protected_hidden = all(fingerprint(records_before[identity]) == fingerprint(records_after.get(identity))
            for identity in set(records_before) - public_ids)
        changed_ids = {row['id'] for row in rows if row['action'] in ('updated', 'resumed')}
        before_map, after_map = {p['id']: p for p in before}, {p['id']: p for p in after}
        timestamps = runtime_time_changes(before_map, after_map, changed_ids) if expected_match else {}
        protected_view = expected_match and protected_public(before, fields, timestamps) == protected_public(after, fields, timestamps)
        remaining = sum(any(has_advertising(value) for field in ('description', 'seoDescription', 'seoTitle')
            for value in (p.get(field) or {}).values()) for p in after)
        replay = [plan_copy(records_after[identity], known[identity], public_ids, context, journal) for identity in sorted(public_ids)]
        idempotent = all(row['action'] not in ('update', 'resume') for row in replay)
        release_matches = client.public('deployment-status').get('release') == package['release']
        preserved = sources_before == source_fingerprint(paths, private)
        proof.update(schema=1, visible=len(after), updated=len(changed_ids), skipped=sum(row['action'] == 'skip' for row in rows),
            remainingCTAs=remaining, protectedFieldsNoChange=protected_cms and protected_hidden and protected_view,
            sourcePreserved=preserved, idempotent=idempotent, verifiedAfterReload=release_matches,
            expectedSetMatch=expected_match, actualRequests=client.requests > 0, requestCount=client.requests,
            realPayments=False, records=rows, sourceFiles=len(sources_before), sourceBeforeSha256=fingerprint(sources_before),
            sourceAfterSha256=fingerprint(source_fingerprint(paths, private)), runtimeTimestampKeysExcluded=timestamps,
            cmsProtectedSha256=fingerprint({identity: protected_data(records_after[identity]['data'], fields.get(identity, []))
                for identity in sorted(records_after)}))
        if remaining or not all(proof[key] for key in ('protectedFieldsNoChange', 'sourcePreserved', 'idempotent',
            'verifiedAfterReload', 'expectedSetMatch', 'actualRequests')):
            raise ValueError('COPY_FINAL_VERIFICATION_FAILED')
    finally:
        proof['actualRequests'] = client.requests > 0
        proof['requestCount'] = client.requests
        proof['sourcePreserved'] = sources_before == source_fingerprint(paths, private)


def main():
    base = target_base(os.environ.get('SEXOGATE_NATIVE_TEST_URL', 'https://127.0.0.1:3188/test'))
    scope = 'preview' if '/native-preview-' in base else 'remote' if base.startswith('https://sexogate.com') else 'local'
    proof_path = ROOT / ('.local/native-marketplace-copy-' + scope + '.json')
    proof = {'schema': 1, 'base': base, 'release': EXPECTED_RELEASE, 'dataset': EXPECTED_DATASET,
        'scriptSha256': sha(Path(__file__)), 'helperSha256': sha(ROOT / 'scripts/native_marketplace_copy.py'),
        'visible': None, 'updated': 0, 'skipped': 0, 'remainingCTAs': None,
        'protectedFieldsNoChange': False, 'sourcePreserved': False, 'idempotent': False,
        'verifiedAfterReload': False, 'expectedSetMatch': False, 'actualRequests': False, 'realPayments': False}
    atomic_json(proof_path, proof)
    try:
        execute(base, proof_path, proof)
    except Exception as error:
        code = str(error) if isinstance(error, ValueError) and re.fullmatch(r'[A-Z_0-9]+', str(error)) else type(error).__name__
        proof['errorCode'] = code
        atomic_json(proof_path, proof)
        print(json.dumps({'copyCompleted': False, 'code': code, 'proof': str(proof_path)}), file=sys.stderr)
        return 1
    atomic_json(proof_path, proof)
    print(json.dumps({'copyCompleted': True, 'visible': proof['visible'], 'updated': proof['updated'],
        'skipped': proof['skipped'], 'remainingCTAs': proof['remainingCTAs'], 'proof': str(proof_path)}), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
