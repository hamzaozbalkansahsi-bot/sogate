"""Normalize permitted public Adore catalog snapshots without evaluating site code.

Run fetch-adore-catalog.ps1 first. Re-running this command is safe during/after
the resumable fetch. It preserves source attribution and never adopts supplier
retail prices, stock, delivery terms or contact information as NODENO's.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse, urljoin, parse_qs
from xml.etree import ElementTree as ET

from lxml import etree, html

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts' / 'source-catalog'
NS = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9', 'i': 'http://www.google.com/schemas/sitemap-image/1.1'}


def clean_text(element) -> str:
    """Readable text with block/BR separation; no script/style/template text."""
    if isinstance(element, str):
        element = html.fragment_fromstring(element, create_parent='div')
    parts = []
    blocks = {'p', 'div', 'li', 'h1', 'h2', 'h3', 'tr'}
    def walk(node):
        if node.tag in ('script','style','template','noscript'):
            return
        if node.tag in blocks or node.tag == 'br':
            parts.append('\n')
        if node.text:
            parts.append(node.text)
        for child in node:
            walk(child)
            if child.tail:
                parts.append(child.tail)
        if node.tag in blocks:
            parts.append('\n')
    walk(element)
    value = ''.join(parts).replace('\xa0', ' ')
    return '\n'.join(line for raw in value.splitlines() if (line := re.sub(r'[\t \r]+', ' ', raw).strip()))


def ld_nodes(tree):
    found = []
    def visit(value):
        if isinstance(value, list):
            for node in value:
                visit(node)
        elif isinstance(value, dict):
            if '@type' in value:
                found.append(value)
            if '@graph' in value:
                visit(value['@graph'])
    for script in tree.xpath('//script[@type="application/ld+json"]'):
        try:
            visit(json.loads(script.text or ''))
        except json.JSONDecodeError:
            continue
    return found


def of_type(node, kind):
    typ = node.get('@type', [])
    return kind == typ or (isinstance(typ, list) and kind in typ)


def category_id(url):
    return urlparse(url).path.strip('/')


def breadcrumbs(nodes):
    bc = next((node for node in nodes if of_type(node, 'BreadcrumbList')), {})
    result = []
    for item in bc.get('itemListElement', []):
        target = item.get('item', '')
        if isinstance(target, dict):
            target = target.get('@id', '')
        result.append({'name': item.get('name', ''), 'sourceUrl': target, 'position': item.get('position')})
    return result


def safe_decimal(value):
    try:
        number = Decimal(str(value))
        return float(number) if number.is_finite() and number >= 0 else None
    except (InvalidOperation, ValueError, TypeError):
        return None


def parse_product(source_html: str, source_url: str, fetched_at: str):
    tree = html.fromstring(source_html)
    nodes = ld_nodes(tree)
    product = next((node for node in nodes if of_type(node, 'Product')), None)
    if not product:
        raise ValueError('NoProductStructuredData')
    offer = product.get('offers', {})
    if isinstance(offer, list):
        offer = offer[0] if offer else {}
    specs = []
    for row in tree.xpath('//*[contains(concat(" ",normalize-space(@class)," ")," adore-row-v5 ")]'):
        labels = row.xpath('./*[contains(@class,"adore-label")]')
        values = row.xpath('./*[contains(@class,"adore-value")]')
        if labels and values:
            label, value = clean_text(labels[0]).rstrip(':').strip(), clean_text(values[0])
            if label and value:
                specs.append({'label': label, 'value': value})
    if not specs:
        for row in tree.xpath('//table//tr'):
            cells = row.xpath('./td|./th')
            if len(cells) == 2:
                label, value = clean_text(cells[0]).rstrip(':').strip(), clean_text(cells[1])
                if label and value and len(label) < 100 and '{{' not in label:
                    specs.append({'label': label, 'value': value})
    description_nodes = tree.xpath('//*[contains(@class,"adore-text-card-v5")]')
    full_nodes = tree.xpath('//*[contains(@class,"adore-product-description-v5")]')
    description = '\n\n'.join(clean_text(e) for e in description_nodes)
    full_description = '\n\n'.join(clean_text(e) for e in full_nodes)
    if not description:
        description = product.get('description', '')
    if not full_description:
        full_description = product.get('description', '')
    images = product.get('image', [])
    if isinstance(images, str):
        images = [images]
    images = [im.get('url', im.get('contentUrl', '')) if isinstance(im, dict) else im for im in images]
    images = list(dict.fromkeys(im for im in images if isinstance(im, str) and urlparse(im).scheme in ('https','http')))
    brand = product.get('brand', {})
    bc = breadcrumbs(nodes)
    category_items = [item for item in bc if item['sourceUrl'].rstrip('/') != source_url.rstrip('/') and category_id(item['sourceUrl'])]
    code = str(product.get('sku', '')).strip()
    product_id = str(product.get('productID', '')).strip()
    if not product_id:
        product_id = 'source-' + hashlib.sha256(source_url.encode()).hexdigest()[:16]
    result = {
        'id': product_id,
        'code': code,
        'title': product.get('name', '').strip(),
        'description': description,
        'fullDescription': full_description,
        'categoryIds': [category_id(item['sourceUrl']) for item in category_items],
        'images': images,
        'specs': specs,
        'sourceUrl': source_url,
        'retailPrice': safe_decimal(offer.get('price')),
        'currency': offer.get('priceCurrency'),
        'salePrice': None,
        'sourceAvailability': offer.get('availability'),
        'sourceBrand': brand.get('name') if isinstance(brand, dict) else brand,
        'sourceGtin': product.get('gtin13', product.get('gtin', product.get('gtin12'))),
        'sourceCategory': product.get('category'),
        'breadcrumbs': bc,
        'fetchedAt': fetched_at,
        'rawDataFile': None,
    }
    if not result['title'] or not result['code'] or not result['images']:
        raise ValueError('MissingRequiredProductField')
    raw = {'sourceUrl': source_url, 'fetchedAt': fetched_at, 'jsonLdProduct': product,
           'breadcrumbs': bc, 'descriptionHtml': '\n'.join(html.tostring(e, encoding='unicode') for e in full_nodes),
           'sourceHtmlSha256': hashlib.sha256(source_html.encode('utf-8')).hexdigest()}
    return result, raw


def parse_category(source_html, source_url, fetched_at):
    tree = html.fromstring(source_html)
    nodes = ld_nodes(tree)
    h1 = tree.xpath('//h1')
    name = clean_text(h1[0]) if h1 else ''
    bc = breadcrumbs(nodes)
    if not name:
        name = next((item['name'] for item in reversed(bc) if item['sourceUrl'].rstrip('/') == source_url.rstrip('/')), '')
    if not name:
        raise ValueError('MissingCategoryName')
    prior = [item for item in bc if category_id(item['sourceUrl']) and item['sourceUrl'].rstrip('/') != source_url.rstrip('/')]
    canonical = tree.xpath('//link[@rel="canonical"]/@href')
    meta_description = tree.xpath('//meta[@name="description"]/@content')
    cards = tree.xpath('//*[contains(concat(" ",normalize-space(@class)," ")," folder-product-list ")]//*[@data-toggle="product"]')
    listed_ids = list(dict.fromkeys(e.get('data-id') for e in cards if e.get('data-id')))
    listed_products = []
    for card in cards:
        hrefs = card.xpath('.//a[@href]/@href')
        if card.get('data-id') and hrefs:
            listed_products.append({'id':card.get('data-id'),'sourceUrl':urljoin(source_url,hrefs[0])})
    pagination_urls = []
    for href in tree.xpath('//a[@href]/@href'):
        target = urljoin(source_url, href)
        parsed = urlparse(target)
        if parsed.hostname == 'www.adoremobilya.com' and any(key in parse_qs(parsed.query) for key in ('pg','page','p')):
            pagination_urls.append(target)
    return {'id': category_id(source_url), 'name': name, 'parentId': category_id(prior[-1]['sourceUrl']) if prior else None,
            'sourceUrl': source_url, 'canonicalSourceUrl': canonical[0] if canonical else source_url,
            'description': meta_description[0] if meta_description else None,
            'listedProductIds': listed_ids, 'paginationUrlsDiscovered':list(dict.fromkeys(pagination_urls)),
            'listedProducts':listed_products,
            'secondaryMembershipCoverage':'initial_public_category_page_only',
            'sourceSitemapEntry': True, 'breadcrumbs': bc, 'fetchedAt': fetched_at}


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


def normalize():
    urls = json.loads((BASE / 'urls.json').read_text(encoding='utf-8-sig'))
    products, categories, errors, pending, excluded, excluded_categories = [], {}, [], [], [], []
    product_ids, codes = {}, {}
    duplicate_ids, duplicate_codes = [], []
    for row in urls:
        path = BASE / 'pages' / (row['key'] + '.html')
        if not path.exists():
            pending.append(row['url'])
            continue
        fetched_at = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
        try:
            source_html = path.read_text(encoding='utf-8')
            if row['kind'] == 'product':
                product, raw = parse_product(source_html, row['url'], fetched_at)
                if product['id'] in product_ids:
                    duplicate_ids.append({'id':product['id'], 'urls':[product_ids[product['id']],row['url']]})
                    continue
                if product['code'] in codes:
                    duplicate_codes.append({'code':product['code'],'urls':[codes[product['code']],row['url']]})
                product_ids[product['id']] = row['url']
                codes[product['code']] = row['url']
                raw_path = BASE / 'products' / (row['key'] + '.json')
                dump(raw_path, raw)
                product['rawDataFile'] = str(raw_path.relative_to(ROOT)).replace('\\','/')
                products.append(product)
                previous = None
                for crumb in product['breadcrumbs']:
                    cat = category_id(crumb['sourceUrl'])
                    if cat and cat in product['categoryIds']:
                        categories.setdefault(cat, {'id':cat,'name':crumb['name'],'parentId':previous,'sourceUrl':crumb['sourceUrl'],'sourceSitemapEntry':False,'inferredFrom':'product_breadcrumb'})
                        previous = cat
            else:
                if not category_id(row['url']):
                    excluded_categories.append({'url':row['url'],'reason':'homepage_in_category_sitemap','key':row['key']})
                    continue
                category = parse_category(source_html, row['url'], fetched_at)
                existing = categories.get(category['id'], {})
                category['parentId'] = category['parentId'] or existing.get('parentId')
                categories[category['id']] = category
        except Exception as exc:
            if row['kind'] == 'product' and isinstance(exc,ValueError) and str(exc) == 'NoProductStructuredData':
                tree = html.fromstring(source_html)
                canonical = tree.xpath('//link[@rel="canonical"]/@href')
                title = tree.xpath('//title/text()')
                if canonical and canonical[0].rstrip('/') != row['url'].rstrip('/'):
                    excluded.append({'url':row['url'],'reason':'source_redirected_to_non_product','canonicalUrl':canonical[0],'pageTitle':title[0] if title else None,'key':row['key']})
                    continue
            errors.append({'url':row['url'],'kind':row['kind'],'key':row['key'],'errorType':type(exc).__name__,'errorCode':str(exc) if isinstance(exc,ValueError) else 'ParseFailed'})
    now = datetime.now(timezone.utc).isoformat()
    collections = []
    for filename, kind in [('model-sitemap.xml','model'),('combination-sitemap.xml','configurator'),('combination_category-sitemap.xml','configurator_collection')]:
        sitemap = BASE/filename
        if sitemap.exists():
            for item in ET.fromstring(sitemap.read_bytes()).findall('s:url',NS):
                url = item.findtext('s:loc',namespaces=NS)
                collections.append({'id':category_id(url),'sourceUrl':url,'kind':kind,'lastmod':item.findtext('s:lastmod',namespaces=NS),'status':'source_url_discovered_not_implemented'})
    for row in urls:
        if row['kind'] == 'category':
            cat=category_id(row['url'])
            if not cat:
                continue
            if cat not in categories:
                # Preserve every sitemap category even while its title is not fetched.
                categories[cat]={'id':cat,'name':None,'parentId':None,'sourceUrl':row['url'],'sourceSitemapEntry':True,'status':'pending_source_fetch'}
    product_lookup = {p['id']:p for p in products}
    secondary_memberships = 0
    category_unresolved_ids = []
    for category in categories.values():
        for product_id in category.get('listedProductIds',[]):
            product = product_lookup.get(product_id)
            if not product:
                product_ref=next((p for p in category.get('listedProducts',[]) if p['id']==product_id),{})
                category_unresolved_ids.append({'categoryId':category['id'],'productId':product_id,'sourceUrl':product_ref.get('sourceUrl')})
                continue
            product.setdefault('categoryMembershipEvidence',[]).append({'categoryId':category['id'],'sourceUrl':category['sourceUrl'],'source':'initial_category_listing'})
            if category['id'] not in product['categoryIds']:
                product['categoryIds'].append(category['id'])
                secondary_memberships += 1
    meta={'source':'https://www.adoremobilya.com','generatedAt':now,'sourceLanguage':'tr','expectedProductUrls':sum(r['kind']=='product' for r in urls),
          'expectedCategoryUrls':sum(r['kind']=='category' for r in urls),'productCount':len(products),'categoryCount':len(categories),'pendingCount':len(pending),
          'additionalBreadcrumbCategoryCount':sum(not c.get('sourceSitemapEntry') for c in categories.values()),
          'excludedSourceCategoryUrlCount':len(excluded_categories),
          'secondaryCategoryMembershipsAdded':secondary_memberships,'secondaryCategoryMembershipComplete':False,
          'secondaryCategoryMembershipScope':'Product breadcrumbs plus visible cards on the initial public category pages. Pagination and dynamically loaded category pages were not crawled.',
          'parseErrorCount':len(errors),'excludedSourceProductUrlCount':len(excluded),'duplicateProductIds':duplicate_ids,'duplicateCodes':duplicate_codes,'complete':not pending and not errors,
          'prices':'retailPrice is a source reference only; salePrice is deliberately null until the merchant supplies approved NODENO prices.',
          'availability':'Source stock is not a supplier stock feed or a NODENO availability promise.',
          'completenessScope':'Public product/category sitemap ingestion only; redirected/retired entries and missing source fields are reported. Model URLs are discovered references; authenticated dealer feed and configurators are not implemented.',
          'mediaStorage':'Source URLs only. Google Drive transfer has not been performed by this importer.'}
    dump(ROOT/'data'/'catalog-source.json',{'products':products,'categories':list(categories.values()),'collections':collections,'meta':meta})
    labels=Counter(spec['label'] for product in products for spec in product['specs'])
    hosts=Counter(urlparse(image).hostname for product in products for image in product['images'])
    corpus={'generatedAt':now,'sourceLanguage':'tr','categories':list(dict.fromkeys(c['name'] for c in categories.values() if c.get('name'))),
            'titles':list(dict.fromkeys(p['title'] for p in products)),
            'descriptions':list(dict.fromkeys(p['description'] for p in products if p['description'])),
            'fullDescriptions':list(dict.fromkeys(p['fullDescription'] for p in products if p['fullDescription'])),
            'specLabels':dict(labels),'specValues':list(dict.fromkeys(s['value'] for p in products for s in p['specs']))}
    dump(BASE/'translation-corpus.json',corpus)
    report={**meta,'imageReferenceCount':sum(len(p['images']) for p in products),'uniqueImageCount':len(set(im for p in products for im in p['images'])),
            'imageHosts':dict(hosts),'missingDescriptions':[p['id'] for p in products if not p['description']],
            'missingTechnicalSpecs':[p['id'] for p in products if not p['specs']],'pendingUrls':pending,'parseErrors':errors,'excludedSourceProductUrls':excluded,
            'categoryListingUnresolvedProductIds':category_unresolved_ids,
            'excludedSourceCategoryUrls':excluded_categories,
            'categorySourceRedirects':[{'id':c['id'],'sourceUrl':c['sourceUrl'],'canonicalSourceUrl':c.get('canonicalSourceUrl')} for c in categories.values() if c.get('canonicalSourceUrl') and c['sourceUrl'].rstrip('/') != c['canonicalSourceUrl'].rstrip('/')],
            'categoryPaginationUrlsDiscovered':list(dict.fromkeys(u for c in categories.values() for u in c.get('paginationUrlsDiscovered',[])))}
    dump(BASE/'report.json',report)
    print(json.dumps({key:report[key] for key in ['productCount','categoryCount','pendingCount','parseErrorCount','imageReferenceCount','imageHosts','complete']},ensure_ascii=False))
    return report


if __name__ == '__main__':
    normalize()
