"""Exact product/merchant/variant matching for public Trendyol paint listings."""
import json
import re
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import urlsplit, parse_qs, urljoin, urlencode, urlunsplit
from lxml import html


def product_id(url):
    p = urlsplit(url)
    m = re.search(r'-p-(\d+)$', p.path)
    if p.scheme != 'https' or p.hostname != 'www.trendyol.com' or p.username or p.password or p.port or not m:
        raise ValueError('untrusted_product_url')
    return m[1]


def source_redirect(original, current, location):
    target = urljoin(current, location)
    if product_id(target) != product_id(original):
        raise ValueError('redirect_product_changed')
    a, b = urlsplit(original), urlsplit(target)
    expected = parse_qs(a.query).get('merchantId', [])
    actual = parse_qs(b.query).get('merchantId', [])
    if actual and expected and actual != expected:
        raise ValueError('redirect_merchant_changed')
    if expected and not actual:
        query = parse_qs(b.query); query['merchantId'] = expected
        target = urlunsplit((b.scheme,b.netloc,b.path,urlencode(query,doseq=True),''))
    return target


def package_value(value):
    matches = re.findall(r'(?<![\d.])(\d+(?:[.,]\d+)?)\s*(ml|lt|litre|l|kg|gr|g)(?![a-z])', str(value).casefold())
    out = set()
    for number, unit in matches:
        number = Decimal(number.replace(',', '.'))
        kind = 'volume' if unit in ['ml','lt','litre','l'] else 'mass'
        scale = 1 if unit in ['ml','gr','g'] else 1000
        out.add((kind, number*scale))
    return out


def offer_review(row):
    title = row['title'].casefold()
    if re.search(r'\bset\b|seti|knitex|ile birlikte|ve dekor|\+', title) and row['sourceProductId'] != '789206022':
        return 'bundle_contents_require_review'
    selected = package_value(row.get('package',''))
    listed = package_value(title)
    if selected and listed and selected.isdisjoint(listed):
        return 'title_and_selected_package_conflict'
    if not selected and row.get('family') not in ['tools','afilli-tools']:
        return 'package_size_missing'
    if row.get('family') == 'diamond' and selected != {('mass', Decimal(600))}:
        return 'manufacturer_600g_and_marketplace_600ml_need_package_confirmation'
    for colour in ['siyah','beyaz']:
        if re.search(r'\b'+colour+r'\b',title) and colour not in row.get('color','').casefold():
            return 'title_and_selected_colour_conflict'
    return None


def states(body):
    result = {}
    for s in html.fromstring(body, parser=html.HTMLParser()).xpath('//script'):
        m = re.match(r'window\["(__envoy[^\"]+)"\]=', s.text or '')
        if m:
            result[m[1]] = json.JSONDecoder().raw_decode(s.text[m.end():])[0]
    return result


def minor(value):
    s = str(value)
    if not re.fullmatch(r'\d{1,7}(?:\.\d{1,2})?', s) or Decimal(s) <= 0:
        raise ValueError('invalid_price')
    return int(Decimal(s) * 100)


def markup(value):
    if type(value) is not int or value <= 0:
        raise ValueError('invalid_minor_price')
    return (value * 130 + 50) // 100


def authorized(merchant):
    return any('yetkilisatici' in b.get('webImageUrl', '').lower() for b in merchant.get('merchantBadges', []))


def parse(body, url, merchant_id=None):
    expected = product_id(url)
    st = states(body)
    p = st.get('__envoy__SHARED_PROPS', {}).get('product', {})
    if str(p.get('id')) != expected:
        raise ValueError('product_identity_changed')
    listing = p.get('merchantListing', {})
    merchant = listing.get('merchant', {})
    if merchant_id is not None and str(merchant.get('id')) != str(merchant_id):
        raise ValueError('merchant_identity_changed')
    selected = [v for v in p.get('variants', []) if v.get('isSelected')]
    if len(selected) != 1:
        raise ValueError('ambiguous_selected_variant')
    variant = listing.get('winnerVariant', {})
    if variant.get('itemNumber') != selected[0].get('itemNumber'):
        raise ValueError('variant_identity_changed')
    price = variant.get('price', {})
    if price.get('currency') != 'TRY':
        raise ValueError('unexpected_currency')
    value = minor(price.get('sellingPrice', {}).get('value'))
    if not variant.get('inStock') or not variant.get('sellable'):
        raise ValueError('source_out_of_stock')
    color = p.get('slicingAttributes', {}).get('DsmColor', '')
    package = selected[0].get('value', '')
    merchant_safe = {'id': merchant.get('id'), 'name': merchant.get('name'), 'score': merchant.get('sellerScore', {}).get('value'), 'authorized': authorized(merchant)}
    alternatives = [{'id': x.get('id'), 'name': x.get('name'), 'score': x.get('sellerScore', {}).get('value'), 'authorized': authorized(x)} for x in listing.get('otherMerchants', [])]
    group = next((json.loads(s.text) for s in html.fromstring(body, parser=html.HTMLParser()).xpath('//script[@type="application/ld+json"]') if json.loads(s.text).get('@type') == 'ProductGroup'), {})
    choices = [x.get('offers', {}).get('url') for x in group.get('hasVariant', [])]
    description = st.get('__envoy_product-description__PROPS', {}).get('htmlContentData')
    return {'sourceProductId': expected, 'sourceCode': str(p.get('productCode', '')), 'brand': p.get('brand', {}).get('name'), 'title': p.get('name'),
            'color': color, 'package': package, 'selectedSize': package, 'itemNumber': str(variant.get('itemNumber')), 'barcode': variant.get('barcode'),
            'sourcePriceMinor': value, 'salePriceMinor': markup(value), 'merchant': merchant_safe, 'alternatives': alternatives,
            'images': p.get('images', []), 'attributes': [{'label': a['key']['name'], 'value': a['value']['name']} for a in p.get('attributes', [])],
            'variantUrls': [u for u in choices if u], 'descriptionData': description,
            'priceBasis': 'merchant_variant_sellingPrice_TRY_excluding_personal_coupon_plus_and_cart_promotions'}


def best_merchant(row):
    candidates = [row['merchant']] + row['alternatives']
    candidates = [m for m in candidates if m['authorized'] and isinstance(m['score'], (int, float)) and m['score'] >= 9.0]
    if not candidates:
        raise ValueError('qualified_merchant_not_verified')
    return sorted(candidates, key=lambda m: (-m['score'], m['id']))[0]
