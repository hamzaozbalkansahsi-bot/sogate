/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/test-native-variants.mjs
 * Açıklama   : Beden ve renk seçimi, sepet ayrımı ve eski sepetlerin güvenli davranışını doğrular.
 */
import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {selectionLine,normalizeSelectionCart,selectionDescription,mergeSelectionLine} from '../native-store/storefront/variants.js';
const p={id:'sg_test',variantSelection:{required:true,mode:'matrix',axes:[{id:'size',label:'Beden',values:[{id:'s',label:'S'},{id:'xl',label:'XL'}]},{id:'color',label:'Renk',values:[{id:'red',label:'Kırmızı'},{id:'black',label:'Siyah'}]}],variants:[{id:'v1',values:{size:'s',color:'red'},active:true},{id:'v2',values:{size:'xl',color:'black'},active:true},{id:'v3',values:{size:'xl',color:'red'},active:false}]}};
const line=(size='xl',color='black',quantity=1)=>({id:p.id,quantity,options:{selection:{size,color}}});
test('Seçim olmadan veya eksik seçimle eklenmez',()=>{assert.throws(()=>selectionLine(p,{id:p.id,quantity:1}));assert.throws(()=>selectionLine(p,{...line(),options:{selection:{size:'xl'}}}));});
test('Geçersiz kombinasyon, pasif varyant ve yabancı alan reddedilir',()=>{for(const item of [line('s','black'),line('xl','red'),{...line(),options:{selection:{size:'xl',color:'black'},price:1}},{...line(),key:'forged'}])assert.throws(()=>selectionLine(p,item));});
test('S ve XL ayrı; aynı seçimin miktarları birleşir',()=>{const rows=normalizeSelectionCart([line('s','red',2),line(),line('xl','black',3)],[p],x=>x);assert.equal(rows.length,2);assert.equal(rows[1].quantity,4);assert.notEqual(rows[0].key,rows[1].key);assert.equal(selectionDescription(p,rows[1],'tr'),'Beden: XL · Renk: Siyah');});
test('Eski belirsiz sepet sessizce beden seçmez',()=>{const rows=normalizeSelectionCart([{id:p.id,quantity:2}],[p],x=>x);assert.equal(rows[0].pendingSelection,true);assert.equal(rows[0].options,undefined);assert.throws(()=>selectionLine(p,rows[0]));});
test('Seçim değişikliği yalnız ilgili satırı değiştirir ve aynı varyantla birleşir',()=>{const a=selectionLine(p,line('s','red',2)),b=selectionLine(p,line('xl','black',3));const rows=mergeSelectionLine([a,b],selectionLine(p,line('xl','black',2)),a.key);assert.equal(rows.length,1);assert.equal(rows[0].quantity,5);assert.equal(rows[0].options.selection.size,'xl');});
test('Stok veya tedarikçi SKU uydurulmadan bağımsız kaynak seçenekleri doğrulanır',()=>{const product={...p,variantSelection:{...p.variantSelection,mode:'options',variants:[]}};assert.equal(selectionLine(product,line('s','black')).options.selection.color,'black');assert.throws(()=>selectionLine(product,line('XXL','black')));});
test('Diğer çekirdeğin miktar kuralları korunur',()=>{const original=rows=>[{...rows[0],quantity:rows.reduce((sum,row)=>sum+row.quantity,0)}];assert.equal(normalizeSelectionCart([{id:'door',quantity:500},{id:'door',quantity:200}],[{id:'door'}],original)[0].quantity,700);});
test('Seçim metinleri bütün açık dillerde tam ve UTF-8 kalır',()=>{const copy=JSON.parse(fs.readFileSync(new URL('../native-store/storefront/variant-copy.json',import.meta.url),'utf8'));assert.deepEqual(Object.keys(copy).sort(),['tr','en','de','ru','ar','fa','az','kk','tk','uz','ky'].sort());for(const values of Object.values(copy)){assert.deepEqual(Object.keys(values).sort(),Object.keys(copy.tr).sort());for(const value of Object.values(values))assert.ok(typeof value==='string'&&value.trim()&&!value.includes('\uFFFD'));}});
