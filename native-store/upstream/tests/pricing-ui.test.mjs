import test from 'node:test';
import assert from 'node:assert/strict';
import {cartPrices,formatMoney,unitPriceMinor,quoteData,quoteText} from '../web/shop-core.js';

const products=[
 {id:'priced',code:'Ndn-A-1',name:{tr:'Dolap',en:'Cabinet',ru:'Шкаф',ar:'خزانة'},salePriceMinor:1133895,currency:'TRY'},
 {id:'small',code:'Ndn-A-2',name:{tr:'Raf',en:'Shelf',ru:'Полка',ar:'رف'},salePriceMinor:60511,currency:'TRY'},
 {id:'unknown',code:'Ndn-A-3',name:{tr:'Masa',en:'Desk',ru:'Стол',ar:'مكتب'},salePriceMinor:null,currency:null},
];

test('price formatting keeps two kurus digits and Turkish lira in all four locales',()=>{
 for(const lang of ['tr','en','ru','ar']){
  const output=formatMoney(1133895,lang);
  const parts=new Intl.NumberFormat(lang,{style:'currency',currency:'TRY',minimumFractionDigits:2,maximumFractionDigits:2}).formatToParts(11338.95);
  assert.ok(output.includes(parts.find(p=>p.type==='currency').value));
  assert.ok(output.includes(parts.find(p=>p.type==='fraction').value));
  assert.notEqual(output,formatMoney(11338,lang));
 }
 for(const invalid of [null,undefined,-1,1.5,'100',Number.MAX_SAFE_INTEGER+1])assert.equal(formatMoney(invalid,'en'),null);
 assert.equal(unitPriceMinor({...products[0],currency:'USD'}),null);
 assert.equal(unitPriceMinor({...products[0],salePriceMinor:'1133895'}),null);
 assert.equal(unitPriceMinor({...products[0],salePriceMinor:null,salePrice:11338.95}),null);
 assert.ok(formatMoney(Number.MAX_SAFE_INTEGER,'en').endsWith('.91'));
});

test('selected basket subtotal uses integer kurus and quantity without floating point drift',()=>{
 const sum=cartPrices([{id:'priced',quantity:3},{id:'small',quantity:7}],products);
 assert.equal(sum.subtotalMinor,3825262);
 assert.equal(sum.items[0].lineTotalMinor,3401685);
 assert.equal(sum.items[1].lineTotalMinor,423577);
 assert.equal(sum.unpricedCount,0);
 assert.equal(sum.quantity,10);
 const selected=cartPrices([{id:'small',quantity:7}],products);
 assert.equal(selected.subtotalMinor,423577);
});

test('unpriced lines stay unknown and mixed baskets report only a partial subtotal',()=>{
 const mixed=cartPrices([{id:'priced',quantity:2},{id:'unknown',quantity:5}],products);
 assert.equal(mixed.subtotalMinor,2267790);
 assert.equal(mixed.unpricedCount,1);
 assert.equal(mixed.items[1].lineTotalMinor,null);
 assert.equal(mixed.items[1].unitPriceMinor,null);
 assert.equal(cartPrices([{id:'unknown',quantity:5}],products).subtotalMinor,null);
 assert.equal(cartPrices([],products).subtotalMinor,null);
});

test('JSON product list preserves exact decimal amounts and identifies missing prices',()=>{
 const result=quoteData([{id:'priced',quantity:3},{id:'unknown',quantity:1}],products,'en');
 assert.equal(result.currency,'TRY');
 assert.equal(result.items[0].unitPrice,'11338.95');
 assert.equal(result.items[0].lineTotal,'34016.85');
 assert.equal(result.items[1].unitPrice,null);
 assert.equal(result.items[1].lineTotal,null);
 assert.equal(result.subtotal,'34016.85');
 assert.equal(result.subtotalType,'partial');
 assert.equal(result.unpricedItemCount,1);
});

test('text exports show actual unit and line prices plus partial subtotals in every locale',()=>{
 for(const lang of ['tr','en','ru','ar']){
  const output=quoteText([{id:'small',quantity:3},{id:'unknown',quantity:1}],products,lang);
  assert.ok(output.includes(formatMoney(60511,lang)));
  assert.ok(output.includes(formatMoney(181533,lang)));
  assert.ok(output.includes('Ndn-A-3'));
  assert.ok(!output.includes(formatMoney(0,lang)));
 }
});
