import test from 'node:test';
import assert from 'node:assert/strict';
import * as app from '../web/app.js';
test('the cabinet-front home shelf uses its exact category regardless of similarly named storage categories',()=>{
 const front={id:'dolap-kapaklari',name:{tr:'Dolap kapakları'}};
 assert.equal(app.homeFrontCategory?.({categories:[{id:'dolaplar',name:{tr:'Dolaplar'}},{id:'kitapliklar',name:{tr:'Kitaplıklar'}},front]}),front);
 assert.equal(app.homeFrontCategory?.({categories:[{id:'dolaplar',name:{tr:'Dolaplar'}}]}),null);
});
