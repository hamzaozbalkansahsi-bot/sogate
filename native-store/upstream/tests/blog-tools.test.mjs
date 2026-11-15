import test from 'node:test';
import assert from 'node:assert/strict';
import { paintEstimate, spaceEstimate, paletteFrom } from '../web/blog-tools.js';

test('paint estimate subtracts openings and applies per-coat coverage once per coat',()=>{
 const x=paintEstimate({length:4,width:3,height:2.5,openings:2,coats:2,coverage:10,basis:'coat',waste:0});
 assert.equal(x.area,33);assert.equal(x.litres,6.6);
});
test('coverage already specified for the full system is not multiplied again',()=>{
 const x=paintEstimate({length:4,width:3,height:2.5,openings:2,coats:2,coverage:10,basis:'system',waste:10});
 assert.equal(x.litres,3.63);
});
test('invalid numbers and openings larger than the gross surface are rejected',()=>{
 for(const patch of [{length:0},{width:Infinity},{openings:99},{coats:0},{coverage:0},{waste:-1},{basis:'made-up'}]) assert.throws(()=>paintEstimate({length:4,width:3,height:2.5,openings:2,coats:2,coverage:10,basis:'coat',waste:0,...patch}));
});
test('space estimate reports the actual remaining gap and an impossible fit',()=>{
 assert.deepEqual(spaceEstimate({room:300,furniture:180,opposite:50}),{remaining:70,fits:true});
 assert.deepEqual(spaceEstimate({room:200,furniture:180,opposite:50}),{remaining:-30,fits:false});
 assert.throws(()=>spaceEstimate({room:300,furniture:-1,opposite:0}));
});
test('palette keeps a valid input colour and produces valid independent swatches',()=>{
 const x=paletteFrom('#8A8249');assert.equal(x[0],'#8A8249');assert.equal(x.length,4);assert.equal(new Set(x).size,4);for(const c of x)assert.match(c,/^#[0-9A-F]{6}$/);assert.throws(()=>paletteFrom('<script>'));
});
