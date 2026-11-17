#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/collect-native-marketplace-expansion.py
# Açıklama   : Korunan kaynakları değiştirmeden izinli kamu kategorilerini tek istekli, kanıtlı kuyruğa genişletir.
import argparse
import hashlib
import json
import math
import os
import re
import sqlite3
import time
import unicodedata
import uuid
from contextlib import closing
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import requests

from native_marketplaces import AGENT, detail_page, fetch, safe_url, search_page

BASE = Path('D:/sexogate-local-artifacts-20261114/private-installs')
SOURCE = BASE / 'marketplace-catalog-20261116-next'
HOME = BASE / 'marketplace-expansion-20261117-research'
LOCAL_REPORT = Path(__file__).resolve().parent.parent / '.local' / 'marketplace-expansion-collection.json'
CATEGORIES = [
    ('lingerie', 'fantezi-giyim-x-c109067'),
    ('costumes', 'fantezi-kostum-x-c109040'),
    ('accessories', 'fantezi-aksesuar-x-c109045'),
    ('games-gifts', 'fantezi-urunleri-x-c146009'),
    ('care', 'kayganlastirici-jel-x-c105538'),
    ('dice', 'kamasutra-zari-y-s44663'),
    ('couple-games', 'cinsel-oyunlar-y-s17909'),
    ('adult-cards', 'oyun-kartlari-x-c108707'),
]


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def atomic_bytes(target, data):
    temporary = target.with_name(target.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        temporary.write_bytes(data)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def youth_coded(value):
    text = unicodedata.normalize('NFKD', value.casefold().replace('ı', 'i'))
    text = ''.join(c for c in text if not unicodedata.combining(c))
    if re.search(r'\b(?:yetiskin\w*|adult\w*)\b', text):
        text = re.sub(r'\b(?:seks|sex|cinsel)\s+bebek\w*\b', ' ', text)
    return bool(re.search(r'\b(?:cocuk\w*|bebek\w*|kids?|child\w*|baby|teen\w*|ergen\w*|lise\w*|ogrenci\w*|okul\w*|school\w*|student\w*)\b', text))


def canonical_redirect(source, location, product_id):
    target = safe_url(urljoin(source, location), {'www.trendyol.com'})
    matched = re.search(r'-p-(\d+)(?:/|$)', urlsplit(target).path)
    if not matched or matched.group(1) != product_id or target == source:
        raise ValueError('SOURCE_REDIRECT_IDENTITY_REVIEW_REQUIRED')
    return target


def initialize():
    HOME.mkdir(parents=True, exist_ok=True)
    for directory in ['raw', 'observations', 'category-pages']:
        (HOME / directory).mkdir(exist_ok=True)
    filename = HOME / 'research.sqlite'
    if not filename.exists():
        source_file = SOURCE / 'research.sqlite'
        source_wal = SOURCE / 'research.sqlite-wal'
        if source_wal.exists() and source_wal.stat().st_size:
            raise ValueError('FROZEN_SOURCE_HAS_WAL_NEEDS_CONSISTENT_SNAPSHOT')
        with closing(sqlite3.connect(f'file:{source_file}?mode=ro&immutable=1', uri=True)) as source:
            with closing(sqlite3.connect(filename)) as target:
                source.backup(target)
    for original in (SOURCE / 'raw').glob('*.html'):
        target = HOME / 'raw' / original.name
        if not target.exists():
            os.link(original, target)
    database = sqlite3.connect(filename)
    database.row_factory = sqlite3.Row
    database.execute('PRAGMA journal_mode=WAL')
    database.executescript('''
    CREATE TABLE IF NOT EXISTS expansion_categories(
      key TEXT PRIMARY KEY,url TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'pending',
      reported_total INTEGER,last_page INTEGER NOT NULL DEFAULT 0,error TEXT,observed_at INTEGER);
    CREATE TABLE IF NOT EXISTS expansion_pages(
      category_key TEXT,page INTEGER,url TEXT,sha256 TEXT,raw_ids_json TEXT,
      selected INTEGER,at INTEGER,PRIMARY KEY(category_key,page));
    CREATE TABLE IF NOT EXISTS expansion_memberships(
      category_key TEXT,platform TEXT,id TEXT,first_seen_at INTEGER,
      PRIMARY KEY(category_key,platform,id));
    CREATE TABLE IF NOT EXISTS expansion_attempts(
      attempt_id INTEGER PRIMARY KEY,platform TEXT,id TEXT,url TEXT,status TEXT,
      error TEXT,sha256 TEXT,raw_path TEXT,at INTEGER);
    CREATE TABLE IF NOT EXISTS expansion_state(key TEXT PRIMARY KEY,value TEXT);
    CREATE TABLE IF NOT EXISTS expansion_initial_ids(platform TEXT,id TEXT,status TEXT,
      PRIMARY KEY(platform,id));
    CREATE TABLE IF NOT EXISTS expansion_redirects(
      platform TEXT,id TEXT,source_url TEXT,target_url TEXT,http_status INTEGER,at INTEGER,
      PRIMARY KEY(platform,id,source_url,target_url));
    ''')
    if not database.execute("SELECT 1 FROM expansion_state WHERE key='initialized'").fetchone():
        database.execute('INSERT INTO expansion_initial_ids SELECT platform,id,status FROM products')
        database.execute("INSERT INTO expansion_state VALUES('initialized',?)", (str(int(time.time())),))
    for row in database.execute("SELECT platform,id,detail_json,listing_json FROM products WHERE status!='excluded_scope'").fetchall():
        data = json.loads(row['detail_json'] or row['listing_json'] or '{}')
        if youth_coded(data.get('title', '')):
            database.execute("UPDATE products SET status='excluded_scope',error='YOUTH_CODED_TITLE' WHERE platform=? AND id=?",
                             (row['platform'], row['id']))
    for key, slug in CATEGORIES:
        database.execute('INSERT OR IGNORE INTO expansion_categories(key,url) VALUES(?,?)', (key, 'https://www.trendyol.com/' + slug))
    database.commit()
    return database


def report(database, state):
    counts = dict(database.execute('SELECT status,COUNT(*) FROM products GROUP BY status').fetchall())
    new = dict(database.execute('''SELECT p.status,COUNT(*) FROM products p LEFT JOIN expansion_initial_ids i
      ON i.platform=p.platform AND i.id=p.id WHERE i.id IS NULL GROUP BY p.status''').fetchall())
    retried = dict(database.execute('''SELECT p.status,COUNT(*) FROM products p JOIN expansion_initial_ids i
      ON i.platform=p.platform AND i.id=p.id WHERE i.status='needs_review' GROUP BY p.status''').fetchall())
    categories = [dict(r) for r in database.execute('''SELECT c.*,COUNT(m.id) AS selected_products
      FROM expansion_categories c LEFT JOIN expansion_memberships m ON m.category_key=c.key GROUP BY c.key''')]
    result = {'state': state, 'database': str(HOME / 'research.sqlite'), 'products': counts,
              'newProducts': new, 'initialNeedsReviewNow': retried, 'categories': categories,
              'observedAt': int(time.time()), 'published': False, 'oldAreasChanged': False,
              'allMarketplaceProductsTransferred': False, 'rateLimit': 'serial; at least1second between requests'}
    target = HOME / 'report.json'
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    os.replace(temporary, target)
    local = LOCAL_REPORT
    local.parent.mkdir(exist_ok=True)
    local_temporary = local.with_suffix('.tmp')
    local_temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    os.replace(local_temporary, local)
    print(encode({'state': state, 'products': counts, 'newProducts': new, 'initialNeedsReviewNow': retried}), flush=True)


def observe(database, raw, row, status, error=None):
    now = int(time.time())
    digest = hashlib.sha256(raw).hexdigest() if raw is not None else None
    path = HOME / 'observations' / (row['id'] + '-' + digest + '.html') if digest else None
    if path and (not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != digest):
        atomic_bytes(path, raw)
    database.execute('''INSERT INTO expansion_attempts(platform,id,url,status,error,sha256,raw_path,at)
      VALUES(?,?,?,?,?,?,?,?)''', (row['platform'], row['id'], row['url'], status, error, digest, str(path) if path else None, now))
    return now, digest, path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pages-per-category', type=int, default=3)
    parser.add_argument('--details', type=int, default=500)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--resolve-redirects', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        assert youth_coded('Fantezi Liseli Kostümü')
        assert youth_coded('Öğrenci kostümü')
        assert not youth_coded('Kadın Fantezi Gecelik')
        assert not youth_coded('Çiftlere Özel Oyun Kartları')
        assert youth_coded('Seksi Erkek Okul Kostümü')
        assert not youth_coded('Yetişkin gerçekçi seks bebekleri')
        assert all('/sr' not in slug for _, slug in CATEGORIES)
        assert canonical_redirect('https://www.trendyol.com/old-p-123', '/new-p-123?merchantId=1', '123') == 'https://www.trendyol.com/new-p-123?merchantId=1'
        for location in ['/new-p-456', 'https://example.com/new-p-123', '/giris']:
            try:
                canonical_redirect('https://www.trendyol.com/old-p-123', location, '123')
            except ValueError:
                pass
            else:
                raise AssertionError('Redirect outside the same public product was accepted')
        print('collector self-test passed')
        return
    if not 1 <= args.pages_per_category <= 20 or not 1 <= args.details <= 2000:
        raise ValueError('COLLECTION_BOUND_REQUIRED')
    database = initialize()
    blocked = database.execute("SELECT value FROM expansion_state WHERE key='blocked'").fetchone()
    if blocked:
        report(database, 'access_blocked')
        database.close()
        raise SystemExit(2)
    last_request = 0.0

    def request(url):
        nonlocal last_request
        time.sleep(max(0, 1.05 - (time.monotonic() - last_request)))
        try:
            return fetch(url)
        finally:
            last_request = time.monotonic()

    def stop(error):
        database.execute("INSERT OR REPLACE INTO expansion_state VALUES('blocked',?)", (str(error),))
        database.commit()
        report(database, 'access_blocked')
        database.close()
        raise SystemExit(2)

    def read_product(row):
        nonlocal last_request
        try:
            return request(row['url']), row['url']
        except ValueError as error:
            if str(error) != 'SOURCE_REDIRECT_REVIEW_REQUIRED' or not args.resolve_redirects:
                raise
        # A normal public canonical redirect is reviewed against the same source product ID.
        # Account/login redirects and another product's replacement are kept under review.
        time.sleep(max(0, 1.05 - (time.monotonic() - last_request)))
        try:
            with requests.get(row['url'], headers={'User-Agent': AGENT, 'Accept': 'text/html,application/json'},
                              timeout=(12, 35), stream=True, allow_redirects=False) as response:
                if response.status_code in [401, 403, 429]:
                    raise PermissionError('SOURCE_ACCESS_' + str(response.status_code))
                if response.status_code not in [301, 302, 303, 307, 308]:
                    raise ValueError('SOURCE_REDIRECT_CHANGED_REVIEW_REQUIRED')
                target = canonical_redirect(row['url'], response.headers.get('Location', ''), row['id'])
                database.execute('INSERT OR IGNORE INTO expansion_redirects VALUES(?,?,?,?,?,?)',
                                 (row['platform'], row['id'], row['url'], target, response.status_code, int(time.time())))
                database.commit()
        finally:
            last_request = time.monotonic()
        return request(target), target

    report(database, 'started')
    # Round-robin discovery covers every product group before collecting deeper pages.
    for page in range(1, args.pages_per_category + 1):
        for key, _ in CATEGORIES:
            category = database.execute('SELECT * FROM expansion_categories WHERE key=?', (key,)).fetchone()
            if category['status'] in ['exhausted', 'repeated_page', 'needs_review']:
                continue
            if database.execute('SELECT 1 FROM expansion_pages WHERE category_key=? AND page=?', (key, page)).fetchone():
                continue
            url = category['url'] + '?pi=' + str(page)
            try:
                raw = request(url)
                digest = hashlib.sha256(raw).hexdigest()
                path = HOME / 'category-pages' / f'{key}-{page}-{digest}.html'
                if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                    atomic_bytes(path, raw)
                data = search_page(raw)
                if type(data['page']) is not int or data['page'] != page:
                    raise ValueError('SOURCE_PAGINATION_MISMATCH')
                if type(data['reportedTotal']) is not int or data['reportedTotal'] < 0:
                    raise ValueError('SOURCE_REPORTED_TOTAL_REVIEW_REQUIRED')
                prior_ids = set()
                for prior in database.execute('SELECT raw_ids_json FROM expansion_pages WHERE category_key=?', (key,)):
                    prior_ids.update(json.loads(prior[0]))
                raw_ids = set(data['rawIds'])
                if not raw_ids or raw_ids <= prior_ids:
                    now = int(time.time())
                    database.execute('INSERT INTO expansion_pages VALUES(?,?,?,?,?,?,?)',
                                     (key, page, url, digest, encode(data['rawIds']), len(data['products']), now))
                    database.execute("UPDATE expansion_categories SET status=?,last_page=?,error=?,observed_at=? WHERE key=?",
                                     ('exhausted' if not raw_ids else 'repeated_page', page, None, now, key))
                    database.commit()
                    continue
                now = int(time.time())
                for product in data['products']:
                    if not re.fullmatch(r'\d+', product['id']):
                        raise ValueError('SOURCE_PRODUCT_ID_REJECTED')
                    status = 'excluded_scope' if youth_coded(product['title']) else 'pending'
                    database.execute('''INSERT OR IGNORE INTO products(platform,id,url,category,listing_json,status,error,updated_at)
                      VALUES(?,?,?,?,?,?,?,?)''', ('trendyol', product['id'], product['url'], encode(product['category']),
                                                encode(product), status, 'YOUTH_CODED_TITLE' if status == 'excluded_scope' else None, now))
                    database.execute('INSERT OR IGNORE INTO expansion_memberships VALUES(?,?,?,?)', (key, 'trendyol', product['id'], now))
                database.execute('INSERT INTO expansion_pages VALUES(?,?,?,?,?,?,?)',
                                 (key, page, url, digest, encode(data['rawIds']), len(data['products']), now))
                total = data['reportedTotal']
                exhausted = isinstance(total, int) and page >= math.ceil(total / 36)
                database.execute('UPDATE expansion_categories SET status=?,reported_total=?,last_page=?,error=NULL,observed_at=? WHERE key=?',
                                 ('exhausted' if exhausted else 'bounded', total, page, now, key))
                database.commit()
                report(database, 'discovering_categories')
            except PermissionError as error:
                stop(error)
            except Exception as error:
                database.rollback()
                database.execute("UPDATE expansion_categories SET status='needs_review',error=?,observed_at=? WHERE key=?",
                                 ('page=' + str(page) + ':' + type(error).__name__ + ':' + str(error)[:160], int(time.time()), key))
                database.commit()
                report(database, 'category_needs_review')

    rows = database.execute('''SELECT p.* FROM products p LEFT JOIN expansion_initial_ids i ON i.platform=p.platform AND i.id=p.id
      WHERE p.status IN ('pending','needs_review') AND (NOT EXISTS(
        SELECT 1 FROM expansion_attempts a WHERE a.platform=p.platform AND a.id=p.id)
        OR (? AND p.error='ValueError:SOURCE_REDIRECT_REVIEW_REQUIRED'))
      ORDER BY CASE WHEN i.status='needs_review' THEN 0 ELSE 1 END,p.id LIMIT ?''', (int(args.resolve_redirects), args.details)).fetchall()
    for index, row in enumerate(rows, 1):
        if not re.fullmatch(r'\d+', row['id']):
            raise ValueError('SOURCE_PRODUCT_ID_REJECTED')
        raw = None
        try:
            raw, actual_url = read_product(row)
            observed_at, _, path = observe(database, raw, row, 'fetched')
            detail = detail_page(raw, actual_url)
            if detail['sourceId'] != row['id']:
                raise ValueError('SOURCE_PRODUCT_ID_MISMATCH')
            detail['observedAt'] = observed_at
            status = 'excluded_scope' if youth_coded(detail['title']) else 'ready'
            database.execute('''UPDATE products SET detail_json=?,status=?,error=?,attempts=attempts+1,updated_at=?
              WHERE platform=? AND id=?''', (encode(detail), status, 'YOUTH_CODED_TITLE' if status == 'excluded_scope' else None,
                                            observed_at, row['platform'], row['id']))
            # Replacing this directory entry never writes into a borrowed hardlinked inode.
            target = HOME / 'raw' / (row['id'] + '.html')
            temporary = target.with_name(target.name + '.' + uuid.uuid4().hex + '.tmp')
            try:
                os.link(path, temporary)
                os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)
            database.execute('UPDATE expansion_attempts SET status=? WHERE attempt_id=(SELECT MAX(attempt_id) FROM expansion_attempts)', (status,))
            database.commit()
        except PermissionError as error:
            observe(database, raw, row, 'access_blocked', str(error))
            stop(error)
        except Exception as error:
            reason = type(error).__name__ + ':' + str(error)[:200]
            observe(database, raw, row, 'needs_review', reason)
            database.execute("UPDATE products SET status='needs_review',error=?,attempts=attempts+1,updated_at=? WHERE platform=? AND id=?",
                             (reason, int(time.time()), row['platform'], row['id']))
            database.commit()
        if index % 10 == 0 or index == len(rows):
            report(database, 'reading_individual_products')
    report(database, 'bounded_collection_pass_finished')
    database.close()


if __name__ == '__main__':
    main()
