import importlib.util
import unittest
from pathlib import Path

R = Path(__file__).resolve().parents[1]
s = importlib.util.spec_from_file_location('paint', R/'lib/marketplace_paints.py')
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)


class PaintSourceTests(unittest.TestCase):
    def test_legitimate_canonical_redirect_preserves_approved_identity(self):
        u='https://www.trendyol.com/filli-boya/test-p-123?merchantId=42'
        self.assertEqual(m.source_redirect(u,u,'/pd/filli-boya/new-name-p-123'),'https://www.trendyol.com/pd/filli-boya/new-name-p-123?merchantId=42')
        for target in ['https://evil.test/test-p-123','/pd/filli-boya/test-p-456','/pd/filli-boya/test-p-123?merchantId=99']:
            with self.assertRaises(ValueError): m.source_redirect(u,u,target)

    def test_packaging_equivalence_is_not_a_density_conversion(self):
        self.assertEqual(m.package_value('0,25 L'),m.package_value('250 ml'))
        self.assertNotEqual(m.package_value('250 g'),m.package_value('250 ml'))
        r={'sourceProductId':'1','family':'afilli','title':'Afilli 250 ml','package':'250 g','color':'Beyaz'}
        self.assertEqual(m.offer_review(r),'title_and_selected_package_conflict')
        r.update(title='Afilli Beyaz 250 ml',package='250 ml',color='Siyah')
        self.assertEqual(m.offer_review(r),'title_and_selected_colour_conflict')
    def test_kurus_markup_rounding(self):
        self.assertEqual(m.markup(199900), 259870)
        self.assertEqual(m.markup(101), 131)
        for v in [0, -1, True, 1.2]:
            with self.assertRaises(ValueError): m.markup(v)

    def test_diamond_requires_manufacturer_mass_instead_of_assuming_density(self):
        r={'sourceProductId':'1148797790','family':'diamond','title':'Liquid Diamond 0.6 Kg','package':'600 gr','color':'Çok Renkli'}
        self.assertIsNone(m.offer_review(r))
        r.update(title='Liquid Diamond 600 ml',package='600 ml')
        self.assertEqual(m.offer_review(r),'manufacturer_600g_and_marketplace_600ml_need_package_confirmation')

    def test_real_saved_product_requires_exact_merchant_and_product(self):
        body = (R/'artifacts/bianca-20261112/sample-pinned.html').read_bytes()
        url = 'https://www.trendyol.com/bianca/test-p-819338039?merchantId=942066'
        row = m.parse(body, url, '942066')
        self.assertEqual(row['sourceProductId'], '819338039')
        self.assertEqual(row['package'], '1 L')
        self.assertEqual(row['sourcePriceMinor'], 199900)
        self.assertEqual(row['merchant']['name'], 'Orjinal Boya')
        with self.assertRaisesRegex(ValueError, 'merchant_identity_changed'): m.parse(body, url, '584353')
        with self.assertRaisesRegex(ValueError, 'product_identity_changed'): m.parse(body, url.replace('819338039', '123'), '942066')

    def test_external_source_and_unknown_score_fail_closed(self):
        for u in ['https://evil.test/x-p-123', 'https://www.trendyol.com.evil.test/x-p-123', 'http://www.trendyol.com/x-p-123', 'https://u:p@www.trendyol.com/x-p-123']:
            with self.assertRaises(ValueError): m.product_id(u)
        with self.assertRaises(ValueError): m.best_merchant({'merchant': {'id':1,'score':None,'authorized':True},'alternatives':[]})

if __name__ == '__main__': unittest.main()
