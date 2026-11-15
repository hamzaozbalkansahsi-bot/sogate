import test from 'node:test';import assert from 'node:assert/strict';
import {campaignStatus,campaignPreview} from '../web/admin-campaigns.js';
test('a saved campaign is never presented as an active published campaign',()=>{
 assert.equal(campaignStatus({version:1,publishedVersion:0,data:{enabled:true,startsAt:10,endsAt:100}},50).label,'Yayın bekliyor');
 const row={version:4,publishedVersion:3,publishedData:{enabled:true,startsAt:10,endsAt:100},activity:{status:'active',appliedProducts:1}};
 assert.equal(campaignStatus(row,50).label,'Aktif · değişiklik bekliyor');assert.equal(campaignStatus(row,101).label,'Sona erdi · değişiklik bekliyor');
 assert.equal(campaignStatus({version:2,publishedVersion:2,publishedData:{enabled:false,startsAt:10,endsAt:100}},50).label,'Devre dışı');
});
test('preview uses the published product base price and exact minor-unit rounding, never an already discounted price',()=>{
 const p=[{id:'2395',campaignBaseMinor:10001,priceMinor:7501,visible:true}];
 assert.deepEqual(campaignPreview({productIds:'2395',percent:30},p),[{id:'2395',baseMinor:10001,priceMinor:7001}]);
 assert.deepEqual(campaignPreview({productIds:'2395',percent:0},p),[]);
 assert.deepEqual(campaignPreview({productIds:'2395',percent:25},[{...p[0],visible:false}]),[]);
});
