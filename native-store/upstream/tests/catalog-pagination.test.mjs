import test from'node:test';import assert from'node:assert/strict';
import{catalogPage,catalogPagination}from'../web/catalog-pagination.js';
test('page two starts after 24 records and rejects malformed and beyond-final requests',()=>{
 assert.deepEqual(catalogPage(50,'2'),{page:2,pages:3,offset:24,valid:true});
 for(const value of ['0','02','-1','2abc','1e2','9999999','4'])assert.equal(catalogPage(50,value).valid,false,value);
});
test('pagination has real links, one currentpage and localized accessible labels',()=>{
 const s=catalogPagination(250,'2','ar',p=>'/?page=catalog&pg='+p,v=>String(v).replaceAll('&','&amp;'));
 assert.match(s,/href="\/\?page=catalog&amp;pg=3"/);assert.equal((s.match(/aria-current="page"/g)||[]).length,1);assert.match(s,/الصفحة التالية/);assert.equal(catalogPagination(4,'','tr',()=>'',String),'');
});
