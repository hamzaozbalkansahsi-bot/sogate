import test from 'node:test';import assert from 'node:assert/strict';import {supplierBoundPrice} from '../lib/supplier-catalog.mjs';
test('paint markup is exactly 30 percent while older wood suppliers retain 20 percent',()=>{
 assert.equal(supplierBoundPrice({id:'alka-old'},{sourcePriceMinor:10001}),12001);
 assert.equal(supplierBoundPrice({id:'paint-ty-123'},{sourcePriceMinor:199900,markupPercent:30,platform:'trendyol',sourceUrl:'https://www.trendyol.com/bianca/test-p-123?merchantId=42'}),259870);
 assert.throws(()=>supplierBoundPrice({id:'alka-old'},{sourcePriceMinor:10000,markupPercent:30,platform:'trendyol',sourceUrl:'https://www.trendyol.com/x-p-123?merchantId=42'}));
 assert.throws(()=>supplierBoundPrice({id:'paint-ty-123'},{sourcePriceMinor:10000,markupPercent:30,platform:'trendyol',sourceUrl:'https://evil.test/x-p-123?merchantId=42'}));
});
