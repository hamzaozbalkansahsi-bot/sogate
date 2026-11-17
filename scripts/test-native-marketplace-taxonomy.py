#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-marketplace-taxonomy.py
# Açıklama   : Gerçek kaynak türlerini ve yanıltıcı genel başlıkları kategori eşlemesinde sınar.
import unittest
from native_marketplace_taxonomy import classify_marketplace

def tree(*rows):
 return [{'id':identifier,'name':name}for identifier,name in rows]

class MarketplaceTaxonomyTest(unittest.TestCase):
 def check_type(self,title,categories,group,subtype,platform='trendyol'):
  result=classify_marketplace(title,categories,platform)
  self.assertEqual((result['group'],result['subtype']),(group,subtype))
  self.assertEqual(result['categoryIds'][0],'sg_'+group)
  if subtype:self.assertEqual(result['categoryIds'][1],'sg_'+group+'_'+subtype)
  return result
 def test_real_boxer_ignores_generated_costume_summary(self):
  self.check_type('GLIMMER GOLD Fantezi Işıltılı Erkek Boxer Serisi',tree((3096,'İç Giyim ve Kostüm'),(3101,'Fantezi Boxer')),'lingerie','boxers')
 def test_actual_costume_without_costume_in_title(self):
  result=self.check_type('Scarlet Bow Eldivenli Mini Elbise',tree((3095,'Fantezi Giyim'),(3097,'Fantezi Kostüm')),'lingerie','costumes')
  self.assertEqual(result['evidence']['sourceCategoryId'],'3097')
 def test_bodysuit_resolves_broad_babydoll_source(self):
  self.check_type('BORDO DANTELLİ BODYSUİT',tree((3096,'Fantezi İç Giyim'),(3100,'Fantezi Babydoll')),'lingerie','bodies')
 def test_stocking_is_not_body(self):
  self.check_type('Leopar Desenli Transparan File Tulum – Vücut Çorabı',tree((3096,'Fantezi İç Giyim'),(3102,'Fantezi Çorap')),'lingerie','tights')
 def test_explicit_costume_resolves_broad_garter_listing(self):
  self.check_type('Kadın Sekreter Fantazi Kostüm, Gecelik',tree((3104,'Fantezi Jartiyer')),'lingerie','costumes')
 def test_vibrating_masturbator_retains_type(self):
  self.check_type('Jlo 5,5 Kg 2 Girişli Titreşimli Mastürbatör Şarjlı',tree((5240,'Cinsel Oyuncak'),(5234,'Mastürbatör')),'toys','masturbators')
 def test_ring_does_not_become_dildo_or_vibrator(self):
  self.check_type('Tırtıklı Titreşimli Penis Halkası Pink',tree((5094,'Penis Halkası')),'toys','rings')
 def test_sleeve_word_condom_is_not_a_contraceptive(self):
  self.check_type('PENİS DİKLEŞTİRİCİ PREZERVATİF KALIN SEKS OYUNCAK',tree((5242,'Penis Kılıfı')),'toys','sleeves')
 def test_harness_vibrator_keeps_source_type(self):
  self.check_type('Harness Vibratör Giyilebilir Vibratör Partnerli Kullanıma Uygun',tree((5097,'Vibratör')),'couples','vibrators')
 def test_ambiguous_body_word_does_not_override_toy_identity(self):
  self.check_type('Body Massage Vibratör',tree((5097,'Vibratör')),'toys','vibrators')
  self.check_type('Body Massage Oil',tree(('care-oils','Masaj Yağları')),'care','oils',platform='hepsiburada')
 def test_cleaning_device_not_anal_toy(self):
  self.check_type('Anal Cleaner 220 Ml Temizleyici Anal Vakum Pompası',tree((5092,'Anal Oyuncak')),'care','cleaners')
 def test_accessory_set_is_not_automatically_gift(self):
  self.check_type('El Ayak Bağlama Kelepçesi BDSM Aleti Seti',tree((5241,'Fantezi Ürünleri')),'accessories','accessories')
 def test_cage_does_not_become_ring(self):
  self.check_type('Penis Kafesi Male Chastity Cage 4 Halkalı',tree((5094,'Penis Halkası')),'accessories','chastity')
 def test_principal_machine_and_support_not_included_accessory(self):
  self.check_type('Premium FULL PAKET SEKS MAKİNESİ Uzaktan Kumandalı',tree((5234,'Mastürbatör')),'toys','machines')
  self.check_type('Şişme Seks Pozisyon Yastığı - Kemer ve Tutacaklı',tree((5241,'Fantezi Ürünleri')),'accessories','positioning')
  self.check_type('Fantazi Ağız Topu',tree((3098,'Fantezi Aksesuar')),'accessories','accessories')
 def test_games_preserve_specific_type(self):
  for title,key in [('Pozisyon Zarları Kamasutra 2li Set','dice'),('Fantezi Zarlar','dice'),('52 Adet Fantezi Kart Oyunu','cards'),('Kamasutra Pozisyonlu Denge Oyunu','games'),('Fantezi Görevli Oyun Çarkı','games')]:
   with self.subTest(title=title):self.check_type(title,tree((5241,'Fantezi Ürünleri')),'couples',key)
 def test_tarot_does_not_copy_child_ancestor(self):
  result=self.check_type('Laura Tuan Sexual Magic Tarot Kartı',tree((2862,'Anne & Bebek & Çocuk'),(2231,'Kutu Oyunu')),'couples','cards')
  self.assertFalse(any('cocuk'in value for value in result['categoryIds']))
 def test_care_types_and_known_source_names(self):
  for title,categories,key in [('Su Bazlı Kayganlaştırıcı',[],'lubricants'),('Masaj Yağı',[],'oils'),('Prezervatif',[],'condoms'),('Oyuncak Temizleyici',[],'cleaners')]:
   with self.subTest(title=title):self.check_type(title,categories,'care',key)
  self.check_type('Model 028',tree(('vendor-private','Fantezi Çorap')),'lingerie','tights',platform='hepsiburada')
 def test_different_platform_ids_are_not_trendyol_ids(self):
  self.check_type('Metal Anal Plug',tree((3097,'Anal Oyuncak')),'toys','plugs',platform='hepsiburada')
 def test_gifts_do_not_steal_other_product_types(self):
  self.check_type('Çiftlere Hediye Seti',[],'gifts',None)
  self.check_type('Siyah Gecelik Çorap Hediyeli',tree((3110,'Fantezi Gecelik')),'lingerie','chemises')
 def test_unknown_type_requires_review_without_guessed_facts(self):
  result=classify_marketplace('MODEL-123',[])
  self.assertIsNone(result['group']);self.assertTrue(result['needsReview']);self.assertEqual(result['categoryIds'],[])
  self.assertFalse(any(key in result for key in ['stockQuantity','barcode','manufacturer','priceMinor']))
 def test_known_generic_toy_root_remains_broad(self):
  result=self.check_type('Model 123',tree((5240,'Cinsel Oyuncak')),'toys',None)
  self.assertFalse(result['needsReview'])
 def test_generic_lingerie_parent_does_not_invent_costume(self):
  self.check_type('Fantezi İç Giyim',tree((3096,'Fantezi İç Giyim')),'lingerie',None)
  self.check_type('Zarif İç Giyim',tree((3096,'Fantezi İç Giyim')),'lingerie',None)
 def test_titles_are_not_mutated_or_replaced_by_translations(self):
  with self.assertRaises(TypeError):classify_marketplace({'tr':'Boxer','en':'Lingerie and Costumes'},[])
  title='İç Giyim ÖZEL — Şişli';categories=tree((3096,'Fantezi İç Giyim'));copy=[dict(row)for row in categories]
  classify_marketplace(title,categories);self.assertEqual(categories,copy);self.assertEqual(title,'İç Giyim ÖZEL — Şişli')
 def test_all_produced_labels_cover_supported_languages(self):
  from native_marketplace_taxonomy import SUBTYPE_LABELS
  from native_catalog import LANGUAGES,loc
  for key,labels in SUBTYPE_LABELS.items():
   localized=loc(labels);self.assertEqual(set(localized),set(LANGUAGES));self.assertTrue(all(localized.values()))
   self.assertFalse(any('\ufffd'in value for value in localized.values()))
   self.assertEqual(len(SUBTYPE_LABELS[key]),len(LANGUAGES),key)

if __name__=='__main__':unittest.main()
