import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {seoPage,seoRobots,seoSitemap,seoDocument} from '../lib/seo.mjs';

const name={tr:'Dolap',en:'Cabinet',ru:'Шкаф',ar:'خزانة'};
const catalog={brand:{name:'NODENO'},meta:{mediaVersion:'a'.repeat(64)},categories:[{id:'storage',parentId:null,name}],products:[
 {id:'p1',code:'NDN-001',modelId:'model-one',modelName:name,name,description:{tr:'Ahşap dolap',en:'Wood cabinet',ru:'Деревянный шкаф',ar:'خزانة خشبية'},variantColor:{tr:'Beyaz',en:'White',ru:'Белый',ar:'أبيض'},images:['/media/p1/0'],categoryIds:['storage'],salePriceMinor:12345,currency:'TRY',availability:'unknown',specs:[]},
 {id:'p2',code:'NDN-002',modelId:'model-one',modelName:name,name,description:{en:'Wood cabinet'},variantColor:{tr:'Meşe',en:'Oak',ru:'Дуб',ar:'بلوط'},images:['/media/p2/0'],categoryIds:['storage'],salePriceMinor:15000,currency:'TRY',availability:'unknown',specs:[]}
]};
const config={brand:{name:'NODENO',domain:'nodenohome.com',website:'https://nodenohome.com',slogan:{tr:'İyi tasarım. Kolay yaşam.',en:'Good design. Easy living.'}},contactEmail:'info@nodenohome.com',contactPhoneUri:'tel:+908503058478',checkoutEnabled:false};
const url=path=>new URL('https://nodenohome.com'+path);

test('published SEO settings are escaped and empty categories or curated filters are not indexed',()=>{
 const custom={...config,seo:{homeTitle_tr:'Ev için NODENO',homeDescription_tr:'Doğrulanmış açıklama',googleVerification:'test"value'}};
 const page=seoPage(catalog,custom,url('/?lang=tr'));assert.equal(page.title,'Ev için NODENO | NODENO');const html=seoDocument('<html><head></head><body><main id="page"></main></body></html>',page);assert.ok(html.includes('google-site-verification'));assert.ok(html.includes('test&quot;value'));
 assert.equal(seoPage({...catalog,products:[]},config,url('/?page=catalog&category=storage')).indexable,false);
 assert.equal(seoPage(catalog,config,url('/?page=catalog&collection=curated')).indexable,false);
});

test('published hero selection is present before JavaScript in each runtime',()=>{
 const altered={...config,appearance:{enabled:true,heroProductId:'p2',heroTitle_en:'A better space',heroBody_en:'Useful storage for home'}};const page=seoPage(catalog,altered,url('/?lang=en'));assert.ok(page.body.includes('/media/p2/0'));assert.ok(page.body.includes('A better space'));assert.ok(page.body.includes('Useful storage for home'));
});

test('product initial HTML, canonical, reciprocal locales and variant data use actual visible facts',()=>{
 for(const locale of ['tr','en','ru','ar']){
  const page=seoPage(catalog,config,url('/?product=p1&lang='+locale));
  assert.equal(page.status,200);assert.equal(page.locale,locale);assert.equal(page.canonical,'https://nodenohome.com/?lang='+locale+'&product=p1');
  assert.deepEqual(page.alternates.map(row=>row.locale),['tr','en','ru','ar','de','az','kk','tk','uz','ky','fa','x-default']);
  assert.ok(page.body.includes(name[locale]));assert.ok(page.body.includes('/media/p1/0'));assert.ok(page.body.includes('NDN-001'));
  const encoded=JSON.stringify(page.jsonld);assert.ok(encoded.includes('ProductGroup'));assert.ok(encoded.includes('NDN-002'));assert.ok(encoded.includes('123.45'));
  assert.ok(!encoded.includes('InStock'));assert.ok(!encoded.includes('aggregateRating'));assert.ok(!encoded.includes('shippingRate'));
 }
});

test('unknown products and categories return 404 while private or faceted routes cannot be indexed',()=>{
 for(const query of ['?product=missing','?page=catalog&category=missing'])assert.equal(seoPage(catalog,config,url('/'+query)).status,404);
 for(const query of ['?page=cart','?page=account','?page=orders','?page=collections','?page=catalog&q=secret','?page=catalog&minPrice=1','?page=catalog&sort=price-asc'])assert.equal(seoPage(catalog,config,url('/'+query)).indexable,false,query);
 assert.equal(seoPage(catalog,config,url('/?page=catalog&category=storage&lang=en')).indexable,true);
});

test('SEO output escapes markup and never trusts a request host or fragment as canonical',()=>{
 const hostile=structuredClone(catalog);hostile.products[0].modelName.en='</script><img src=x onerror=alert(1)>';
 const page=seoPage(hostile,config,new URL('https://attacker.invalid/?lang=en&product=p1#fake'));
 const html=seoDocument('<html lang="tr"><head><title>Old</title><meta name="description" content="Old"></head><body><main id="page" tabindex="-1">Loading</main></body></html>',page);
 assert.ok(!html.includes('attacker.invalid'));assert.ok(!html.includes('<img src=x'));assert.ok(html.includes('rel="canonical"'));assert.ok(html.includes('lang="en"'));
 assert.equal((html.match(/name="description"/g)||[]).length,1);assert.ok(html.includes('application/ld+json'));
});

test('product canonical ignores unrelated category context',()=>{
 assert.equal(seoPage(catalog,config,url('/?lang=en&product=p1&category=storage')).canonical,'https://nodenohome.com/?lang=en&product=p1');
});
test('price eligibility matches storefront limits',()=>{
 const oversized=structuredClone(catalog);oversized.products[0].salePriceMinor=Number.MAX_SAFE_INTEGER;
 const selected=seoPage(oversized,config,url('/?product=p1')).jsonld.find(row=>row['@type']==='Product');
 assert.equal(selected.sku,'NDN-001');assert.equal(selected.offers,undefined);
});

test('sitemaps expose real canonical products in each language and robots permits approved image discovery',()=>{
 const robots=seoRobots();assert.ok(robots.includes('Sitemap: https://nodenohome.com/sitemap.xml'));assert.ok(!robots.includes('Disallow: /media/'));assert.ok(robots.includes('Disallow: /api/'));
 const index=seoSitemap(catalog,config,'index');assert.ok(index.includes('sitemap-products-en.xml'));
 const products=seoSitemap(catalog,config,'products','en');assert.ok(products.includes('?lang=en&amp;product=p1'));assert.ok(products.includes('image:image'));assert.ok(!products.includes('<lastmod>'));assert.ok(!products.includes('page=cart'));
 const hidden=structuredClone(catalog);hidden.products[0].published=false;assert.ok(!seoSitemap(hidden,config,'products','en').includes('product=p1'));
});

test('PHP and JavaScript metadata agree on locale, canonical, status, price and private page policy',()=>{
 const php=process.env.NODENO_PHP||fileURLToPath(new URL('../artifacts/runtime-php/php.exe',import.meta.url));
 const cases=['?product=p1&lang=ar','?product=p1&category=storage&lang=en','?page=catalog&category=storage&lang=en','?product=missing','?page=cart'];
 for(const query of cases){
  const child=spawnSync(php,['tests/fixtures/seo-runtime.php'],{input:JSON.stringify({catalog,config,query}),encoding:'utf8'});assert.equal(child.status,0,child.stderr);
  const actual=JSON.parse(child.stdout),want=seoPage(catalog,config,url('/'+query));
  for(const field of ['locale','canonical','status','indexable'])assert.deepEqual(actual[field],want[field],field+query);
  if(query.includes('product=p1')){assert.ok(JSON.stringify(actual.jsonld).includes('123.45'));assert.ok(actual.body.includes(name[new URL('https://nodenohome.com/'+query).searchParams.get('lang')||'tr']));}
 }
});


test('organization associates canonical social profiles in server and browser metadata',()=>{
 const socials=[{url:'https://www.instagram.com/nodeno_home/'},{url:'https://x.com/nodenohome'},{url:'https://x.com/nodenohome'}],c={...config,socials};
 const browser=seoPage(catalog,c,url('/?lang=tr')).jsonld.find(x=>x['@type']==='Organization');
 assert.deepEqual(browser.sameAs,[socials[0].url,socials[1].url]);
 const php=fileURLToPath(new URL('../artifacts/runtime-php/php.exe',import.meta.url));const fixture=fileURLToPath(new URL('./fixtures/seo-runtime.php',import.meta.url));
 const result=spawnSync(php,[fixture],{input:JSON.stringify({catalog,config:c,query:'lang=tr'}),encoding:'utf8'});assert.equal(result.status,0,result.stderr);
 assert.deepEqual(JSON.parse(result.stdout).jsonld.find(x=>x['@type']==='Organization').sameAs,browser.sameAs);
});
