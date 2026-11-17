#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-marketplaces.py
# Açıklama   : Kaynak fiyatı, UTF-8, güvenli JSON ayrıştırma ve cinsel ürün kapsamını sınar.
import unittest,json
from native_marketplaces import minor,markup_15,props,adult_item,detail_page,safe_url,marketplace_group,marketplace_claim_review
class MarketplaceTest(unittest.TestCase):
 def test_category_evidence_precedes_ambiguous_title(self):
  self.assertEqual(marketplace_group('Fantezi Erkek Boxer',[{'id':3096}]),'lingerie')
  self.assertEqual(marketplace_group('Eldivenli Mini Elbise',[{'id':3097}]),'lingerie')
  self.assertEqual(marketplace_group('Harness Vibratör Partnerli',[{'id':5097}]),'couples')
  self.assertEqual(marketplace_group('Şarjlı Mastürbatör',[{'id':5234}]),'toys')
  self.assertEqual(marketplace_group('Penis Kılıfı Prezervatif',[{'id':5242}]),'toys')
  self.assertEqual(marketplace_group('Pozisyon Zarları',[]),'couples')
  self.assertEqual(marketplace_group('Kayganlaştırıcı Jel',[]),'care')
  self.assertEqual(marketplace_group('El ve Bilek Kelepçesi',[]),'accessories')
 def test_unverified_claim_stems_require_review(self):
  for title in ['Penis Dikleştirici','İlişkiyi Uzatan Halka','Erken Önleyici','Su Geçirmez Vibratör','Büyütücü Pompa']:
   self.assertTrue(marketplace_claim_review(title),title)
  self.assertFalse(marketplace_claim_review('22 cm Silikon Dokulu Oyuncak'))
 def test_integer_money(self):
  self.assertEqual(minor('451.10'),45110);self.assertEqual(markup_15(45110),51877);self.assertEqual(markup_15(1),1);self.assertIsNone(minor(True));self.assertIsNone(minor('NaN'));self.assertIsNone(markup_15(12.5))
 def test_plain_json_not_executed(self):
  self.assertEqual(props('<script>window["X"]={"title":"İç Giyim Şişli"};evil()</script>','X')['title'],'İç Giyim Şişli')
  with self.assertRaises(ValueError):props('<script>window["X"]=eval("x")</script>','X')
 def test_hosts(self):
  for url in ['http://www.trendyol.com/','https://www.trendyol.com.evil.invalid/','https://user@www.trendyol.com/','https://127.0.0.1/']:
   with self.assertRaises(ValueError):safe_url(url)
 def test_scope(self):
  self.assertTrue(adult_item({'name':'Fantezi zar ve oyun kartı'}));self.assertFalse(adult_item({'name':'Çocuk gecelik'}));self.assertFalse(adult_item({'name':'Kanal ölçü aleti'}))
 def test_original_code_and_price_basis(self):
  p={'id':1,'name':'İç Giyim','productCode':'ABC-XL-Ç','images':['https://cdn.dsmcdn.com/example.jpg'],'variants':[{'itemNumber':2,'value':'XL','inStock':True}],'merchantListing':{'winnerVariant':{'price':{'currency':'TRY','sellingPrice':{'value':100},'originalPrice':{'value':80},'discountedPrice':{'value':60}}}}}
  doc='<script>window["__envoy__SHARED_PROPS"]='+json.dumps({'product':p})+'</script><script type="application/ld+json">'+json.dumps({'@type':'Product','description':'Ölçü ve bakım bilgisi.'})+'</script>'
  row=detail_page(doc,'https://www.trendyol.com/product-p-1');self.assertEqual(row['sku'],'seo-ABC-XL-Ç');self.assertEqual(row['salePriceMinor'],11500);self.assertIsNone(row['stockQuantity']);self.assertEqual(row['variants'][0]['size'],'XL');self.assertNotIn('review',row)
 def test_product_group_real_code_and_description(self):
  p={'id':7,'name':'Fantezi Giyim','images':[],'variants':[],'merchantListing':{'winnerVariant':{'price':{'currency':'TRY','sellingPrice':{'value':100}}}}}
  doc='<script>window["__envoy__SHARED_PROPS"]='+json.dumps({'product':p})+'</script><script type="application/ld+json">'+json.dumps({'@type':'ProductGroup','sku':'MODEL-XL','description':'İstanbul için ürün açıklaması.'})+'</script>'
  row=detail_page(doc,'https://www.trendyol.com/product-p-7');self.assertEqual(row['sourceCode'],'MODEL-XL');self.assertNotIn('description',row['missingFields'])
 def test_real_codes_keep_internal_spaces_reject_markup_and_controls(self):
  for code,expected in [('KD 0367','seo-KD 0367'),('Byzon Telefon Kontrollü 01','seo-Byzon Telefon Kontrollü 01'),('İÇ GİYİM ŞİŞLİ','seo-İÇ GİYİM ŞİŞLİ'),('A\nB',None),('A<B',None),('A\x7fB',None),('x'*121,None)]:
   product={'id':9,'name':'Gerçek kaynak ürünü','productCode':code};doc='<script>window["__envoy__SHARED_PROPS"]='+json.dumps({'product':product})+'</script>'
   self.assertEqual(detail_page(doc,'https://www.trendyol.com/p-p-9')['sku'],expected)
if __name__=='__main__':unittest.main()
