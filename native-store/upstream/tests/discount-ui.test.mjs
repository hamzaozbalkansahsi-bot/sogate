import test from 'node:test';
import assert from 'node:assert/strict';
import {discountInfo,formatDiscount,quoteData,quoteText,formatMoney,cartPrices} from '../web/shop-core.js';
import {shopTranslate} from '../web/shop-i18n.js';

const product={id:'1',code:'Ndn-REAL-1',name:{tr:'Dolap',en:'Cabinet',ru:'Шкаф',ar:'خزانة'},currency:'TRY',salePriceMinor:90000,previousPriceMinor:100000};

test('discount display requires a valid earlier price above the current actual price',()=>{
 assert.deepEqual(discountInfo(product),{previousPriceMinor:100000,salePriceMinor:90000,discountPercent:10});
 for(const previous of [undefined,null,'100000',0,-1,90000,89999,100000.5,Number.MAX_SAFE_INTEGER])assert.equal(discountInfo({...product,previousPriceMinor:previous}),null);
 for(const invalid of [{currency:'USD'},{salePriceMinor:null},{salePriceMinor:0},{salePriceMinor:'90000'}])assert.equal(discountInfo({...product,...invalid}),null);
 assert.equal(discountInfo({...product,previousPriceMinor:undefined,discountPercent:90,retailPrice:100000}),null);
});

test('discount percent derives from exact amounts and tolerates currency rounding without a false free offer',()=>{
 assert.equal(discountInfo({...product,previousPriceMinor:1133895,salePriceMinor:1020506,discountPercent:99}).discountPercent,10);
 assert.equal(discountInfo({...product,previousPriceMinor:10000,salePriceMinor:9050}).discountPercent,9);
 assert.equal(discountInfo({...product,previousPriceMinor:10000,salePriceMinor:9440}).discountPercent,5);
 assert.equal(discountInfo({...product,previousPriceMinor:10000,salePriceMinor:8000}).discountPercent,20);
 assert.equal(discountInfo({...product,previousPriceMinor:10000,salePriceMinor:9999}).discountPercent,0);
 assert.equal(discountInfo({...product,previousPriceMinor:10000,salePriceMinor:1}).discountPercent,99);
 for(const lang of ['tr','en','ru','ar']){
  const label=formatDiscount(10,lang);
  assert.ok(label.includes(new Intl.NumberFormat(lang,{style:'percent',maximumFractionDigits:0}).format(.1)));
  assert.notEqual(shopTranslate('previousPrice',lang),'previousPrice');
  assert.notEqual(shopTranslate('salePrice',lang),'salePrice');
 }
 for(const invalid of [null,0,-1,100,'10',10.5])assert.equal(formatDiscount(invalid,'tr'),null);
});

test('previous prices are disclosed in four-language exports while basket totals use only the current sale price',()=>{
 const basket=[{id:'1',quantity:3}],data=quoteData(basket,[product],'en'),item=data.items[0];
 assert.equal(item.previousUnitPriceMinor,100000);assert.equal(item.previousUnitPrice,'1000.00');
 assert.equal(item.unitPriceMinor,90000);assert.equal(item.unitPrice,'900.00');
 assert.equal(item.previousLineTotalMinor,300000);assert.equal(item.previousLineTotal,'3000.00');
 assert.equal(item.lineTotalMinor,270000);assert.equal(item.discountPercent,10);
 assert.equal(data.subtotalMinor,270000);assert.equal(cartPrices(basket,[product]).subtotalMinor,270000);
 for(const lang of ['tr','en','ru','ar']){
  const output=quoteText(basket,[product],lang);
  assert.ok(output.includes(shopTranslate('previousUnitPrice',lang)));
  assert.ok(output.includes(formatMoney(100000,lang)));
  assert.ok(output.includes(formatMoney(90000,lang)));
  assert.ok(output.includes(formatDiscount(10,lang)));
 }
});

test('ordinary and invalid-reference prices do not create discount claims in exports',()=>{
 const ordinary={...product,previousPriceMinor:undefined,discountPercent:50};
 const item=quoteData([{id:'1',quantity:1}],[ordinary],'tr').items[0];
 assert.equal(item.previousUnitPriceMinor,undefined);assert.equal(item.discountPercent,undefined);
 for(const lang of ['tr','en','ru','ar']){
  const output=quoteText([{id:'1',quantity:1}],[ordinary],lang);
  assert.ok(!output.includes(shopTranslate('previousUnitPrice',lang)));
  assert.ok(!output.includes(formatDiscount(50,lang)));
 }
});
