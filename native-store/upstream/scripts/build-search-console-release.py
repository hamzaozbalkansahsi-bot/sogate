"""Prepare an immutable, config-only ownership-verification release on the exact live base."""
from pathlib import Path
import hashlib, json, os, re, secrets, requests

R = Path(__file__).resolve().parents[1]
E = R / 'artifacts/search-console-20261111'
E.mkdir(exist_ok=True)
sha = lambda body: hashlib.sha256(body).hexdigest()
token = json.loads((R / 'data/brand.json').read_bytes())['seo']['googleVerification']
assert re.fullmatch(r'[A-Za-z0-9_-]{20,100}', token)
health_response = requests.get('https://nodenohome.com/api/health?gsc=' + secrets.token_hex(8), timeout=45)
health_response.raise_for_status()
health = health_response.json()
candidates = [f.parent.parent for f in (R / 'artifacts').glob('cpanel-release*/private/release.json') if json.loads(f.read_bytes()).get('releaseHash') == health['releaseHash']]
assert len(candidates) == 1, 'Exact immutable live base required'
B = candidates[0]
manifest = json.loads((B / 'private/release.json').read_bytes())
assert not manifest.get('testOnly') and health['mediaReady']
config = json.loads((B / 'private/config.json').read_bytes())
assert config.get('seo', {}).get('googleVerification') in (None, '', token), 'Existing owner token protected'
public = requests.get('https://nodenohome.com/api/config', timeout=45)
public.raise_for_status()
assert public.json().get('seo', {}).get('googleVerification') in (None, '', token), 'Published owner token protected'
config['seo'] = {**config.get('seo', {}), 'googleVerification': token}
body = (json.dumps(config, ensure_ascii=False, separators=(',', ':')) + '\n').encode()
assert body != (B / 'private/config.json').read_bytes(), 'Verification already packaged'
O = R / os.environ.get('NODENO_GSC_OUTPUT', 'artifacts/cpanel-release-search-console-20261111-r1')
assert O.parent == R / 'artifacts' and O.name.startswith('cpanel-release-') and not O.exists()
for name, digest in manifest['files'].items():
    source = B / name
    assert not source.is_symlink() and sha(source.read_bytes()) == digest, 'Base integrity mismatch'
    target = O / name
    target.parent.mkdir(parents=True, exist_ok=True)
    if name == 'private/config.json':
        target.write_bytes(body)
    else:
        os.link(source, target)
files = {**manifest['files'], 'private/config.json': sha(body)}
fp = hashlib.sha256()
for name in sorted(files):
    fp.update((name + '\0' + files[name] + '\0').encode())
updated = {**manifest, 'releaseHash': fp.hexdigest(), 'files': files}
(O / 'private/release.json').write_text(json.dumps(updated, indent=2) + '\n')
proof = {'prepared': True, 'base': B.relative_to(R).as_posix(), 'release': O.relative_to(R).as_posix(), 'baseReleaseHash': manifest['releaseHash'], 'releaseHash': updated['releaseHash'], 'changedFiles': ['private/config.json'], 'products': manifest['products'], 'tokenSha256': sha(token.encode()), 'publicFilesUnchanged': True}
(E / 'release.json').write_text(json.dumps(proof, indent=2) + '\n')
print(json.dumps(proof))
