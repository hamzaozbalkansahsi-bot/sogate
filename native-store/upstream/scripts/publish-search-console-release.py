"""Publish only the verified config delta, retaining all media and commerce gates."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, importlib.util, json, secrets, subprocess, sys, time

R = Path(__file__).resolve().parents[1]
E = R / 'artifacts/search-console-20261111'
parser = argparse.ArgumentParser()
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
spec = importlib.util.spec_from_file_location('gsc_deploy', R / 'scripts/deploy-cpanel.py')
d = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d
spec.loader.exec_module(d)
proof = json.loads((E / 'release.json').read_bytes())
base = d.load_release(R / proof['base'])
release = d.load_release(R / proof['release'])
assert base['manifest']['releaseHash'] == proof['baseReleaseHash'] and release['manifest']['releaseHash'] == proof['releaseHash']
browser = json.loads((E / 'browser.json').read_bytes())
assert browser['passed'] and browser['releaseHash'] == proof['releaseHash'] and len(browser['checks']) >= 2
assert base['all_bytes'].keys() == release['all_bytes'].keys()
changed = {name for name, body in release['all_bytes'].items() if base['all_bytes'][name] != body}
assert changed == {'private/config.json', 'private/release.json'}
old_config = json.loads(base['all_bytes']['private/config.json'])
new_config = json.loads(release['all_bytes']['private/config.json'])
token = json.loads((R / 'data/brand.json').read_bytes())['seo']['googleVerification']
assert hashlib.sha256(token.encode()).hexdigest() == proof['tokenSha256']
assert new_config == {**old_config, 'seo': {**old_config.get('seo', {}), 'googleVerification': token}}
cleanup_file = R / 'artifacts/media-cleanup.json'
cleanup = json.loads(cleanup_file.read_bytes())
audit = json.loads((R / 'artifacts/measurement-orders/full-media-audit.json').read_bytes())
assert cleanup['publicationReady'] is True and audit['passed'] and audit['sourceReportSha256'] == d.sha256(cleanup_file.read_bytes())
assert audit['mediaVersion'] == release['manifest']['mediaVersion']
for row in cleanup['images'].values():
    for field, digest, folder in [('sourcePath', 'sourceSha', 'media-originals'), ('path', 'outputSha', 'media-cleaned')]:
        path = R / row[field]
        assert not path.is_symlink() and path.resolve().is_relative_to((R / 'artifacts' / folder).resolve()) and d.sha256(path.read_bytes()) == row[digest]
catalog = json.loads(release['all_bytes']['private/catalog.json'])
d.validate_supplier_publication(R, release, catalog)
owner_spec = importlib.util.spec_from_file_location('gsc_owner_gate', R / 'lib/owner_media_gate.py')
owner = importlib.util.module_from_spec(owner_spec)
owner_spec.loader.exec_module(owner)
owner.verify_owner_catalogues(R, release)
subprocess.run(['node', str(R / 'scripts/verify-current-media.mjs'), str(R), str(release['directory'])], check=True)
backend = d.CpanelBackend(allow_writes=args.apply)
health = backend.public_health()
assert health['releaseHash'] == proof['baseReleaseHash']
plan = d.make_plan(release, backend)
print(json.dumps({'ready': True, 'privateConfigOnly': True, 'publicFilesUnchanged': True, 'mediaVerified': True}), flush=True)
if not args.apply:
    sys.exit(0)
private = plan['privateRoot']
old_private = d.HOME + '/nodeno-releases/' + proof['baseReleaseHash'] + '/private'
def switch_pointer(body):
    content_type, payload = d.multipart({'dir': d.HOME, 'overwrite': '1'}, {'nodeno-runtime.php': body})
    d.successful_upload(backend.post('/execute/Fileman/upload_files', payload, content_type))
with d.deployment_lease(backend):
    assert backend.public_health()['releaseHash'] == proof['baseReleaseHash']
    old_pointer = d.text_content(backend, d.HOME, 'nodeno-runtime.php')
    assert old_pointer.count(old_private.encode()) == 1
    new_pointer = old_pointer.replace(old_private.encode(), private.encode())
    backup = d.HOME + '/nodeno-backups/' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-gsc-' + secrets.token_hex(4)
    d.ensure_directory(backend, backup, private=True, permissions='0700')
    backend.upload(backup, {'nodeno-runtime.php': old_pointer})
    d.ensure_directory(backend, private, private=True, permissions='0700')
    d.ensure_directory(backend, private + '/cache', private=True, permissions='0700')
    backend.upload(private, {name[8:]: body for name, body in release['all_bytes'].items() if name.startswith('private/')})
    assert d.text_content(backend, private, 'config.json') == release['all_bytes']['private/config.json']
    assert d.text_content(backend, private, 'release.json') == release['all_bytes']['private/release.json']
    assert d.text_content(backend, d.HOME, 'nodeno-runtime.php') == old_pointer
    try:
        switch_pointer(new_pointer)
        for _ in range(4):
            current = backend.public_health()
            if current.get('releaseHash') == proof['releaseHash']:
                break
            time.sleep(1)
        assert current['releaseHash'] == proof['releaseHash'] and current['products'] == health['products'] and current['mediaReady'] and current['checkoutEnabled'] == health['checkoutEnabled']
        actual_config = json.loads(backend._public_get('/api/config', 2_000_000))
        assert actual_config.get('seo', {}).get('googleVerification') == token, 'Published configuration masks verification token'
        head = backend._public_get('/', 8_000_000).decode('utf8').partition('</head>')[0]
        assert head.count('name="google-site-verification"') == 1 and 'name="google-site-verification" content="' + token + '"' in head, 'Live crawler head lacks verification token'
    except Exception:
        switch_pointer(old_pointer)
        assert backend.public_health()['releaseHash'] == proof['baseReleaseHash']
        raise
    result = {'passed': True, 'live': True, 'releaseHash': proof['releaseHash'], 'baseReleaseHash': proof['baseReleaseHash'], 'backupRoot': backup, 'publicFilesUnchanged': True, 'catalogAndMediaUnchanged': True, 'accountAndPaymentSettingsPreserved': True, 'liveConfigAndCrawlerTagVerified': True, 'googleOwnershipClickPending': True}
    (E / 'deployment.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)
