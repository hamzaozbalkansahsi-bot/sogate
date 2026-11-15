#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-catalog-taxonomy.py
# Açıklama   : Alt kategorilerin gerçek ürün türü, dil ve değişmez ürün kimliği ilişkisini doğrular.
import unittest
from native_catalog_taxonomy import apply_taxonomy,TYPES
from native_catalog import LANGUAGES

class TaxonomyTests(unittest.TestCase):
 def classify(self,name,group='lingerie',source=None):
  product={'id':'stable-id','name':{'tr':name},'categoryIds':['sg_'+group],'salePriceMinor':13000}
  data={'products':[product],'categories':[{'id':'sg_'+group,'parentId':None}], 'workbench':[{'id':'stable-id','group':group,'sourceCategories':source or []}]}
  categories=apply_taxonomy(data);return product,categories
 def test_liona_product_breadcrumb_is_not_a_category(self):
  p,c=self.classify('Liona Kırmızı Dantelli Gecelik',source=[{'name':'Anasayfa'},{'name':'Liona Kırmızı Dantelli Gecelik'}]);self.assertEqual(p['categoryIds'],['sg_lingerie','sg_lingerie_chemises']);self.assertEqual(len(c),2)
 def test_plus_size_secondary_relationship(self):
  p,c=self.classify('Büyük Beden Jartiyer Takımı');self.assertEqual(p['categoryIds'],['sg_lingerie','sg_lingerie_garters','sg_lingerie_plus'])
 def test_pump_is_not_dildo(self):
  p,c=self.classify('Penis Pompası','toys');self.assertEqual(p['categoryIds'],['sg_toys','sg_toys_pumps'])
 def test_stock_price_identity_unchanged(self):
  p,c=self.classify('Saten Gecelik');self.assertEqual((p['id'],p['salePriceMinor']),('stable-id',13000));self.assertNotIn('stockQuantity',p)
 def test_all_category_locales_and_unique_keys(self):
  self.assertEqual(len(TYPES),len(set(row[0]for row in TYPES)))
  for key,pattern,labels in TYPES:self.assertEqual(len(labels),len(LANGUAGES));self.assertTrue(all(labels))

if __name__=='__main__':unittest.main()
