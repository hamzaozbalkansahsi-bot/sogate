"""PHP SEO regressions for the expanded catalogue and actual supplier variations."""
from pathlib import Path
import json,subprocess,unittest
R=Path(__file__).resolve().parents[1]
def loc(text):return dict.fromkeys(['tr','en','ru','ar'],text)
def item(id,**extra):return {'id':id,'code':'ND-'+id,'name':loc('Wood trim '+id),'modelName':loc('Wood trim '+id),'description':loc('Unfinished wood for furniture projects.'),'categoryIds':['wood'],'images':['/assets/suppliers/'+'a'*64+'.png'],'productType':'supplier-item','currency':'TRY','salePriceMinor':12000,'saleUnit':'piece','variantColor':loc(''),'specs':[],**extra}
class CatalogSeoTests(unittest.TestCase):
 def page(self,rows,query,config=None):
  catalog={'products':rows,'categories':[{'id':'wood','name':loc('Wood components'),'parentId':None}],'meta':{}}
  code="require 'hosting/seo.php';$d=json_decode(stream_get_contents(STDIN),true);echo json_encode(nodenoSeoPage($d['catalog'],$d['config'],$d['query']),JSON_UNESCAPED_UNICODE);"
  run=subprocess.run([str(R/'artifacts/runtime-php/php.exe'),'-r',code],cwd=R,input=json.dumps({'catalog':catalog,'query':query,'config':config or{}}).encode(),capture_output=True);self.assertEqual(run.returncode,0,run.stderr);return json.loads(run.stdout)
 def test_descriptive_home_metadata_keeps_the_actual_hero_slogan(self):
  titles={'tr':'Mobilya ve ahşap ürünler','en':'Furniture and wooden components','ru':'Мебель и деревянные комплектующие','ar':'أثاث ومكونات خشبية'}
  for lang,title in titles.items():
   config={'brand':{'slogan':loc('Good design. Easy living.')}};p=self.page([item('a')],{'lang':lang},config);self.assertEqual(p['title'],title+' | NODENO');self.assertIn('Good design. Easy living.</h1>',p['body']);self.assertIn('MDF'if lang in ['tr','en','ar']else'МДФ',p['description'])
   config['seo']={'homeTitle_'+lang:'Custom title','homeDescription_'+lang:'Custom description'};custom=self.page([item('a')],{'lang':lang},config);self.assertEqual(custom['title'],'Custom title | NODENO');self.assertEqual(custom['description'],'Custom description')
 def test_code_only_search_title_uses_real_category_without_renaming_the_product(self):
  p=self.page([item('code',name=loc('AP1089'),modelName=loc('AP1089'),description=loc('AP1089'))],{'product':'code','lang':'en'});self.assertEqual(p['title'],'AP1089 - Wood components | NODENO');self.assertIn('Wood components',p['description']);self.assertEqual(next(x for x in p['jsonld']if x['@type']=='Product')['name'],'AP1089');self.assertIn('>AP1089</h1>',p['body'])
 def test_pages_make_all_records_crawlable_with_self_canonical(self):
  rows=[item(str(i))for i in range(25)];first=self.page(rows,{'lang':'en','page':'catalog','category':'wood'});second=self.page(rows,{'lang':'en','page':'catalog','category':'wood','pg':'2'})
  self.assertIn('pg=2',first['body']);self.assertIn('product=0',first['body']);self.assertNotIn('product=24',first['body']);self.assertIn('product=24',second['body']);self.assertTrue(second['indexable']);self.assertTrue(second['canonical'].endswith('&pg=2'));self.assertTrue(all('pg=2'in a['url']for a in second['alternates']));self.assertNotEqual(first['title'],second['title'])
  listing=next(x for x in second['jsonld']if x['@type']=='CollectionPage');self.assertEqual(listing['mainEntity']['numberOfItems'],1);self.assertEqual(listing['mainEntity']['itemListElement'][0]['position'],25)
 def test_invalid_and_out_of_range_pagination_is_not_a_soft_404(self):
  for pg in ['0','-2','2x','9999999999999999999999999','2']:
   page=self.page([item('a')],{'page':'catalog','pg':pg});self.assertEqual(page['status'],404,pg);self.assertFalse(page['indexable']);self.assertIsNone(page['canonical'])
  self.assertNotIn('pg=',self.page([item('a')],{'page':'catalog','pg':'1'})['canonical'])
  categories=self.page([item('a')],{'page':'categories','pg':'2'});self.assertEqual(categories['status'],200);self.assertFalse(categories['indexable']);self.assertNotIn('pg=',categories['canonical'])
 def test_singleton_is_product_and_does_not_claim_colour_variants(self):
  page=self.page([item('a')],{'product':'a','lang':'en'});selected=next(x for x in page['jsonld']if x['@type']=='Product');self.assertEqual(selected['sku'],'ND-a');self.assertFalse(any(x['@type']=='ProductGroup'for x in page['jsonld']))
 def test_real_material_choices_and_unselected_parent_are_not_fake_colours(self):
  def variant(id,wood):return item(id,modelId='family',specs=[{'label':loc('Ağaç cinsi'),'value':loc(wood)}],variantLabel=loc(wood))
  rows=[item('parent',modelId='family',variationSelectionRequired=True),variant('pine','Pine'),variant('beech','Beech')];page=self.page(rows,{'product':'pine','lang':'en'});group=next(x for x in page['jsonld']if x['@type']=='ProductGroup');self.assertEqual(group['variesBy'],['https://schema.org/material']);self.assertEqual(len(group['hasVariant']),2);self.assertNotIn('color',group['hasVariant'][0]);self.assertEqual(group['hasVariant'][0]['material'],'Pine');self.assertIn('Pine',page['description'])
  selected=next(x for x in page['jsonld']if x['@type']=='Product');self.assertEqual(selected['isVariantOf']['@id'],group['@id']);self.assertNotIn('Colour:',page['body']);self.assertIn('Product option',page['body'])
 def test_unknown_units_do_not_become_unconditional_offers(self):
  page=self.page([item('a',saleUnit='quote')],{'product':'a'});selected=next(x for x in page['jsonld']if x['@type']=='Product');self.assertNotIn('offers',selected);self.assertNotIn('availability',selected)
  measured=self.page([item('m',saleUnit='metre',quantityPolicy={'minimum':3,'step':3},salePriceMinor=10200)],{'product':'m'});self.assertNotIn('offers',next(x for x in measured['jsonld']if x['@type']=='Product'))
 def test_actual_packaged_brand_matches_the_visible_product_and_is_escaped(self):
  for brand in ['APEL','APEL <tag>']:
   page=self.page([item('glue',productBrand=brand)],{'product':'glue'});selected=next(x for x in page['jsonld']if x['@type']=='Product');self.assertEqual(selected['brand']['name'],brand);self.assertNotIn('<tag>',page['body']);self.assertIn('APEL',page['body'])
 def test_sitemap_pagination_and_image_versions_are_stable_and_owned(self):
  code="require 'hosting/seo.php';$d=json_decode(stream_get_contents(STDIN),true);echo json_encode(['xml'=>nodenoSeoSitemap($d,[],'pages','en'),'robots'=>nodenoSeoRobots(),'static'=>nodenoSeoImages($d['products'][0],$d),'door'=>nodenoSeoImages($d['door'],$d)]);"
  catalog={'products':[item(str(i))for i in range(25)],'categories':[{'id':'wood','name':loc('Wood components')}],'meta':{'mediaVersion':'b'*64,'doorCatalogVersion':'c'*64},'door':item('door',productType='door',images=['/media/door/0'])};run=subprocess.run([str(R/'artifacts/runtime-php/php.exe'),'-r',code],cwd=R,input=json.dumps(catalog).encode(),capture_output=True);self.assertEqual(run.returncode,0,run.stderr);data=json.loads(run.stdout)
  self.assertIn('page=catalog&amp;pg=2',data['xml']);self.assertNotIn('page=categories&amp;pg=2',data['xml']);self.assertNotIn('?',data['static'][0]);self.assertTrue(data['door'][0].endswith('?v='+'c'*64));self.assertIn('Allow: /api/catalog$',data['robots']);self.assertIn('Allow: /api/supplier-products/',data['robots']);self.assertIn('Disallow: /api/',data['robots'])
if __name__=='__main__':unittest.main()
