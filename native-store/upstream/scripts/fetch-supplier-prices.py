"""Read current official public selling prices for exact immutable SKUs.

No write to shop data, supplier accounts, baskets or payment endpoints.
Uses the unconditional, VAT-inclusive JSON-LD Offer.price, not a struck-through
list price or payment-method discount. All arithmetic uses Decimal/kurus.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import re
import threading
import time
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from urllib.parse import urlparse

import requests
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/catalog-expansion'
PAGES = OUT / 'price-pages'
UA = 'NODENO-PricingVerification/1.0 (+https://nodenohome.com; authorized retailer)'
STATE = threading.local()


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def sha(content):
    return hashlib.sha256(content).hexdigest()


def allowed(url):
    parsed = urlparse(url)
    return parsed.scheme == 'https' and parsed.hostname in {'www.adoremobilya.com', 'adoremobilya.com'} and not parsed.username and not parsed.password and parsed.port in (None, 443)


def session():
    if not hasattr(STATE, 'session'):
        STATE.session = requests.Session()
        STATE.session.headers.update({'User-Agent': UA, 'Cache-Control': 'no-cache', 'Accept-Language': 'tr-TR,tr;q=0.9'})
    return STATE.session


def nodes(tree):
    def walk(node):
        if isinstance(node, list):
            for item in node:
                yield from walk(item)
        elif isinstance(node, dict):
            if '@type' in node:
                yield node
            if '@graph' in node:
                yield from walk(node['@graph'])
    for element in tree.xpath('//script[@type="application/ld+json"]'):
        try:
            yield from walk(json.loads(element.text or ''))
        except (json.JSONDecodeError, TypeError):
            continue


def is_product(node):
    value = node.get('@type')
    return value == 'Product' or isinstance(value, list) and 'Product' in value


def kurus(value):
    # JSON-LD numbers use a decimal point, never Turkish thousands separators.
    raw = str(value)
    if not re.fullmatch(r'\d+(?:\.\d{1,2})?', raw):
        raise ValueError('invalid_price_decimal')
    amount = Decimal(raw)
    if not amount.is_finite() or amount <= 0 or amount > Decimal('100000000'):
        raise ValueError('nonpositive_or_invalid_price')
    return int((amount * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def parse(content, expected):
    tree = html.fromstring(content)
    candidates = [node for node in nodes(tree) if is_product(node) and str(node.get('sku', '')).strip() == expected['code']]
    if len(candidates) != 1:
        raise ValueError('exact_sku_not_unique_or_missing')
    product = candidates[0]
    source_id = str(product.get('productID', '')).strip()
    if expected.get('id') and source_id != str(expected['id']):
        raise ValueError('source_product_id_changed')
    offer = product.get('offers')
    if isinstance(offer, list):
        if len(offer) != 1:
            raise ValueError('ambiguous_offers')
        offer = offer[0]
    if not isinstance(offer, dict) or offer.get('@type') != 'Offer':
        raise ValueError('missing_single_public_offer')
    if offer.get('priceCurrency') != 'TRY':
        raise ValueError('unverified_currency')
    original = kurus(offer.get('price'))
    sale = int((Decimal(original) * Decimal('1.30')).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    visible = [' '.join(el.itertext()).strip() for el in tree.xpath('//*[@data-toggle="price-sell-vat"]')]
    visible = list(dict.fromkeys(re.sub(r'\s+', '', x) for x in visible if x.strip()))
    # Official template suppresses kurus, so verify its displayed whole-lira
    # amount is a rounding of the exact machine-readable public selling price.
    if len(visible) != 1 or not re.fullmatch(r'[0-9.]+(?:,[0-9]{1,2})?', visible[0]):
        raise ValueError('missing_or_ambiguous_visible_selling_price')
    displayed = Decimal(visible[0].replace('.', '').replace(',', '.'))
    if abs(displayed * 100 - original) > 50:
        raise ValueError('visible_and_structured_price_conflict')
    expiry = offer.get('priceValidUntil')
    if expiry and datetime.fromisoformat(expiry).date() < datetime.now(timezone.utc).date():
        raise ValueError('expired_public_offer')
    return {
        'matchedSku': str(product['sku']).strip(), 'matchedProductId': source_id,
        'sourcePrice': str(offer['price']), 'sourcePriceMinor': original,
        'currency': 'TRY', 'salePriceMinor': sale, 'salePrice': str((Decimal(sale) / 100).quantize(Decimal('.01'))),
        'displayedSourcePrice': visible[0], 'sourceAvailability': offer.get('availability'),
        'priceValidUntil': expiry, 'priceBasis': 'jsonld_offer_price_vat_inclusive_unconditional_selling_price',
        'displayPriceVerified': True,
    }


def fetch(product):
    row = {'productId': str(product['id']), 'sourceCode': product['code'], 'sourceUrl': product['sourceUrl']}
    if not allowed(product['sourceUrl']):
        return {**row, 'status': 'unavailable', 'reason': 'untrusted_source_url'}
    key = sha(product['sourceUrl'].encode())[:24]
    receipt = PAGES / (key + '.json')
    for attempt in range(3):
        try:
            # Reuse only a fresh, exact-body-verified snapshot from this task;
            # immutable earlier import prices are never accepted as live proof.
            if attempt == 0 and receipt.exists():
                cached = json.loads(receipt.read_bytes())
                age = (datetime.now(timezone.utc) - datetime.fromisoformat(cached['fetchedAt'])).total_seconds()
                content = (PAGES / (key + '.html')).read_bytes()
                if cached.get('sourceUrl') == product['sourceUrl'] and 0 <= age < 7200 and sha(content) == cached.get('sourceDocumentSha256'):
                    evidence = parse(content, product)
                    return {**row, **cached, **evidence, 'status': 'verified'}
            time.sleep(.35 * (attempt + 1))
            response = session().get(product['sourceUrl'], timeout=(10, 40), allow_redirects=True)
            if not allowed(response.url):
                raise ValueError('redirect_outside_official_site')
            if response.status_code != 200:
                raise ValueError('http_status_' + str(response.status_code))
            if len(response.content) < 10000:
                raise ValueError('incomplete_source_document')
            evidence = parse(response.content, product)
            saved = {'fetchedAt': utcnow(), 'httpStatus': response.status_code, 'finalUrl': response.url,
                     'sourceDocumentSha256': sha(response.content), 'sourceDocumentFile': (PAGES / (key + '.html')).relative_to(ROOT).as_posix()}
            (PAGES / (key + '.html')).write_bytes(response.content)
            receipt.write_text(json.dumps({**row, **saved, **evidence}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            return {**row, **saved, **evidence, 'status': 'verified'}
        except (requests.RequestException, ValueError, KeyError, OSError, InvalidOperation) as error:
            reason = str(error) if isinstance(error, ValueError) else type(error).__name__
            if attempt == 2:
                return {**row, 'status': 'unavailable', 'reason': reason, 'checkedAt': utcnow()}
    raise AssertionError('unreachable')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    source = json.loads((ROOT / 'data/catalog-source.json').read_bytes())
    products = source['products'][:args.limit] if args.limit else source['products']
    PAGES.mkdir(parents=True, exist_ok=True)
    found = []
    started = utcnow()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for index, row in enumerate(pool.map(fetch, products), 1):
            found.append(row)
            if index % 25 == 0:
                print(json.dumps({'completed': index, 'total': len(products), 'statuses': dict(Counter(p['status'] for p in found))}), flush=True)
    result = {'schema': 1, 'generatedAt': utcnow(), 'startedAt': started,
              'supplier': 'https://www.adoremobilya.com', 'currency': 'TRY',
              'pricingRule': {'multiplier': '1.30', 'rounding': 'ROUND_HALF_UP', 'minorUnit': 100,
                              'basis': 'unconditional_vat_inclusive_current_public_selling_price', 'conditionalPaymentDiscountsExcluded': True},
              'counts': dict(Counter(p['status'] for p in found)), 'products': found}
    name = 'prices.json' if not args.limit else 'prices-sample.json'
    (OUT / name).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'output': name, 'products': len(found), **result['counts']}), flush=True)


if __name__ == '__main__':
    main()
