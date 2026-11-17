#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/native_marketplace_review_rules.py
# Açıklama   : Açık inceleme kararlarını değişmez kaynak kimliği, gerçek fiyat ve sınırlı olgusal metinle uygular.
"""Pure review projection; no filesystem, network, publication or country approval writes.

apply_review returns independent (product, work) dictionaries. Decisions accept only
literal True for copyApproved + identityConfirmed, and winnerOnlyApproved. Audit
identity and rawSha256 (or retained priceWinnerEvidence.sha256) are mandatory before
any approval can resolve a hold. Unresolved regulatory and youth cases remain held.
"""
import copy
import hashlib
import html
import json
import re
import unicodedata
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from urllib.parse import urlsplit


# These are explicitly audited adult-toy identities, not reusable copy templates.
COPY_RULES = {
    'sg_ty_44eb1cfc9cb6d577': ('1100540830', 'KissersSubat01', '5095',
        'Maximizer Pro Şarjlı Vakum Pompası', 'Şarjlı çalışma tipine sahip Maximizer Pro vakum pompası.'),
    'sg_ty_e906b5fc3d975492': ('104712729', 'KokteylPUMP2', '5095',
        'Manuel Vakum Penis Pompası', 'Manuel çalışma tipine sahip vakum penis pompası.'),
    'sg_ty_8e26676397e967e7': ('104777973', 'KokteylFWM1', '5097',
        'Şarjlı Titreşimli Vibratör', 'Şarjlı çalışma tipine sahip titreşimli vibratör.'),
    'sg_ty_8bcf3fdcd618862f': ('105273239', '13-PR-SET', '5094',
        '3’lü Penis Halkası Seti', 'Üç parçalı penis halkası seti. Manuel çalışma tipine sahiptir.'),
    'sg_ty_1d8a1ce255e78f5e': ('1079403226', 'KissOcak01', '5242',
        'Dokulu Testis Bölümlü Penis Kılıfı', 'Dokulu dış yüzeyi ve testis bölümü bulunan penis kılıfı.'),
    'sg_ty_9a2e84b5b0a338ee': ('1148167152', 'lrsgg1', '5235',
        'Giyilebilir İkili Yapay Göğüs', 'İkili, giyilebilir yapay göğüs.'),
    'sg_ty_a9e0e77624175120': ('1150760707', 'dr.jam3lühalka', '5094',
        '3’lü Penis Halkası Seti', 'Üç parçalı penis halkası seti. Manuel çalışma tipine sahiptir.'),
    'sg_ty_a9a2529d6231f16e': ('1177752334', 'g6', '5094',
        '3’lü Penis Halkası Seti', 'Üç parçalı penis halkası seti.'),
    'sg_ty_b23610f00f84eda3': ('1222992940', 'PNTR-0150', '5242',
        'Şeffaf Penis Kılıfı', 'Şeffaf tasarımlı penis kılıfı.'),
    'sg_ty_a783ea231ced9469': ('135494589', 'LS1395-3', '5094',
        '3’lü Penis Halkası Seti', 'Üç parçalı penis halkası seti. Manuel çalışma tipine sahiptir.'),
    'sg_ty_24436799b954bffc': ('232965916', 'LS2114', '5094',
        'Pilli Titreşimli Penis Halkası', 'Pilli çalışma tipine sahip titreşimli penis halkası.'),
    'sg_ty_1f2716d310ae2655': ('809523577', 'MONAMİ005', '5242',
        'MONAMİ005 Penis Kılıfı', 'MONAMİ005 kodlu penis kılıfı.'),
    'sg_ty_61f8d3a0eb617b1e': ('819022218', '4002448192060', '5097',
        'USB Şarjlı Titreşimli Uyarıcı', 'USB şarjlı çalışma tipine sahip titreşimli uyarıcı.'),
    'sg_ty_5f1fb17c73381c94': ('837848932', '357542742575637', '5097',
        'Dil Biçimli Titreşimli Vibratör', 'Dil biçimli titreşimli vibratör.'),
    'sg_ty_8704d93dbaf6ea9e': ('897633705', 'LS1645-5', '5095',
        'USB Şarjlı Vakum Penis Pompası', 'USB şarjlı çalışma tipine sahip vakum penis pompası.'),
}
TEXT_FIELDS = ('name', 'modelName', 'description', 'seoTitle', 'seoDescription')
YOUTH_SIZE = re.compile(r'\b\d+\s*[-–/]?\s*\d*\s*(?:ay|yas|month|year)\b')
CLAIMS = re.compile(
    r'\b(?:medikal|medical|tedavi|treatment|klinik|clinical|antialerjik|hipoalerjenik|'
    r'hypoallergenic|waterproof|buyut\w*|kalinlastir\w*|dikles\w*|geciktir\w*|ereksiyon)\b|'
    r'su gecirmez|suya dayanikli|iliskiyi uzat|sure(?:yi)? uzat|erken (?:bosalma|onleyici)')
REGULATED_GOODS = re.compile(
    r'\b(?:hap|tablet\w*|kapsul\w*|ilac\w*|viagra|cialis|lidokain|lidocaine|'
    r'benzokain|benzocaine|anestezik|anesthetic|anaesthetic|tedavi\w*|treatment|'
    r'tibbi cihaz|medical device)\b')


def _fold(value):
    text = unicodedata.normalize('NFKD', str(value).casefold().replace('ı', 'i'))
    return ''.join(c for c in text if not unicodedata.combining(c))


def _text(value):
    return re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]*>', ' ', str(value or '')))).strip()


def _strings(value):
    if isinstance(value, dict):
        return ' '.join(_strings(v) for v in value.values())
    if isinstance(value, list):
        return ' '.join(_strings(v) for v in value)
    return str(value or '')


def _claims(value):
    # Punctuation in source words does not make a health/performance promise factual.
    normalized = re.sub(r'(?<=\w)\.{2,}(?=\w)', '', _fold(_strings(value)))
    return bool(CLAIMS.search(normalized))


def _hold(product, work, reason):
    work['reviewHolds'] = sorted(set(work.get('reviewHolds', [])) | {reason})
    product['eligibilityHold'] = work['eligibilityHold'] = True


def _minor(value):
    if isinstance(value, bool):
        raise ValueError('REVIEW_PRICE_INVALID')
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number <= 0:
            raise ValueError('REVIEW_PRICE_INVALID')
        result = int((number * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
        if result > 10000000000:
            raise ValueError('REVIEW_PRICE_INVALID')
        return result
    except (InvalidOperation, TypeError, OverflowError):
        raise ValueError('REVIEW_PRICE_INVALID') from None


def _shared_props(raw):
    try:
        document = raw.decode('utf8')
        marker = re.search(r'''window\[\s*["']__envoy__SHARED_PROPS["']\s*\]\s*=\s*''', document)
        if not marker:
            raise ValueError('REVIEW_RAW_JSON_INVALID')
        result = json.JSONDecoder().raw_decode(document[marker.end():])[0]['product']
        if not isinstance(result, dict):
            raise ValueError('REVIEW_RAW_JSON_INVALID')
        return result
    except (UnicodeError, KeyError, TypeError, json.JSONDecodeError):
        raise ValueError('REVIEW_RAW_JSON_INVALID') from None


def _validate(product, work, detail, raw_html, audit):
    raw = raw_html.encode('utf8') if isinstance(raw_html, str) else raw_html
    if not isinstance(raw, bytes) or len(raw) > 10000000 or not isinstance(audit, dict):
        raise ValueError('REVIEW_RAW_HASH_INVALID')
    digest = hashlib.sha256(raw).hexdigest()
    recorded_hash = audit.get('rawSha256') or (audit.get('priceWinnerEvidence') or {}).get('sha256')
    hashes = [recorded_hash, detail.get('sourceSha256'), (work.get('source') or {}).get('htmlSha256')]
    if any(value != digest for value in hashes):
        raise ValueError('REVIEW_RAW_HASH_MISMATCH')
    shared = _shared_props(raw)
    identifier = str(shared.get('id') or '')
    expected_ids = [detail.get('sourceId')]
    expected_ids += [audit[key] for key in ('rawSourceId', 'sourceId') if key in audit]
    if len(expected_ids) < 2 or not identifier or any(str(value) != identifier for value in expected_ids):
        raise ValueError('REVIEW_SOURCE_ID_MISMATCH')
    if work.get('rawSourceId') is not None and str(work['rawSourceId']) != identifier:
        raise ValueError('REVIEW_SOURCE_ID_MISMATCH')
    if product.get('id') != work.get('id') or audit.get('id') != product.get('id'):
        raise ValueError('REVIEW_PRODUCT_ID_MISMATCH')
    code = _text(shared.get('productCode'))
    expected_codes = [detail.get('sourceCode'), audit.get('sourceCode'), work.get('source', {}).get('sourceSku')]
    if not code or any(value != code for value in expected_codes):
        raise ValueError('REVIEW_SOURCE_CODE_MISMATCH')
    if any(value != 'seo-' + code for value in [product.get('sku'), product.get('code'), work.get('sku')]):
        raise ValueError('REVIEW_SOURCE_CODE_MISMATCH')
    source_url = detail.get('sourceUrl')
    if not isinstance(source_url, str):
        raise ValueError('REVIEW_SOURCE_ID_MISMATCH')
    url = urlsplit(source_url)
    if url.scheme != 'https' or url.hostname != 'www.trendyol.com' or not url.path.endswith('-p-' + identifier):
        raise ValueError('REVIEW_SOURCE_ID_MISMATCH')
    if work.get('source', {}).get('url') != source_url or audit.get('sourceUrl', source_url) != source_url:
        raise ValueError('REVIEW_SOURCE_ID_MISMATCH')
    title = _text(shared.get('name'))
    if detail.get('title') != title or audit.get('sourceTitle', title) != title:
        raise ValueError('REVIEW_SOURCE_TITLE_MISMATCH')
    winner = (shared.get('merchantListing') or {}).get('winnerVariant') or {}
    price = winner.get('price') or {}
    regular = _minor((price.get('sellingPrice') or {}).get('value'))
    final = (regular * 115 + 50) // 100
    if price.get('currency') != 'TRY' or detail.get('currency') != 'TRY' or product.get('currency') != 'TRY':
        raise ValueError('REVIEW_PRICE_CURRENCY_MISMATCH')
    for value, expected in [(detail.get('undiscountedPriceMinor'), regular),
                            (detail.get('salePriceMinor'), final), (product.get('salePriceMinor'), final),
                            (work.get('source', {}).get('retailPriceMinor'), regular)]:
        if type(value) is not int or value != expected:
            raise ValueError('REVIEW_SOURCE_PRICE_MISMATCH')
    if product.get('privateRetailReference', regular) != regular:
        raise ValueError('REVIEW_SOURCE_PRICE_MISMATCH')
    return shared, winner, regular, final


def _archive(product, work, detail):
    work.setdefault('sourceReviewOriginal', copy.deepcopy({
        'publicText': {key: product.get(key) for key in (*TEXT_FIELDS, 'slug')},
        'publicFacts': product.get('facts'), 'publicAttributes': product.get('attributes'),
        'facts': work.get('facts'), 'sourceAttributes': work.get('sourceAttributes'),
        'sourceDescription': work.get('sourceDescription'), 'sourceVariants': work.get('sourceVariants'),
    }))
    work.setdefault('rawSourceTitle', detail['title'])
    work.setdefault('rawSourceDescription', detail.get('sourceDescription'))
    work.setdefault('rawSourceAttributes', copy.deepcopy(detail.get('attributes', [])))
    work.setdefault('rawSourceVariants', copy.deepcopy(detail.get('variants', [])))
    work.setdefault('rawSourceId', detail['sourceId'])


def _neutral_copy(product, work, detail, shared):
    rule = COPY_RULES.get(product['id'])
    if not rule:
        return False
    source_id, code, category, title, summary = rule
    if source_id != str(detail['sourceId']) or code != detail['sourceCode']:
        raise ValueError('REVIEW_COPY_ID_MISMATCH')
    if any(str(value.get('id')) != category for value in [detail.get('category') or {}, shared.get('category') or {}]):
        return False
    if product.get('productType') != 'adult-product':
        return False
    _archive(product, work, detail)
    work['rawSourceClaims'] = {'title': detail['title'], 'description': detail.get('sourceDescription'),
                               'attributes': copy.deepcopy(detail.get('attributes', []))}
    cleared_facts = set()
    for container in (product.get('facts', {}), work.get('facts', {})):
        for key, value in list(container.items()):
            if _claims(value):
                container[key] = None
                cleared_facts.add(key)
    if cleared_facts:
        work['missingFields'] = sorted(set(work.get('missingFields', [])) | cleared_facts)
    product['attributes'] = [v for v in product.get('attributes', []) if not _claims(v)]
    work['sourceAttributes'] = [v for v in work.get('sourceAttributes', []) if not _claims(v)]
    for field in ('name', 'modelName', 'seoTitle'):
        product.setdefault(field, {})['tr'] = title
    description = summary + ' Ürün kodu: ' + product['sku'] + '.'
    product.setdefault('description', {})['tr'] = description
    product.setdefault('seoDescription', {})['tr'] = description[:165]
    for field in TEXT_FIELDS:
        for language, value in product.get(field, {}).items():
            if language != 'tr' and _claims(value):
                cleaned = value.replace(detail['title'], title)
                cleaned = cleaned.replace(detail.get('sourceDescription') or '\x00', summary)
                product[field][language] = cleaned if not _claims(cleaned) else ' '.join(
                    value for value in [product.get('brand'), detail['sourceCode']] if value)
    product['slug'] = re.sub('[^a-z0-9]+', '-', _fold(title)).strip('-') + '-' + product['id'][-8:]
    work['sourceDescription'] = summary
    work['copyReviewApplied'] = {'identityConfirmed': True, 'copyApproved': True,
                                 'rule': 'audited-adult-toy-neutral-copy-v1'}
    work['reviewHolds'] = [flag for flag in work.get('reviewHolds', [])
                          if flag not in ('manufacturer_claim_review', 'description')]
    return True


def _winner_only(product, work, detail, shared, winner, regular, final):
    item = str(winner.get('itemNumber') or '')
    source_variants = {str(v.get('itemNumber')): v for v in shared.get('variants', [])}
    detail_variants = {str(v.get('sourceVariantId')): v for v in detail.get('variants', [])}
    selected = source_variants.get(item)
    observed = detail_variants.get(item)
    if not selected or not observed or winner.get('inStock') is not True or winner.get('sellable') is not True:
        raise ValueError('REVIEW_WINNER_ID_MISMATCH')
    size = _text(selected.get('value'))
    if not size or selected.get('inStock') is not True or selected.get('isSelected') is not True:
        raise ValueError('REVIEW_WINNER_ID_MISMATCH')
    if observed.get('sourceInStock') is not True or observed.get('size') != size:
        raise ValueError('REVIEW_WINNER_ID_MISMATCH')
    attributes = winner.get('variantAttributes') or []
    if not any(v.get('attributeName') == 'Beden' and v.get('attributeValue') == size for v in attributes):
        raise ValueError('REVIEW_WINNER_ID_MISMATCH')
    unfiltered = work.get('sourceVariantsUnfiltered', work.get('sourceVariants', []))
    offered = [v for v in unfiltered if str(v.get('id')) == item]
    if len(offered) != 1 or offered[0].get('isActive') is not True:
        raise ValueError('REVIEW_WINNER_ID_MISMATCH')
    if not any(v.get('name') == 'Beden' and v.get('value') == size for v in offered[0].get('attributes', [])):
        raise ValueError('REVIEW_WINNER_ID_MISMATCH')
    _archive(product, work, detail)
    previous_sizes = (product.get('facts') or {}).get('sizeOptions')
    work['sourceVariantsUnfiltered'] = copy.deepcopy(unfiltered)
    work['sourceVariants'] = copy.deepcopy(offered)
    work['withheldVariantReasons'] = [
        {'id': str(v.get('id')), 'reason': 'regular_price_not_independently_verified'
         if v.get('isActive') else 'source_unavailable'}
        for v in unfiltered if str(v.get('id')) != item]
    for target in (product, work):
        target.setdefault('facts', {})['sizeOptions'] = size
    for attribute in product.get('attributes', []):
        if _fold((attribute.get('name') or {}).get('tr', '')) in ('beden', 'beden secenekleri'):
            attribute['value'] = {lang: size for lang in attribute.get('value', {})}
    if previous_sizes:
        for field in ('description', 'seoDescription'):
            for language, value in product.get(field, {}).items():
                product[field][language] = value.replace(previous_sizes, size)
    work['winnerPriceReview'] = {'itemNumber': item, 'size': size, 'regularPriceMinor': regular,
        'salePriceMinor': final, 'evidence': 'merchantListing.winnerVariant.price.sellingPrice.value',
        'currentVariantPricesAreNotRegularPrices': True}
    work['reviewHolds'] = [v for v in work.get('reviewHolds', []) if v != 'variant_price_review']


def apply_review(product, work, source_detail, raw_html, decision, audit_entry):
    """Apply only explicitly approved, source-bound projections and return deep copies."""
    p, w = copy.deepcopy(product), copy.deepcopy(work)
    detail, decision = source_detail, decision or {}
    sizes = [v.get('size', '') for v in detail.get('variants', [])]
    if detail.get('sourceCode') == 'AJM9106' or any(YOUTH_SIZE.search(_fold(size)) for size in sizes):
        _hold(p, w, 'inconsistent_youth_size_source')
        return p, w
    regulated_text = ' '.join(_strings(detail.get(key)) for key in
                              ('title', 'category', 'attributes', 'ingredients', 'sourceDescription'))
    if REGULATED_GOODS.search(_fold(regulated_text)):
        _hold(p, w, 'regulatory_review_required')
        return p, w
    approve_copy = decision.get('copyApproved') is True and decision.get('identityConfirmed') is True
    approve_winner = decision.get('winnerOnlyApproved') is True
    if not approve_copy and not approve_winner:
        if _claims(detail.get('title')):
            _hold(p, w, 'manufacturer_claim_review')
        return p, w
    shared, winner, regular, final = _validate(p, w, detail, raw_html, audit_entry)
    raw_regulated = ' '.join(_strings(shared.get(key)) for key in ('name', 'category', 'attributes'))
    if REGULATED_GOODS.search(_fold(raw_regulated)):
        _hold(p, w, 'regulatory_review_required')
        return p, w
    changed = False
    if approve_copy:
        changed = _neutral_copy(p, w, detail, shared)
        if not changed:
            _hold(p, w, 'manufacturer_claim_review')
    if approve_winner:
        _winner_only(p, w, detail, shared, winner, regular, final)
        changed = True
    if _claims(detail.get('title')) and not w.get('copyReviewApplied'):
        _hold(p, w, 'manufacturer_claim_review')
    if changed:
        p['eligibilityHold'] = w['eligibilityHold'] = bool(w.get('reviewHolds'))
    return p, w
