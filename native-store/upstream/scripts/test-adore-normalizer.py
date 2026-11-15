"""Meaningful importer tests against the saved, real Lungo source fixture."""
import importlib.util
import json
from pathlib import Path
from urllib.parse import urlparse
import unittest

spec = importlib.util.spec_from_file_location('normalizer', Path(__file__).with_name('normalize-adore-catalog.py'))
normalizer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(normalizer)
FIXTURE = normalizer.ROOT / 'tests' / 'fixtures' / 'lungo.html'
URL = 'https://www.adoremobilya.com/kahve-kosesi-6-kapakli-tek-cekmeceli-cok-amacli-dolap-florida-mese/-beyaz-120x195x45-cm'


class NormalizerTests(unittest.TestCase):
    def test_real_product_fields_keep_turkish_and_supplier_boundaries(self):
        product, raw = normalizer.parse_product(FIXTURE.read_text(encoding='utf-8'), URL, '2026-10-31T00:00:00+00:00')
        self.assertEqual(product['id'], '5015')
        self.assertEqual(product['code'], 'ADR-861-FB-2')
        self.assertIn('Kahve Köşesi', product['title'])
        self.assertEqual(product['retailPrice'], 11989.0)
        self.assertEqual(product['currency'], 'TRY')
        self.assertIsNone(product['salePrice'])
        self.assertEqual(product['categoryIds'], ['mutfak-banyo', 'mutfak-dolaplari'])
        self.assertEqual(len(product['images']), 10)
        self.assertEqual(dict((s['label'],s['value']) for s in product['specs'])['Ürün Rengi'], 'Florida Meşe / Beyaz')
        self.assertIn('120 x 195 x 45 cm', product['fullDescription'])
        self.assertNotIn('0850 346 85 85', product['description'])
        self.assertIn('0850 346 85 85', raw['descriptionHtml'])

    def test_text_sanitization_drops_executable_and_preserves_breaks(self):
        self.assertEqual(normalizer.clean_text('<div>Ölçü<br>120 × 45 cm<script>evil()</script><p>Meşe</p></div>'), 'Ölçü\n120 × 45 cm\nMeşe')

    def test_missing_product_is_not_silently_accepted(self):
        with self.assertRaisesRegex(ValueError,'NoProductStructuredData'):
            normalizer.parse_product('<html><h1>Home page</h1></html>',URL,'now')

    def test_non_finite_or_negative_prices_are_rejected(self):
        for value in ('NaN','Infinity','-1',None,'abc'):
            self.assertIsNone(normalizer.safe_decimal(value))
        self.assertEqual(normalizer.safe_decimal('1234.56'),1234.56)

    def test_ingested_dataset_preserves_references_without_selling_source_prices(self):
        catalog_path = normalizer.ROOT/'data'/'catalog-source.json'
        if not catalog_path.exists():
            self.skipTest('Run the resumable import first.')
        catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
        products, categories = catalog['products'], {c['id'] for c in catalog['categories']}
        self.assertTrue(products)
        self.assertEqual(len({p['id'] for p in products}),len(products))
        for p in products:
            self.assertIsNone(p['salePrice'],p['code'])
            self.assertTrue(p['code'])
            self.assertTrue(p['images'])
            self.assertTrue(set(p['categoryIds']).issubset(categories),p['code'])
            self.assertNotIn('\ufffd',p['title'],p['code'])
            self.assertNotIn('<script',p['description'])
            for image in p['images']:
                self.assertEqual(urlparse(image).hostname,'witcdn.adoremobilya.com')
        if catalog['meta']['complete']:
            report = json.loads((normalizer.ROOT/'data'/'catalog-report.json').read_text(encoding='utf-8'))
            self.assertFalse(report['pendingUrls'])
            self.assertFalse(report['parseErrors'])
            self.assertEqual(len(products)+len(report['duplicateProductIds'])+len(report['excludedSourceProductUrls']),catalog['meta']['expectedProductUrls'])


if __name__=='__main__':
    unittest.main()
