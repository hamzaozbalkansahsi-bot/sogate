import test from 'node:test';import assert from 'node:assert/strict';
import {paintRecommendations} from '../web/paint-recommendations.js';
const paint=(id,surface='wood',family=id)=>({id,modelId:family,productBrand:'Bianca',productType:'supplier-item',salePriceMinor:1000,images:['/approved.jpg'],paintUse:{directUnpainted:[surface]}});
test('unpainted material match is explicit and never treats finished furniture or unknown surfaces as raw',()=>{
 const rows=[paint('a'),paint('b','metal'),paint('c','mdf')];assert.deepEqual(paintRecommendations({finishState:'unpainted',paintSurface:'wood'},rows).map(p=>p.id),['a']);
 for(const p of [{},{paintSurface:'wood'},{finishState:'finished',paintSurface:'wood'},{finishState:'unpainted',paintSurface:'unknown'}])assert.equal(paintRecommendations(p,rows).length,0);
});
test('paint suggestions collapse colour variants and exclude hidden, unavailable and indirect coats',()=>{
 const rows=[paint('a','wood','same'),paint('b','wood','same'),{...paint('hidden'),hidden:true},{...paint('price'),salePriceMinor:null},{...paint('topcoat'),paintUse:{directUnpainted:[]}}];
 assert.deepEqual(paintRecommendations({finishState:'unpainted',paintSurface:'wood'},rows).map(p=>p.id),['a']);
});
