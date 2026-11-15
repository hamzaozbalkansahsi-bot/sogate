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
