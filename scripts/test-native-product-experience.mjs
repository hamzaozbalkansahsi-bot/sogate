/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/test-native-product-experience.mjs
 * Açıklama   : Ürün bilgisi, dürüst öneri seçimi ve sayfa içi iade HTML'sini denetler.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {productDiscovery,productFacts,productStory,visibleProducts} from '../native-store/storefront/product-experience-core.js';
import {renderProductExplore,renderProductStory,renderProductFeatures,renderProductNavigation,renderProductReturns} from '../native-store/storefront/product-experience-renderers.js';
const localPhp=fileURLToPath(new URL('../.local/php-runtime/php.exe',import.meta.url));
const phpBinary=process.env.PHP_BINARY||(process.platform==='win32'&&fs.existsSync(localPhp)?localPhp:'php');
const copy=JSON.parse(fs.readFileSync(new URL('../native-store/storefront/product-experience-copy.json',import.meta.url),'utf8'));
const categories=[{id:'root',name:{tr:'İç Giyim'},parentId:null},{id:'night',name:{tr:'Gecelikler'},parentId:'root'},{id:'costume',name:{tr:'Kostümler'},parentId:'root'},{id:'empty',name:{tr:'Boş'},parentId:null}];
const make=(id,category='night',extra={})=>({id,code:'seo-'+id,name:{tr:'Dantel detaylı model '+id},brand:'JUBELS',images:['/media/'+id+'/0'],categoryIds:['root',category],...extra});
const selected=make('one'),products=[selected,make('two'),make('three'),make('four'),make('five','costume'),make('six','costume'),make('seven','costume'),make('hidden','night',{hidden:true}),make('draft','night',{published:false}),make('no-photo','night',{images:[]}),make('duplicate','night',{modelId:'two'})];
const catalog={products,categories};let passed=0;const check=(name,run)=>{run();passed++;};
const escape=v=>String(v).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const href=(page,params={})=>'/test/?'+new URLSearchParams({page,lang:'tr',...params});
const ctx={catalog,config:{},locale:'tr',esc:escape,href,copy:copy.tr,factLabels:{materials:'Malzeme',sizes:'Beden seçenekleri'},image:p=>'<img src="/test/media/'+escape(p.id)+'/0" alt="">',productCard:p=>'<article data-product="'+escape(p.id)+'">'+escape(p.code)+'</article>',recent:[]};
check('only actual public photographed unique products',()=>assert.deepEqual(visibleProducts(products).map(p=>p.id),['one','two','three','four','five','six','seven']));
check('original data never mutated',()=>{const original=JSON.stringify(catalog);productDiscovery(selected,catalog,{});assert.equal(JSON.stringify(catalog),original);});
check('selected item is never recommended to itself',()=>{const m=productDiscovery(selected,catalog,{});for(const key of ['similar','complementary','selection','popular'])assert(!m[key].some(p=>p.id==='one'));});
check('no claimed popularity without actual source metrics',()=>{const m=productDiscovery(selected,catalog,{productPopularity:{source:'supplier-sold',asOf:'2026-11-17',counts:{two:999}}});assert.equal(m.hasPopularity,false);assert.equal(m.popular.length,0);});
check('actual defined order metric orders known public ids',()=>{const m=productDiscovery(selected,catalog,{productPopularity:{source:'fulfilled-order-lines',asOf:'2026-11-17',counts:{two:2,three:7,unknown:100,draft:200,hidden:300}}});assert.equal(m.hasPopularity,true);assert.deepEqual(m.popular.map(p=>p.id),['three','two']);});
check('non-integer or non-positive metric cannot create popularity',()=>{const m=productDiscovery(selected,catalog,{productPopularity:{source:'fulfilled-order-lines',asOf:'2026-11-17',counts:{two:1.5,three:0,four:-2}}});assert.equal(m.hasPopularity,false);});
check('collection cards all have actual 3-product mosaics and counts',()=>{const m=productDiscovery(selected,catalog,{});assert(m.collections.length>=2);for(const group of m.collections){assert.equal(group.products.length,3);assert(group.count>=3);assert(group.params.category);assert(group.products.every(p=>!p.hidden&&p.published!==false&&p.images.length));}});
check('empty and unknown discovery links are absent',()=>{const m=productDiscovery(selected,catalog,{});assert(!m.links.some(p=>p.params.category==='empty'));assert(m.links.every(p=>p.params.category||p.params.brand));});
check('CMS collection filters hidden product and handles actual title',()=>{const m=productDiscovery(selected,catalog,{collections:[{id:'curated',data:{enabled:true,title:'Bordo seçkisi',productIds:'one,two,three,hidden'}}]});assert.equal(m.collections[0].id,'curated');assert.equal(m.collections[0].count,3);assert.equal(m.collections[0].title,'Bordo seçkisi');});
check('recent excludes missing private duplicate and current',()=>{const m=productDiscovery(selected,catalog,{},['unknown','hidden','one','two','two','three']);assert.deepEqual(m.recent.map(p=>p.id),['two','three']);});
check('real facts, decimal numbers and Turkish characters remain',()=>{const facts=productFacts({...selected,storefrontFacts:{materials:'Polyester',sizes:'S/M, L/XL',dimensions:'2,6 cm'},specs:[{label:{tr:'Malzeme'},value:{tr:'Polyester'}}]},'tr',ctx.factLabels);assert.equal(facts.length,3);assert.equal(facts.find(v=>v.id==='dimensions').value,'2,6 cm');});
check('enriched translated source fields take precedence and SKU stays outside highlights',()=>{const facts=productFacts({...selected,storefrontStory:{en:{fields:[{key:'colors',title:'Colour options',value:'yellow'},{key:'composition',title:'Material composition',value:'95% polyester, 5% elastane'},{key:'productCode',title:'Product code',value:'seo-one'}]}},storefrontFacts:{colors:'Sarı'}},'en',{colors:'Colour options'});assert.deepEqual(facts,[{id:'colors',label:'Colour options',value:'yellow'},{id:'composition',label:'Material composition',value:'95% polyester, 5% elastane'}]);});
check('story preserves paragraphs and removes exact intro duplication',()=>{const p={...selected,description:{tr:'Giriş.\n\nÖlçü 2,6 cm.\n\nİğne oyası detayı.'},storefrontStory:{tr:{intro:'Giriş.'}}};const story=productStory(p,'tr');assert.deepEqual(story.paragraphs,['Ölçü 2,6 cm.','İğne oyası detayı.']);});
check('source paragraph is visible HTML and expands with native details',()=>{const html=renderProductStory({...selected,storefrontStory:{tr:{intro:'İlk paragraf.',paragraphs:['Kaynakta verilen ikinci paragraf.'],bullets:['Gerçek özellik']}}},ctx);assert(html.includes('sg-product-story'));assert(html.includes('<details'));assert(html.includes('Kaynakta verilen ikinci paragraf.'));assert(html.includes('Devamını gör'));});
check('empty continuation control is not displayed',()=>assert(!renderProductStory({...selected,description:{tr:'Yalnız gerçek giriş.'}},ctx).includes('<details')));
check('all product prose is escaped',()=>{const html=renderProductStory({...selected,storefrontStory:{tr:{intro:'<img onerror=alert(1)>',paragraphs:['<script>bad()</script>']}}},ctx);assert(!html.includes('<script>'));assert(html.includes('&lt;script&gt;'));});
check('full features keep real SKU without exposing pricing internals',()=>{const html=renderProductFeatures({...selected,privateRetailReference:12345,storefrontFacts:{materials:'Polyester'}},ctx);assert(html.includes('seo-one'));assert(!html.includes('12345'));assert(html.includes('id="sg-all-features"'));});
check('return navigation stays on product and uses source policy objects',()=>{const html=renderProductNavigation(selected,ctx)+renderProductReturns(selected,{...ctx,returnPolicy:{title:'İade ve iptal',items:[{title:'Koruyucu unsur',body:'Gerçek politika özeti.'}]}});assert(html.includes('href="#product-faq"'));assert(!html.includes('page=help'));assert(html.includes('Gerçek politika özeti.'));assert(!html.includes('[object Object]'));});
check('feedback is an accessible real product action',()=>{const html=renderProductExplore(selected,ctx);assert(html.includes('data-sg-feedback="one"'));assert(html.includes('Geri bildirim ver'));assert(html.includes('id="product-shelf-productSimilar"'));assert(html.includes('id="product-shelf-productComplementary"'));assert(!html.includes('Popüler ürünler'));assert(html.includes('Seçili ürünler'));});
check('all supported language copies are complete and text only',()=>{assert.equal(Object.keys(copy).length,11);for(const locale of Object.keys(copy))assert(Object.values(copy[locale]).every(v=>typeof v==='string'&&v.trim()&&!/<[^>]+>/u.test(v)));});
check('PHP first HTML and client select the identical discovery model',()=>{const script=fileURLToPath(new URL('test-native-product-experience.php',import.meta.url));const server=JSON.parse(execFileSync(phpBinary,[script,'--model-json'],{encoding:'utf8'}));assert.deepEqual(server,productDiscovery(selected,catalog,{}));});
console.log(JSON.stringify({passed,realProviderCalled:false,sourceSnapshotChanged:false}));
