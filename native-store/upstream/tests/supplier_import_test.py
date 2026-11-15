import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class SupplierImportTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('supplier_import', ROOT/'scripts/import-wood-suppliers.py')
        self.assertTrue(Path(spec.origin).exists(), 'Supplier importer must exist')
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)

    def test_markup_is_not_margin_and_rounds_in_kurus(self):
        self.assertEqual(self.m.markup(10005,20),12006)
        self.assertEqual(self.m.markup(10005,30),13007)
        self.assertEqual(self.m.money('1.684,80 TL'),168480)
        self.assertEqual(self.m.money('58772.39', decimal='.'),5877239)
        with self.assertRaises(ValueError): self.m.money('-30 TL')

    def test_identity_keeps_source_sku_and_is_supplier_scoped(self):
        a=self.m.identity('alka','4156','https://alkaahsap.com/urun/a/')
        b=self.m.identity('altinis','4156','https://www.altinisagac.com/urun/a')
        self.assertNotEqual(a,b)
        self.assertTrue(a[1].startswith('ND-ALK-4156'))
        self.assertEqual(a,self.m.identity('alka','4156','https://alkaahsap.com/urun/a/'))

    def test_altinis_uses_visible_stock_code_not_marketing_schema_sku(self):
        body=(ROOT/'artifacts/supplier-expansion/altinis-sample.html').read_bytes()
        p=self.m.parse_altinis(body,'https://www.altinisagac.com/urun/elif-cay-takimi-120x59x95-cm-7217')
        self.assertEqual(p['sourceCode'],'4156')
        self.assertEqual(p['sourcePriceMinor'],5877239)
        self.assertEqual(p['salePriceMinor'],7052687)
        self.assertTrue(p['images'])
        self.assertIn('Ahşap Oturma Grubu',p['categories'])

    def test_alka_variable_range_never_becomes_exact_selling_price(self):
        import json
        rows=json.loads((ROOT/'artifacts/supplier-expansion/alka-store-sample.json').read_bytes())
        row=next(x for x in rows if x['variations'])
        p=self.m.parse_alka(row)
        self.assertIsNone(p['salePriceMinor'])
        self.assertEqual(p['priceStatus'],'variant_selection_required')
        self.assertEqual(p['sourceCode'],self.m.text(row['sku']))

    def test_alka_quote_request_is_distinguished_from_numeric_price(self):
        body=(ROOT/'artifacts/supplier-expansion/alka-zero-0.html').read_bytes()
        found=self.m.alka_visible_offer(body)
        self.assertEqual(found['status'],'quote_required')
        self.assertIsNone(found['sourcePriceMinor'])
        found=self.m.alka_visible_offer(b'<div class="summary"><p class="price"><del><bdi>100.00</bdi></del><ins><span class="woocommerce-Price-amount"><bdi>85.00</bdi></span></ins><span class="wd-price-unit">Metre</span></p></div>')
        self.assertEqual(found['sourcePriceMinor'],8500)
        self.assertEqual(found['salesUnit'],'Metre')

    def test_archive_compression_is_lossless_and_zero_price_does_not_drop_product(self):
        import gzip,tempfile
        with tempfile.TemporaryDirectory() as folder:
            file=Path(folder)/'source.html';raw=b'<html>source proof</html>';file.write_bytes(gzip.compress(raw))
            self.assertEqual(self.m.read_archive(file),raw)
        body=(ROOT/'artifacts/supplier-expansion/altinis-sample.html').read_bytes().replace(b'58772.39',b'0.00').replace(b'58.772,39',b'0,00')
        row=self.m.parse_altinis(body,'https://www.altinisagac.com/urun/example-1')
        self.assertEqual(row['sourceCode'],'4156')
        self.assertIsNone(row['salePriceMinor'])

if __name__=='__main__':unittest.main()
