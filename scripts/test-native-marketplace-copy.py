#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-marketplace-copy.py
# Açıklama   : Pazaryeri reklam cümlesinin olgular ve kullanıcı düzenlemeleri korunarak temizlendiğini sınar.
import copy
import importlib.util
import json
import unittest
import hashlib
from tempfile import TemporaryDirectory
from unittest.mock import patch
from pathlib import Path

from native_marketplace_copy import clean_text, clean_data, has_advertising, plan_copy, apply_copy, protected_data
from native_marketplace_import_guard import fingerprint, normalize_generic_brand

IDENTITY = 'sg_ty_copy_fixture'
CONTEXT = {'base': 'https://sexogate.com/test', 'release': 'e' * 24, 'dataset': 'd' * 32}
CTA = 'Bu ürünün yorumlarını inceleyin, Trendyol’a özel fırsatlarla satın alın!'


def fixture():
    data = {'visible': True, 'sku': 'seo-İÇ-01', 'brand': 'Marka', 'priceMinor': 11500,
        'description_tr': 'Başlangıç anlatımı. Ölçü: 2.6 cm. Ürün kodu: seo-İÇ-01. ' + CTA + ' Malzeme: pamuk.',
        'description_en': 'Original description.', 'title_tr': 'Ürün', 'seoDescription_tr': 'Ürün. Kod: seo-İÇ-01.',
        'imageApprovedIndices': '0', 'coverIndex': 0, 'sizeOptions': 'S, M', 'colorOptions': 'Bordo'}
    return {'id': IDENTITY, 'version': 4, 'publishedVersion': 4, 'data': data}


class FakeApi:
    def __init__(self, record):
        self.record = copy.deepcopy(record)
        self.calls = []
        self.fail_publish = False
        self.concurrent = False

    def __call__(self, path, body=None, method='POST'):
        self.calls.append((path, copy.deepcopy(body), method))
        if body is None:
            if self.concurrent and self.record['version'] == 5:
                self.record['version'] += 1
                self.record['data']['sizeOptions'] = 'XL'
            return {'record': copy.deepcopy(self.record)}
        if body['version'] != self.record['version']:
            raise RuntimeError('API_409')
        if path.endswith('/publish'):
            if self.fail_publish:
                raise RuntimeError('simulated_transport_failure')
            self.record['version'] += 1
            self.record['publishedVersion'] = self.record['version']
        else:
            self.record['version'] += 1
            self.record['data'] = copy.deepcopy(body['data'])
        return {'data': copy.deepcopy(self.record)}


class CopyCleanerTest(unittest.TestCase):
    def test_removes_whole_known_advertising_sentence_only(self):
        value = 'Ürün başlığı. ' + CTA + ' Ölçü: 2.6 cm. Fiyat: 1.150,00 TL.'
        cleaned, removed = clean_text(value)
        self.assertEqual(cleaned, 'Ürün başlığı. Ölçü: 2.6 cm. Fiyat: 1.150,00 TL.')
        self.assertEqual(removed, [CTA])

    def test_newlines_and_turkish_uppercase(self):
        cleaned, removed = clean_text('Hamza ÖZBALKAN\nTRENDYOL İÇİN YORUMLARINI İNCELEYİN!\nİstanbul, Iğdır, Şişli.')
        self.assertEqual(cleaned, 'Hamza ÖZBALKAN\nİstanbul, Iğdır, Şişli.')
        self.assertEqual(len(removed), 1)

    def test_nonmatching_platform_mentions_and_cta_are_unchanged(self):
        for value in ['Kaynak: Trendyol. Ölçü: 2.6 cm.', 'Ürün yorumlarını inceleyin.',
                      'Trendyol ürün bilgisi. Ayrı satırda satın alın.', 'Elle yazılan not.']:
            self.assertEqual(clean_text(value), (value, []))

    def test_description_and_only_matching_seo_are_cleaned(self):
        data = fixture()['data']
        data['seoDescription_tr'] += ' ' + CTA
        original = copy.deepcopy(data)
        cleaned, fields, removed = clean_data(data)
        self.assertEqual(set(fields), {'description_tr', 'seoDescription_tr'})
        self.assertEqual(data, original)
        self.assertEqual(fingerprint(protected_data(cleaned, fields)), fingerprint(protected_data(data, fields)))
        self.assertEqual(cleaned['priceMinor'], 11500)
        self.assertEqual(len(removed), 2)

    def test_other_language_and_unapproved_fields_are_not_changed(self):
        data = fixture()['data']
        data['description_en'] = CTA
        data['title_tr'] = CTA
        cleaned, fields, removed = clean_data(data)
        self.assertEqual(cleaned['description_en'], CTA)
        self.assertEqual(cleaned['title_tr'], CTA)
        self.assertEqual(fields, ['description_tr'])


class CopyGuardTest(unittest.TestCase):
    def plan(self, record=None, journal=None, context=None):
        original = fixture()
        return plan_copy(record or original, [original['data']], {IDENTITY},
                         context or CONTEXT, journal or {})

    def test_exact_public_baseline_can_be_cleaned(self):
        plan = self.plan()
        self.assertEqual(plan['action'], 'update')
        self.assertEqual(plan['changedFields'], ['description_tr'])

    def test_normalized_generic_brand_is_a_known_baseline(self):
        record = fixture()
        record['data']['brand'] = 'Genel Markalar'
        record['data']['title_en'] = 'Genel Markalar Adult Toys'
        current = copy.deepcopy(record)
        current['data'] = normalize_generic_brand(current['data'])
        self.assertEqual(plan_copy(current, [record['data']], {IDENTITY}, CONTEXT, {})['action'], 'update')

    def test_any_manual_field_change_with_cta_is_preserved(self):
        for key, value in [('priceMinor', 13000), ('sizeOptions', 'XL'), ('description_tr', 'Elle not. ' + CTA)]:
            record = fixture()
            record['data'][key] = value
            self.assertEqual(self.plan(record)['action'], 'skip')

    def test_hidden_or_concurrent_public_draft_never_published(self):
        record = fixture()
        record['version'] += 1
        self.assertEqual(self.plan(record)['action'], 'skip')
        original = fixture()
        self.assertEqual(plan_copy(original, [original['data']], set(), CONTEXT, {})['action'], 'skip')
        original['publishedVersion'] = 0
        self.assertEqual(self.plan(original)['action'], 'skip')

    def test_nonmatching_manual_text_has_no_write(self):
        record = fixture()
        record['data']['description_tr'] = 'Kullanıcının özgün ve korunacak metni.'
        self.assertEqual(self.plan(record)['action'], 'no_change')

    def test_save_publish_uses_versions_and_repeat_has_no_mutation(self):
        record = fixture()
        api, journal = FakeApi(record), {}
        result = apply_copy(api, record, [record['data']], {IDENTITY}, CONTEXT, journal, lambda: None)
        self.assertEqual(result['action'], 'updated')
        mutations = [call for call in api.calls if call[1] is not None]
        self.assertEqual([call[1]['version'] for call in mutations], [4, 5])
        self.assertEqual(api.record['version'], 6)
        self.assertEqual(api.record['publishedVersion'], 6)
        self.assertEqual(journal[IDENTITY]['phase'], 'published')
        second = apply_copy(api, api.record, [record['data']], {IDENTITY}, CONTEXT, journal, lambda: None)
        self.assertEqual(second['action'], 'already_clean')
        self.assertEqual(len([call for call in api.calls if call[1] is not None]), 2)

    def test_saved_public_draft_resumes_without_second_put(self):
        record = fixture()
        api, journal = FakeApi(record), {}
        api.fail_publish = True
        with self.assertRaises(RuntimeError):
            apply_copy(api, record, [record['data']], {IDENTITY}, CONTEXT, journal, lambda: None)
        self.assertEqual(api.record['publishedVersion'], 4)
        self.assertEqual(api.record['version'], 5)
        self.assertEqual(journal[IDENTITY]['phase'], 'saved')
        api.fail_publish = False
        result = apply_copy(api, api.record, [record['data']], {IDENTITY}, CONTEXT, journal, lambda: None)
        self.assertEqual(result['action'], 'resumed')
        self.assertEqual(sum(call[2] == 'PUT' for call in api.calls), 1)

    def test_other_context_or_prepared_intent_cannot_resume(self):
        record = fixture()
        api, journal = FakeApi(record), {}
        api.fail_publish = True
        with self.assertRaises(RuntimeError):
            apply_copy(api, record, [record['data']], {IDENTITY}, CONTEXT, journal, lambda: None)
        changed_context = {**CONTEXT, 'base': 'https://sexogate.com/test/native-preview-' + 'a' * 16}
        self.assertEqual(plan_copy(api.record, [record['data']], {IDENTITY}, changed_context, journal)['action'], 'skip')
        journal[IDENTITY]['phase'] = 'prepared'
        self.assertEqual(plan_copy(api.record, [record['data']], {IDENTITY}, CONTEXT, journal)['action'], 'skip')

    def test_concurrent_change_after_save_stops_publish(self):
        record = fixture()
        api, journal = FakeApi(record), {}
        api.concurrent = True
        with self.assertRaisesRegex(ValueError, 'COPY_CONCURRENT'):
            apply_copy(api, record, [record['data']], {IDENTITY}, CONTEXT, journal, lambda: None)
        self.assertFalse(any(call[0].endswith('/publish') for call in api.calls))

    def test_version_conflict_is_not_retried(self):
        class RacingApi(FakeApi):
            def __call__(self, path, body=None, method='POST'):
                if body is not None and method == 'PUT':
                    self.record['version'] += 1
                return super().__call__(path, body, method)
        record = fixture()
        api, journal = RacingApi(record), {}
        with self.assertRaisesRegex(RuntimeError, 'API_409'):
            apply_copy(api, record, [record['data']], {IDENTITY}, CONTEXT, journal, lambda: None)
        self.assertEqual(sum(call[2] == 'PUT' for call in api.calls), 1)
        self.assertEqual(journal[IDENTITY]['phase'], 'prepared')
        self.assertFalse(any(call[0].endswith('/publish') for call in api.calls))

    def test_unconfirmed_empty_copy_does_not_activate_source_fallback(self):
        record = fixture()
        record['data']['description_tr'] = CTA
        self.assertEqual(plan_copy(record, [record['data']], {IDENTITY}, CONTEXT, {})['action'], 'skip')


ROOT = Path(__file__).resolve().parent.parent


class CopyCliBoundaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('copy_cli_boundary', ROOT / 'scripts/clean-native-marketplace-copy.py')
        cls.cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.cli)

    def package_fixture(self, folder):
        root = Path(folder)
        (root / '.local').mkdir()
        bundle = root / 'native-stage-fixture' / 'bundle'
        bundle.mkdir(parents=True)
        archive = root / 'package.zip'
        archive.write_bytes(b'unit-fixture-only')
        package = {'release': 'a' * 24, 'bundle': str(bundle), 'archive': str(archive),
            'dataset': self.cli.EXPECTED_DATASET, 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}
        manifest = {'release': package['release'], 'dataset': package['dataset'], 'checkoutEnabled': False}
        return root, bundle, package, manifest

    def test_reviewed_package_accepts_new_release_for_same_frozen_dataset(self):
        with TemporaryDirectory() as folder:
            root, bundle, package, manifest = self.package_fixture(folder)
            (root / '.local/native-stage-package.json').write_text(json.dumps(package), 'utf8')
            (bundle / 'deployment-manifest.json').write_text(json.dumps(manifest), 'utf8')
            with patch.object(self.cli, 'ROOT', root):
                self.assertEqual(self.cli.reviewed_package_release(), 'a' * 24)

    def test_reviewed_package_rejects_wrong_archive_manifest_dataset_and_open_checkout(self):
        mutations = [('archive', None), ('release', 'b' * 24), ('dataset', 'c' * 32), ('checkoutEnabled', True)]
        for field, value in mutations:
            with self.subTest(field=field), TemporaryDirectory() as folder:
                root, bundle, package, manifest = self.package_fixture(folder)
                if field == 'archive':
                    Path(package['archive']).write_bytes(b'changed-after-review')
                else:
                    manifest[field] = value
                (root / '.local/native-stage-package.json').write_text(json.dumps(package), 'utf8')
                (bundle / 'deployment-manifest.json').write_text(json.dumps(manifest), 'utf8')
                with patch.object(self.cli, 'ROOT', root), self.assertRaisesRegex(ValueError, 'COPY_REVIEWED_PACKAGE_REQUIRED'):
                    self.cli.reviewed_package_release()

    def test_only_exact_test_mounts_are_allowed(self):
        for base in ['https://127.0.0.1:3188/test', 'https://sexogate.com/test/',
                     'https://sexogate.com/test/native-preview-' + 'a' * 16]:
            self.assertEqual(self.cli.target_base(base), base.rstrip('/'))
        for base in ['http://sexogate.com/test', 'https://sexogate.com', 'https://sexogate.com/testevil',
                     'https://example.com/test', 'https://sexogate.com/test?x=1',
                     'https://127.0.0.1:3189/test', 'https://sexogate.com/test/../',
                     'https://sexogate.com/test/native-preview-INVALID']:
            with self.subTest(base=base), self.assertRaisesRegex(ValueError, 'COPY_TARGET_REJECTED'):
                self.cli.target_base(base)

    def test_public_guard_preserves_other_languages_and_money(self):
        before = [{'id': IDENTITY, 'description': {'tr': 'before', 'en': 'same'}, 'salePriceMinor': 11500}]
        after = copy.deepcopy(before)
        after[0]['description']['tr'] = 'after'
        fields = {IDENTITY: ['description_tr']}
        self.assertEqual(self.cli.protected_public(before, fields), self.cli.protected_public(after, fields))
        after[0]['salePriceMinor'] += 1
        self.assertNotEqual(self.cli.protected_public(before, fields), self.cli.protected_public(after, fields))
        after[0]['salePriceMinor'] -= 1
        after[0]['description']['en'] = 'changed'
        self.assertNotEqual(self.cli.protected_public(before, fields), self.cli.protected_public(after, fields))

    def test_runtime_timestamp_exclusions_are_exact_and_monotonic(self):
        before = {IDENTITY: {'updatedAt': 5, 'priceMinor': 11500}}
        after = {IDENTITY: {'updatedAt': 6, 'priceMinor': 11500}}
        self.assertEqual(self.cli.runtime_time_changes(before, after, {IDENTITY}), {IDENTITY: ['updatedAt']})
        after[IDENTITY]['updatedAt'] = 4
        with self.assertRaisesRegex(ValueError, 'COPY_RUNTIME_TIMESTAMP_INVALID'):
            self.cli.runtime_time_changes(before, after, {IDENTITY})


@unittest.skipUnless((ROOT / '.local/native-stage-package.json').is_file(), 'Local retained package unavailable')
class RetainedCopyTest(unittest.TestCase):
    def test_real_803_candidates_keep_all_noncopy_fields(self):
        from native_marketplace_import_guard import project_initials
        package = json.loads((ROOT / '.local/native-stage-package.json').read_text('utf8'))
        if package['dataset'] != '057fb50f7d5887fee341e3d5b4a3dd64':
            self.skipTest('This retained source fixture belongs to the reviewed November dataset')
        private = Path(package['bundle']) / 'private'
        catalog = json.loads((private / 'catalog.json').read_text('utf8'))
        products = [p for p in catalog['products'][2194:] if p['visualApprovedIndices'] and not p['eligibilityHold']]
        self.assertEqual(len(products), 803)
        initials = project_initials(ROOT / '.local/php-runtime/php.exe', private, products)
        changed = 0
        for identity, data in initials.items():
            target, fields, removed = clean_data(data)
            self.assertEqual(fingerprint(protected_data(data, fields)), fingerprint(protected_data(target, fields)))
            self.assertFalse(has_advertising(target['description_tr']))
            changed += bool(fields)
        self.assertEqual(changed, 785)


if __name__ == '__main__':
    unittest.main()
