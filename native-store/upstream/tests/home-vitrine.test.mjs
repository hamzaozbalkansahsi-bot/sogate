import test from 'node:test';
import assert from 'node:assert/strict';
import {vitrineProducts,renderHomeVitrine,mountHomeVitrine} from '../web/home-vitrine.js';
test('the homepage never promotes hidden, unpublished, duplicate or unpictured products',()=>{
 const hero={id:'a',images:['/a']},rows={a:hero,b:{id:'b',images:['/b'],hidden:true},c:{id:'c',images:[]},d:{id:'d',images:['/d'],published:false},e:{id:'e',images:['/e']}};
 assert.deepEqual(vitrineProducts(hero,['a','b','c','d','e','unknown'].map(product=>({product})),id=>rows[id]).map(r=>r.product.id),['a','e']);
});
test('an entirely unavailable selection renders nothing and creates no carousel timers',()=>{
 assert.equal(renderHomeVitrine({hero:null,campaigns:[],byId:()=>null,locale:'tr',esc:String,t:String}), '');
 assert.equal(typeof mountHomeVitrine(null),'function');
});
