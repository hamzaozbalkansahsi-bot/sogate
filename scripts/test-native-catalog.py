#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-catalog.py
# Açıklama   : İlk aktarım fiyatını, gerçek veri sınırlarını, SEO temizliğini ve kaynak eşlemesini sınar.
import importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('native_catalog',Path(__file__).with_name('native_catalog.py'));catalog=importlib.util.module_from_spec(spec);spec.loader.exec_module(catalog)
class CatalogTests(unittest.TestCase):
 def test_markup_integer(self):
  self.assertEqual(catalog.markup(85500),111150);self.assertEqual(catalog.markup(5),7);self.assertIsNone(catalog.markup(None));self.assertIsNone(catalog.markup(0))
 def test_missing_description(self):
  for value in [None,'None','undefined','null','']:self.assertEqual(catalog.plain(value),'')
 def test_plain_safe_utf8(self):
  self.assertEqual(catalog.plain('<p>Ölçü ve Özellikler &amp; İç Giyim</p><script>bad()</script>'),'Ölçü ve Özellikler & İç Giyim')
 def test_source_ids_stable(self):
  row={'sourceUrl':'https://www.liona.com.tr/urun.html','sku':'İÇ-01'};self.assertEqual(catalog.product_id('liona',row),catalog.product_id('liona',{**row,'quotedRetailMinor':10}));self.assertNotEqual(catalog.product_id('liona',row),catalog.product_id('sistina',row))
 def test_no_health_promises(self):
  self.assertNotIn('tedavi',catalog.safe_description('Dantel kumaş. Hastalığı tedavi eder. Kesin sonuç sağlar.').lower())
 def test_real_barcode_only(self):
  self.assertEqual(catalog.gtin('4006381333931'),'4006381333931');self.assertIsNone(catalog.gtin('4006381333932'));self.assertIsNone(catalog.gtin('1234'))
 def test_supplier_is_not_warehouse(self):
  p,w=catalog.make_product('liona',{'sourceUrl':'https://www.liona.com.tr/a.html','title':'Liona Kırmızı Dantelli String','sku':'LS1','quotedRetailMinor':10001,'quotedCurrency':'TRY','publicInStock':True,'description':'Dantel detaylı string.','images':[]},None)
  self.assertFalse(p['stockKnown']);self.assertIsNone(p['stockQuantity']);self.assertEqual(w['facts']['costMinor'],None);self.assertEqual(p['salePriceMinor'],13001);self.assertTrue(w['source']['publicInStock'])
 def test_all_seo_locales_have_text(self):
  p,_=catalog.make_product('liona',{'sourceUrl':'https://www.liona.com.tr/a.html','title':'Liona Kırmızı String','sku':'ABC','quotedRetailMinor':10000,'quotedCurrency':'TRY','images':[]},None)
  for language in catalog.LANGUAGES:
   for field in ['name','description','seoTitle','seoDescription']:self.assertTrue(p[field][language]);self.assertNotIn('\ufffd',p[field][language])
if __name__=='__main__':unittest.main()
