import test from 'node:test';
import assert from 'node:assert/strict';
import {seoPage,seoSitemap,seoURL,seoRobots}from'../web/seo-core.js';
import {spawnSync}from'node:child_process';
import path from'node:path';
const text=value=>({tr:value,en:value,ru:value,ar:value});
const photo='/assets/suppliers/'+'b'.repeat(64)+'.jpg';
const item=(id,extra={})=>({id,code:'ND-'+id,name:text('Carved table leg '+id),modelName:text('Carved table leg '+id),modelId:id,productType:'supplier-item',description:text('Carefully shaped wooden furniture component.'),images:[photo],categoryIds:['legs'],currency:'TRY',salePriceMinor:12345,saleUnit:'piece',specs:[{label:text('Sales unit'),value:text('piece')}],...extra});
const catalog=products=>({products,categories:[{id:'legs',parentId:null,name:text('Furniture legs')}],meta:{mediaVersion:'a'.repeat(64)}});
const page=(c,query)=>seoPage(c,{},new URL('https://nodenohome.com/'+query));

test('pagination exposes later products through ordinary links with their own canonicals and alternates',()=>{
 const c=catalog(Array.from({length:51},(_,i)=>item('leg-'+i)));const first=page(c,'?page=catalog&lang=en&category=legs');const second=page(c,'?page=catalog&lang=en&category=legs&pg=2');
 assert.match(first.body,/pg=2/);assert.doesNotMatch(first.body,/product=leg-24"/);assert.match(second.body,/product=leg-24/);assert.doesNotMatch(second.body,/product=leg-0"/);
 assert.equal(second.canonical,'https://nodenohome.com/?lang=en&page=catalog&category=legs&pg=2');assert.ok(second.alternates.every(r=>r.url.includes('pg=2')));assert.equal(second.status,200);assert.equal(second.indexable,true);assert.match(second.title,/Page 2/);
 assert.equal(page(c,'?page=catalog&pg=1').canonical,'https://nodenohome.com/?lang=tr&page=catalog');
 for(const pg of ['0','-1','1.5','x','02','1000000']){const invalid=page(c,'?page=catalog&pg='+pg);assert.equal(invalid.status,404,pg);assert.equal(invalid.canonical,null);assert.equal(invalid.indexable,false);}
 const list=second.jsonld.find(r=>r['@type']==='CollectionPage');assert.equal(list.mainEntity.itemListElement[0].position,25);
 assert.equal(seoURL('catalog','en',{category:'legs',pg:2}),second.canonical);
});

test('supplier variants use real material and size, selected Product, and parent is not a purchasable variant',()=>{
 const base=item('beech',{modelId:'moulding',modelName:text('Door moulding'),name:text('Door moulding'),variantLabel:text('Wood species: Beech / Width: 40 mm'),specs:[{label:{tr:'Ağaç cinsi',en:'Wood species'},value:{tr:'Kayın',en:'Beech'}},{label:{tr:'Genişlik',en:'Width'},value:text('40 mm')}],saleUnit:'metre'});
 const oak=item('oak',{...base,id:'oak',code:'ND-oak',variantLabel:text('Wood species: Oak / Width: 50 mm'),specs:[{label:{tr:'Ağaç cinsi',en:'Wood species'},value:{tr:'Meşe',en:'Oak'}},{label:{tr:'Genişlik',en:'Width'},value:text('50 mm')}]});
 const parent=item('parent',{...base,id:'parent',code:'ND-parent',variationSelectionRequired:true,salePriceMinor:null});const c=catalog([base,oak,parent]);const result=page(c,'?product=beech&lang=en');
 const selected=result.jsonld.find(r=>r['@type']==='Product');assert.equal(selected.sku,'ND-beech');assert.equal(selected.material,'Beech');assert.match(selected.size,/40 mm/);assert.match(result.title,/Beech/);assert.match(result.body,/Wood species: Beech/);
 const group=result.jsonld.find(r=>r['@type']==='ProductGroup');assert.deepEqual(group.variesBy,['https://schema.org/material','https://schema.org/size']);assert.deepEqual(group.hasVariant.map(r=>r.sku),['ND-beech','ND-oak']);assert.doesNotMatch(JSON.stringify(group),/schema.org\/color/);
 assert.notEqual(result.description,page(c,'?product=oak&lang=en').description);assert.ok(!JSON.stringify(group).includes('InStock'));
});

test('singletons do not invent color groups, item brand is preserved and quote units carry no unconditional offer',()=>{
 const c=catalog([item('glue',{productBrand:'APEL',saleUnit:'quote'})]);const result=page(c,'?product=glue&lang=en');const selected=result.jsonld.find(r=>r['@type']==='Product');
 assert.equal(selected.brand.name,'APEL');assert.equal(selected.offers,undefined);assert.equal(result.jsonld.some(r=>r['@type']==='ProductGroup'),false);
 assert.ok(!result.body.includes('Colour: <strong></strong>'));
 const xml=seoSitemap(c,{},'products','en');assert.match(xml,/<image:loc>https:\/\/nodenohome.com\/assets\/suppliers\//);assert.ok(!xml.includes('<lastmod>'));
 c.products=[item('trim',{saleUnit:'metre',salePriceMinor:10200,quantityPolicy:{minimum:3,step:3,unit:'metre'}})];assert.equal(page(c,'?product=trim&lang=en').jsonld.find(r=>r['@type']==='Product').offers,undefined);
});

test('listing sitemap pages and full breadcrumbs expose every catalog level without indexable category pagination',()=>{
 const c=catalog(Array.from({length:51},(_,i)=>item('leg-'+i)));c.categories.unshift({id:'wood',parentId:null,name:text('Wooden components')});c.categories[1].parentId='wood';
 const p=page(c,'?product=leg-0&lang=en');const breadcrumb=p.jsonld.find(r=>r['@type']==='BreadcrumbList');assert.deepEqual(breadcrumb.itemListElement.map(r=>r.name),['Home','Wooden components','Furniture legs','Carved table leg leg-0']);
 const xml=seoSitemap(c,{},'pages','en');assert.match(xml,/category=legs&amp;pg=3/);assert.match(xml,/page=catalog&amp;pg=2/);assert.doesNotMatch(xml,/page=categories&amp;pg=/);
 const duplicate=page(c,'?page=categories&pg=2&lang=en');assert.equal(duplicate.status,200);assert.equal(duplicate.indexable,false);assert.equal(duplicate.canonical,'https://nodenohome.com/?lang=en&page=categories');
});

test('PHP and JavaScript share selected schemas, descriptions, pagination and four-language canonical policy',()=>{
 const base=item('beech',{modelId:'trim',name:text('Beech moulding'),modelName:text('Beech moulding'),variantLabel:text('Wood species: Beech'),specs:[{label:{tr:'Ağaç cinsi',en:'Wood species'},value:text('Beech')}]});const oak=item('oak',{...base,id:'oak',code:'ND-oak',modelName:text('Oak moulding'),name:text('Oak moulding'),variantLabel:text('Wood species: Oak'),specs:[{label:{tr:'Ağaç cinsi',en:'Wood species'},value:text('Oak')}]});const c=catalog([base,oak,...Array.from({length:50},(_,i)=>item('leg-'+i))]);
 for(const lang of ['tr','en','ru','ar'])for(const query of ['?lang='+lang+'&product=beech','?lang='+lang+'&page=catalog&category=legs&pg=2','?lang='+lang+'&page=catalog&pg=0','?lang='+lang+'&page=categories&pg=2']){
  const child=spawnSync(path.resolve('artifacts/runtime-php/php.exe'),['tests/fixtures/seo-runtime.php'],{input:JSON.stringify({catalog:c,config:{},query}),encoding:'utf8'});assert.equal(child.status,0,child.stderr);const actual=JSON.parse(child.stdout),expected=page(c,query);
  for(const field of ['canonical','alternates','status','indexable','title','description','jsonld','image'])assert.deepEqual(actual[field],expected[field],field+' '+query);
 }
});

test('hydrating a full supplier description refreshes SPA metadata without a release or route change',async()=>{
 const originalDocument=globalThis.document,originalLocation=globalThis.location,nodes=[];const c=catalog([item('trim',{modelName:text('Moulding'),name:text('Moulding'),description:text('Moulding')})]);
 globalThis.location={href:'https://nodenohome.com/?lang=en&product=trim',pathname:'/',search:'?lang=en&product=trim'};
 globalThis.document={title:'',documentElement:{lang:'en'},querySelector:()=>null,head:{querySelectorAll:()=>nodes.slice(),append:node=>nodes.push(node)},createElement:tag=>({tag,attributes:{},dataset:{},setAttribute(key,value){this.attributes[key]=value;},remove(){nodes.splice(nodes.indexOf(this),1);}})};
 try{const {updateStoreSEO}=await import('../web/seo-ui.js?hydration-regression');updateStoreSEO(c,{});const description=()=>nodes.find(n=>n.attributes.name==='description').content;const before=description();c.products[0].description=text('Supplied unfinished and unvarnished. Painting is optional.');updateStoreSEO(c,{});assert.notEqual(description(),before);assert.match(description(),/Supplied unfinished/);}finally{globalThis.document=originalDocument;globalThis.location=originalLocation;}
});

test('crawlable public rendering APIs do not grant private API access and image revisions match each media family',()=>{
 const robots=seoRobots();assert.ok(robots.includes('Disallow: /api/'));for(const allowed of ['Allow: /api/catalog$','Allow: /api/catalog?','Allow: /api/config$','Allow: /api/supplier-products/'])assert.ok(robots.includes(allowed));assert.ok(!robots.includes('Allow: /api/accounts/'));
 const c=catalog([item('door',{productType:'door',images:['/media/door/0']})]);c.meta.doorCatalogVersion='d'.repeat(64);const door=page(c,'?product=door&lang=en');assert.equal(door.image,'https://nodenohome.com/media/door/0?v='+'d'.repeat(64));
 c.products=[item('trim')];const supplier=page(c,'?product=trim&lang=en');assert.equal(supplier.image,'https://nodenohome.com'+photo);assert.ok(!supplier.image.includes('?v='));
 const unknown=item('pending',{colorReviewPending:true,variantColor:text('Unreviewed pink')});c.products=[unknown];const pending=page(c,'?product=pending&lang=en');assert.ok(!pending.title.includes('pink'));assert.ok(!pending.description.includes('pink'));assert.equal(pending.jsonld.find(r=>r['@type']==='Product').color,undefined);
});

test('homepage metadata describes the real assortment while the visible hero retains the approved slogan',()=>{
 const c=catalog([item('leg')]),titles={tr:'Mobilya ve ahşap ürünler',en:'Furniture and wooden components',ru:'Мебель и деревянные комплектующие',ar:'أثاث ومكونات خشبية'},slogans={tr:'İyi tasarım. Kolay yaşam.',en:'Good design. Easy living.',ru:'Продуманный дизайн. Простая жизнь.',ar:'تصميم متقن. حياة أسهل.'};
 for(const lang of ['tr','en','ru','ar']){const config={brand:{slogan:slogans}},url=new URL('https://nodenohome.com/?lang='+lang),p=seoPage(c,config,url);assert.equal(p.title,titles[lang]+' | NODENO');assert.ok(p.body.includes('<h1 tabindex="-1">'+slogans[lang]+'</h1>'));assert.match(p.description,/MDF|МДФ/);const custom=seoPage(c,{...config,seo:{['homeTitle_'+lang]:'Custom title',['homeDescription_'+lang]:'Custom description'}},url);assert.equal(custom.title,'Custom title | NODENO');assert.equal(custom.description,'Custom description');}
});

test('code-only models gain factual category context in search metadata without changing their identity',()=>{
 const c=catalog([item('ornament',{name:text('AP1089'),modelName:text('AP1089'),description:text('AP1089')})]);const p=page(c,'?product=ornament&lang=en');assert.equal(p.title,'AP1089 - Furniture legs | NODENO');assert.match(p.description,/AP1089 - Furniture legs/);assert.equal(p.jsonld.find(r=>r['@type']==='Product').name,'AP1089');assert.ok(p.body.includes('<h1 id="product-title" tabindex="-1">AP1089</h1>'));
});
