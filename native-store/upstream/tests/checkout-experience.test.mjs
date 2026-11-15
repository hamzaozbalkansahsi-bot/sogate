import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {cleanCheckoutDraft,saveCheckoutDraft,loadCheckoutDraft,clearCheckoutDraft} from '../web/checkout-draft.js';
import {execFileSync} from 'node:child_process';
import path from 'node:path';
test('shipping markup applies exactly once to doors, measured fronts and addons, preserving furniture prices',()=>{
 const code="require 'hosting/payment-core.php';$c=['meta'=>['shippingPolicyVersion'=>'2026-11-12-included'],'products'=>[['id'=>'d','salePriceMinor'=>10000,'productType'=>'door','door'=>['charges'=>['glazing'=>1000]]],['id'=>'f','salePriceMinor'=>5000,'productType'=>'furniture']]];$a=nodenoShippingCatalog($c);echo json_encode([$a,nodenoShippingCatalog($a)]);";
 const [a,b]=JSON.parse(execFileSync(path.resolve('artifacts/runtime-php/php.exe'),['-r',code],{encoding:'utf8'}));assert.deepEqual(a,b);assert.equal(a.products[0].salePriceMinor,12000);assert.equal(a.products[0].door.charges.glazing,1200);assert.equal(a.products[1].salePriceMinor,5000);
});
test('checkout draft survives reload in the tab, excludes unrelated fields, and clears on identity change',()=>{
 const entries=new Map();globalThis.sessionStorage={setItem:(k,v)=>entries.set(k,v),getItem:k=>entries.get(k),removeItem:k=>entries.delete(k)};
 saveCheckoutDraft({details:{name:'Example',email:'test@example.test',sameBilling:false,cardNumber:'never-store-this'},review:{paid:true}});
 assert.deepEqual(loadCheckoutDraft(),{details:{name:'Example',email:'test@example.test',sameBilling:false},review:null});
 clearCheckoutDraft();assert.deepEqual(loadCheckoutDraft(),{details:{},review:null});assert.deepEqual(cleanCheckoutDraft(null),{details:{},review:null});delete globalThis.sessionStorage;
});

test('member refresh retains a long address while another identity cannot recover the draft',()=>{
 const entries=new Map();globalThis.sessionStorage={setItem:(k,v)=>entries.set(k,v),getItem:k=>entries.get(k),removeItem:k=>entries.delete(k)};const line1='A'.repeat(1000);
 saveCheckoutDraft({details:{line1}},'member-1');assert.equal(loadCheckoutDraft('member-1').details.line1,line1);assert.deepEqual(loadCheckoutDraft('member-2'),{details:{},review:null});assert.equal(entries.size,0);delete globalThis.sessionStorage;
});
test('card checkout redirects directly without an automatic agreement download or a second continue button',async()=>{
 const source=await readFile(new URL('../web/payments.js',import.meta.url),'utf8');
 assert.doesNotMatch(source,/download\.click\(|URL\.createObjectURL|data-payment-continue/);
 assert.match(source,/location\.assign\(url.href\)/);
});

test('shipping adjustment precedes VAT, preserves unknown prices and does not enable foreign card payments',()=>{
 const code="require 'hosting/payment-core.php';$c=['meta'=>['shippingPolicyVersion'=>'2026-11-12-included'],'products'=>[['id'=>'d','code'=>'D','name'=>'Door','currency'=>'TRY','salePriceMinor'=>10000,'productType'=>'door','door'=>['charges'=>[]]],['id'=>'unknown','salePriceMinor'=>null,'productType'=>'cabinet-front']]];$q=nodenoPaymentQuote($c,[['id'=>'d','quantity'=>5]],'TR');$a=nodenoShippingCatalog($c);$foreign='';try{nodenoPaymentQuote($c,[['id'=>'d','quantity'=>10]],'DE');}catch(InvalidArgumentException $e){$foreign=$e->getMessage();}echo json_encode([$q,$a['products'][1],$foreign]);";
 const [q,unknown,foreign]=JSON.parse(execFileSync(path.resolve('artifacts/runtime-php/php.exe'),['-r',code],{encoding:'utf8'}));assert.equal(q.netMinor,60000);assert.equal(q.vatMinor,12000);assert.equal(q.totalMinor,72000);assert.deepEqual(q.freight,{kind:'included',includedInCharge:true,feeMinor:0});assert.equal(unknown.salePriceMinor,null);assert.equal(foreign,'payment_country_not_supported');
});

test('new shipping terms change only section four and keep the version idempotent',()=>{
 const code="require 'hosting/payment-admin.php';$s=['termsVersion'=>'v1','terms'=>['tr'=>\"1. First\\n\\n4. Old freight\\nOld content\\n\\n5. Last\"]];$a=nodenoShippingSeller($s);echo json_encode([$a,nodenoShippingSeller($a)]);";
 const [a,b]=JSON.parse(execFileSync(path.resolve('artifacts/runtime-php/php.exe'),['-r',code],{encoding:'utf8'}));assert.deepEqual(a,b);assert.match(a.terms.tr,/Türkiye içi standart/);assert.match(a.terms.tr,/1\. First/);assert.match(a.terms.tr,/5\. Last/);assert.doesNotMatch(a.terms.tr,/Old freight/);
});

test('all native locale dictionaries cover every added shipping and legal source',async()=>{
 const extra=JSON.parse(await readFile('data/localization/checkout-shipping-20261112.json','utf8'));const root='artifacts/cpanel-release-checkout-experience-20261112/';
 for(const lang of ['de','az','kk','tk','uz','ky','fa'])for(const file of [`public/locales/${lang}.json`,`private/locale.${lang}.json`]){
  const dictionary=JSON.parse(await readFile(root+file,'utf8'));for(const [i,source]of extra.sources.entries())assert.equal(dictionary.translations[source],extra[lang][i]);assert.ok(dictionary.translations['Pre-contract information']);
 }
});
