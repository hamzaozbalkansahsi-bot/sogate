import test from 'node:test';
import assert from 'node:assert/strict';
import {normalizeCatalog} from '../lib/catalog.mjs';
const source={products:[{id:'1',code:'ABC-001',title:'Base Kitaplık',description:'Gerçek ürün açıklaması.',categoryIds:['books'],images:['https://witcdn.adoremobilya.com/real.jpg'],retailPrice:1234,currency:'TRY',sourceAvailability:'InStock',specs:[{label:'Ürün Ölçüleri',value:'80 x 100 x 30 cm'}]}],categories:[{id:'home',name:'Ev',parentId:null},{id:'books',name:'Kitaplıklar',parentId:'home'}],meta:{generatedAt:'2026-10-31',complete:true}};
test('normalizer keeps source identity while masking supplier media and prices',()=>{
 const {catalog,media}=normalizeCatalog(source);
 const p=catalog.products[0];
 assert.equal(p.code,'ABC-001'); assert.equal(p.salePrice,null); assert.equal(p.availability,'unknown');
 assert.equal(p.retailPrice,undefined); assert.equal(p.sourceAvailability,undefined);
 assert.deepEqual(p.images,['/media/1/0']); assert.equal(media['1'][0],'https://witcdn.adoremobilya.com/real.jpg');
 assert.equal(p.description.tr,'Gerçek ürün açıklaması.');
});
test('category counts include descendants and parent cycles never hang',()=>{
 const {catalog}=normalizeCatalog(source);
 assert.equal(catalog.categories.find(c=>c.id==='home').count,1);
 assert.equal(catalog.categories.find(c=>c.id==='books').count,1);
 const cyclic={...source,categories:[{id:'books',name:'Kitaplıklar',parentId:'home'},{id:'home',name:'Ev',parentId:'books'}]};
 assert.equal(normalizeCatalog(cyclic).catalog.products.length,1);
});
test('unsafe media cannot become a published proxy target',()=>{
 const bad={...source,products:[{...source.products[0],images:['https://127.0.0.1/secret']}]};
 const {catalog,report}=normalizeCatalog(bad);
 assert.deepEqual(catalog.products[0].images,[]);
 assert.equal(report.productsMissingImages,1);
});
test('duplicate IDs and missing codes fail instead of hiding catalog loss',()=>{
 assert.throws(()=>normalizeCatalog({...source,products:[...source.products,...source.products]}),/duplicate/i);
 assert.throws(()=>normalizeCatalog({...source,products:[{...source.products[0],code:''}]}),/code/i);
});
test('every published product has native locale labels and no inherited price',()=>{
 const {catalog}=normalizeCatalog(source);
 for(const lang of ['tr','en','ru','ar']) {
  assert.ok(catalog.products[0].name[lang]);
  assert.ok(catalog.products[0].description[lang]);
  assert.ok(catalog.products[0].specs[0].label[lang]);
 }
 assert.equal(catalog.meta.productCount,1);
});
test('supplier shipping warranty and price promises never become NODENO descriptions',()=>{
 const unsafe={...source,products:[{...source.products[0],description:'Garanti Süresi:7 Yıl. Siparişleriniz 2 iş günü içerisinde kargoya teslim edilmektedir. 0850 346 85 85',specs:[...source.products[0].specs,{label:'Ürün Özellikleri',value:'Ücretsiz kargo ve 7 yıl garanti.'},{label:'Teslimat Bilgisi',value:'İki günde teslimat'},{label:'Ürün Özellikleri',value:'Türkiye’de ilk ve sadece Adore Mobilya’da'},{label:'Ürün Özellikleri',value:'Sadece mağazalarımızda satılmaktadır.'}]}]};
 const {catalog}=normalizeCatalog(unsafe);
 const p=catalog.products[0];
 assert.doesNotMatch(JSON.stringify(p),/0850|7 Yıl|2 iş günü|Ücretsiz kargo|İki günde teslimat/);
 assert.ok(p.description.tr.includes('ABC-001'));
 assert.equal(p.specs.length,1);
 assert.ok(p.specs[0].value.tr.includes('80 x 100 x 30'));
});
