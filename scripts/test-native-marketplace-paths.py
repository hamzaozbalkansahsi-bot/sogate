#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-marketplace-paths.py
# Açıklama   : Katalog yolu, sayaç, özet ve bağlantı kaçışlarını geçici dosyalarla sınar.
import hashlib
import os
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest.mock import patch
from native_marketplace_paths import marketplace_paths


class MarketplacePathsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='sexogate-paths-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.source = self.base / 'marketplace-catalog-20261116'
        self.prepared = self.source / 'prepared'
        self.prepared.mkdir(parents=True)
        self.catalog = self.prepared / 'catalog-data.json'
        self.catalog.write_bytes(b'{"fixture":"frozen-source"}')
        self.selection = {
            'path': str(self.prepared), 'dataset': 'd' * 32,
            'sha256': hashlib.sha256(self.catalog.read_bytes()).hexdigest(),
            'products': 2195, 'newProducts': 1, 'sourceProducts': 2,
            'mediaRoot': str(self.source / 'media'),
            'legacyMediaRoot': str(self.base / 'native-catalog-20261115' / 'media'),
        }
        self.resolve()

    def resolve(self, **changes):
        return marketplace_paths({**self.selection, **changes}, _test_base=self.base)

    def rejected(self, error, **changes):
        with self.assertRaisesRegex(ValueError, '^' + error + '$'):
            self.resolve(**changes)

    def symlink(self, link, target, *, directory=False):
        try:
            link.symlink_to(target, target_is_directory=directory)
        except OSError as error:
            self.skipTest('Symlink oluşturma yetkisi yok: ' + str(error.winerror if hasattr(error, 'winerror') else error.errno))

    def test_frozen_source_returns_all_five_canonical_paths(self):
        paths = self.resolve()
        self.assertEqual(paths.source, self.source)
        self.assertEqual(paths.prepared, self.prepared)
        self.assertEqual(paths.media, self.source / 'media')
        self.assertEqual(paths.legacyMedia, self.base / 'native-catalog-20261115' / 'media')
        self.assertEqual(paths.legacyPrepared, self.base / 'native-catalog-20261115' / 'prepared')
        with self.assertRaises(FrozenInstanceError):
            paths.source = self.base

    def test_expansion_source_uses_own_media_and_same_legacy(self):
        source = self.base / 'marketplace-catalog-20261117'
        paths = self.resolve(path=str(source / 'prepared'), mediaRoot=str(source / 'media'))
        self.assertEqual(paths.source, source)
        self.assertEqual(paths.media, source / 'media')
        self.assertEqual(paths.legacyMedia, self.resolve().legacyMedia)

    def test_missing_catalog_is_allowed_before_preparation(self):
        self.catalog.unlink()
        self.assertEqual(self.resolve().prepared, self.prepared)

    def test_catalog_hash_change_is_rejected(self):
        self.catalog.write_bytes(b'{"fixture":"modified"}')
        self.rejected('MARKETPLACE_CATALOG_HASH_MISMATCH')

    def test_valid_uppercase_hex_is_accepted(self):
        self.resolve(dataset=self.selection['dataset'].upper(), sha256=self.selection['sha256'].upper())

    def test_dataset_and_hash_formats_are_mandatory(self):
        for field, size in [('dataset', 32), ('sha256', 64)]:
            for value in [None, 1, 'a' * (size - 1), 'a' * (size + 1), 'z' * size, ' ' + 'a' * size]:
                with self.subTest(field=field, value=value):
                    self.rejected('MARKETPLACE_' + field.upper() + '_INVALID', **{field: value})

    def test_counts_must_be_nonnegative_integers(self):
        for field in ['products', 'newProducts', 'sourceProducts']:
            for value in [None, True, False, -1, 1.0, '1']:
                with self.subTest(field=field, value=value):
                    self.rejected('MARKETPLACE_COUNT_INVALID', **{field: value})

    def test_product_count_includes_exactly_2194_legacy_rows(self):
        self.rejected('MARKETPLACE_PRODUCT_COUNT_MISMATCH', products=2194)
        self.rejected('MARKETPLACE_PRODUCT_COUNT_MISMATCH', products=2196)
        self.resolve(products=2194, newProducts=0, sourceProducts=0)

    def test_source_count_cannot_be_below_new_products(self):
        self.rejected('MARKETPLACE_SOURCE_COUNT_MISMATCH', sourceProducts=0)

    def test_non_mapping_selection_is_rejected(self):
        for selection in [None, [], 'selection']:
            with self.subTest(selection=selection), self.assertRaisesRegex(ValueError, '^MARKETPLACE_SELECTION_INVALID$'):
                marketplace_paths(selection, _test_base=self.base)

    def test_only_two_exact_source_roots_are_allowed(self):
        for name in ['marketplace-catalog-20261116-next', 'marketplace-catalog-20261118', 'native-catalog-20261115', 'elsewhere']:
            with self.subTest(name=name):
                self.rejected('MARKETPLACE_SOURCE_ROOT_NOT_ALLOWED', path=str(self.base / name / 'prepared'))

    def test_prepared_must_be_exact_direct_child(self):
        for path in [self.prepared / 'nested', self.source, self.source / 'Prepared', self.base.parent / 'prepared']:
            with self.subTest(path=path):
                self.rejected('MARKETPLACE_SOURCE_ROOT_NOT_ALLOWED', path=str(path))

    def test_relative_and_parent_traversal_are_rejected(self):
        for path in ['marketplace-catalog-20261116/prepared', str(self.source / '..' / self.source.name / 'prepared')]:
            with self.subTest(path=path):
                self.rejected('MARKETPLACE_PREPARED_PATH_INVALID', path=path)

    def test_media_must_belong_to_selected_source(self):
        for media in [self.prepared / 'media', self.base / 'marketplace-catalog-20261117' / 'media']:
            with self.subTest(media=media):
                self.rejected('MARKETPLACE_MEDIA_ROOT_MISMATCH', mediaRoot=str(media))

    def test_legacy_media_root_is_fixed(self):
        self.rejected('MARKETPLACE_LEGACY_MEDIA_ROOT_MISMATCH', legacyMediaRoot=str(self.source / 'media'))

    def test_missing_or_invalid_paths_are_rejected(self):
        for key, code in [('path', 'PREPARED'), ('mediaRoot', 'MEDIA'), ('legacyMediaRoot', 'LEGACY_MEDIA')]:
            for value in [None, '', 2, '\x00']:
                with self.subTest(key=key, value=value):
                    self.rejected('MARKETPLACE_' + code + '_PATH_INVALID', **{key: value})

    def test_environment_cannot_override_base(self):
        with patch.dict(os.environ, {'MARKETPLACE_BASE': str(self.base), 'MARKETPLACE_SOURCE_ROOT': str(self.source)}):
            with self.assertRaisesRegex(ValueError, '^MARKETPLACE_SOURCE_ROOT_NOT_ALLOWED$'):
                marketplace_paths(self.selection)

    def test_file_cannot_replace_media_directory(self):
        (self.source / 'media').write_bytes(b'not a directory')
        self.rejected('MARKETPLACE_PATH_TYPE_INVALID')

    def test_directory_cannot_replace_catalog_file(self):
        self.catalog.unlink()
        self.catalog.mkdir()
        self.rejected('MARKETPLACE_PATH_TYPE_INVALID')

    def test_source_symlink_to_outside_is_rejected(self):
        outside = self.base / 'outside'
        outside.mkdir()
        source = self.base / 'marketplace-catalog-20261117'
        self.symlink(source, outside, directory=True)
        self.rejected('MARKETPLACE_PATH_ESCAPE', path=str(source / 'prepared'), mediaRoot=str(source / 'media'))

    def test_media_symlink_to_another_allowed_source_is_rejected(self):
        other = self.base / 'marketplace-catalog-20261117' / 'media'
        other.mkdir(parents=True)
        self.symlink(self.source / 'media', other, directory=True)
        self.rejected('MARKETPLACE_PATH_ESCAPE')

    def test_catalog_file_symlink_cannot_escape_prepared(self):
        target = self.base / 'other-catalog.json'
        target.write_bytes(self.catalog.read_bytes())
        self.catalog.unlink()
        self.symlink(self.catalog, target)
        self.rejected('MARKETPLACE_PATH_ESCAPE')

    def test_legacy_directory_symlink_is_rejected(self):
        target = self.base / 'other-legacy'
        target.mkdir()
        self.symlink(self.base / 'native-catalog-20261115', target, directory=True)
        self.rejected('MARKETPLACE_PATH_ESCAPE')


if __name__ == '__main__':
    unittest.main()
