"""Portable artifact packaging when the host's Node directory copier fails.

Run only after the Sites source helper has committed and verified its push.
No application files, credentials or source tree are included in the archive.
"""
import argparse
import hashlib
import json
import subprocess
import tarfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--archive', required=True)
args = parser.parse_args()
archive = Path(args.archive)
if not archive.is_absolute() or not archive.name.endswith('.tar.gz'):
    raise SystemExit('An absolute .tar.gz destination is required.')
if subprocess.check_output(['git', 'status', '--porcelain'], cwd=root, text=True).strip():
    raise SystemExit('Commit and synchronize the exact source before packaging.')
commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
source_manifest = json.loads((root / '.openai/hosting.json').read_text(encoding='utf-8'))
built_manifest = json.loads((root / 'dist/.openai/hosting.json').read_text(encoding='utf-8'))
if source_manifest != built_manifest or not source_manifest.get('project_id'):
    raise SystemExit('Built and source hosting manifests must match.')
expected = {'server/index.js', '.openai/hosting.json'}
dist = root / 'dist'
actual = {p.relative_to(dist).as_posix() for p in dist.rglob('*') if p.is_file()}
if actual != expected or any(p.is_symlink() for p in dist.rglob('*')):
    raise SystemExit('Unexpected build output; only the Worker and hosting manifest may be packaged.')
worker_bytes = (dist / 'server/index.js').read_bytes()
if b'export default createApplication(' not in worker_bytes:
    raise SystemExit('A valid Worker artifact is required.')
archive.parent.mkdir(parents=True, exist_ok=True)
temporary = archive.with_name(archive.name + '.part')
with tarfile.open(temporary, 'w:gz', format=tarfile.PAX_FORMAT) as tar:
    for rel in sorted(expected):
        file = dist / rel
        info = tar.gettarinfo(str(file), arcname='dist/' + rel)
        info.mode, info.uid, info.gid, info.uname, info.gname = 0o644, 0, 0, '', ''
        with file.open('rb') as stream:
            tar.addfile(info, stream)
with tarfile.open(temporary, 'r:gz') as tar:
    if {member.name for member in tar.getmembers()} != {'dist/' + item for item in expected}:
        raise SystemExit('Archive member validation failed.')
    if tar.extractfile('dist/server/index.js').read() != worker_bytes:
        raise SystemExit('Archived Worker differs from the verified build.')
temporary.replace(archive)
print(json.dumps({'project_id': source_manifest['project_id'], 'commit_sha': commit,
                  'archive': str(archive), 'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                  'worker_sha256': hashlib.sha256(worker_bytes).hexdigest(), 'size_bytes': archive.stat().st_size}))
