/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/test-native-relocation.mjs
 * Açıklama   : Alt yol derlemesinde URL'leri taşırken yol ayraçlarının korunmasını doğrular.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import {relocateJs,relocateText,MOUNT} from '../native-store/deploy/relocate.mjs';
test('account helper suffixes remain relative while the helper fetch root is mounted',()=>{
 const source="async function api(path){return fetch('/api/account'+path);}api('/social');api('/state','PUT');api('/addresses');";
 const out=relocateJs(source);assert.ok(out.includes("fetch('"+MOUNT+"/api/account'+path)"));assert.ok(out.includes("api('/social')"));assert.ok(out.includes("api('/state','PUT')"));assert.ok(out.includes("api('/addresses')"));
 assert.equal(relocateJs(out),out);
});
test('account address identifiers and conditional auth actions retain their helper-relative paths',()=>{
 const source="async function api(path){return fetch('/api/account'+path);}api('/addresses/'+id);api(register?'/register':'/login','POST');api(`/orders/${id}`);";
 const out=relocateJs(source);assert.ok(out.includes("api('/addresses/'+id)"));assert.ok(out.includes("api(register?'/register':'/login','POST')"));assert.ok(out.includes('api(`/orders/${id}`)'));assert.equal(relocateJs(out),out);
});
test('root navigation and API URLs relocate while child separators and date delimiters stay unchanged',()=>{
 const code="const url=new URL('/',location.origin);const data=fetch('/api/catalog');const child='/'+id;const parts=value.split('/');";
 const out=relocateJs(code);assert.ok(out.includes("new URL('"+MOUNT+"/',location.origin)"));assert.ok(out.includes("fetch('"+MOUNT+"/api/catalog')"));assert.ok(out.includes("const child='/'+id"));assert.ok(out.includes("value.split('/')"));
});
test('template endpoints and embedded HTML resources receive one mount prefix',()=>{
 const out=relocateJs('const url=`/api/items/${id}`;const view=`<img src="/assets/logo.svg">`;');assert.ok(out.includes('`'+MOUNT+'/api/items/${id}`'));assert.ok(out.includes('src="'+MOUNT+'/assets/logo.svg"'));assert.equal(relocateJs(out),out);
});
test('own host relocates and external provider URLs remain untouched',()=>{
 const out=relocateText('https://nodenohome.com/blog https://accounts.google.com/auth');assert.ok(out.includes('https://sexogate.com'+MOUNT+'/blog'));assert.ok(out.includes('https://accounts.google.com/auth'));
});
test('admin child actions stay relative after encoded identifiers and conditional concatenation',()=>{
 const code="api(route+'/'+encodeURIComponent(id)+'/editor');api(route+(id?'/'+id:'')+(publish?'/save-publish':''));const url='/api/admin/'+id+'/editor';";
 const out=relocateJs(code);assert.ok(out.includes("encodeURIComponent(id)+'/editor'"));assert.ok(out.includes("publish?'/save-publish':''"));assert.ok(out.includes("url='"+MOUNT+"/api/admin/'+id+'/editor'"));
});
test('both media allowlist expressions relocate so product images render beneath the mount',()=>{
 const code=String.raw`const source=/^\/media\/[a-z]+\/\d+$/;const path=/^\/media\/[a-z]+\/\d+$/;`;
 const out=relocateJs(code);assert.equal(out.split(String.raw`/^\/__SEXOGATE_MOUNT__\/media\/`).length-1,2);assert.ok(!out.includes(String.raw`/^\/media\/`));
});
