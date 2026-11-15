"""Publish only verified social URLs; retain every live application/media byte."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
import os
import secrets
import subprocess
import sys
import urllib.request

R = Path(__file__).resolve().parents[1]
E = R / 'artifacts/social-links-20261112'
B = R / 'artifacts/cpanel-release-storefront-recovery-20261112'
O = R / 'artifacts/cpanel-release-social-links-pinterest-20261112'
BASE_HASH = 'f9453eba124fed16cd7a10fef7e064d542bfe6fd257b9aa17e14feec9b9cfec2'
EXPECTED = {
    'instagram': 'https://www.instagram.com/nodeno_home/',
    'facebook': 'https://www.facebook.com/nodenohome/',
    'youtube': 'https://www.youtube.com/@nodenohome',
    'tiktok': 'https://www.tiktok.com/@nodeno.home',
    'x': 'https://x.com/nodenohome',
    'pinterest': 'https://www.pinterest.com/nodenohome/',
    'linkedin': 'https://www.linkedin.com/company/nodenohome/',
}


def module():
    spec = importlib.util.spec_from_file_location('social_link_deployment', R/'scripts/deploy-cpanel.py')
    d = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = d
    spec.loader.exec_module(d)
    return d


def require(value, code):
    if not value:
        raise RuntimeError(code)


def emit(stage, **fields):
    print(json.dumps({'stage': stage, **fields}), flush=True)


def get_json(path):
    request = urllib.request.Request('https://nodenohome.com'+path, headers={'Cache-Control': 'no-cache'})
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.load(response)


def switch_pointer(d, backend, body):
    # HOME itself is deliberately rejected by the generic directory uploader.
    # Use the existing publisher's narrowly scoped, lease-protected operation.
    d.require_deployment_lease(backend)
    content_type, payload = d.multipart({'dir':d.HOME, 'overwrite':'1'}, {'nodeno-runtime.php':body})
    d.successful_upload(backend.post('/execute/Fileman/upload_files', payload, content_type))
    require(d.text_content(backend, d.HOME, 'nodeno-runtime.php') == body, 'runtime_readback_failed')


def prepare(d):
    base = d.load_release(B)
    require(base['manifest']['releaseHash'] == BASE_HASH, 'unexpected_base')
    brand = json.loads((R/'data/brand.json').read_bytes())
    require({s['id']: s['url'] for s in brand['socials']} == EXPECTED, 'unverified_social_url')
    require(len(brand['socials']) == len(EXPECTED), 'duplicate_social_url')
    config = json.loads(base['all_bytes']['private/config.json'])
    config['socials'] = brand['socials']
    body = (json.dumps(config, ensure_ascii=False, separators=(',', ':'))+'\n').encode()
    marker = b' <meta name="p:domain_verify" content="9d9b9982b35fcc574dc9032a9f47c691">'
    source_html = (R/'web/index.html').read_bytes()
    require(source_html.count(marker) == 1, 'pinterest_source_verification_missing')
    old_html = base['all_bytes']['private/index.html']
    require(old_html.count(b'<head>') == 1 and b'p:domain_verify' not in old_html, 'unexpected_verification_base')
    html = old_html.replace(b'<head>', b'<head>\n'+marker)
    before = json.loads(base['all_bytes']['private/config.json'])
    require({k:v for k,v in before.items() if k != 'socials'} == {k:v for k,v in config.items() if k != 'socials'}, 'non_social_config_changed')
    E.mkdir(exist_ok=True)
    if not O.exists():
        for name, original in base['all_bytes'].items():
            if name == 'private/release.json':
                continue
            target = O/name
            target.parent.mkdir(parents=True, exist_ok=True)
            if name == 'private/config.json':
                target.write_bytes(body)
            elif name == 'private/index.html':
                target.write_bytes(html)
            else:
                os.link(B/name, target)
        hashes = {name:d.sha256((O/name).read_bytes()) for name in sorted(base['manifest']['files'])}
        fingerprint = hashlib.sha256()
        for name, digest in hashes.items():
            fingerprint.update((name+'\0'+digest+'\0').encode())
        manifest = {**base['manifest'], 'releaseHash':fingerprint.hexdigest(), 'files':hashes}
        (O/'private/release.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    candidate = d.load_release(O)
    require(candidate['all_bytes']['private/config.json'] == body, 'candidate_social_config_changed')
    require(candidate['all_bytes']['private/index.html'] == html, 'candidate_pinterest_tag_changed')
    changed = {n for n,b in candidate['all_bytes'].items() if b != base['all_bytes'].get(n)}
    require(changed == {'private/config.json','private/index.html','private/release.json'}, 'non_social_release_changed')
    require(set(candidate['all_bytes']) == set(base['all_bytes']), 'file_inventory_changed')
    proof = {'prepared':True, 'base':B.relative_to(R).as_posix(), 'release':O.relative_to(R).as_posix(),
             'baseReleaseHash':BASE_HASH, 'releaseHash':candidate['manifest']['releaseHash'],
             'changedFiles':sorted(changed), 'socials':brand['socials'], 'publicAssetsUnchanged':True,
             'cataloguePricesMediaAndCommerceUnchanged':True}
    (E/'release.json').write_text(json.dumps(proof, indent=2)+'\n', encoding='utf-8')
    return base, candidate, proof


def verify_unchanged_media(d, candidate, proof):
    # The complete publication audit is already sealed; this config-only delta
    # rechecks its binding and every original/output instead of replaying OCR.
    cleanup_path = R/'artifacts/media-cleanup.json'
    cleanup = json.loads(cleanup_path.read_bytes())
    audit = json.loads((R/'artifacts/measurement-orders/full-media-audit.json').read_bytes())
    require(cleanup.get('publicationReady') is True and cleanup.get('testOnly', False) is False, 'media_not_publication_ready')
    require(audit['passed'] is True and audit['sourceReportSha256'] == d.sha256(cleanup_path.read_bytes()), 'media_audit_changed')
    require(audit['mediaVersion'] == candidate['manifest']['mediaVersion'], 'media_version_changed')
    for name, digest in audit['files'].items():
        require(d.sha256(candidate['all_bytes'][name]) == digest, 'audited_media_changed')
    for index, row in enumerate(cleanup['images'].values(), 1):
        for field, digest, folder in [('sourcePath','sourceSha','media-originals'),('path','outputSha','media-cleaned')]:
            path = R/row[field]
            require(not path.is_symlink() and path.resolve().is_relative_to((R/'artifacts'/folder).resolve()), 'media_path_rejected')
            require(d.sha256(path.read_bytes()) == row[digest], 'media_bytes_changed')
        if index % 1000 == 0:
            emit('media_hash_progress', verified=index, total=len(cleanup['images']))
    d.validate_supplier_publication(R, candidate)
    spec = importlib.util.spec_from_file_location('social_links_owner_media', R/'lib/owner_media_gate.py')
    owner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(owner)
    owner.verify_owner_catalogues(R, candidate)
    subprocess.run(['node', str(R/'scripts/verify-current-media.mjs'), str(R), str(O)], check=True)
    (E/'media.json').write_text(json.dumps({'passed':True, 'releaseHash':proof['releaseHash'], 'allOriginalAndOutputHashesVerified':True, 'priorPublicationAuditBindingVerified':True})+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--resume-staged', action='store_true', help='reuse the exact already-uploaded private package after readback')
    args = parser.parse_args()
    d = module()
    base, candidate, proof = prepare(d)
    emit('local_candidate_verified', **proof)
    require(get_json('/api/health')['releaseHash'] == BASE_HASH, 'live_base_changed')
    emit('checking_existing_media')
    verify_unchanged_media(d, candidate, proof)
    backend = d.CpanelBackend(allow_writes=args.apply)
    plan = d.make_plan(candidate, backend)
    require(backend.public_health()['releaseHash'] == BASE_HASH, 'remote_base_changed')
    if not args.apply:
        emit('plan_verified', releaseHash=proof['releaseHash'], changedPublicFiles=0)
        return
    acceptance = json.loads((E/'browser-local.json').read_bytes())
    review = json.loads((E/'code-review.json').read_bytes())
    require(acceptance['passed'] is True and acceptance['releaseHash'] == proof['releaseHash'], 'candidate_browser_acceptance_missing')
    require(review['passed'] is True and review['releaseHash'] == proof['releaseHash'], 'code_review_missing')
    old_private = d.HOME+'/nodeno-releases/'+BASE_HASH+'/private'
    private = plan['privateRoot']
    with d.deployment_lease(backend):
        require(backend.public_health()['releaseHash'] == BASE_HASH, 'live_changed_before_lease')
        old_pointer = d.text_content(backend, d.HOME, 'nodeno-runtime.php')
        require(old_pointer.count(old_private.encode()) == 1, 'unexpected_runtime_pointer')
        new_pointer = old_pointer.replace(old_private.encode(), private.encode())
        require(new_pointer.replace(private.encode(), old_private.encode()) == old_pointer, 'storage_or_runtime_options_changed')
        backup = d.HOME+'/nodeno-backups/'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-social-links-'+secrets.token_hex(4)
        d.ensure_directory(backend, backup, private=True, permissions='0700')
        backend.upload(backup, {'nodeno-runtime.php':old_pointer})
        require(d.text_content(backend, backup, 'nodeno-runtime.php') == old_pointer, 'backup_failed')
        d.ensure_directory(backend, private, private=True, permissions='0700')
        d.ensure_directory(backend, private+'/cache', private=True, permissions='0700')
        files = {n[8:]:b for n,b in candidate['all_bytes'].items() if n.startswith('private/')}
        if args.resume_staged:
            require(d.text_content(backend, private, 'release.json') == files['release.json'], 'resume_manifest_mismatch')
            emit('reusing_previously_staged_package', privateFiles=len(files))
        else:
            for index, (name, body) in enumerate(sorted(files.items()), 1):
                backend.upload(private, {name:body})
                emit('staging_private_file', file=name, current=index, total=len(files))
        listing = d.listing(backend, private)
        require(all(listing.get(n,{}).get('type') == 'file' and int(listing[n]['size']) == len(b) for n,b in files.items()), 'staged_file_size_mismatch')
        for name in ['config.json','release.json','index.html']:
            require(d.text_content(backend, private, name) == files[name], 'staged_file_readback_mismatch')
        require(d.text_content(backend, d.HOME, 'nodeno-runtime.php') == old_pointer, 'runtime_changed_during_staging')
        require(backend.public_health()['releaseHash'] == BASE_HASH, 'base_changed_during_staging')
        try:
            switch_pointer(d, backend, new_pointer)
            health = backend.public_health()
            require(health['releaseHash'] == proof['releaseHash'] and health['products'] == base['manifest']['products'] and health['mediaReady'] is True and health['checkoutEnabled'] is True, 'live_health_mismatch')
            require(get_json('/api/config')['socials'] == proof['socials'], 'live_social_config_mismatch')
        except BaseException:
            switch_pointer(d, backend, old_pointer)
            require(backend.public_health()['releaseHash'] == BASE_HASH, 'rollback_failed')
            raise
    record = {**proof, 'passed':True, 'live':True, 'backupRoot':backup,
              'accountAndPaymentStoragePreserved':True, 'remoteDeletions':False, 'liveCheckoutPreserved':True}
    (E/'deployment.json').write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
    emit('deployment_verified', releaseHash=proof['releaseHash'], publicFilesChanged=0)


if __name__ == '__main__':
    main()
