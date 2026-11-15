import test from 'node:test';
import assert from 'node:assert/strict';
import {doorOptions,doorLineKey,doorPrice,doorMinimum,doorCartStatus,convertTryMinor} from '../web/door-core.js';

const door={id:'door-nd683-1',salePriceMinor:696500,currency:'TRY',productType:'door',door:{kind:'interior',finishGroup:'pvc-soft',glassAvailable:true,charges:{depth:{17:18000,19:30000,21:45500},architrave18:66000,glazing:99000,hardware:50000}}};
test('source-based door options add known surcharges once per set',()=>{
 const options=doorOptions({frameDepth:19,architrave18:true,glazed:true,hardware:true},door);
 const price=doorPrice(door,options);
 assert.equal(price.unitPriceMinor,941500);assert.equal(price.requiresQuote,false);
 assert.equal(doorPrice(door,{}).unitPriceMinor,696500);
});
test('special heights, handles and veneer painting require a quote instead of invented charges',()=>{
 for(const options of [{height:212},{handle:true},{openingWidthMm:900}])assert.equal(doorPrice(door,options).requiresQuote,true);
 assert.equal(doorPrice({...door,door:{...door.door,finishGroup:'veneer'}},{}).requiresQuote,true);
 assert.equal(doorPrice({...door,salePriceMinor:null},{}).unitPriceMinor,null);
});
test('configurations have stable separate identities and reject unknown or invalid choices',()=>{
 assert.equal(doorLineKey(door.id,doorOptions({},door)),doorLineKey(door.id,doorOptions({},door)));
 assert.notEqual(doorLineKey(door.id,doorOptions({},door)),doorLineKey(door.id,doorOptions({frameDepth:21},door)));
 for(const value of [{frameDepth:16},{hardware:'true'},{price:1},{height:NaN},{openingWidthMm:-1}])assert.throws(()=>doorOptions(value,door));
});
test('minimum counts mixed door sets only and uses delivery country',()=>{
 const profile={id:'profile-sp1003',productType:'door-profile'};
 assert.equal(doorMinimum('TR'),5);assert.equal(doorMinimum('DE'),10);assert.throws(()=>doorMinimum(''));
 assert.equal(doorCartStatus([{id:door.id,quantity:4},{id:profile.id,quantity:100}], [door,profile],'TR').eligible,false);
 assert.equal(doorCartStatus([{id:door.id,quantity:5}], [door],'TR').eligible,true);
 assert.equal(doorCartStatus([{id:door.id,quantity:5}], [door],'DE').missing,5);
 assert.equal(doorCartStatus([{id:profile.id,quantity:2}], [profile],'DE').eligible,true);
});
test('foreign money uses exact weekly selling rates including currency unit and rounding',()=>{
 assert.equal(convertTryMinor(550000,{rateMicros:55000000,unit:1},2),10000);
 assert.equal(convertTryMinor(550000,{rateMicros:50000000,unit:1},2),11000);
 assert.equal(convertTryMinor(50000,{rateMicros:25000000,unit:100},0),2000);
 assert.equal(convertTryMinor(1,{rateMicros:2000000,unit:1},2),1);
 assert.throws(()=>convertTryMinor(500,{rateMicros:0,unit:1},2));
});
