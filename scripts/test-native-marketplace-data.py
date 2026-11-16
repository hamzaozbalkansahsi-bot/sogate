#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-marketplace-data.py
# Açıklama   : Hazırlanmış gerçek kayıtları bağımsız kaynak, değişmez arşiv, görsel hash ve seçenek kanıtlarıyla karşılaştırır.
import hashlib,json,sqlite3,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;BASE=Path('D:/sexogate-local-artifacts-20261114/private-installs');HOME=BASE/'marketplace-catalog-20261116'
class MarketplaceDataTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.selection=json.loads((ROOT/'.local/native-marketplace-selection.json').read_text('utf8'));cls.prepared=Path(cls.selection['path']);cls.data=json.loads((cls.prepared/'catalog-data.json').read_text('utf8'));cls.legacy=json.loads((BASE/'native-catalog-20261115/prepared/catalog-data.json').read_text('utf8'));cls.new=cls.data['products'][2194:]
  with sqlite3.connect(HOME/'research.sqlite')as db:cls.source={json.loads(r[0])['sourceUrl']:json.loads(r[0])for r in db.execute("SELECT detail_json FROM products WHERE status='ready'")}
  cls.work={key:value for f in(cls.prepared/'catalog-workbench').glob('*.json')for key,value in json.loads(f.read_text('utf8')).items()}
 def test_archived_rows_preserved(self):self.assertEqual(self.data['products'][:2194],self.legacy['products'])
 def test_source_codes_and_prices(self):
  for p in self.new:
   w=self.work[p['id']];source=self.source[w['source']['url']];self.assertEqual(p['code'],'seo-'+source['sourceCode']);self.assertEqual(w['source']['retailPriceMinor'],source['undiscountedPriceMinor']);self.assertEqual(p['salePriceMinor'],source['salePriceMinor']);self.assertEqual(w['source']['htmlSha256'],source['sourceSha256'])
 def test_no_invented_variant_combinations(self):
  for p in self.new:
   w=self.work[p['id']];source=self.source[w['source']['url']];actual={v['sourceVariantId']:v for v in source['variants']}
   for v in w['sourceVariants']:
    self.assertIn(v['id'],actual);self.assertEqual(v['attributes'][0],{'name':'Beden','value':actual[v['id']]['size']});self.assertIsNone(v['sku']);self.assertEqual(v['isActive'],actual[v['id']]['sourceInStock'])
 def test_media_original_bytes_and_review(self):
  for p in self.new:
   w=self.work[p['id']]
   for m in w['media']:self.assertEqual(hashlib.sha256((HOME/'media'/m['file']).read_bytes()).hexdigest(),m['sha256']);self.assertEqual((HOME/'media'/m['file']).stat().st_size,m['bytes'])
   self.assertEqual(p['visualApprovedIndices'],[0]if w['coverReview']['coverApproved']else[])
 def test_missing_facts_not_fabricated(self):
  for p in self.new:
   ids={str(c.get('id'))for c in self.work[p['id']]['sourceCategories']}
   if '3096'in ids:self.assertEqual(p['categoryIds'][0],'sg_lingerie')
   if ids.intersection({'5234','5235','5092','5094','5095','5097','5242','5243'}):self.assertNotEqual(p['categoryIds'][0],'sg_care')
   if 'dikleştirici'in p['name']['tr'].lower():self.assertTrue(p['eligibilityHold'])
  for p in self.new:self.assertIsNone(p['stockQuantity']);self.assertFalse(p['stockKnown']);self.assertFalse(p['published']);self.assertTrue(p['hidden']);self.assertFalse(p['referencePriceVerified']);self.assertEqual(p['additionalDiscountPercent'],0)
 def test_deferred_rows_count_and_utf8(self):
  manifest=json.loads((self.prepared/'catalog-sources.json').read_text('utf8'));self.assertEqual(len(self.new)+len(manifest['marketplaceDeferred']),len(self.source));self.assertFalse(manifest['allMarketplaceProductsTransferred']);self.assertEqual(len({p['code']for p in self.data['products']}),len(self.data['products']))
  for p in self.new:
   self.assertTrue(p['seoTitle']['tr']);self.assertTrue(p['seoDescription']['tr']);self.assertNotIn('\ufffd',p['name']['tr']);self.assertNotIn('ÅŸ',p['description']['tr'])
if __name__=='__main__':unittest.main()
