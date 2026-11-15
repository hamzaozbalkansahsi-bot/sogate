import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {normalizeCatalog} from '../lib/catalog.mjs';

const supplierBrand=/(?:adore(?:\s*mobilya)?|адор[еэ](?:\s+мобил[ьяя])?|[اأإآ]دور(?:ي|ه)?(?:\s+موبيليا)?)/iu;
const locales=['tr','en','ru','ar'];
const source=JSON.parse(await readFile(new URL('../data/catalog-source.json',import.meta.url),'utf8'));

function displayStrings(catalog) {
 const values=[];
 const visit=(value,path)=>{
  if(typeof value==='string')values.push({path,value});
  else if(Array.isArray(value))value.forEach((item,index)=>visit(item,`${path}[${index}]`));
  else if(value&&typeof value==='object')for(const [key,item] of Object.entries(value))visit(item,`${path}.${key}`);
 };
 visit(catalog.brand,'brand');
 catalog.categories.forEach((category,index)=>visit(category.name,`categories[${index}].name`));
 catalog.products.forEach((product,index)=>{for(const key of ['name','description','specs'])visit(product[key],`products[${index}].${key}`);});
 return values;
}

function fixture(brand='Adore Mobilya') {
 return {categories:[{id:'adore-collection',parentId:null,name:brand}],products:[{
  id:'1',code:'ADR-001',title:`${brand} Base Kitaplık 80x100x30 cm`,description:`${brand} 80 x 100 x 30 cm kitaplık.`,
  categoryIds:['adore-collection'],images:['https://witcdn.adoremobilya.com/adore-original-photo.jpg'],
  sourceBrand:'Adore Mobilya',specs:[{label:'Ürün Ölçüleri',value:'80 x 100 x 30 cm'},{label:'Ürün Özellikleri',value:`${brand}\n18 mm Yonga Levha`},{label:'Üretim Yeri',value:'Türkiye'}],
 }],meta:{complete:true}};
}

test('house-brand presentation becomes NODENO across source spellings without dropping specifications',()=>{
 for(const brand of ['Adore Mobilya','ADOREMOBİLYA','Адоре','Адоре Мобиля','أدور موبيليا','آدور']) {
  const raw=fixture(brand),{catalog}=normalizeCatalog(raw),product=catalog.products[0];
  for(const locale of locales){
   assert.match(product.name[locale],/NODENO/,`${brand}: title/${locale}`);
   assert.match(catalog.categories[0].name[locale],/NODENO/,`${brand}: category/${locale}`);
   assert.ok(product.specs.some(row=>row.value[locale].includes('NODENO')),`${brand}: retained technical row/${locale}`);
  }
  assert.deepEqual(displayStrings(catalog).filter(({value})=>supplierBrand.test(value)),[],brand);
 }
});

test('presentation keeps Turkish possessive grammar and does not damage unrelated model words',()=>{
 const raw=fixture();raw.products[0].description="Adore Mobilya'nın 18 mm gövdesi. Adore'de bulunan model.";
 const {catalog}=normalizeCatalog(raw);
 assert.equal(catalog.products[0].description.tr,"NODENO'nun 18 mm gövdesi. NODENO'da bulunan model.");
 const unrelated=fixture();unrelated.products[0].title='Adorable Base Kitaplık';
 assert.match(normalizeCatalog(unrelated).catalog.products[0].name.tr,/Adorable/);
});

test('manufacturer patent attribution is not falsely reassigned while real technical features survive',()=>{
 const catalog=normalizeCatalog(source).catalog,product=catalog.products.find(p=>p.id==='4583');
 const text=product.specs.map(row=>row.value.tr).join('\n');
 for(const fact of ['çelik gövde','karbon fiber','mouse pad','C tipi','USB','yükseklik'])assert.ok(text.includes(fact),fact);
 assert.doesNotMatch(text,/patent/i);
 for(const id of ['4583','4584','4585']){
  const description=catalog.products.find(p=>p.id===id).description.tr;
  assert.doesNotMatch(description,/patent/i,id);
  assert.match(description,/USB/,id);
  assert.match(description,/\d+ x \d+ x \d+ cm/,id);
 }
});

test('normalization preserves input archive, product identities, measurements, country and trusted media origins',()=>{
 const raw=fixture(),before=JSON.stringify(raw),{catalog,media}=normalizeCatalog(raw),product=catalog.products[0];
 assert.equal(JSON.stringify(raw),before);
 assert.equal(product.id,'1');assert.equal(product.code,'ADR-001');
 assert.equal(catalog.categories[0].id,'nodeno-collection');assert.deepEqual(product.categoryIds,['nodeno-collection']);
 assert.deepEqual(media['1'],['https://witcdn.adoremobilya.com/adore-original-photo.jpg']);
 assert.deepEqual(product.images,['/media/1/0']);
 assert.equal(product.specs.find(row=>row.label.tr==='Ürün Ölçüleri').value.tr,'80 x 100 x 30 cm');
 assert.equal(product.specs.find(row=>row.label.tr==='Üretim Yeri').value.tr,'Türkiye');
 assert.equal(product.sourceBrand,undefined);
});

test('all actual public catalog display strings are free of supplier branding in every locale',()=>{
 const before=JSON.stringify(source),{catalog}=normalizeCatalog(source);
 assert.equal(catalog.products.length,667);assert.equal(catalog.categories.length,104);
 assert.deepEqual(displayStrings(catalog).filter(({value})=>supplierBrand.test(value)),[]);
 assert.equal(JSON.stringify(source),before);
 assert.deepEqual(catalog.meta.translationPending,{en:0,ru:0,ar:0});
});

test('public category URLs remove supplier branding while preserving hierarchy and membership counts',()=>{
 const raw=fixture();raw.categories.push({id:'books',name:'Kitaplıklar',parentId:'adore-collection'});raw.products[0].categoryIds.push('books');
 const before=JSON.stringify(raw),{catalog}=normalizeCatalog(raw);
 assert.equal(JSON.stringify(raw),before);
 assert.equal(catalog.categories[1].parentId,'nodeno-collection');
 assert.equal(catalog.categories[0].count,1);
 assert.deepEqual(catalog.products[0].categoryIds,['nodeno-collection','books']);
 const actual=normalizeCatalog(source).catalog;
 assert.equal(new Set(actual.categories.map(c=>c.id)).size,104);
 assert.doesNotMatch(JSON.stringify(actual),/adore/iu);
 assert.ok(actual.categories.some(c=>c.id==='oyuncu-mobilyalari'));
 assert.ok(actual.categories.some(c=>c.id==='tgif-serisi'));
 assert.ok(actual.products.every(p=>p.categoryIds.every(id=>actual.categories.some(c=>c.id===id))));
});
