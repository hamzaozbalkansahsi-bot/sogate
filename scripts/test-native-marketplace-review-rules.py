#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-marketplace-review-rules.py
# Açıklama   : İnceleme kararlarında kaynak kimliği, fiyat, iddia ve yetişkin beden güvenliğini doğrular.
import copy
import hashlib
import json
import sqlite3
import unittest
from pathlib import Path

from native_marketplace_review_rules import apply_review


def fixture():
    shared = {
        'id': 104712729, 'productCode': 'KokteylPUMP2',
        'name': 'Büyütücü Vakum Penis Pompası',
        'brand': {'name': 'Kokteyl'}, 'category': {'id': 5095, 'name': 'Penis Pompası'},
        'attributes': [], 'variants': [],
        'merchantListing': {'winnerVariant': {'itemNumber': 99, 'inStock': True,
            'sellable': True, 'price': {'currency': 'TRY',
                'sellingPrice': {'value': 400}, 'discountedPrice': {'value': 350}}}},
    }
    raw = ('<script>window["__envoy__SHARED_PROPS"]=' +
           json.dumps({'product': shared}, ensure_ascii=False) + ';</script>').encode('utf8')
    sha = hashlib.sha256(raw).hexdigest()
    url = 'https://www.trendyol.com/kokteyl/buyutucu-vakum-penis-pompasi-p-104712729?boutiqueId=61&merchantId=1343431'
    source = {'sourceId': '104712729', 'sourceCode': 'KokteylPUMP2', 'sourceUrl': url,
        'sourceSha256': sha, 'title': shared['name'], 'brand': 'Kokteyl',
        'sourceDescription': 'Büyütücü pompa, medikal silikon, su geçirmez.',
        'category': shared['category'], 'categoryTree': [shared['category']],
        'attributes': [{'name': 'Çalışma Tipi', 'value': 'Manuel'}], 'variants': [],
        'undiscountedPriceMinor': 40000, 'salePriceMinor': 46000, 'currency': 'TRY'}
    identity = 'sg_ty_e906b5fc3d975492'
    texts = {'tr': source['title'], 'en': 'Kokteyl Adult Toys KokteylPUMP2'}
    p = {'id': identity, 'sku': 'seo-KokteylPUMP2', 'code': 'seo-KokteylPUMP2',
        'brand': 'Kokteyl', 'categoryIds': ['sg_toys', 'sg_toys_pumps'],
        'productType': 'adult-product', 'name': copy.deepcopy(texts),
        'modelName': copy.deepcopy(texts), 'description': copy.deepcopy(texts),
        'seoTitle': copy.deepcopy(texts), 'seoDescription': copy.deepcopy(texts),
        'slug': 'buyutucu-vakum-penis-pompasi-3d975492', 'salePriceMinor': 46000,
        'privateRetailReference': 40000, 'currency': 'TRY', 'published': False,
        'hidden': True, 'eligibilityHold': True, 'stockKnown': False, 'stockQuantity': None,
        'taxTreatment': 'unverified', 'facts': {'materials': 'Medikal silikon',
            'dimensions': '20 cm'}, 'attributes': [
                {'name': {'tr': 'Malzeme'}, 'value': {'tr': 'Medikal silikon'}},
                {'name': {'tr': 'Ölçü'}, 'value': {'tr': '20 cm'}}]}
    w = {'id': identity, 'sku': p['sku'], 'brand': 'Kokteyl',
        'facts': copy.deepcopy(p['facts']), 'sourceDescription': source['sourceDescription'],
        'sourceAttributes': [{'name': 'Malzeme', 'value': 'Medikal silikon'},
            {'name': 'Çalışma Tipi', 'value': 'Manuel'}],
        'sourceVariants': [], 'source': {'url': url, 'sourceSku': 'KokteylPUMP2',
            'htmlSha256': sha, 'retailPriceMinor': 40000},
        'eligibilityHold': True, 'publicationApproved': False,
        'reviewHolds': ['manufacturer_claim_review']}
    audit = {'id': identity, 'sourceId': '104712729', 'sourceCode': 'KokteylPUMP2',
        'sourceUrl': url, 'sourceTitle': source['title'], 'rawSha256': sha}
    return p, w, source, raw, audit


APPROVED = {'copyApproved': True, 'identityConfirmed': True}


class ReviewRulesTest(unittest.TestCase):
    def run_review(self, decision=None, change=None):
        p, w, source, raw, audit = fixture()
        if change:
            change(p, w, source, audit)
        return apply_review(p, w, source, raw, decision or {}, audit)

    def test_no_decision_returns_independent_unchanged_copies(self):
        p, w, source, raw, audit = fixture()
        result = apply_review(p, w, source, raw, {}, audit)
        self.assertEqual(result, (p, w))
        result[0]['facts']['dimensions'] = 'changed'
        self.assertEqual(p['facts']['dimensions'], '20 cm')

    def test_copy_requires_both_explicit_approvals(self):
        for decision in [{'copyApproved': True}, {'identityConfirmed': True},
                         {'copyApproved': 'true', 'identityConfirmed': True}]:
            p, w = self.run_review(decision)
            self.assertTrue(p['eligibilityHold'])
            self.assertIn('Büyütücü', p['name']['tr'])

    def test_approved_copy_updates_all_public_tr_fields_and_keeps_identity(self):
        original, work, source, raw, audit = fixture()
        p, w = apply_review(original, work, source, raw, APPROVED, audit)
        self.assertEqual(p['name']['tr'], 'Manuel Vakum Penis Pompası')
        for field in ['name', 'modelName', 'description', 'seoTitle', 'seoDescription']:
            self.assertNotIn('Büyütücü', p[field]['tr'])
            self.assertIn('penis pompası', p[field]['tr'].lower())
        self.assertNotIn('buyutucu', p['slug'])
        for field in ['id', 'sku', 'code', 'brand', 'categoryIds', 'productType',
                      'published', 'hidden', 'stockKnown', 'stockQuantity', 'taxTreatment']:
            self.assertEqual(p[field], original[field])
        self.assertFalse(p['eligibilityHold'])
        self.assertNotIn('manufacturer_claim_review', w['reviewHolds'])
        self.assertEqual(w['rawSourceTitle'], source['title'])
        self.assertEqual(w['rawSourceDescription'], source['sourceDescription'])
        self.assertEqual(w['sourceReviewOriginal']['sourceAttributes'], work['sourceAttributes'])
        self.assertEqual(work['sourceDescription'], source['sourceDescription'])

    def test_unverified_medical_qualifiers_cannot_leak_through_facts(self):
        p, w = self.run_review(APPROVED)
        self.assertIsNone(p['facts']['materials'])
        self.assertIsNone(w['facts']['materials'])
        self.assertEqual(p['facts']['dimensions'], '20 cm')
        self.assertEqual(len(p['attributes']), 1)
        self.assertEqual(w['sourceAttributes'], [{'name': 'Çalışma Tipi', 'value': 'Manuel'}])
        self.assertNotIn('medikal', w['sourceDescription'].lower())
        self.assertIn('materials', w['missingFields'])

    def test_copy_reapplication_keeps_original_private_evidence(self):
        p, w, source, raw, audit = fixture()
        first = apply_review(p, w, source, raw, APPROVED, audit)
        second = apply_review(*first, source, raw, APPROVED, audit)
        self.assertEqual(first, second)

    def test_foreign_unknown_hold_is_never_cleared(self):
        p, w = self.run_review(APPROVED, lambda p, w, s, a: w['reviewHolds'].append('country_document_required'))
        self.assertTrue(p['eligibilityHold'])
        self.assertEqual(w['reviewHolds'], ['country_document_required'])

    def test_wrong_raw_hash_rejected(self):
        with self.assertRaisesRegex(ValueError, 'REVIEW_.*HASH'):
            self.run_review(APPROVED, lambda p, w, s, a: a.update(rawSha256='0' * 64))

    def test_missing_audit_hash_rejected(self):
        with self.assertRaisesRegex(ValueError, 'REVIEW_.*HASH'):
            self.run_review(APPROVED, lambda p, w, s, a: a.pop('rawSha256'))

    def test_wrong_source_code_rejected(self):
        with self.assertRaisesRegex(ValueError, 'REVIEW_.*CODE'):
            self.run_review(APPROVED, lambda p, w, s, a: a.update(sourceCode='OTHER'))

    def test_wrong_raw_source_id_rejected(self):
        with self.assertRaisesRegex(ValueError, 'REVIEW_.*ID'):
            self.run_review(APPROVED, lambda p, w, s, a: a.update(rawSourceId='777'))

    def test_wrong_source_price_or_markup_rejected(self):
        for change in [lambda p, w, s, a: s.update(undiscountedPriceMinor=35000),
                       lambda p, w, s, a: p.update(salePriceMinor=40250),
                       lambda p, w, s, a: w['source'].update(retailPriceMinor=35000)]:
            with self.assertRaisesRegex(ValueError, 'REVIEW_.*PRICE'):
                self.run_review(APPROVED, change)

    def test_wrong_raw_identity_rejected_even_with_matching_hash(self):
        p, w, source, raw, audit = fixture()
        changed = raw.replace(b'104712729', b'104712728')
        sha = hashlib.sha256(changed).hexdigest()
        source['sourceSha256'] = w['source']['htmlSha256'] = audit['rawSha256'] = sha
        with self.assertRaisesRegex(ValueError, 'REVIEW_.*ID'):
            apply_review(p, w, source, changed, APPROVED, audit)

    def test_unknown_claim_product_remains_held(self):
        p, w, source, raw, audit = fixture()
        p['id'] = w['id'] = audit['id'] = 'sg_ty_unknown'
        p, w = apply_review(p, w, source, raw, APPROVED, audit)
        self.assertTrue(p['eligibilityHold'])
        self.assertIn('Büyütücü', p['name']['tr'])

    def test_source_description_anesthetic_is_never_neutralized(self):
        p, w, source, raw, audit = fixture()
        source['sourceDescription'] = 'İçerik: Lidocaine.'
        p, w = apply_review(p, w, source, raw, APPROVED, audit)
        self.assertTrue(p['eligibilityHold'])
        self.assertIn('regulatory_review_required', w['reviewHolds'])
        self.assertIn('Büyütücü', p['name']['tr'])

    def test_medical_treatment_and_anesthetic_ingredient_are_not_relabelled(self):
        for term in ['Lidokain', 'Benzocaine', 'tedavi tableti']:
            p, w, source, raw, audit = fixture()
            source['attributes'].append({'name': 'İçerik', 'value': term})
            p, w = apply_review(p, w, source, raw, APPROVED, audit)
            self.assertTrue(p['eligibilityHold'])
            self.assertIn('regulatory_review_required', w['reviewHolds'])
            self.assertIn('Büyütücü', p['name']['tr'])

    def test_non_adult_source_category_cannot_use_neutral_copy(self):
        p, w, source, raw, audit = fixture()
        source['category'] = {'id': 999, 'name': 'Tıbbi Cihaz'}
        p, w = apply_review(p, w, source, raw, APPROVED, audit)
        self.assertTrue(p['eligibilityHold'])
        self.assertIn('Büyütücü', p['name']['tr'])

    def test_suspect_youth_option_is_not_silently_deleted(self):
        p, w, source, raw, audit = fixture()
        source['variants'] = [{'sourceVariantId': 'child', 'size': '0-3 AY', 'sourceInStock': True}]
        w['sourceVariants'] = [{'id': 'child', 'isActive': True,
                                'attributes': [{'name': 'Beden', 'value': '0-3 AY'}]}]
        p, result = apply_review(p, w, source, raw, APPROVED, audit)
        self.assertTrue(p['eligibilityHold'])
        self.assertIn('inconsistent_youth_size_source', result['reviewHolds'])
        self.assertEqual(result['sourceVariants'], w['sourceVariants'])


FIRST = Path('D:/sexogate-local-artifacts-20261114/private-installs/marketplace-catalog-20261116')


@unittest.skipUnless((FIRST / 'research.sqlite').is_file(), 'Private retained source fixtures unavailable')
class RetainedWinnerEvidenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.products = {p['id']: p for p in json.loads((FIRST / 'prepared/catalog-data.json').read_text('utf8'))['products']}
        cls.work = {k: v for f in (FIRST / 'prepared/catalog-workbench').glob('*.json')
                    for k, v in json.loads(f.read_text('utf8')).items()}
        with sqlite3.connect((FIRST / 'research.sqlite').resolve().as_uri() + '?mode=ro', uri=True) as db:
            cls.source = {json.loads(row[0])['sourceUrl']: json.loads(row[0]) for row in
                          db.execute("SELECT detail_json FROM products WHERE status='ready'")}

    def review(self, identity):
        p, w = self.products[identity], self.work[identity]
        source = self.source[w['source']['url']]
        raw = (FIRST / 'raw' / (source['sourceId'] + '.html')).read_bytes()
        audit = {'id': identity, 'rawSourceId': source['sourceId'], 'sourceCode': source['sourceCode'],
                 'rawSha256': source['sourceSha256'], 'sourceUrl': source['sourceUrl']}
        return p, w, source, raw, audit

    def test_real_selected_winners_use_their_regular_price_only(self):
        cases = [
            ('sg_ty_3d4c35a63d51cc79', '1684936183', 'L', 199962, 229956),
            ('sg_ty_61e1b476f662cda3', '1739334488', 'S/M', 64900, 74635),
            ('sg_ty_7f865a00a711fe7a', '1710832027', 'S', 75335, 86635),
        ]
        for identity, item, size, regular, final in cases:
            with self.subTest(identity=identity):
                p, w, source, raw, audit = self.review(identity)
                before = copy.deepcopy((p, w))
                result, review = apply_review(p, w, source, raw, {'winnerOnlyApproved': True}, audit)
                self.assertEqual([v['id'] for v in review['sourceVariants']], [item])
                self.assertEqual(review['facts']['sizeOptions'], size)
                self.assertEqual(result['facts']['sizeOptions'], size)
                self.assertEqual(result['salePriceMinor'], final)
                self.assertEqual(review['source']['retailPriceMinor'], regular)
                self.assertEqual(review['sourceVariantsUnfiltered'], w['sourceVariants'])
                self.assertEqual(len(review['withheldVariantReasons']), len(w['sourceVariants']) - 1)
                self.assertNotIn('variant_price_review', review['reviewHolds'])
                self.assertFalse(result['eligibilityHold'])
                self.assertEqual((p, w), before)
                self.assertEqual(result['stockQuantity'], None)
                self.assertFalse(result['published'])
                self.assertEqual((result, review), apply_review(result, review, source, raw,
                    {'winnerOnlyApproved': True}, audit))

    def test_real_ajm9106_whole_product_stays_held(self):
        p, w, source, raw, audit = self.review('sg_ty_15a821e7c51bac79')
        result, review = apply_review(p, w, source, raw,
                                     {'winnerOnlyApproved': True, **APPROVED}, audit)
        self.assertTrue(result['eligibilityHold'])
        self.assertIn('inconsistent_youth_size_source', review['reviewHolds'])
        self.assertEqual(review['sourceVariants'], w['sourceVariants'])
        self.assertTrue(any(v['size'] == '0-3 AY' for v in source['variants']))

    def test_all_fourteen_copy_identities_keep_their_real_category(self):
        from native_marketplace_review_rules import COPY_RULES
        for identity in COPY_RULES:
            with self.subTest(identity=identity):
                p, w, source, raw, audit = self.review(identity)
                audit['sourceTitle'] = source['title']
                result, review = apply_review(p, w, source, raw, APPROVED, audit)
                self.assertEqual(result['name']['tr'], COPY_RULES[identity][3])
                self.assertEqual(result['categoryIds'], p['categoryIds'])
                self.assertEqual(result['brand'], p['brand'])
                self.assertEqual(review['rawSourceTitle'], source['title'])


if __name__ == '__main__':
    unittest.main()
