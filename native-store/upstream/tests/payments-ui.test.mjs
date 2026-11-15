import test from 'node:test';import assert from 'node:assert/strict';
import {paymentContext,paymentItems,paymentText} from '../web/payments.js';
import * as paymentView from '../web/payments.js';
test('the current checkout protocol redirects directly with the revised consent protocol',()=>{assert.equal(paymentView.paymentDocumentFlowVersion,2);});
test('contract copy URLs remain same-origin and copy/continue actions are translated',()=>{
 assert.equal(paymentView.paymentDocumentPath?.('/api/payments/order/'+'a'.repeat(64)+'/documents'),'/api/payments/order/'+'a'.repeat(64)+'/documents');
 for(const bad of ['https://evil.example/file','//evil.example','/api/payments/order/x/documents'])assert.throws(()=>paymentView.paymentDocumentPath(bad));
 for(const lang of ['tr','en','ru','ar'])for(const key of ['documentCopy','documentSaved','continuePayment','privacyNotice'])assert.notEqual(paymentText(lang,key),key);
});
test('payment context requires the current validated review and changes on account, address, route and basket edits',()=>{
 const s={page:'checkout',step:'review',owner:'guest',items:[{id:'p1',quantity:1}],contact:{email:'buyer@example.test'}};
 assert.ok(paymentContext(s));for(const patch of [{step:'details'},{page:'cart'},{owner:'other'},{items:[{id:'p1',quantity:2}]},{contact:{email:'other@example.test'}}])assert.notEqual(paymentContext({...s,...patch}),paymentContext(s));
 assert.equal(paymentContext({...s,step:'details'}),null);
 assert.deepEqual(paymentItems([{id:'p1',quantity:1,unitPriceMinor:1}]),[{id:'p1',quantity:1}]);
 for(const lang of ['tr','en','ru','ar'])assert.notEqual(paymentText(lang,'ready'), 'ready');
});

test('payment result distinguishes returned, partial, pending and failed refunds from awaiting payment',()=>{
 for(const [status,refund,want]of [['paid',null,'paid'],['refunded','succeeded','refunded'],['partially_refunded','succeeded','partiallyRefunded'],['paid','pending','refundPending'],['paid','failed','refundFailed'],['pending',null,'pending'],['expired',null,'expired']])assert.equal(paymentView.paymentResultKey?.(status,refund),want);
 for(const lang of ['tr','en','ru','ar'])for(const key of ['refunded','partiallyRefunded','refundPending','refundFailed','refundAmount'])assert.notEqual(paymentText(lang,key),key);
});
