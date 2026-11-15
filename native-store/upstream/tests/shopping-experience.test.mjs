import test from 'node:test';
import assert from 'node:assert/strict';
import {rankProductSearch,searchCategoryMatches,rememberSearch} from '../web/catalog-search.js';
import {numericDimensions} from '../web/product-specs.js';
import {filterProducts} from '../web/shop-core.js';
import {fitAssessment,parseSpaceMeasure,comparisonIds,comparisonRows,replaceCartVariant,favoritesToCart,validateCollections,mergeCollectionLists} from '../web/shopping-core.js';
const dims=value=>[{label:{tr:'Ürün Ölçüleri'},value:{tr:value,en:value,ru:value,ar:value}}];
const p=(id,name,color,price=10000,model=id)=>({id,modelId:model,code:'Ndn-ADR-'+id+'-BB-1',modelName:{tr:name,en:name},name:{tr:name,en:name},variantColor:{tr:color,en:color},currency:'TRY',salePriceMinor:price,specs:dims('90 x 120 x 40 cm (Genişlik x Yükseklik x Derinlik)')});
const products=[p('520','Çok Amaçlı Dolap','Beyaz',10000,'cabinet'),p('521','Çok Amaçlı Dolap','Meşe',11000,'cabinet'),p('700','Dekoratif Kitaplık','Beyaz',20000),p('900','Çalışma Masası','Ceviz',30000)];

test('catalogue combines ranked queries and conservative explicit dimensional bounds, with unknown dimensions excluded only for an active axis',()=>{
 const adjustable={...products[0],id:'adjustable',specs:dims('80-100 x 120 x 40 cm (GxYxD)')},unknown={...products[1],id:'unknown',specs:dims('90 x 120 x 40 cm')};
 const list=[...products,adjustable,unknown];
 assert.deepEqual(filterProducts(list,{query:'beyaz dolap',maxWidth:95,maxHeight:120,maxDepth:40}).map(p=>p.id),['520']);
 assert.equal(filterProducts(list,{maxWidth:100}).some(p=>p.id==='adjustable'),true);
 assert.equal(filterProducts(list,{maxWidth:95}).some(p=>p.id==='adjustable'),false);
 assert.equal(filterProducts(list).some(p=>p.id==='unknown'),true);
 assert.equal(filterProducts(list,{maxDepth:40}).some(p=>p.id==='unknown'),false);
 assert.equal(filterProducts(list,{maxWidth:89}).length,0);
});
test('search recognizes compact product codes, folded Turkish words and all query terms without mutating products',()=>{
 assert.equal(rankProductSearch(products,'ADR 520 BB 1','tr')[0].id,'520');
 assert.deepEqual(rankProductSearch(products,'calisma ceviz','tr').map(p=>p.id),['900']);
 assert.deepEqual(rankProductSearch(products,'beyaz dolap','tr').map(p=>p.id),['520']);
 assert.deepEqual(products.map(p=>p.id),['520','521','700','900']);
});
test('controlled typo tolerance handles one missing/transposed letter but never guesses numeric codes',()=>{
 assert.equal(rankProductSearch(products,'kitaplk','tr')[0].id,'700');
 assert.equal(rankProductSearch(products,'dloap meşe','tr')[0].id,'521');
 assert.deepEqual(rankProductSearch(products,'ADR 529 BB 1','tr'),[]);
 assert.deepEqual(rankProductSearch(products,'masa beyaz','tr'),[]);
});
test('category search is localized and search history is bounded, deduplicated and excludes contact-like input',()=>{
 const categories=[{id:'work',name:{tr:'Çalışma odası',en:'Study room'}},{id:'hall',name:{tr:'Antre',en:'Hallway'}}];
 assert.equal(searchCategoryMatches(categories,'study','en')[0].id,'work');
 assert.deepEqual(rememberSearch(['dolap','kitaplık'],' dolap '),['dolap','kitaplık']);
 assert.deepEqual(rememberSearch(['dolap'],'person@example.com'),['dolap']);
 assert.deepEqual(rememberSearch(['dolap'],'08503058478'),['dolap']);
 assert.equal(rememberSearch(Array.from({length:10},(_,i)=>'ürün '+i),'masa').length,6);
});
test('numeric dimensions preserve explicit axes and adjustable intervals without guessing axis order',()=>{
 const data=numericDimensions(dims('91,5 x 90–110 x 37 cm (GxYxD)'));assert.deepEqual(data.width,{min:91.5,max:91.5});assert.deepEqual(data.height,{min:90,max:110});
 assert.deepEqual(numericDimensions(dims('90 x 120 x 40 cm (YxGxD)')),{width:null,height:null,depth:null});
 for(const raw of ['','-1','1e3','12.123','Infinity','10001'])assert.equal(parseSpaceMeasure(raw),null);
 assert.equal(parseSpaceMeasure(' 91,50 '),91.5);
});
test('fit outcomes distinguish proven fit, insufficient space, adjustable uncertainty and missing measurements',()=>{
 assert.equal(fitAssessment(products[0],{width:90,height:120,depth:40}).status,'fits');
 assert.equal(fitAssessment(products[0],{width:89,height:130,depth:50}).status,'tooLarge');
 assert.equal(fitAssessment({...products[0],specs:dims('90 x 90-110 x 40 cm (GxYxD)')},{width:100,height:100,depth:50}).status,'check');
 assert.equal(fitAssessment({...products[0],specs:[]},{width:100,height:100,depth:50}).status,'unknown');
});
test('comparison is variant aware, uses actual prices, includes missing values and filters only equal rows',()=>{
 assert.deepEqual(comparisonIds('520,520,700,missing,521,900,other',products),['520','700','521','900']);
 const rows=comparisonRows([products[0],products[1]],'tr');assert.deepEqual(rows.find(r=>r.key==='color').values,['Beyaz','Meşe']);
 assert.equal(rows.find(r=>r.key==='width').different,false);assert.equal(rows.find(r=>r.key==='price').different,true);
 const unknown=comparisonRows([products[0],{...products[2],specs:[]}],'en');assert.equal(unknown.find(r=>r.key==='width').values[1],null);
});
test('cart colour change merges same-family SKU quantities and preserves selection without silent clamping',()=>{
 const cart=[{id:'520',quantity:2},{id:'521',quantity:3},{id:'700',quantity:1}];
 const result=replaceCartVariant(cart,'520','521',products,new Set(['520']));
 assert.deepEqual(result.cart,[{id:'521',quantity:5},{id:'700',quantity:1}]);assert.deepEqual([...result.selected],['521']);
 assert.throws(()=>replaceCartVariant([{id:'520',quantity:99},{id:'521',quantity:1}],'520','521',products,new Set()),/quantity_limit/);
 assert.throws(()=>replaceCartVariant(cart,'520','700',products,new Set()),/invalid_variant/);assert.equal(cart[0].quantity,2);
});
test('adding favorites keeps quantities of existing lines and refuses line overflow atomically',()=>{
 const cart=[{id:'520',quantity:99}];assert.deepEqual(favoritesToCart(cart,['520','521','521'],products),[{id:'520',quantity:99},{id:'521',quantity:1}]);
 const many=Array.from({length:101},(_,i)=>p(String(i),'Dolap','Beyaz'));assert.throws(()=>favoritesToCart(many.slice(0,100).map(p=>({id:p.id,quantity:1})),['100'],many),/cart_limit/);
});
test('collections validate real products and limits; merging same IDs is idempotent and keeps target names',()=>{
 const a={id:'a'.repeat(32),name:'Salon',items:['520','700']},b={...a,name:'Yeni ad',items:['521','520']};
 assert.deepEqual(validateCollections([a],products),[a]);assert.deepEqual(mergeCollectionLists([a],[b],products),[{...a,items:['520','700','521']}]);
 assert.deepEqual(mergeCollectionLists(mergeCollectionLists([a],[b],products),[b],products),mergeCollectionLists([a],[b],products));
 assert.throws(()=>validateCollections([{...a,items:['unknown']}],products),/invalid_product/);
 assert.throws(()=>validateCollections([{...a,name:' '}],products),/invalid_collection_name/);
 assert.throws(()=>validateCollections([a,a],products),/invalid_collection/);
 assert.throws(()=>validateCollections(Array.from({length:21},(_,i)=>({...a,id:i.toString(16).padStart(32,'0')})),products),/collections_limit/);
});
