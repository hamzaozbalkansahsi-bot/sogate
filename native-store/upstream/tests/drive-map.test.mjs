import test from 'node:test';
import assert from 'node:assert/strict';
import {selectDriveMappings} from '../lib/drive-map.mjs';
const url='https://witcdn.adoremobilya.com/real.jpg';
const valid={fileId:'valid-file-id-123',folderId:'valid-folder-id-123',status:'uploaded',verifiedAt:'2026-10-31T12:00:00Z',sha256:'a'.repeat(64),md5:'b'.repeat(32),mimeType:'image/jpeg',size:1234,sourceUrl:url};
test('only verified uploads for the same catalog image can replace source media',()=>{
 const data={images:{'1:0':valid,'1:1':{...valid,status:'reserved'},'1:2':{...valid,sourceUrl:'https://witcdn.adoremobilya.com/stale.jpg'},'1:3':{...valid,verifiedAt:null}}};
 assert.deepEqual(Object.keys(selectDriveMappings(data,{'1':[url,url,url,url]})),['1:0']);
 assert.equal(selectDriveMappings(data,{'1':[url]})['1:0'].fileId,'valid-file-id-123');
});
