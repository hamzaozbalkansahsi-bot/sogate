import test from 'node:test';import assert from 'node:assert/strict';
import {supplierQuantity,supplierPolicy,supplierPriceSuffix,supplierTaxNote} from '../web/supplier-products.js';
test('minimum linear metres and increments are enforced',()=>{const p={productType:'supplier-item',quantityPolicy:{unit:'metre',minimum:3,step:3}};assert.equal(supplierQuantity(1,p),3);assert.equal(supplierQuantity(4,p),6);assert.equal(supplierQuantity(100,p),99);assert.equal(supplierPriceSuffix(p,'en'),' / linear metre');});
test('gross supplier offer is not labelled net',()=>{assert.equal(supplierTaxNote({productType:'supplier-item',priceTaxPolicy:'vat_included'},'en'),'VAT included');assert.equal(supplierTaxNote({productType:'supplier-item',priceTaxPolicy:'unspecified'},'en'),'');});
test('existing quantities keep their usual policy',()=>assert.deepEqual(supplierPolicy({}),{minimum:1,step:1,maximum:99}));
