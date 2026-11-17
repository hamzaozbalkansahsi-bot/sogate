#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/collect-native-product-gallery.py
# Açıklama   : Dondurulmuş kamu galerilerini ayrı özel önbelleğe indirir; hiçbir fotoğrafa yayın onayı vermez.
import argparse
import concurrent.futures
import hashlib
import ipaddress
import json
import os
import socket
import threading
import time
import uuid
import warnings
from pathlib import Path
from urllib.parse import urlsplit

import requests
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
BASE = Path('D:/sexogate-local-artifacts-20261114/private-installs')
TARGET = BASE / 'product-gallery-20261117'
DATASET = '057fb50f7d5887fee341e3d5b4a3dd64'
HOSTS = {'cdn.dsmcdn.com'}
FORMATS = {'JPEG': ('image/jpeg', 'jpg'), 'PNG': ('image/png', 'png'), 'WEBP': ('image/webp', 'webp')}
MAX_BYTES = 12 * 1024 * 1024
MAX_PIXELS = 40000000
Image.MAX_IMAGE_PIXELS = MAX_PIXELS


def dump(path, value):
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf8')
    temporary.replace(path)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def safe_url(url, resolve=True):
    p = urlsplit(url)
    if (p.scheme != 'https' or p.hostname not in HOSTS or p.username or p.password
            or p.port not in (None, 443) or p.fragment or not p.path.startswith('/')):
        raise ValueError('GALLERY_SOURCE_URL_REJECTED')
    if resolve:
        addresses = socket.getaddrinfo(p.hostname, 443, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(row[4][0]).is_global for row in addresses):
            raise ValueError('GALLERY_PRIVATE_ADDRESS_REJECTED')
    return url


def probe(path, declared_mime=None):
    size = path.stat().st_size
    if not 0 < size <= MAX_BYTES:
        raise ValueError('GALLERY_IMAGE_SIZE_REJECTED')
    with warnings.catch_warnings():
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        with Image.open(path) as source:
            width, height = source.size
            if width < 1 or height < 1 or width * height > MAX_PIXELS or source.format not in FORMATS:
                raise ValueError('GALLERY_IMAGE_SIGNATURE_REJECTED')
            mime, extension = FORMATS[source.format]
            source.verify()
    if declared_mime and declared_mime.split(';', 1)[0].lower().strip() not in (mime, 'image/jpg' if mime == 'image/jpeg' else mime):
        raise ValueError('GALLERY_IMAGE_MIME_MISMATCH')
    return {'sha256': digest(path), 'mime': mime, 'width': width, 'height': height,
            'bytes': size, 'extension': extension, 'originalBytesChanged': False}


class Collector:
    def __init__(self):
        self.stop = threading.Event()
        self.rate_lock = threading.Lock()
        self.next_start = 0.0
        self.access_block = None
        self.attempts = 0

    def acquire(self):
        with self.rate_lock:
            if self.stop.is_set():
                return False
            delay = self.next_start - time.monotonic()
            if delay > 0 and self.stop.wait(delay):
                return False
            if self.stop.is_set():
                return False
            self.next_start = time.monotonic() + 0.55
            self.attempts += 1
            return True

    def download(self, url):
        if self.stop.is_set():
            return url, {'state': 'not_requested_after_access_block'}
        temporary = TARGET / 'media' / (uuid.uuid4().hex + '.part')
        try:
            safe_url(url)
            if not self.acquire():
                return url, {'state': 'not_requested_after_access_block'}
            with requests.Session() as session:
                session.trust_env = False
                with session.get(url, headers={'User-Agent': 'SEXOGATE-Authorized-Catalog/1.0', 'Accept': 'image/jpeg,image/png,image/webp'},
                        timeout=(12, 40), stream=True, allow_redirects=False) as response:
                    if response.status_code in (401, 403, 429):
                        self.access_block = self.access_block or response.status_code
                        self.stop.set()
                        return url, {'state': 'access_blocked', 'httpStatus': response.status_code}
                    if response.is_redirect:
                        return url, {'state': 'failed', 'reason': 'GALLERY_REDIRECT_REJECTED'}
                    if response.status_code != 200:
                        return url, {'state': 'failed', 'httpStatus': response.status_code}
                    declared = response.headers.get('Content-Type', '').split(';', 1)[0].strip().lower()
                    if declared not in ('image/jpeg', 'image/jpg', 'image/png', 'image/webp'):
                        raise ValueError('GALLERY_HTTP_MIME_REJECTED')
                    if int(response.headers.get('Content-Length', '0')) > MAX_BYTES:
                        raise ValueError('GALLERY_IMAGE_SIZE_REJECTED')
                    count = 0
                    with temporary.open('xb') as stream:
                        for chunk in response.iter_content(65536):
                            count += len(chunk)
                            if count > MAX_BYTES:
                                raise ValueError('GALLERY_IMAGE_SIZE_REJECTED')
                            stream.write(chunk)
            info = probe(temporary, declared)
            target = TARGET / 'media' / (info['sha256'] + '.' + info['extension'])
            if target.exists():
                if digest(target) != info['sha256']:
                    raise ValueError('GALLERY_CACHE_HASH_CHANGED')
                temporary.unlink()
            else:
                temporary.replace(target)
            return url, {**info, 'file': target.name, 'state': 'ready', 'origin': 'downloaded'}
        except Exception as error:
            reason = str(error) if isinstance(error, ValueError) and str(error).startswith('GALLERY_') else type(error).__name__
            return url, {'state': 'failed', 'reason': reason}
        finally:
            if temporary.exists() and temporary.resolve().is_relative_to((TARGET / 'media').resolve()):
                temporary.unlink()


def make_sheets(manifest, final=False):
    seen_hashes = {image['sha256'] for sheet in manifest['sheets'] for image in sheet['images']}
    by_hash = {}
    for slot in manifest['slots']:
        key = slot['productId'] + ':' + str(slot['sourceIndex'])
        asset = manifest['assets'].get(slot['sourceUrl'], {})
        if slot['review'] != 'pending_human_review' or asset.get('state') != 'ready':
            continue
        if asset['sha256'] in manifest['products'][slot['productId']]['baseHashes'].values():
            continue
        association = {'slot': key, 'productId': slot['productId'], 'code': slot['code'],
                       'sourceIndex': slot['sourceIndex'], 'sourceSha256': slot['sourceSha256']}
        by_hash.setdefault(asset['sha256'], {'asset': asset, 'associations': []})['associations'].append(association)
    # Aynı byte'ların sonradan gelen kaynak ilişkileri tek inceleme görselinde tutulur.
    manifest['reviewAssociations'] = {sha: row['associations'] for sha, row in by_hash.items()}
    pending = [row for sha, row in by_hash.items() if sha not in seen_hashes]
    if not final:
        pending = pending[:len(pending) // 30 * 30]
    font_path = Path('C:/Windows/Fonts/arial.ttf')
    font = ImageFont.truetype(str(font_path), 18) if font_path.is_file() else ImageFont.load_default()
    for start in range(0, len(pending), 30):
        group = pending[start:start + 30]
        page = len(manifest['sheets']) + 1
        sheet = Image.new('RGB', (1400, 2280), '#fbf4ef')
        draw = ImageDraw.Draw(sheet)
        images = []
        for index, row in enumerate(group):
            asset = row['asset']; association = row['associations'][0]
            x, y = index % 5 * 280, index // 5 * 380
            with Image.open(TARGET / 'media' / asset['file']) as image:
                thumbnail = image.convert('RGB'); thumbnail.thumbnail((264, 286))
                sheet.paste(thumbnail, (x + (280 - thumbnail.width) // 2, y + 4))
            label = association['code']
            for line_index in range(2):
                draw.text((x + 8, y + 294 + line_index * 22), label[line_index * 25:(line_index + 1) * 25], fill='#24191d', font=font)
            draw.text((x + 8, y + 340), 'Kaynak #' + str(association['sourceIndex']) + (' / +' + str(len(row['associations']) - 1) if len(row['associations']) > 1 else ''), fill='#5a0a20', font=font)
            images.append({'position': index, 'sha256': asset['sha256'], 'file': asset['file'],
                           'associations': row['associations'], 'review': 'pending_human_review'})
        name = 'gallery-review-' + str(page).zfill(4) + '.jpg'
        path = TARGET / 'review-sheets' / name
        if path.exists():
            raise ValueError('GALLERY_IMMUTABLE_SHEET_EXISTS')
        sheet.save(path, format='JPEG', quality=88, optimize=True)
        manifest['sheets'].append({'file': name, 'sha256': digest(path), 'images': images,
                                   'originalImagesChanged': False})
        dump(TARGET / 'review-sheets' / (name + '.json'), manifest['sheets'][-1])


def summary(manifest, collector=None):
    assets = list(manifest['assets'].values())
    return {'schema': 1, 'state': manifest['state'], 'sourceDataset': DATASET, 'publicProducts': len(manifest['products']),
        'sourceSlots': len(manifest['slots']), 'uniqueUrls': len(manifest['assets']),
        'readyAssets': sum(a.get('state') == 'ready' for a in assets),
        'downloadedAssets': sum(a.get('state') == 'ready' and a.get('origin') == 'downloaded' for a in assets),
        'existingAssetsLinked': sum(a.get('state') == 'ready' and a.get('origin') == 'existing_cache' for a in assets),
        'failedAssets': sum(a.get('state') == 'failed' for a in assets), 'reviewSheets': len(manifest['sheets']),
        'accessBlock': collector.access_block if collector else manifest.get('accessBlock'),
        'newApprovalsGranted': 0, 'publishedOrUploaded': False, 'sourceCatalogChanged': False,
        'manifest': str(TARGET / 'manifest.json'), 'reviewDirectory': str(TARGET / 'review-sheets')}


def collect():
    if TARGET.resolve() != BASE.resolve() / 'product-gallery-20261117':
        raise ValueError('GALLERY_TARGET_REJECTED')
    selection_file = ROOT / '.local/native-marketplace-selection.json'
    selection = json.loads(selection_file.read_text('utf8')); prepared = Path(selection['path']); home = prepared.parent
    if selection.get('dataset') != DATASET or digest(prepared / 'catalog-data.json') != selection['sha256']:
        raise ValueError('GALLERY_FROZEN_SOURCE_MISMATCH')
    TARGET.mkdir(exist_ok=True)
    proof_file = TARGET / 'immutable-source-proof.json'
    if not proof_file.is_file():
        baseline = ROOT / 'docs/native-marketplace-source-local-results.json'
        proof_file.write_bytes(baseline.read_bytes())
    proven = json.loads(proof_file.read_text('utf8'))
    if (proven.get('dataset') != DATASET or proven.get('loadedNew') != 958
            or proven.get('fingerprint', {}).get('catalogDataSha256') != selection['sha256']
            or not proven.get('executions')
            or any(result.get('exitCode') != 0 for result in proven['executions'].values())):
        raise ValueError('GALLERY_IMMUTABLE_SOURCE_PROOF_REQUIRED')
    data = json.loads((prepared / 'catalog-data.json').read_text('utf8'))
    public = [p for p in data['products'][2194:] if p['images'] and p['visualApprovedIndices'] and not p['eligibilityHold'] and p['salePriceMinor']]
    observed_file = ROOT / '.local/native-product-gallery-public-before.json'
    observed = json.loads(observed_file.read_text('utf8'))
    if len(public) != 803 or {p['id'] for p in public} != set(observed['byProduct']):
        raise ValueError('GALLERY_ACTUAL_PUBLIC_SET_MISMATCH')
    work = {k: v for f in (prepared / 'catalog-workbench').glob('*.json') for k, v in json.loads(f.read_text('utf8')).items()}
    cache = json.loads((home / 'images.json').read_text('utf8'))
    source_proof = {'selection': digest(selection_file), 'catalog': digest(prepared / 'catalog-data.json'),
                    'cache': digest(home / 'images.json'), 'actualPublic': digest(observed_file),
                    'immutableSourceProof': digest(proof_file),
                    'workbench': {f.name: digest(f) for f in sorted((prepared / 'catalog-workbench').glob('*.json'))}}
    for path in [TARGET, TARGET / 'media', TARGET / 'review-sheets']:
        path.mkdir(exist_ok=True)
    path = TARGET / 'manifest.json'
    if path.is_file():
        manifest = json.loads(path.read_text('utf8'))
        if manifest.get('sourceProof') != source_proof or manifest.get('sourceDataset') != DATASET:
            raise ValueError('GALLERY_RESUME_SOURCE_CHANGED')
        if manifest.get('state') == 'access_blocked':
            raise ValueError('GALLERY_ACCESS_REVIEW_REQUIRED')
    else:
        manifest = {'schema': 1, 'state': 'preparing', 'sourceDataset': DATASET, 'sourceProof': source_proof,
                    'products': {}, 'slots': [], 'assets': {}, 'sheets': []}
        for product in sorted(public, key=lambda p: p['id']):
            w = work[product['id']]; media = w['media']; source_sha = w['source']['htmlSha256']
            approved = {media[int(index)]['sourceUrl'] for index in product['visualApprovedIndices']}
            base_urls = {item['sourceUrl'] for item in media}
            manifest['products'][product['id']] = {'code': product['code'], 'sourceSha256': source_sha,
                'baseHashes': {str(index): item['sha256'] for index, item in enumerate(media)}}
            for index, url in enumerate(w['sourceImages']):
                safe_url(url, resolve=False)
                review = 'existing_approved' if url in approved else 'existing_rejected' if url in base_urls else 'pending_human_review'
                manifest['slots'].append({'productId': product['id'], 'code': product['code'], 'sourceSha256': source_sha,
                    'sourceIndex': index, 'sourceUrl': url, 'review': review, 'approved': review == 'existing_approved'})
                manifest['assets'].setdefault(url, {'state': 'pending'})
    collector = Collector()
    def load_asset(url):
        if collector.stop.is_set():
            return url, {'state': 'not_requested_after_access_block'}
        cached = cache.get(url)
        if not cached or not (home / 'media' / cached['file']).is_file():
            return collector.download(url)
        try:
            original = home / 'media' / cached['file']
            if not original.resolve().is_relative_to((home / 'media').resolve()):
                raise ValueError('GALLERY_EXISTING_CACHE_PATH_REJECTED')
            info = probe(original, cached['mime'])
            if info['sha256'] != cached['sha256']:
                raise ValueError('GALLERY_EXISTING_CACHE_HASH_MISMATCH')
            target = TARGET / 'media' / (info['sha256'] + '.' + info['extension'])
            if not target.exists():
                os.link(original, target)
            elif digest(target) != info['sha256']:
                raise ValueError('GALLERY_CACHE_HASH_CHANGED')
            return url, {**info, 'state': 'ready', 'origin': 'existing_cache', 'file': target.name}
        except Exception as error:
            collector.stop.set()
            reason = str(error) if isinstance(error, ValueError) else type(error).__name__
            return url, {'state': 'failed', 'reason': reason}
    def checkpoint(final=False):
        make_sheets(manifest, final=final)
        dump(path, manifest)
        state = summary(manifest, collector)
        dump(TARGET / 'status.json', state); dump(ROOT / '.local/native-product-gallery-status.json', state)
        print(json.dumps(state), flush=True)
    queue = [url for url, item in manifest['assets'].items() if item.get('state') != 'ready']
    manifest['state'] = 'collecting'; checkpoint()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for index, (url, asset) in enumerate(pool.map(load_asset, queue), 1):
            manifest['assets'][url] = asset
            if index % 30 == 0:
                checkpoint()
    manifest['accessBlock'] = collector.access_block
    manifest['state'] = 'access_blocked' if collector.access_block else 'complete' if all(a.get('state') == 'ready' for a in manifest['assets'].values()) else 'partial'
    after = {'selection': digest(selection_file), 'catalog': digest(prepared / 'catalog-data.json'),
             'cache': digest(home / 'images.json'), 'actualPublic': digest(observed_file),
             'immutableSourceProof': digest(proof_file),
             'workbench': {f.name: digest(f) for f in sorted((prepared / 'catalog-workbench').glob('*.json'))}}
    if after != source_proof:
        raise ValueError('GALLERY_FROZEN_SOURCE_CHANGED')
    checkpoint(final=True)


def self_test():
    for url in ['http://cdn.dsmcdn.com/a.jpg', 'https://127.0.0.1/a.jpg', 'https://cdn.dsmcdn.com.evil/a.jpg',
                'https://user:password@cdn.dsmcdn.com/a.jpg', 'https://cdn.dsmcdn.com:444/a.jpg', 'https://cdn.dsmcdn.com/a.jpg#x']:
        try:
            safe_url(url, resolve=False)
        except ValueError:
            continue
        raise AssertionError('unsafe URL accepted')
    safe_url('https://cdn.dsmcdn.com/actual/a.jpg', resolve=False)
    stopped = Collector(); stopped.stop.set()
    assert stopped.download('https://cdn.dsmcdn.com/a.jpg')[1]['state'] == 'not_requested_after_access_block'
    print(json.dumps({'passed': 8, 'networkCalled': False, 'sourceChanged': False}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--self-test', action='store_true'); args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        collect()
