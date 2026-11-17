#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-marketplace-import-guard.py
# Açıklama   : Eski inceleme kayıtlarının yalnız değişmemiş taslaklardan sürüm ve niyet kanıtıyla yükseltildiğini sınar.
import copy
import json
import unittest
from pathlib import Path

from native_marketplace_import_guard import (
    canonical_data, fingerprint, normalize_generic_brand, plan_upgrade,
    guarded_upgrade, project_initials, frozen_baseline,
)

IDENTITY = 'sg_ty_guard_fixture'
DATASET = 'f' * 32


def example():
    baseline = {'visible': False, 'sku': 'seo-SKU', 'brand': 'Genel Markalar',
        'title_tr': 'Eski başlık', 'title_en': 'Genel Markalar Adult Toys SKU',
        'description_en': 'Genel Markalar Adult Toys SKU.',
        'seoTitle_en': 'Genel Markalar Adult Toys SKU', 'seoDescription_en': 'Genel Markalar Adult Toys SKU.',
        'slug': 'eski-baslik', 'coverIndex': 0, 'imageApprovedIndices': '', 'priceMinor': 11500}
    target = {**baseline, 'visible': True, 'title_tr': 'Yeni olgusal başlık',
              'slug': 'yeni-baslik', 'imageApprovedIndices': '0'}
    record = {'id': IDENTITY, 'version': 1, 'publishedVersion': 0,
              'data': copy.deepcopy(baseline)}
    return baseline, target, record


class FakeApi:
    def __init__(self, record):
        self.record = copy.deepcopy(record)
        self.calls = []
        self.concurrent = False
        self.fail_publish = False

    def __call__(self, path, body=None, method='POST'):
        self.calls.append((path, copy.deepcopy(body), method))
        if body is None:
            if self.concurrent and self.record['version'] == 2:
                self.record['data']['priceMinor'] += 1
                self.record['version'] += 1
            return {'record': copy.deepcopy(self.record)}
        if body['version'] != self.record['version']:
            raise RuntimeError('API_409_version_conflict')
        if path.endswith('/publish'):
            if self.fail_publish:
                raise RuntimeError('simulated_transport_failure')
            self.record['version'] += 1
            self.record['publishedVersion'] = self.record['version']
        else:
            self.record['data'] = canonical_data(body['data'])
            self.record['version'] += 1
        return {'data': copy.deepcopy(self.record)}


class ImportGuardTest(unittest.TestCase):
    def plan(self, record=None, target=None, eligible=True, journal=None):
        baseline, default_target, default_record = example()
        return plan_upgrade(IDENTITY, record or default_record, baseline,
                            target or default_target, DATASET, journal or {}, eligible=eligible)

    def test_untouched_initial_draft_is_upgradeable(self):
        self.assertEqual(self.plan()['action'], 'upgrade')

    def test_exact_known_brand_normalization_is_only_v2_exception(self):
        baseline, target, record = example()
        record.update(version=2, data=normalize_generic_brand(canonical_data(baseline)))
        self.assertEqual(self.plan(record)['action'], 'upgrade')
        record['data']['description_en'] = 'Adult Toys SKU.'
        self.assertEqual(self.plan(record)['action'], 'preserve')

    def test_arbitrary_v2_or_later_drafts_are_preserved(self):
        baseline, target, record = example()
        for version in [2, 3, 99]:
            record['version'] = version
            self.assertEqual(self.plan(record)['action'], 'preserve')

    def test_manual_data_and_extra_fields_are_preserved(self):
        for field, value in [('priceMinor', 12345), ('title_tr', 'Elle değişti'), ('note', 'manual')]:
            baseline, target, record = example()
            record['data'][field] = value
            self.assertEqual(self.plan(record)['action'], 'preserve')

    def test_changed_source_price_never_reprices_old_record(self):
        baseline, target, record = example()
        target['priceMinor'] += 1
        result = self.plan(record, target)
        self.assertEqual(result['action'], 'preserve')
        self.assertEqual(result['reason'], 'target_price_changed')

    def test_published_and_out_of_scope_records_are_never_overwritten(self):
        baseline, target, record = example()
        record.update(version=3, publishedVersion=3)
        self.assertEqual(self.plan(record)['action'], 'preserve')
        self.assertEqual(self.plan(eligible=False)['reason'], 'not_approved_old_hold')

    def test_php_trim_keeps_nonbreaking_space_and_types(self):
        self.assertEqual(canonical_data({'a': ' \tİstanbul\n'}), {'a': 'İstanbul'})
        self.assertEqual(canonical_data({'a': '\u00a0İstanbul\u00a0'}), {'a': '\u00a0İstanbul\u00a0'})
        self.assertNotEqual(fingerprint({'value': True}), fingerprint({'value': 1}))

    def test_guarded_real_api_shape_uses_current_versions_and_is_idempotent(self):
        baseline, target, record = example()
        api = FakeApi(record)
        journal = {}
        writes = []
        saved = guarded_upgrade(api, IDENTITY, baseline, target, DATASET, journal,
                                lambda: writes.append(copy.deepcopy(journal)), eligible=True)
        self.assertEqual(saved['action'], 'upgraded')
        self.assertEqual(api.record['version'], 3)
        self.assertEqual(api.record['publishedVersion'], 3)
        mutations = [call for call in api.calls if call[1] is not None]
        self.assertEqual([call[1]['version'] for call in mutations], [1, 2])
        self.assertEqual([call[2] for call in mutations], ['PUT', 'POST'])
        self.assertEqual(api.record['data']['priceMinor'], baseline['priceMinor'])
        self.assertEqual(api.record['data']['brand'], '')
        count = len(mutations)
        again = guarded_upgrade(api, IDENTITY, baseline, target, DATASET, journal,
                                lambda: None, eligible=True)
        self.assertEqual(again['action'], 'already_current')
        self.assertEqual(len([call for call in api.calls if call[1] is not None]), count)
        self.assertEqual(journal[IDENTITY]['phase'], 'published')

    def test_concurrent_edit_after_put_blocks_publish(self):
        baseline, target, record = example()
        api = FakeApi(record)
        api.concurrent = True
        with self.assertRaisesRegex(ValueError, 'GUARD_CONCURRENT'):
            guarded_upgrade(api, IDENTITY, baseline, target, DATASET, {}, lambda: None, eligible=True)
        self.assertFalse(any(call[0].endswith('/publish') for call in api.calls))

    def test_api_version_conflict_is_not_retried_or_published(self):
        class RacingApi(FakeApi):
            def __call__(self, path, body=None, method='POST'):
                if body is not None and method == 'PUT':
                    self.record['version'] += 1
                return super().__call__(path, body, method)
        baseline, target, record = example()
        api, journal = RacingApi(record), {}
        with self.assertRaisesRegex(RuntimeError, 'API_409_version_conflict'):
            guarded_upgrade(api, IDENTITY, baseline, target, DATASET, journal, lambda: None, eligible=True)
        self.assertEqual(sum(call[2] == 'PUT' for call in api.calls), 1)
        self.assertEqual(journal[IDENTITY]['phase'], 'prepared')
        self.assertFalse(any(call[0].endswith('/publish') for call in api.calls))

    def test_saved_intent_recovers_publish_without_second_put(self):
        baseline, target, record = example()
        api = FakeApi(record)
        journal = {}
        api.fail_publish = True
        with self.assertRaisesRegex(RuntimeError, 'simulated_transport_failure'):
            guarded_upgrade(api, IDENTITY, baseline, target, DATASET, journal, lambda: None, eligible=True)
        self.assertEqual(journal[IDENTITY]['phase'], 'saved')
        api.fail_publish = False
        result = guarded_upgrade(api, IDENTITY, baseline, target, DATASET, journal, lambda: None, eligible=True)
        self.assertEqual(result['action'], 'resumed')
        self.assertEqual(sum(call[2] == 'PUT' for call in api.calls), 1)

    def test_target_equality_without_saved_intent_does_not_publish_draft(self):
        baseline, target, record = example()
        record.update(version=2, data=normalize_generic_brand(canonical_data(target)))
        self.assertEqual(self.plan(record)['action'], 'preserve')

    def test_corrupt_or_other_dataset_intent_cannot_resume(self):
        baseline, target, record = example()
        api = FakeApi(record)
        journal = {}
        api.fail_publish = True
        with self.assertRaises(RuntimeError):
            guarded_upgrade(api, IDENTITY, baseline, target, DATASET, journal, lambda: None, eligible=True)
        for key, value in [('dataset', '0' * 32), ('targetSha256', '0' * 64), ('phase', 'prepared'), ('scope', 'another-base-or-release')]:
            changed = copy.deepcopy(journal)
            changed[IDENTITY][key] = value
            result = plan_upgrade(IDENTITY, api.record, baseline, target, DATASET, changed, eligible=True)
            self.assertEqual(result['action'], 'preserve')


ROOT = Path(__file__).resolve().parent.parent


@unittest.skipUnless((ROOT / '.local/native-stage-package.json').is_file(), 'Local packaged PHP unavailable')
class PhpProjectionTest(unittest.TestCase):
    def test_frozen_51_baseline_uses_actual_packaged_php_projection(self):
        products, held, proof = frozen_baseline()
        self.assertEqual(len(products), 131)
        self.assertEqual(len(held), 51)
        self.assertEqual(proof['sha256'], 'd6828498854e6763207b134da811cfbdd6c9d9b82166b96d644624ddf36f4263')
        package = json.loads((ROOT / '.local/native-stage-package.json').read_text('utf8'))
        initial = project_initials(ROOT / '.local/php-runtime/php.exe', Path(package['bundle']) / 'private', products)
        self.assertEqual(len(initial), 131)
        self.assertTrue(all(initial[key]['visible'] is False for key in held))
        self.assertEqual(sum(value['visible'] is True for value in initial.values()), 80)
        source = next(p for p in products if p['id'] in held)
        row = initial[source['id']]
        self.assertEqual(row['priceMinor'], source['salePriceMinor'])
        self.assertEqual(row['title_tr'], source['name']['tr'].strip(' \t\n\r\x00\x0b'))


if __name__ == '__main__':
    unittest.main()
