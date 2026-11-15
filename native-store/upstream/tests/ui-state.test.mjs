import test from 'node:test';
import assert from 'node:assert/strict';
import {normalizeCart, filterProducts, categoryFamily, quoteText} from '../web/app.js';

const products = [
  {id:'p1',code:'ND-İ001',name:{tr:'Çalışma Masası',en:'Work desk'},categoryIds:['desks']},
  {id:'p2',code:'ND-002',name:{tr:'Kitaplık',en:'Bookcase'},categoryIds:['storage']}
];
test('restored cart rejects stale products and invalid quantities',()=>{
  assert.deepEqual(normalizeCart([{id:'p1',quantity:4},{id:'removed',quantity:1},{id:'p2',quantity:-3}],products),[{id:'p1',quantity:4}]);
  assert.deepEqual(normalizeCart([{id:'p1',quantity:10000}],products),[{id:'p1',quantity:99}]);
  assert.deepEqual(normalizeCart(null,products),[]);
});
test('search finds Turkish characters and exact product codes',()=>{
  assert.equal(filterProducts(products,{query:'CALISMA',locale:'tr'}).length,1);
  assert.equal(filterProducts(products,{query:'nd-i001',locale:'tr'})[0].id,'p1');
  assert.equal(filterProducts(products,{query:'bookcase',locale:'en'})[0].id,'p2');
});
test('parent category includes children and does not loop through malformed trees',()=>{
  const categories=[{id:'furniture',parentId:null},{id:'desks',parentId:'furniture'},{id:'storage',parentId:'furniture'},{id:'cycle',parentId:'cycle'}];
  assert.deepEqual([...categoryFamily('furniture',categories)],['furniture','desks','storage']);
  assert.equal(filterProducts(products,{category:'furniture',categories}).length,2);
  assert.deepEqual([...categoryFamily('cycle',categories)],['cycle']);
});
test('quote export contains item codes and quantities without invented prices',()=>{
  const output=quoteText([{id:'p1',quantity:3}],products,'en');
  assert.match(output,/ND-İ001/);
  assert.match(output,/3/);
  assert.match(output,/Work desk/);
  assert.doesNotMatch(output,/₺|USD|0\.00/);
});
